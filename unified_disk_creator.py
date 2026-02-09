import logging
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
#!/usr/bin/env python3
"""
统一磁盘创建器
支持多种环境选择方式：交互选择、命令行指定、记住上次选择
"""

import sys
import os
import json
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from env_manager import EnvironmentManager
from smart_disk_creator import SmartDiskCreator
from utils.audit import ArcherAudit
from Hosts import Hosts
from volumes import Volumes

class UnifiedDiskCreator:
    def __init__(self):
        self.env_manager = EnvironmentManager()
        self.current_env = None
        self.connection_info = None
        self.last_env_file = Path(".last_disk_env")
        
    def get_last_environment(self) -> str:
        """获取上次使用的环境"""
        try:
            if self.last_env_file.exists():
                with open(self.last_env_file, 'r') as f:
                    return f.read().strip()
        except:
            pass
        return None
    
    def save_last_environment(self, env_id: str):
        """保存最后使用的环境"""
        try:
            with open(self.last_env_file, 'w') as f:
                f.write(env_id)
        except:
            pass
    
    def list_environments(self) -> list:
        """列出所有环境"""
        return self.env_manager.list_environments()
    
    def select_environment_interactive(self, env_hint: str = None) -> str:
        """交互式环境选择"""
        environments = self.list_environments()
        
        if not environments:
            logger.error("❌ 没有配置的环境，请先添加环境")
            return None
        
        # 如果有提示，尝试过滤
        if env_hint:
            filtered = [env for env in environments 
                       if env_hint.lower() in env.get('id', '').lower() 
                       or env_hint.lower() in env.get('name', '').lower()]
            if len(filtered) == 1:
                logger.info(f"🎯 自动匹配环境: {filtered[0]['name']}")
                return filtered[0]['id']
            elif filtered:
                environments = filtered
        
        logger.info("\n🌐 可用环境列表:")
        logger.info("=" * 80)
        logger.info(f"{'序号':<4} {'环境ID':<12} {'名称':<20} {'地址':<25} {'描述':<20}")
        logger.info("-" * 80)
        
        for i, env in enumerate(environments, 1):
            logger.info(f"{i:<4} {env['id']:<12} {env['name']:<20} "
                  f"{env['url']:<25} {env['description'][:18]:<20}")
        
        logger.info("=" * 80)
        
        while True:
            try:
                choice = input(f"\n请选择环境 (1-{len(environments)}) 或输入环境ID: ").strip()
                
                # 尝试按序号选择
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(environments):
                        selected_env = environments[idx]
                        logger.info(f"✅ 选择环境: {selected_env['name']}")
                        return selected_env['id']
                
                # 尝试按ID选择
                for env in environments:
                    if env['id'] == choice:
                        logger.info(f"✅ 选择环境: {env['name']}")
                        return env['id']
                
                logger.error("❌ 无效选择，请重新输入")
                
            except KeyboardInterrupt:
                logger.info("\n👋 操作已取消")
                return None
    
    def check_environment(self, env_id: str) -> bool:
        """检查环境可用性"""
        self.connection_info = self.env_manager.get_connection_info(env_id)
        
        if not self.connection_info:
            logger.error(f"❌ 环境不存在: {env_id}")
            return False
        
        logger.info(f"🔗 正在连接环境: {self.connection_info['name']}")
        logger.info(f"📡 地址: {self.connection_info['url']}")
        
        # 测试连接
        try:
            audit = ArcherAudit(
                self.connection_info['username'],
                self.connection_info['password'], 
                self.connection_info['url']
            )
            
            if audit.setSession():
                logger.info(f"✅ 环境连接成功: {self.connection_info['name']}")
                self.current_env = env_id
                self.save_last_environment(env_id)
                return True
            else:
                logger.error(f"❌ 环境连接失败: {self.connection_info['name']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 连接测试失败: {e}")
            return False
    
    def create_disk(self, size_gb: int, use_case: str = "standard", 
                   env_id: str = None, interactive: bool = True) -> bool:
        """创建磁盘"""
        
        # 环境选择逻辑
        if env_id:
            # 命令行指定环境
            logger.info(f"🎯 使用指定环境: {env_id}")
            target_env = env_id
        elif interactive:
            # 交互式选择
            last_env = self.get_last_environment()
            if last_env:
                use_last = input(f"检测到上次环境: {last_env}，是否使用？(y/n): ").strip().lower()
                if use_last in ['y', 'yes', '']:
                    target_env = last_env
                else:
                    target_env = self.select_environment_interactive()
            else:
                target_env = self.select_environment_interactive()
        else:
            # 非交互模式，尝试使用默认环境
            target_env = self.get_last_environment()
            if not target_env:
                # 尝试生产环境
                environments = self.list_environments()
                for env in environments:
                    if 'prod' in env.get('id', '').lower() or '生产' in env.get('name', ''):
                        target_env = env['id']
                        break
                else:
                    target_env = environments[0]['id'] if environments else None
        
        if not target_env:
            logger.error("❌ 未选择环境，操作取消")
            return False
        
        # 环境验证
        if not self.check_environment(target_env):
            logger.info("💡 建议检查:")
            logger.info("   • 网络连接是否正常")
            logger.info("   • 用户名密码是否正确") 
            logger.info("   • 环境地址是否可访问")
            return False
        
        # 使用智能磁盘创建器
        try:
            logger.info(f"\n🚀 在环境 '{self.connection_info['name']}' 中创建 {size_gb}GB 磁盘...")
            
            creator = SmartDiskCreator(
                self.connection_info['username'],
                self.connection_info['password'],
                self.connection_info['url']
            )
            
            success = creator.create_disk_smart(size_gb, use_case)
            
            if success:
                logger.info(f"\n🎉 磁盘在环境 '{self.connection_info['name']}' 中创建成功!")
                logger.info(f"🌐 环境地址: {self.connection_info['url']}")
                logger.info(f"💾 磁盘大小: {size_gb}GB")
                logger.info(f"📋 用例类型: {use_case}")
            else:
                logger.info(f"\n💥 在环境 '{self.connection_info['name']}' 中创建失败")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 创建过程发生错误: {e}")
            return False
    
    def batch_create_disks(self, disk_configs: list, env_id: str = None) -> dict:
        """批量创建磁盘"""
        logger.info("🔥 批量磁盘创建模式")
        logger.info("=" * 60)
        
        if not env_id:
            env_id = self.select_environment_interactive()
        
        if not env_id or not self.check_environment(env_id):
            return {"success": False, "error": "环境选择失败"}
        
        results = {
            "total": len(disk_configs),
            "success": [],
            "failed": [],
            "environment": self.connection_info['name']
        }
        
        for i, config in enumerate(disk_configs, 1):
            logger.info(f"\n📁 创建第 {i}/{len(disk_configs)} 个磁盘...")
            success = self.create_disk(
                config.get('size', 10),
                config.get('use_case', 'standard'),
                env_id,
                interactive=False  # 批量模式不重复选择环境
            )
            
            if success:
                results["success"].append({
                    'disk_num': i,
                    'size': config.get('size', 10),
                    'use_case': config.get('use_case', 'standard')
                })
            else:
                results["failed"].append({
                    'disk_num': i,
                    'size': config.get('size', 10),
                    'error': '创建失败'
                })
        
        return results

