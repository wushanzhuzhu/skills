#!/usr/bin/env python3
"""
错误处理模块 - MCP Client Skill错误处理和重试机制
提供分层错误处理、智能重试、熔断器等功能
"""

import time
import logging
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
import traceback
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum

class ErrorLevel(Enum):
    """错误级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """错误类别"""
    NETWORK = "network"
    SESSION = "session"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    BUSINESS = "business"
    SYSTEM = "system"

@dataclass
class ErrorInfo:
    """错误信息"""
    category: ErrorCategory
    level: ErrorLevel
    message: str
    exception: Exception
    context: Dict[str, Any]
    timestamp: float
    retryable: bool = True
    max_retries: int = 3

class CircuitBreaker:
    """
    熔断器 - 防止级联失败
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """通过熔断器调用函数"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logging.info("🔧 熔断器状态: HALF_OPEN")
            else:
                raise Exception("熔断器开启，拒绝调用")
        
        try:
            result = func(*args, **kwargs)
            
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                logging.info("✅ 熔断器状态: CLOSED")
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logging.warning(f"🚨 熔断器状态: OPEN (失败次数: {self.failure_count})")
            
            raise e

class RetryManager:
    """
    重试管理器 - 智能重试机制
    """
    
    def __init__(self):
        self.circuit_breakers = {}
        
    def get_circuit_breaker(self, key: str) -> CircuitBreaker:
        """获取熔断器"""
        if key not in self.circuit_breakers:
            self.circuit_breakers[key] = CircuitBreaker()
        return self.circuit_breakers[key]
    
    def retry_with_backoff(self, func: Callable, max_retries: int = 3, 
                         base_delay: float = 1.0, backoff_factor: float = 2.0,
                         circuit_breaker_key: str = None, *args, **kwargs) -> Any:
        """
        指数退避重试策略
        
        Args:
            func: 要重试的函数
            max_retries: 最大重试次数
            base_delay: 基础延迟时间
            backoff_factor: 退避因子
            circuit_breaker_key: 熔断器键名
        """
        last_exception = None
        
        # 使用熔断器（如果指定）
        if circuit_breaker_key:
            circuit_breaker = self.get_circuit_breaker(circuit_breaker_key)
            return circuit_breaker.call(
                self._execute_with_retry,
                func, max_retries, base_delay, backoff_factor, *args, **kwargs
            )
        
        return self._execute_with_retry(func, max_retries, base_delay, backoff_factor, *args, **kwargs)
    
    def _execute_with_retry(self, func: Callable, max_retries: int, 
                           base_delay: float, backoff_factor: float, *args, **kwargs) -> Any:
        """执行重试逻辑"""
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    delay = base_delay * (backoff_factor ** attempt)
                    logging.warning(f"🔄 重试 {attempt + 1}/{max_retries}，{delay:.1f}秒后重试: {str(e)}")
                    time.sleep(delay)
                else:
                    logging.error(f"❌ 重试失败，已达最大重试次数: {max_retries}")
        
        raise last_exception

class ErrorHandler:
    """
    错误处理器 - 分层错误处理和分类
    """
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.retry_manager = RetryManager()
        self.error_history = []
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(f"{__name__}.ErrorHandler")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def classify_error(self, exception: Exception, context: Dict = None) -> ErrorInfo:
        """分类错误并生成错误信息"""
        error_message = str(exception)
        context = context or {}
        
        # 基于错误消息和类型分类
        if "connection" in error_message.lower() or "network" in error_message.lower():
            category = ErrorCategory.NETWORK
            level = ErrorLevel.HIGH
            retryable = True
            max_retries = 3
            
        elif "session" in error_message.lower() or "未保存" in error_message:
            category = ErrorCategory.SESSION
            level = ErrorLevel.MEDIUM
            retryable = True
            max_retries = 2
            
        elif "authentication" in error_message.lower() or "权限" in error_message:
            category = ErrorCategory.AUTHENTICATION
            level = ErrorLevel.HIGH
            retryable = False
            max_retries = 0
            
        elif "验证" in error_message.lower() or "不存在" in error_message or "缺少" in error_message:
            category = ErrorCategory.VALIDATION
            level = ErrorLevel.LOW
            retryable = False
            max_retries = 0
            
        elif "资源" in error_message.lower() or "空间" in error_message.lower():
            category = ErrorCategory.BUSINESS
            level = ErrorLevel.MEDIUM
            retryable = True
            max_retries = 1
            
        else:
            category = ErrorCategory.SYSTEM
            level = ErrorLevel.CRITICAL
            retryable = True
            max_retries = 2
        
        error_info = ErrorInfo(
            category=category,
            level=level,
            message=error_message,
            exception=exception,
            context=context,
            timestamp=time.time(),
            retryable=retryable,
            max_retries=max_retries
        )
        
        # 记录错误历史
        self.error_history.append(error_info)
        
        return error_info
    
    def handle_error(self, exception: Exception, context: Dict = None) -> Dict[str, Any]:
        """
        处理错误并生成标准化响应
        
        Args:
            exception: 异常对象
            context: 上下文信息
            
        Returns:
            Dict: 标准化错误响应
        """
        error_info = self.classify_error(exception, context)
        
        # 记录错误
        self._log_error(error_info)
        
        # 生成错误响应
        error_response = {
            "success": False,
            "error": {
                "category": error_info.category.value,
                "level": error_info.level.value,
                "message": error_info.message,
                "retryable": error_info.retryable,
                "max_retries": error_info.max_retries,
                "context": error_info.context
            },
            "timestamp": error_info.timestamp
        }
        
        # 添加恢复建议
        recovery_suggestion = self._get_recovery_suggestion(error_info)
        if recovery_suggestion:
            error_response["recovery_suggestion"] = recovery_suggestion
        
        return error_response
    
    def _log_error(self, error_info: ErrorInfo):
        """记录错误日志"""
        log_level_map = {
            ErrorLevel.LOW: logging.INFO,
            ErrorLevel.MEDIUM: logging.WARNING,
            ErrorLevel.HIGH: logging.ERROR,
            ErrorLevel.CRITICAL: logging.CRITICAL
        }
        
        level = log_level_map.get(error_info.level, logging.ERROR)
        
        log_message = (
            f"[{error_info.category.value.upper()}] "
            f"{error_info.message} "
            f"(Context: {error_info.context})"
        )
        
        self.logger.log(level, log_message)
        
        if error_info.level == ErrorLevel.CRITICAL:
            self.logger.debug(f"Critical error traceback:\n{traceback.format_exc()}")
    
    def _get_recovery_suggestion(self, error_info: ErrorInfo) -> Optional[str]:
        """获取错误恢复建议"""
        suggestions = {
            ErrorCategory.NETWORK: "检查网络连接，确认服务地址正确，尝试稍后重试",
            ErrorCategory.SESSION: "重新建立会话，检查认证信息是否正确",
            ErrorCategory.AUTHENTICATION: "检查用户名和密码，确认账号权限正确",
            ErrorCategory.VALIDATION: "检查输入参数格式和完整性，参考API文档",
            ErrorCategory.BUSINESS: "检查资源可用性，可能需要释放资源或联系管理员",
            ErrorCategory.SYSTEM: "联系系统管理员，提供详细错误信息"
        }
        
        base_suggestion = suggestions.get(error_info.category, "")
        
        if error_info.retryable:
            return f"{base_suggestion} (可重试 {error_info.max_retries} 次)"
        else:
            return base_suggestion
    
    def execute_with_error_handling(self, func: Callable, *args, 
                                   circuit_breaker_key: str = None,
                                   max_retries: int = 3, **kwargs) -> Dict[str, Any]:
        """
        带错误处理的函数执行
        
        Args:
            func: 要执行的函数
            circuit_breaker_key: 熔断器键名
            max_retries: 最大重试次数
        """
        try:
            # 获取错误分类以确定重试策略
            def execute_func():
                return func(*args, **kwargs)
            
            # 如果可以重试，使用重试管理器
            error_info = self.classify_error(Exception("dummy"), {})
            if error_info.retryable and max_retries > 0:
                result = self.retry_manager.retry_with_backoff(
                    execute_func, 
                    max_retries=max_retries,
                    circuit_breaker_key=circuit_breaker_key
                )
            else:
                result = execute_func()
            
            return {
                "success": True,
                "data": result,
                "execution_info": {
                    "circuit_breaker_used": circuit_breaker_key is not None,
                    "retries_attempted": 0
                }
            }
            
        except Exception as e:
            context = {
                "function": func.__name__ if hasattr(func, '__name__') else str(func),
                "args": str(args)[:100],  # 限制长度
                "circuit_breaker_key": circuit_breaker_key
            }
            
            return self.handle_error(e, context)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        if not self.error_history:
            return {"total_errors": 0}
        
        # 按类别统计
        category_stats = {}
        level_stats = {}
        
        for error_info in self.error_history:
            # 类别统计
            category = error_info.category.value
            category_stats[category] = category_stats.get(category, 0) + 1
            
            # 级别统计
            level = error_info.level.value
            level_stats[level] = level_stats.get(level, 0) + 1
        
        # 熔断器状态
        circuit_breaker_stats = {}
        for key, breaker in self.retry_manager.circuit_breakers.items():
            circuit_breaker_stats[key] = {
                "state": breaker.state,
                "failure_count": breaker.failure_count,
                "threshold": breaker.failure_threshold
            }
        
        return {
            "total_errors": len(self.error_history),
            "category_distribution": category_stats,
            "level_distribution": level_stats,
            "circuit_breakers": circuit_breaker_stats,
            "most_common_error": max(category_stats.items(), key=lambda x: x[1]) if category_stats else None
        }
    
    def clear_error_history(self):
        """清空错误历史"""
        self.error_history.clear()
        self.logger.info("📋 错误历史已清空")


# 全局错误处理器实例
global_error_handler = ErrorHandler()

def handle_error(exception: Exception, context: Dict = None) -> Dict[str, Any]:
    """全局错误处理函数"""
    return global_error_handler.handle_error(exception, context)

def execute_with_error_handling(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """全局错误处理执行函数"""
    return global_error_handler.execute_with_error_handling(func, *args, **kwargs)

def get_error_statistics() -> Dict[str, Any]:
    """获取全局错误统计"""
    return global_error_handler.get_error_statistics()