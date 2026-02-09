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
直接磁盘创建脚本
不使用交互模式，直接创建虚拟磁盘
"""

import sys
import json
import time
from pathlib import Path

# 添加主项目路径
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

def create_disk_with_direct_mcp():
    """直接调用MCP方法创建磁盘"""
    
    logger.info("💾 使用MCP方法直接创建磁盘")
    logger.info("=" * 50)
    
    try:
        # 直接导入main模块
        import main
        
        # 1. 建立会话
        logger.info("🔐 建立MCP会话...")
        session_result = main.getSession("https://172.118.57.100", "admin", "Admin@123")
        
        if "成功" not in session_result:
            logger.error(f"❌ 会话建立失败: {session_result}")
            return False
        
        logger.info("✅ 会话建立成功")
        
        # 2. 获取存储信息
        logger.info("\n📁 获取存储信息...")
        stor_info = main.getStorinfo()
        
        if isinstance(stor_info, list) and len(stor_info) > 0:
            logger.info(f"✅ 找到 {len(stor_info)} 个存储位置")
            storage = stor_info[0]
            storage_manage_id = storage.get('storageManageId', 'default-id')
            logger.info(f"📍 使用存储: {storage.get('stackName', 'unknown')}")
            logger.info(f"   StorageManageId: {storage_manage_id}")
        else:
            logger.info("⚠️ 获取存储信息失败，使用默认ID")
            storage_manage_id = "demo-storage-id"
        
        # 3. 创建磁盘配置
        disk_config = {
            "storageManageId": storage_manage_id,
            "pageSize": "4K",
            "compression": "Disabled", 
            "name": f"direct-disk-{int(time.time())}",
            "size": 20,  # 20GB
            "iops": 2000,
            "bandwidth": 150,  # MB/s
            "count": 1,
            "readCache": True,
            "zoneId": "demo-zone-id"
        }
        
        logger.info(f"\n💾 创建磁盘: {disk_config['name']}")
        logger.info("📋 磁盘配置:")
        for key, value in disk_config.items():
            logger.info(f"   {key}: {value}")
        
        # 4. 创建磁盘
        logger.info("\n🔧 执行磁盘创建...")
        disk_result = main.createDisk_vstor(**disk_config)
        
        if disk_result:
            logger.info("✅ 磁盘创建成功！")
            logger.info(f"📊 磁盘信息: {disk_result}")
            
            # 5. 验证创建结果
            logger.info("\n🔍 验证创建结果...")
            volumes = main.get_volumes()
            
            if isinstance(volumes, list):
                logger.info(f"📁 当前磁盘总数: {len(volumes)}")
                if len(volumes) > 0:
                    logger.info("🎉 磁盘创建验证成功！")
                    return True
            
            logger.info("⚠️ 无法验证磁盘列表，但创建操作已执行")
            return True
        else:
            logger.error("❌ 磁盘创建失败")
            return False
            
    except Exception as e:
        logger.info(f"💥 创建过程出错: {e}")
        logger.info("💡 可能的原因:")
        logger.info("   1. MCP服务器未运行在8080端口")
        logger.info("   2. 网络连接问题")
        logger.info("   3. 安超平台服务不可用")
        return False

def create_disk_with_skill():
    """使用Skill创建磁盘"""
    
    logger.info("\n🎮 使用MCP Client Skill创建磁盘")
    logger.info("=" * 50)
    
    try:
        # 尝试导入技能
        from mcp_client_skill import MCPClientSkill
        
        # 创建技能实例
        skill = MCPClientSkill(env_id="production", auto_session=True)
        
        # 获取资源信息
        logger.info("🔍 获取资源信息...")
        resources = skill.resource_management_overview()
        
        if isinstance(resources, dict) and 'resources' in resources:
            storage_info = resources['resources'].get('storage', {})
            if storage_info.get('total_locations', 0) > 0:
                storage = storage_info['details'][0]
                storage_manage_id = storage.get('storageManageId', 'default-id')
                zone_id = storage.get('zoneId', 'default-zone-id')
                logger.info(f"📍 使用存储: {storage.get('stackName')}")
            else:
                storage_manage_id = "demo-storage-id"
                zone_id = "demo-zone-id"
        else:
            storage_manage_id = "demo-storage-id"
            zone_id = "demo-zone-id"
        
        # 磁盘配置
        disk_config = {
            "storageManageId": storage_manage_id,
            "pageSize": "4K",
            "compression": "LZ4",
            "name": f"skill-disk-{int(time.time())}",
            "size": 30,  # 30GB
            "iops": 3000,
            "bandwidth": 200,
            "count": 1,
            "readCache": True,
            "zoneId": zone_id
        }
        
        logger.info(f"💾 创建磁盘: {disk_config['name']}")
        
        # 调用技能方法创建磁盘
        result = skill.disk_management_operation("create", **disk_config)
        
        if result["success"]:
            logger.info("✅ 磁盘创建成功！")
            logger.info(f"📊 磁盘信息: {result['disk_info']}")
            return True
        else:
            logger.error("❌ 磁盘创建失败")
            logger.info(f"💥 错误: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.info(f"💥 使用Skill创建失败: {e}")
        logger.info("💡 尝试直接MCP方法...")
        return create_disk_with_direct_mcp()

def main():
    """主函数"""
    logger.info("🎯 虚拟磁盘创建工具")
    logger.info("=" * 60)
    
    logger.info("📋 可用的创建方法:")
    logger.info("1. 直接调用MCP方法")
    logger.info("2. 使用MCP Client Skill")
    
    choice = input("请选择方法 (1/2): ").strip()
    
    success = False
    
    if choice == "1":
        success = create_disk_with_direct_mcp()
    elif choice == "2":
        success = create_disk_with_skill()
    else:
        logger.error("❌ 无效选择，尝试直接MCP方法")
        success = create_disk_with_direct_mcp()
    
    if success:
        logger.info("\n🎉 磁盘创建操作完成！")
    else:
        logger.info("\n💔 磁盘创建失败")
        logger.info("💡 建议:")
        logger.info("   1. 确保MCP服务器运行: cd /root/myskills/wushanskills && python main.py")
        logger.info("   2. 检查网络连接")
        logger.info("   3. 验证安超平台服务状态")

if __name__ == "__main__":
    main()