def main():
    """命令行界面"""
    parser = argparse.ArgumentParser(description='统一磁盘创建器')
    parser.add_argument('command', choices=['create', 'batch', 'env-list'], 
                       help='命令类型')
    parser.add_argument('--size', type=int, help='磁盘大小(GB)')
    parser.add_argument('--use-case', default='standard', 
                       choices=['test', 'standard', 'performance'],
                       help='用例类型')
    parser.add_argument('--env', help='指定环境ID')
    parser.add_argument('--non-interactive', action='store_true', 
                       help='非交互模式')
    
    args = parser.parse_args()
    
    creator = UnifiedDiskCreator()
    
    if args.command == 'create':
        if not args.size:
            logger.error("❌ 请提供磁盘大小: --size <GB>")
            return
        
        creator.create_disk(
            args.size,
            args.use_case,
            args.env,
            not args.non_interactive
        )
    
    elif args.command == 'batch':
        # 示例批量配置
        batch_config = [
            {"size": 10, "use_case": "test"},
            {"size": 20, "use_case": "standard"}, 
            {"size": 50, "use_case": "performance"}
        ]
        
        results = creator.batch_create_disks(batch_config, args.env)
        
        logger.info(f"\n📊 批量创建结果:")
        logger.info("=" * 60)
        logger.info(f"✅ 成功: {len(results['success'])}/{results['total']}")
        logger.error(f"❌ 失败: {len(results['failed'])}/{results['total']}")
        logger.info(f"🌐 环境: {results['environment']}")
    
    elif args.command == 'env-list':
        creator.env_manager.display_environments_table()

if __name__ == "__main__":
    main()