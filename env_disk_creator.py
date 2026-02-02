#!/usr/bin/env python3
"""
智能环境感知磁盘创建器
自动环境选择 + 参数验证 + 智能配置
"""

import sys
import os
import json
from env_manager import EnvironmentManager

class EnvironmentAwareDiskCreator:
    """环境感知的磁盘创建器"""
    
    def __init__(self):
        self.env_manager = EnvironmentManager()
        self.current_env = None
        self.connection_info = None
    
    def select_environment_interactive(self) -> str:
        """交互式环境选择"""
        environments = self.env_manager.list_environments()
        
        if not environments:
            print("❌ 没有配置的环境，请先添加环境")
            return None
        
        print("\n🌐 可用环境列表:")
        print("=" * 70)
        print(f"{'序号':<4} {'环境ID':<12} {'名称':<15} {'地址':<25} {'描述':<20}")
        print("-" * 70)
        
        for i, env in enumerate(environments, 1):
            print(f"{i:<4} {env['id']:<12} {env['name']:<15} "
                  f"{env['url']:<25} {env['description'][:18]:<20}")
        
        print("=" * 70)
        
        while True:
            try:
                choice = input(f"\n请选择环境 (1-{len(environments)}) 或输入环境ID: ").strip()
                
                # 尝试按序号选择
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(environments):
                        selected_env = environments[idx]
                        return selected_env['id']
                
                # 尝试按ID选择
                for env in environments:
                    if env['id'] == choice:
                        return env['id']
                
                print("❌ 无效选择，请重新输入")
                
            except KeyboardInterrupt:
                print("\n👋 操作已取消")
                return None
    
    def auto_select_environment(self, env_hint: str = None) -> str:
        """自动环境选择"""
        if not env_hint:
            # 没有提示，返回第一个生产环境
            environments = self.env_manager.list_environments()
            for env in environments:
                if 'prod' in env.get('tags', []) or '生产' in env.get('name', ''):
                    return env['id']
            # 如果没有生产环境，返回第一个
            return environments[0]['id'] if environments else None
        
        # 有提示，搜索匹配环境
        results = self.env_manager.search_environments(env_hint)
        if len(results) == 1:
            return results[0]['id']
        elif len(results) > 1:
            print(f"🔍 找到 {len(results)} 个匹配环境，请手动选择:")
            return self.select_environment_interactive()
        else:
            print(f"❌ 没有找到匹配 '{env_hint}' 的环境")
            return self.select_environment_interactive()
    
    def check_environment(self, env_id: str) -> bool:
        """检查环境可用性"""
        self.connection_info = self.env_manager.get_connection_info(env_id)
        
        if not self.connection_info:
            print(f"❌ 环境不存在: {env_id}")
            return False
        
        print(f"🔗 正在连接环境: {self.connection_info['name']}")
        print(f"📡 地址: {self.connection_info['url']}")
        
        # 测试连接
        try:
            from utils.audit import ArcherAudit
            
            audit = ArcherAudit(
                self.connection_info['username'],
                self.connection_info['password'], 
                self.connection_info['url']
            )
            
            if audit.setSession():
                print(f"✅ 环境连接成功: {self.connection_info['name']}")
                self.current_env = env_id
                return True
            else:
                print(f"❌ 环境连接失败: {self.connection_info['name']}")
                return False
                
        except Exception as e:
            print(f"❌ 连接测试失败: {e}")
            return False
    
    def create_disk_with_env_selection(self, disk_size_gb: int, 
                                     use_case: str = "standard",
                                     env_hint: str = None):
        """带环境选择的磁盘创建"""
        
        print("🎯 智能磁盘创建器 (环境感知版)")
        print("=" * 50)
        
        # 1. 环境选择
        if env_hint:
            print(f"🔍 搜索匹配环境: {env_hint}")
            env_id = self.auto_select_environment(env_hint)
        else:
            print("📋 请选择目标环境:")
            env_id = self.select_environment_interactive()
        
        if not env_id:
            print("❌ 未选择环境，操作取消")
            return False
        
        # 2. 环境验证
        if not self.check_environment(env_id):
            print("💡 建议检查:")
            print("   • 网络连接是否正常")
            print("   • 用户名密码是否正确") 
            print("   • 环境地址是否可访问")
            return False
        
        # 3. 使用智能磁盘创建器
        try:
            from smart_disk_creator import SmartDiskCreator
            
            creator = SmartDiskCreator(
                self.connection_info['username'],
                self.connection_info['password'],
                self.connection_info['url']
            )
            
            print(f"\n🚀 在环境 '{self.connection_info['name']}' 中创建磁盘...")
            success = creator.create_disk_smart(disk_size_gb, use_case)
            
            if success:
                print(f"\n🎉 磁盘在环境 '{self.connection_info['name']}' 中创建成功!")
                print(f"🌐 环境地址: {self.connection_info['url']}")
            else:
                print(f"\n💥 在环境 '{self.connection_info['name']}' 中创建失败")
            
            return success
            
        except Exception as e:
            print(f"❌ 创建过程发生错误: {e}")
            return False
    
    def quick_create_batch_disks(self, disk_config: list):
        """批量创建磁盘"""
        print("🔥 批量磁盘创建模式")
        print("=" * 50)
        
        # 选择环境
        env_id = self.select_environment_interactive()
        if not env_id or not self.check_environment(env_id):
            return False
        
        results = []
        
        for i, config in enumerate(disk_config, 1):
            print(f"\n📁 创建第 {i}/{len(disk_config)} 个磁盘...")
            success = self.create_disk_with_env_selection(
                config.get('size', 10),
                config.get('use_case', 'standard'),
                env_id
            )
            results.append({
                'disk_num': i,
                'size': config.get('size', 10),
                'success': success,
                'environment': self.connection_info['name']
            })
        
        # 显示批量结果
        print("\n📊 批量创建结果:")
        print("=" * 60)
        success_count = sum(1 for r in results if r['success'])
        print(f"✅ 成功: {success_count}/{len(results)}")
        print(f"❌ 失败: {len(results) - success_count}/{len(results)}")
        
        for result in results:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} 磁盘 {result['disk_num']}: "
                  f"{result['size']}GB @ {result['environment']}")

