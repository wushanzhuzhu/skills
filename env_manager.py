#!/usr/bin/env python3
"""
环境配置管理器
管理多个环境的连接信息，支持动态选择
"""

import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

import os
from typing import Dict, List, Optional

class EnvironmentManager:
    """环境管理器"""
    
    def __init__(self, config_file: str = "environments.json"):
        self.config_file = config_file
        self.environments = {}
        self.load_environments()
    
    def load_environments(self):
        """加载环境配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.environments = json.load(f)
                logger.info(f"✅ 已加载 {len(self.environments)} 个环境配置")
            except Exception as e:
                logger.error(f"❌ 加载环境配置失败: {e}")
                self.environments = self._get_default_environments()
        else:
            logger.info("📝 首次运行，创建默认环境配置")
            self.environments = self._get_default_environments()
            self.save_environments()
    
    def _get_default_environments(self) -> Dict:
        """获取默认环境配置"""
        return {
            "production": {
                "name": "生产环境",
                "url": "https://172.118.57.100",
                "username": "admin", 
                "password": "Admin@123",
                "description": "主要生产环境，用于正式业务",
                "tags": ["prod", "main", "正式"],
                "storage_backend": "iscsi"
            },
            "test": {
                "name": "测试环境", 
                "url": "https://192.168.1.100",
                "username": "admin",
                "password": "Test@123",
                "description": "测试环境，用于功能验证",
                "tags": ["test", "dev", "测试"],
                "storage_backend": "iscsi"
            },
            "dev": {
                "name": "开发环境",
                "url": "https://10.0.0.100", 
                "username": "developer",
                "password": "Dev@123",
                "description": "开发环境，用于代码调试",
                "tags": ["dev", "debug", "开发"],
                "storage_backend": "local"
            }
        }
    
    def save_environments(self):
        """保存环境配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.environments, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 环境配置已保存到 {self.config_file}")
        except Exception as e:
            logger.error(f"❌ 保存环境配置失败: {e}")
    
    def list_environments(self) -> List[Dict]:
        """列出所有环境"""
        environments_list = []
        for env_id, env_info in self.environments.items():
            environments_list.append({
                "id": env_id,
                **env_info
            })
        return environments_list
    
    def get_environment(self, env_id: str) -> Optional[Dict]:
        """获取指定环境"""
        return self.environments.get(env_id)
    
    def add_environment(self, env_id: str, env_info: Dict):
        """添加环境"""
        self.environments[env_id] = env_info
        self.save_environments()
        logger.info(f"✅ 已添加环境: {env_id} - {env_info.get('name')}")
    
    def update_environment(self, env_id: str, env_info: Dict):
        """更新环境"""
        if env_id in self.environments:
            self.environments[env_id].update(env_info)
            self.save_environments()
            logger.info(f"✅ 已更新环境: {env_id}")
        else:
            logger.error(f"❌ 环境不存在: {env_id}")
    
    def delete_environment(self, env_id: str):
        """删除环境"""
        if env_id in self.environments:
            env_name = self.environments[env_id].get('name', env_id)
            del self.environments[env_id]
            self.save_environments()
            logger.info(f"✅ 已删除环境: {env_id} - {env_name}")
        else:
            logger.error(f"❌ 环境不存在: {env_id}")
    
    def search_environments(self, keyword: str) -> List[Dict]:
        """搜索环境"""
        results = []
        keyword = keyword.lower()
        for env_id, env_info in self.environments.items():
            # 搜索ID、名称、描述、标签
            if (keyword in env_id.lower() or 
                keyword in env_info.get('name', '').lower() or
                keyword in env_info.get('description', '').lower() or
                any(keyword in tag.lower() for tag in env_info.get('tags', []))):
                results.append({"id": env_id, **env_info})
        return results
    
    def display_environments_table(self, environments: List[Dict] = None):
        """显示环境表格"""
        if environments is None:
            environments = self.list_environments()
        
        if not environments:
            logger.info("📭 没有找到环境配置")
            return
        
        logger.info("\n🌐 环境列表:")
        logger.info("=" * 80)
        logger.info(f"{'ID':<12} {'名称':<15} {'地址':<20} {'用户名':<10} {'描述':<20}")
        logger.info("-" * 80)
        
        for env in environments:
            logger.info(f"{env['id']:<12} {env['name']:<15} {env['url']:<20} "
                  f"{env['username']:<10} {env['description'][:18]:<20}")
        
        logger.info("=" * 80)
    
    def get_connection_info(self, env_id: str) -> Optional[Dict]:
        """获取环境连接信息"""
        env = self.get_environment(env_id)
        if env:
            return {
                "url": env.get("url"),
                "username": env.get("username"),
                "password": env.get("password"),
                "name": env.get("name"),
                "storage_backend": env.get("storage_backend")
            }
        return None

