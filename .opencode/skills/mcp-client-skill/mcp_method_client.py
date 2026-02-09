#!/usr/bin/env python3
"""
MCP Method Client - MCP方法调用客户端
提供Skill调用MCP Server方法的统一封装接口
"""

import sys
import time
import json
import logging
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

# 添加主项目路径
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

@dataclass
class MCPCallResult:
    """MCP调用结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    method_name: str = ""
    parameters: Dict = None
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "method_name": self.method_name,
            "parameters": self.parameters
        }

class MCPMethodClient:
    """
    MCP方法调用客户端
    
    提供Skill调用MCP Server方法的统一接口：
    - 方法调用封装
    - 参数验证和处理
    - 结果标准化
    - 错误处理
    - 性能监控
    """
    
    def __init__(self, auto_session: bool = True):
        self.logger = self._setup_logger()
        self.auto_session = auto_session
        self.session_manager = None
        self._method_registry = self._register_mcp_methods()
        
        # 性能统计
        self.call_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "methods_used": {}
        }
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(f"{__name__}.MCPMethodClient")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _register_mcp_methods(self) -> Dict:
        """注册所有可用的MCP方法"""
        methods = {
            # 会话管理
            'getSession': {
                'module': 'main',
                'function': 'getSession',
                'description': '建立MCP会话',
                'parameters': ['url', 'name', 'password'],
                'required_params': ['url']
            },
            
            # 系统状态查询
            'get_audit': {
                'module': 'main',
                'function': 'get_audit',
                'description': '获取认证信息',
                'parameters': [],
                'required_params': []
            },
            
            'get_clusterStor': {
                'module': 'main',
                'function': 'get_clusterStor',
                'description': '获取集群存储信息',
                'parameters': [],
                'required_params': []
            },
            
            # 资源查询
            'get_image': {
                'module': 'main',
                'function': 'get_image',
                'description': '获取镜像信息',
                'parameters': [],
                'required_params': []
            },
            
            'get_instances': {
                'module': 'main',
                'function': 'get_instances',
                'description': '获取虚拟机实例信息',
                'parameters': [],
                'required_params': []
            },
            
            'get_volumes': {
                'module': 'main',
                'function': 'get_volumes',
                'description': '获取磁盘信息',
                'parameters': [],
                'required_params': []
            },
            
            'getStorinfo': {
                'module': 'main',
                'function': 'getStorinfo',
                'description': '获取存储信息列表',
                'parameters': [],
                'required_params': []
            },
            
            'getImagebystorageManageId': {
                'module': 'main',
                'function': 'getImagebystorageManageId',
                'description': '根据存储管理ID获取镜像',
                'parameters': [],
                'required_params': []
            },
            
            # 资源操作
            'createInstance_noNet': {
                'module': 'main',
                'function': 'createInstance_noNet',
                'description': '创建无网卡虚拟机',
                'parameters': [
                    'name', 'hostname', 'videoModel', 'imageId', 'storname',
                    'cpu', 'memory', 'balloonSwitch', 'size', 'rebuildPriority',
                    'numaEnable', 'vncPwd', 'bigPageEnable', 'vmActive',
                    'cloneType', 'audioType', 'adminPassword', 'haEnable', 'priority'
                ],
                'required_params': ['name', 'hostname', 'videoModel', 'imageId', 'storname', 'cpu', 'memory']
            },
            
            'createDisk_vstor': {
                'module': 'main',
                'function': 'createDisk_vstor',
                'description': '创建虚拟磁盘',
                'parameters': [
                    'storageManageId', 'pageSize', 'compression', 'name',
                    'size', 'iops', 'bandwidth', 'count', 'readCache', 'zoneId'
                ],
                'required_params': ['storageManageId', 'pageSize', 'compression', 'name', 'size', 'iops', 'bandwidth', 'count', 'readCache', 'zoneId']
            },
            
            'deleteDisk': {
                'module': 'main',
                'function': 'deleteDisk',
                'description': '删除虚拟磁盘',
                'parameters': ['diskId'],
                'required_params': ['diskId']
            },
            
            # 数据库操作
            'db_query_simple': {
                'module': 'main',
                'function': 'db_query_simple',
                'description': '数据库查询',
                'parameters': ['sql', 'database'],
                'required_params': ['sql', 'database']
            },
            
            # SSH操作
            'sshexecute_command': {
                'module': 'main',
                'function': 'sshexecute_command',
                'description': 'SSH执行命令',
                'parameters': ['hostip', 'command', 'port', 'username', 'key_path'],
                'required_params': ['hostip', 'command']
            }
        }
        
        self.logger.info(f"📋 注册了 {len(methods)} 个MCP方法")
        return methods
    
    def get_available_methods(self) -> Dict[str, Dict]:
        """获取所有可用的MCP方法"""
        return self._method_registry.copy()
    
    def get_method_info(self, method_name: str) -> Optional[Dict]:
        """获取指定方法的信息"""
        return self._method_registry.get(method_name)
    
    def _validate_parameters(self, method_name: str, parameters: Dict) -> Tuple[bool, str]:
        """验证方法参数"""
        method_info = self.get_method_info(method_name)
        if not method_info:
            return False, f"方法不存在: {method_name}"
        
        required_params = method_info.get('required_params', [])
        for param in required_params:
            if param not in parameters or parameters[param] is None:
                return False, f"缺少必需参数: {param}"
        
        return True, ""
    
    def _import_mcp_function(self, module_name: str, function_name: str):
        """动态导入MCP函数"""
        try:
            module = __import__(module_name, fromlist=[function_name])
            return getattr(module, function_name)
        except ImportError as e:
            raise ImportError(f"无法导入模块 {module_name}: {e}")
        except AttributeError as e:
            raise AttributeError(f"模块 {module_name} 中没有函数 {function_name}: {e}")
    
    def _ensure_session(self) -> bool:
        """确保会话已建立"""
        if not self.auto_session:
            return True
            
        if self.session_manager is None:
            try:
                from .session_manager import SessionManager
                self.session_manager = SessionManager()
            except ImportError:
                # fallback for relative import issues
                from session_manager import SessionManager
                self.session_manager = SessionManager()
        
        # 检查会话健康状态
        health = self.session_manager.check_session_health()
        if not health.get('healthy', False):
            self.logger.info("🔄 会话不健康，尝试重新建立...")
            result = self.session_manager.establish_session()
            return result.get('success', False)
        
        return True
    
    def call_method(self, method_name: str, **parameters) -> MCPCallResult:
        """
        调用单个MCP方法
        
        Args:
            method_name: 方法名称
            **parameters: 方法参数
            
        Returns:
            MCPCallResult: 调用结果
        """
        start_time = time.time()
        
        # 验证方法存在
        method_info = self.get_method_info(method_name)
        if not method_info:
            error_msg = f"方法不存在: {method_name}"
            self.logger.error(f"❌ {error_msg}")
            return MCPCallResult(
                success=False,
                error=error_msg,
                execution_time=time.time() - start_time,
                method_name=method_name,
                parameters=parameters
            )
        
        # 验证参数
        valid, error_msg = self._validate_parameters(method_name, parameters)
        if not valid:
            self.logger.error(f"❌ 参数验证失败: {error_msg}")
            return MCPCallResult(
                success=False,
                error=error_msg,
                execution_time=time.time() - start_time,
                method_name=method_name,
                parameters=parameters
            )
        
        # 确保会话（除了getSession本身）
        if method_name != 'getSession' and not self._ensure_session():
            error_msg = "会话建立失败或会话不健康"
            self.logger.error(f"❌ {error_msg}")
            return MCPCallResult(
                success=False,
                error=error_msg,
                execution_time=time.time() - start_time,
                method_name=method_name,
                parameters=parameters
            )
        
        # 调用方法
        try:
            self.logger.info(f"🔧 调用MCP方法: {method_name}")
            self.logger.debug(f"📋 参数: {parameters}")
            
            # 导入并调用MCP函数
            mcp_function = self._import_mcp_function(
                method_info['module'],
                method_info['function']
            )
            
            # 执行方法调用
            result = mcp_function(**parameters)
            
            execution_time = time.time() - start_time
            
            # 更新统计信息
            self._update_call_stats(method_name, True, execution_time)
            
            self.logger.info(f"✅ MCP方法调用成功: {method_name} (耗时: {execution_time:.2f}s)")
            self.logger.debug(f"📊 结果: {result}")
            
            return MCPCallResult(
                success=True,
                data=result,
                execution_time=execution_time,
                method_name=method_name,
                parameters=parameters
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"方法调用异常: {str(e)}"
            
            # 更新统计信息
            self._update_call_stats(method_name, False, execution_time)
            
            self.logger.error(f"❌ MCP方法调用失败: {method_name}")
            self.logger.error(f"💥 异常: {e}")
            self.logger.debug(f"📋 详细错误: {traceback.format_exc()}")
            
            return MCPCallResult(
                success=False,
                error=error_msg,
                execution_time=execution_time,
                method_name=method_name,
                parameters=parameters
            )
    
    def batch_call(self, method_calls: List[Dict], max_workers: int = 3) -> List[MCPCallResult]:
        """
        批量调用MCP方法
        
        Args:
            method_calls: 方法调用列表，格式: [{"method": "method_name", "params": {...}}, ...]
            max_workers: 最大并发数
            
        Returns:
            List[MCPCallResult]: 调用结果列表
        """
        self.logger.info(f"🔄 开始批量调用 {len(method_calls)} 个MCP方法")
        
        results = []
        
        # 序列化执行（避免并发问题）
        for i, call in enumerate(method_calls):
            method_name = call.get('method')
            parameters = call.get('params', {})
            
            self.logger.info(f"📋 执行第 {i+1}/{len(method_calls)} 个调用: {method_name}")
            
            result = self.call_method(method_name, **parameters)
            results.append(result)
            
            # 添加延迟避免API频率限制
            if i < len(method_calls) - 1:
                time.sleep(1)
        
        successful_calls = sum(1 for r in results if r.success)
        self.logger.info(f"📊 批量调用完成: {successful_calls}/{len(method_calls)} 成功")
        
        return results
    
    def async_call(self, method_name: str, **parameters):
        """异步调用MCP方法（预留接口）"""
        # TODO: 实现真正的异步调用
        return self.call_method(method_name, **parameters)
    
    def _update_call_stats(self, method_name: str, success: bool, execution_time: float):
        """更新调用统计信息"""
        self.call_stats["total_calls"] += 1
        
        if success:
            self.call_stats["successful_calls"] += 1
        else:
            self.call_stats["failed_calls"] += 1
        
        if method_name not in self.call_stats["methods_used"]:
            self.call_stats["methods_used"][method_name] = {
                "count": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "success_count": 0
            }
        
        stats = self.call_stats["methods_used"][method_name]
        stats["count"] += 1
        stats["total_time"] += execution_time
        stats["avg_time"] = stats["total_time"] / stats["count"]
        
        if success:
            stats["success_count"] += 1
    
    def get_call_statistics(self) -> Dict:
        """获取调用统计信息"""
        stats = self.call_stats.copy()
        
        # 计算成功率
        if stats["total_calls"] > 0:
            stats["success_rate"] = stats["successful_calls"] / stats["total_calls"]
        else:
            stats["success_rate"] = 0.0
        
        # 计算最常用的方法
        if stats["methods_used"]:
            stats["most_used_method"] = max(
                stats["methods_used"].items(),
                key=lambda x: x[1]["count"]
            )[0]
        else:
            stats["most_used_method"] = None
        
        return stats
    
    def reset_statistics(self):
        """重置统计信息"""
        self.call_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "methods_used": {}
        }
        self.logger.info("📊 调用统计信息已重置")


# 便捷函数
def create_mcp_client(auto_session: bool = True) -> MCPMethodClient:
    """创建MCP客户端实例"""
    return MCPMethodClient(auto_session=auto_session)


# 测试代码
if __name__ == "__main__":
    # 创建MCP客户端
    mcp_client = MCPMethodClient()
    
    # 显示可用方法
    methods = mcp_client.get_available_methods()
    logger.info(f"📋 可用MCP方法 ({len(methods)} 个):")
    for method_name, method_info in methods.items():
        logger.info(f"  - {method_name}: {method_info['description']}")
    
    # 测试调用
    logger.info(f"\n🔧 测试MCP方法调用...")
    
    # 1. 测试获取会话信息
    logger.info(f"\n1️⃣ 测试 get_audit:")
    result = mcp_client.call_method("get_audit")
    logger.info(f"结果: {result.to_dict()}")
    
    # 2. 测试获取存储信息
    logger.info(f"\n2️⃣ 测试 getStorinfo:")
    result = mcp_client.call_method("getStorinfo")
    logger.info(f"结果: {result.success}")
    if result.success:
        logger.info(f"存储数量: {len(result.data) if isinstance(result.data, list) else 'N/A'}")
    
    # 3. 显示统计信息
    logger.info(f"\n📊 调用统计:")
    stats = mcp_client.get_call_statistics()
    logger.info(json.dumps(stats, indent=2, ensure_ascii=False))