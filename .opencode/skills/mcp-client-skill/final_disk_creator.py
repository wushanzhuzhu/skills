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
最终简化版磁盘创建脚本
在正确目录下运行，解决所有路径问题
"""

import main
import time
import json

def main():
    logger.info("💾 创建虚拟磁盘 - 最终简化版")
    logger.info("=" * 50)
    
    try:
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
        logger.info(f"存储信息类型: {type(stor_info)}")
        
        storage_manage_id = "demo-storage-id"
        zone_id = "demo-zone-id"
        
        if isinstance(stor_info, list) and len(stor_info) > 0:
            logger.info(f"✅ 找到 {len(stor_info)} 个存储位置")
            storage = stor_info[0]
            storage_manage_id = storage.get('storageManageId', 'demo-storage-id')
            zone_id = storage.get('zoneId', 'demo-zone-id')
            logger.info(f"📍 使用存储: {storage.get('stackName', 'unknown')}")
            logger.info(f"StorageManageId: {storage_manage_id}")
            logger.info(f"ZoneId: {zone_id}")
        else:
            logger.info("⚠️ 获取存储信息失败，使用默认ID")
        
        logger.info("\n💾 3. 创建虚拟磁盘...")
        
        # 磁盘配置
        disk_name = f"final-disk-{int(time.time())}"
        
        logger.info(f"磁盘名称: {disk_name}")
        logger.info(f"存储ID: {storage_manage_id}")
        logger.info(f"区域ID: {zone_id}")
        logger.info(f"磁盘大小: 20GB")
        logger.info(f"页面大小: 4K")
        logger.info(f"压缩方式: Disabled")
        logger.info(f"IOPS: 2000")
        logger.info(f"带宽: 150MB/s")
        logger.info(f"读缓存: 启用")
        
        # 创建磁盘
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
            logger.info(f"磁盘信息: {json.dumps(disk_result, indent=2, ensure_ascii=False)}")
            
            # 验证创建结果
            logger.info("\n🔍 4. 验证创建结果...")
            volumes = main.get_volumes()
            
            if isinstance(volumes, list):
                logger.info(f"📁 当前磁盘总数: {len(volumes)}")
                
                # 查找新创建的磁盘
                for disk in volumes:
                    if isinstance(disk, dict) and disk.get('name') == disk_name:
                        logger.info(f"✅ 找到新创建的磁盘")
                        logger.info(f"磁盘详情: {json.dumps(disk, indent=2, ensure_ascii=False)}")
                        break
                else:
                    logger.info("⚠️ 未找到新创建的磁盘（可能需要等待同步）")
            else:
                logger.info("⚠️ 无法获取磁盘列表")
                
        else:
            logger.error("❌ 磁盘创建失败")
            
        logger.info("\n🎉 操作完成")
        
    except Exception as e:
        logger.info(f"💥 执行过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        
        logger.info("\n💡 故障排除建议:")
        logger.info("1. 确保MCP服务器正在运行: python main.py")
        logger.info("2. 检查网络连接到 https://172.118.57.100")
        logger.info("3. 验证用户名和密码是否正确")
        logger.info("4. 确认安超平台服务正常运行")

if __name__ == "__main__":
    main()