def main():
    """命令行界面"""
    import sys
    
    creator = EnvironmentAwareDiskCreator()
    
    if len(sys.argv) < 2:
        print("🔧 环境感知磁盘创建器")
        print("python env_disk_creator.py [命令] [参数]")
        print("\n命令:")
        print("  create <size> [use_case] [env_hint]  - 创建磁盘")
        print("  batch                           - 批量创建(交互式)")
        print("  env-list                        - 列出环境")  
        print("  env-show <env_id>               - 显示环境详情")
        print("  test <env_id>                   - 测试环境连接")
        return
    
    command = sys.argv[1]
    
    if command == "create":
        if len(sys.argv) < 3:
            print("❌ 请提供磁盘大小 (GB)")
            return
        
        disk_size = int(sys.argv[2])
        use_case = sys.argv[3] if len(sys.argv) > 3 else "standard"
        env_hint = sys.argv[4] if len(sys.argv) > 4 else None
        
        creator.create_disk_with_env_selection(disk_size, use_case, env_hint)
    
    elif command == "batch":
        # 示例批量配置
        batch_config = [
            {"size": 10, "use_case": "test"},
            {"size": 20, "use_case": "standard"},
            {"size": 50, "use_case": "performance"}
        ]
        creator.quick_create_batch_disks(batch_config)
    
    elif command == "env-list":
        creator.env_manager.display_environments_table()
    
    elif command == "env-show":
        if len(sys.argv) < 3:
            print("❌ 请提供环境ID")
            return
        env = creator.env_manager.get_environment(sys.argv[2])
        if env:
            print(f"\n📋 环境详情: {sys.argv[2]}")
            print("=" * 40)
            for key, value in env.items():
                print(f"{key}: {value}")
        else:
            print(f"❌ 环境不存在: {sys.argv[2]}")
    
    elif command == "test":
        if len(sys.argv) < 3:
            print("❌ 请提供环境ID")
            return
        creator.check_environment(sys.argv[2])

if __name__ == "__main__":
    main()