# CLI命令行界面
def main():
    """命令行界面"""
    import sys
    
    manager = EnvironmentManager()
    
    if len(sys.argv) < 2:
        logger.info("🔧 环境管理器使用说明:")
        logger.info("python env_manager.py [命令] [参数]")
        logger.info("\n命令:")
        logger.info("  list                    - 列出所有环境")
        logger.info("  show <env_id>           - 显示指定环境详情")
        logger.info("  add <env_id>            - 添加环境(交互式)")
        logger.info("  delete <env_id>         - 删除环境")
        logger.info("  search <keyword>        - 搜索环境")
        logger.info("  connect <env_id>        - 获取连接信息")
        logger.info("  reload                  - 重新加载配置")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        manager.display_environments_table()
    
    elif command == "show":
        if len(sys.argv) < 3:
            logger.error("❌ 请提供环境ID")
            return
        env_id = sys.argv[2]
        env = manager.get_environment(env_id)
        if env:
            logger.info(f"\n📋 环境详情: {env_id}")
            logger.info("=" * 40)
            for key, value in env.items():
                logger.info(f"{key}: {value}")
        else:
            logger.error(f"❌ 环境不存在: {env_id}")
    
    elif command == "add":
        if len(sys.argv) < 3:
            logger.error("❌ 请提供环境ID")
            return
        env_id = sys.argv[2]
        
        logger.info(f"📝 添加环境: {env_id}")
        name = input("环境名称: ")
        url = input("环境地址: ")
        username = input("用户名: ")
        password = input("密码: ")
        description = input("描述: ")
        
        env_info = {
            "name": name,
            "url": url,
            "username": username, 
            "password": password,
            "description": description,
            "tags": [],
            "storage_backend": "iscsi"
        }
        
        manager.add_environment(env_id, env_info)
    
    elif command == "delete":
        if len(sys.argv) < 3:
            logger.error("❌ 请提供环境ID")
            return
        env_id = sys.argv[2]
        manager.delete_environment(env_id)
    
    elif command == "search":
        if len(sys.argv) < 3:
            logger.error("❌ 请提供搜索关键词")
            return
        keyword = sys.argv[2]
        results = manager.search_environments(keyword)
        logger.info(f"\n🔍 搜索结果: '{keyword}'")
        manager.display_environments_table(results)
    
    elif command == "connect":
        if len(sys.argv) < 3:
            logger.error("❌ 请提供环境ID")
            return
        env_id = sys.argv[2]
        conn_info = manager.get_connection_info(env_id)
        if conn_info:
            logger.info(f"\n🔗 连接信息: {conn_info['name']}")
            logger.info("=" * 40)
            logger.info(f"URL: {conn_info['url']}")
            logger.info(f"用户名: {conn_info['username']}")
            logger.info(f"密码: {conn_info['password']}")
            logger.info(f"存储后端: {conn_info['storage_backend']}")
        else:
            logger.error(f"❌ 环境不存在: {env_id}")
    
    elif command == "reload":
        manager.load_environments()
        logger.info("🔄 配置已重新加载")

if __name__ == "__main__":
    main()