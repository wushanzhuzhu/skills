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
最简单的磁盘创建脚本
直接导入main模块创建虚拟磁盘
"""

import sys
import time

# 添加主项目路径
sys.path.insert(0, '/root/myskills/wushanskills')
# 添加utils路径
sys.path.insert(0, '/root/myskills/wushanskills/utils')
sys.path.insert(0, '/root/myskills/wushanskills/utils/tools')

def main():
    logger.info("💾 创建虚拟磁盘 - 最简版本")
    logger.info("=" * 50)
    
    try:
        # 直接导入main模块
        import main
        
        logger.info("🔐 1. 建立MCP会话...")
        
        # 建立会话
        session_result = main.getSession("https://172.118.57.100", "admin", "Admin@123")
        logger.info(f"会话结果: {session_result}")
        
        if "成功" not in session_result:
            logger.error("❌ 会话建立失败，无法继续")
            return
        
        logger.info("✅ 会话建立成功")
        
        logger.info("\n📁 2. 获取存储信息...")
        
        # 获取存储信息
        stor_info = main.getStorinfo()
        logger.info(f"存储信息: {stor_info}")
        
        # 解析存储信息
        storage_manage_id = "demo-storage-id"
        zone_id = "demo-zone-id"
        
        if isinstance(stor_info, list) and len(stor_info) > 0:
            storage = stor_info[0]
            storage_manage_id = storage.get('storageManageId', 'demo-storage-id')
            zone_id = storage.get('zoneId', 'demo-zone-id')
            logger.info(f"使用存储: {storage.get('stackName', 'unknown')}")
            logger.info(f"StorageManageId: {storage_manage_id}")
            logger.info(f"ZoneId: {zone_id}")
        
        logger.info("\n💾 3. 创建虚拟磁盘...")
        
        # 磁盘配置
        disk_name = f"simple-disk-{int(time.time())}"
        
        logger.info(f"磁盘名称: {disk_name}")
        logger.info(f"存储ID: {storage_manage_id}")
        logger.info(f"区域ID: {zone_id}")
        logger.info("磁盘大小: 20GB")
        logger.info("页面大小: 4K")
        logger.info("压缩方式: Disabled")
        logger.info("IOPS: 2000")
        logger.info("带宽: 150MB/s")
        logger.info("读缓存: 启用")
        
        # 调用createDisk_vstor方法
        logger.info("\n🔧 执行磁盘创建...")
        
        disk_result = main.createDisk_vstor(
            storageManageId=storage_manage_id,
            pageSize="4K",
            compression="Disabled",
            name=disk_name,
            size=20,  # 20GB
            iops=2000,
            bandwidth=150,  # MB/s
            count=1,
            readCache=True,
            zoneId=zone_id
        )
        
        logger.info(f"创建结果: {disk_result}")
        
        if disk_result:
            logger.info("✅ 磁盘创建成功！")
            logger.info(f"磁盘信息: {disk_result}")
            
            # 验证创建结果
            logger.info("\n🔍 4. 验证创建结果...")
            volumes = main.get_volumes()
            
            if isinstance(volumes, list):
                logger.info(f"当前磁盘总数: {len(volumes)}")
                
                # 查找新创建的磁盘
                for disk in volumes:
                    if isinstance(disk, dict) and disk.get('name') == disk_name:
                        logger.info(f"✅ 找到新创建的磁盘: {disk}")
                        break
                else:
                    logger.info("⚠️ 未找到新创建的磁盘（可能需要等待同步）")
            else:
                logger.info("⚠️ 无法获取磁盘列表")
                
        else:
            logger.error("❌ 磁盘创建失败")
            
    except ImportError as e:
        logger.error(f"❌ 导入main模块失败: {e}")
        logger.info("💡 请确保:")
        logger.info("   1. 在正确的目录下运行此脚本")
        logger.info("   2. main.py文件存在")
        logger.info("   3. Python路径配置正确")
        
    except Exception as e:
        logger.info(f"💥 执行过程中发生异常: {e}")
        logger.info("💡 可能的原因:")
        logger.info("   1. MCP服务器未运行")
        logger.info("   2. 网络连接问题")
        logger.info("   3. 安超平台服务不可用")
        logger.info("   4. 权限不足")
        
    logger.info("\n🎉 脚本执行完成")

if __name__ == "__main__":
    main()