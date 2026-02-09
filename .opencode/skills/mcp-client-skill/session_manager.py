#!/usr/bin/env python3
"""
Session Manager - MCP Client Skill会话生命周期管理
负责管理Skill与MCP Server的会话建立、维护和清理
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
from pathlib import Path
from typing import Dict, Optional, Any, Tuple

# 添加主项目路径
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

class SessionManager:
    """
    会话管理器
    
    负责Skill与MCP Server之间的会话生命周期管理：
    - 会话建立和初始化
    - 会话状态监控
    - 会话刷新和恢复
    - 环境配置管理
    """
    
    def __init__(self, env_config_path: str = None):
        self.logger = self._setup_logger()
        # 优先查找.opencode目录下的配置，然后查找项目根目录
        if env_config_path:
            self.env_config_path = env_config_path
        else:
            # 先尝试.opencode目录
            opencode_config = Path(__file__).parents[2] / "environments.json"
            if opencode_config.exists():
                self.env_config_path = str(opencode_config)
            else:
                # 再尝试项目根目录
                root_config = Path(__file__).parents[4] / "environments.json"
                self.env_config_path = str(root_config)
        
        self.env_config = self._load_env_config()
        self._session_cache = {}
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(f"{__name__}.SessionManager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _load_env_config(self) -> Dict:
        """加载环境配置"""
        try:
            if Path(self.env_config_path).exists():
                with open(self.env_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"✅ 加载环境配置: {len(config.get('environments', {}))} 个环境")
                return config
            else:
                self.logger.warning(f"⚠️ 环境配置文件不存在: {self.env_config_path}")
                return {"environments": {}}
        except Exception as e:
            self.logger.error(f"❌ 加载环境配置失败: {e}")
            return {"environments": {}}
    
    def get_available_environments(self) -> Dict[str, Dict]:
        """获取可用环境列表"""
        return self.env_config.get('environments', {})
    
    def get_environment_info(self, env_id: str) -> Optional[Dict]:
        """获取指定环境信息"""
        environments = self.get_available_environments()
        env_info = environments.get(env_id)
        
        if env_info:
            self.logger.info(f"✅ 获取环境信息: {env_id}")
        else:
            available = list(environments.keys())
            self.logger.error(f"❌ 环境不存在: {env_id}，可用环境: {available}")
            
        return env_info
    
    def establish_session(self, env_id: str = None, url: str = None, 
                         username: str = "admin", password: str = "Admin@123") -> Dict:
        """
        建立MCP会话
        
        Args:
            env_id: 环境标识符
            url: 直接提供的URL（优先级高于env_id）
            username: 用户名
            password: 密码
            
        Returns:
            Dict: 会话建立结果
        """
        self.logger.info("🔐 开始建立MCP会话...")
        
        # 确定连接参数
        if url:
            connection_params = {
                'url': url,
                'username': username,
                'password': password,
                'description': '直接连接'
            }
        elif env_id:
            env_info = self.get_environment_info(env_id)
            if not env_info:
                return {
                    "success": False,
                    "error": f"环境配置不存在: {env_id}",
                    "available_environments": list(self.get_available_environments().keys())
                }
            
            connection_params = {
                'url': env_info['url'],
                'username': env_info.get('username', username),
                'password': env_info.get('password', password),
                'description': env_info.get('description', env_id)
            }
        else:
            # 尝试默认配置
            environments = self.get_available_environments()
            if 'production' in environments:
                return self.establish_session(env_id='production')
            elif environments:
                default_env = list(environments.keys())[0]
                self.logger.info(f"📍 使用默认环境: {default_env}")
                return self.establish_session(env_id=default_env)
            else:
                return self.establish_session(url="https://172.118.57.100")
        
        # 调用MCP的getSession方法
        return self._call_get_session(connection_params)
    
    def _call_get_session(self, connection_params: Dict) -> Dict:
        """调用MCP的getSession方法"""
        try:
            # 动态导入MCP方法
            from main import getSession, global_state
            
            self.logger.info(f"🌐 连接环境: {connection_params['description']}")
            self.logger.info(f"🔗 URL: {connection_params['url']}")
            self.logger.info(f"👤 用户: {connection_params['username']}")
            
            # 调用getSession建立会话
            result = getSession(
                connection_params['url'],
                connection_params['username'],
                connection_params['password']
            )
            
            # 分析会话建立结果
            if "成功" in result:
                session_info = self._analyze_session_result(global_state)
                session_info.update({
                    "success": True,
                    "connection_params": connection_params,
                    "session_message": result
                })
                
                # 缓存会话信息
                session_key = connection_params['url']
                self._session_cache[session_key] = {
                    "info": session_info,
                    "timestamp": time.time(),
                    "connection_params": connection_params
                }
                
                self.logger.info(f"✅ MCP会话建立成功")
                return session_info
            else:
                self.logger.error(f"❌ MCP会话建立失败: {result}")
                return {
                    "success": False,
                    "error": f"会话建立失败: {result}",
                    "connection_params": connection_params
                }
                
        except ImportError as e:
            self.logger.error(f"❌ 无法导入MCP模块: {e}")
            return {
                "success": False,
                "error": f"MCP模块导入失败: {e}"
            }
        except Exception as e:
            self.logger.error(f"❌ 建立会话时发生异常: {e}")
            return {
                "success": False,
                "error": f"会话建立异常: {e}",
                "connection_params": connection_params
            }
    
    def _analyze_session_result(self, global_state) -> Dict:
        """分析会话建立结果"""
        try:
            # 检查全局状态
            session_analysis = {
                "global_state_initialized": global_state is not None,
                "components": {}
            }
            
            if global_state:
                # 检查各组件状态
                session_analysis["components"] = {
                    "audit": {
                        "initialized": global_state.audit is not None,
                        "base_url": getattr(global_state.audit, 'base_url', None) if global_state.audit else None,
                        "username": getattr(global_state.audit, 'username', None) if global_state.audit else None
                    },
                    "host": {
                        "initialized": global_state.host is not None,
                        "zone": getattr(global_state.host, 'zone', None) if global_state.host else None,
                        "cluster_id": getattr(global_state.host, 'clusterId', None) if global_state.host else None
                    },
                    "image": {
                        "initialized": global_state.image is not None,
                        "images_count": len(getattr(global_state.image, 'images', [])) if global_state.image else 0
                    },
                    "instances": {
                        "initialized": global_state.instances is not None,
                        "instances_count": len(getattr(global_state.instances, 'instances', [])) if global_state.instances else 0
                    },
                    "volumes": {
                        "initialized": global_state.volumes is not None,
                        "disks_count": len(getattr(global_state.volumes, 'disks', [])) if global_state.volumes else 0
                    },
                    "database": {
                        "initialized": global_state.db is not None
                    }
                }
            
            return session_analysis
            
        except Exception as e:
            self.logger.error(f"❌ 分析会话结果时发生异常: {e}")
            return {
                "global_state_initialized": False,
                "error": f"会话分析失败: {e}"
            }
    
    def check_session_health(self) -> Dict:
        """检查当前会话健康状态"""
        try:
            from main import global_state
            
            if not global_state:
                return {
                    "healthy": False,
                    "error": "全局状态未初始化"
                }
            
            # 检查关键组件
            critical_components = ['audit', 'host']
            for component in critical_components:
                if getattr(global_state, component, None) is None:
                    return {
                        "healthy": False,
                        "error": f"关键组件 {component} 未初始化"
                    }
            
            return {
                "healthy": True,
                "message": "会话状态健康"
            }
            
        except ImportError as e:
            return {
                "healthy": False,
                "error": f"无法导入MCP模块: {e}"
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": f"会话健康检查异常: {e}"
            }
    
    def refresh_session(self) -> Dict:
        """刷新当前会话"""
        self.logger.info("🔄 刷新MCP会话...")
        
        # 获取最近的连接参数
        if not self._session_cache:
            return {
                "success": False,
                "error": "没有可刷新的会话缓存"
            }
        
        # 使用最近的连接参数重新建立会话
        latest_session = max(self._session_cache.values(), key=lambda x: x['timestamp'])
        connection_params = latest_session['connection_params']
        
        return self.establish_session(**connection_params)
    
    def get_session_summary(self) -> Dict:
        """获取会话状态摘要"""
        try:
            from main import global_state
            
            summary = {
                "session_cached": len(self._session_cache),
                "current_session": None,
                "health_status": self.check_session_health()
            }
            
            if global_state and global_state.audit:
                summary["current_session"] = {
                    "base_url": getattr(global_state.audit, 'base_url', None),
                    "username": getattr(global_state.audit, 'username', None),
                    "components_status": {
                        "host": global_state.host is not None,
                        "image": global_state.image is not None,
                        "instances": global_state.instances is not None,
                        "volumes": global_state.volumes is not None,
                        "database": global_state.db is not None
                    }
                }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ 获取会话摘要失败: {e}")
            return {
                "error": f"会话摘要获取失败: {e}"
            }


# 便捷函数
def create_session_manager(env_config_path: str = None) -> SessionManager:
    """创建会话管理器实例"""
    return SessionManager(env_config_path)


# 测试代码
if __name__ == "__main__":
    # 创建会话管理器
    session_mgr = SessionManager()
    
    # 显示可用环境
    environments = session_mgr.get_available_environments()
    logger.info("🌐 可用环境:")
    for env_id, env_info in environments.items():
        logger.info(f"  - {env_id}: {env_info.get('description', '无描述')}")
    
    # 建立会话
    if environments:
        env_id = list(environments.keys())[0]
        logger.info(f"\n🔐 尝试建立会话: {env_id}")
        result = session_mgr.establish_session(env_id=env_id)
        
        logger.info(f"会话建立结果:")
        logger.info(f"  成功: {result.get('success')}")
        if not result.get('success'):
            logger.info(f"  错误: {result.get('error')}")
        else:
            logger.info(f"  组件状态: {result.get('components', {})}")
    
    # 检查会话健康状态
    health = session_mgr.check_session_health()
    logger.info(f"\n🏥 会话健康状态: {health}")
    
    # 获取会话摘要
    summary = session_mgr.get_session_summary()
    logger.info(f"\n📋 会话摘要: {summary}")