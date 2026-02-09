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
简化版磁盘创建脚本
直接使用mcp_client_skill创建虚拟磁盘，避免交互模式问题
"""

import sys
import json
import time
from pathlib import Path

# 添加主项目路径
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client_skill import MCPClientSkill

def create_single_disk():
    """创建单个虚拟磁盘的简化示例"""
    
    logger.info("💾 创建虚拟磁盘 - 简化版本")
    logger.info("=" * 50)
    
    # 1. 创建技能实例
    skill = MCPClientSkill(env_id="production")
    
    # 2. 获取存储资源信息
    logger.info("🔍 获取存储资源信息...")
    try:
        resources = skill.resource_management_overview()
        
        if isinstance(resources, dict) and 'resources' in resources:
            storage_info = resources['resources'].get('storage', {})
            logger.info(f"📁 存储位置数量: {storage_info.get('total_locations', 0)}")
            
            if storage_info.get('details'):
                logger.info("🗂️ 可用存储位置:")
                for i, storage in enumerate(storage_info['details'], 1):
                    logger.info(f"   {i}. {storage.get('stackName', 'unknown')} - {storage.get('storageBackend', 'unknown')}")
                
                # 使用第一个存储位置
                storage = storage_info['details'][0]
                storage_manage_id = storage.get('storageManageId', 'default-storage-id')
                zone_id = storage.get('zoneId', 'default-zone-id')
                logger.info(f"\n📍 使用存储: {storage.get('stackName')}")
                logger.info(f"   StorageManageId: {storage_manage_id}")
                logger.info(f"   ZoneId: {zone_id}")
            else:
                logger.info("⚠️ 没有找到存储详情，使用默认配置")
                storage_manage_id = "default-storage-id"
                zone_id = "default-zone-id"
        else:
            logger.info("⚠️ 资源获取失败，使用默认配置")
            storage_manage_id = "default-storage-id"
            zone_id = "default-zone-id"
            
    except Exception as e:
        logger.warning(f"⚠️ 获取资源信息失败: {e}")
        logger.info("💡 使用默认配置继续")
        storage_manage_id = "demo-storage-id"
        zone_id = "demo-zone-id"
    
    # 3. 配置磁盘参数
    logger.info("\n💾 配置磁盘参数...")
    
    disk_config = {
        "storageManageId": storage_manage_id,
        "pageSize": "4K",
        "compression": "Disabled",
        "name": f"demo-disk-{int(time.time())}",
        "size": 20,  # 20GB
        "iops": 2000,
        "bandwidth": 150,  # MB/s
        "count": 1,
        "readCache": True,
        "zoneId": zone_id
    }
    
    logger.info("📋 磁盘配置:")
    for key, value in disk_config.items():
        logger.info(f"   {key}: {value}")
    
    # 4. 执行磁盘创建
    logger.info(f"\n🔧 开始创建磁盘: {disk_config['name']}")
    logger.info("⏳ 正在调用MCP方法...")
    
    try:
        result = skill.disk_management_operation("create", **disk_config)
        
        if result["success"]:
            logger.info("✅ 磁盘创建成功！")
            logger.info(f"📊 磁盘信息: {result['disk_info']}")
            
            # 5. 验证创建结果
            logger.info("\n🔍 验证创建结果...")
            try:
                volumes_result = skill.mcp_client.call_method("get_volumes")
                if volumes_result.success:
                    logger.info(f"📁 当前磁盘总数: {len(volumes_result.data) if isinstance(volumes_result.data, list) else 0}")
                    logger.info("✅ 磁盘创建验证完成")
                else:
                    logger.info("⚠️ 无法验证磁盘列表")
            except Exception as e:
                logger.warning(f"⚠️ 验证过程出错: {e}")
                
        else:
            logger.error("❌ 磁盘创建失败")
            logger.info(f"💥 错误信息: {result.get('error')}")
            logger.info(f"📋 使用的参数: {result.get('parameters_used')}")
            
    except Exception as e:
        logger.info(f"💥 创建过程发生异常: {e}")
        logger.info("💡 这可能是因为:")
        logger.info("   1. MCP服务器未运行")
        logger.info("   2. 会话未建立")
        logger.info("   3. 存储配置不正确")

def create_multiple_disks():
    """创建多个磁盘的示例"""
    
    logger.info("\n📦 批量创建磁盘示例")
    logger.info("=" * 50)
    
    skill = MCPClientSkill(env_id="production")
    
    # 批量配置
    disk_configs = []
    base_config = {
        "storageManageId": "demo-storage-id",
        "pageSize": "4K",
        "compression": "Disabled",
        "iops": 2000,
        "bandwidth": 150,
        "count": 1,
        "readCache": True,
        "zoneId": "demo-zone-id"
    }
    
    # 创建3个不同大小的磁盘
    sizes = [10, 20, 30]  # 10GB, 20GB, 30GB
    
    for i, size in enumerate(sizes):
        config = base_config.copy()
        config['name'] = f"batch-disk-{int(time.time())}-{i+1}"
        config['size'] = size
        disk_configs.append(config)
    
    logger.info(f"📋 准备创建 {len(disk_configs)} 个磁盘:")
    for i, config in enumerate(disk_configs, 1):
        logger.info(f"   {i}. {config['name']} - {config['size']}GB")
    
    # 批量创建
    results = []
    for i, config in enumerate(disk_configs, 1):
        logger.info(f"\n💾 创建第 {i}/{len(disk_configs)} 个磁盘: {config['name']}")
        
        result = skill.disk_management_operation("create", **config)
        results.append(result)
        
        if result["success"]:
            logger.info(f"   ✅ 创建成功")
        else:
            logger.info(f"   ❌ 创建失败: {result.get('error')}")
        
        # 添加延迟避免API频率限制
        if i < len(disk_configs):
            logger.info("   ⏳ 等待2秒...")
            time.sleep(2)
    
    # 统计结果
    success_count = sum(1 for r in results if r["success"])
    logger.info(f"\n📊 批量创建结果:")
    logger.info(f"   总数: {len(results)}")
    logger.info(f"   成功: {success_count}")
    logger.info(f"   失败: {len(results) - success_count}")
    logger.info(f"   成功率: {success_count/len(results)*100:.1f}%")

def main():
    """主函数"""
    logger.info("🎮 MCP Client Skill 磁盘创建工具")
    logger.info("=" * 60)
    
    logger.info("📚 本工具提供:")
    logger.info("1. 创建单个虚拟磁盘")
    logger.info("2. 批量创建多个虚拟磁盘")
    logger.info("3. 自动验证创建结果")
    logger.info("4. 详细的错误处理")
    
    choice = input("\n请选择操作 (1/2): ").strip()
    
    if choice == "1":
        create_single_disk()
    elif choice == "2":
        create_multiple_disks()
    else:
        logger.error("❌ 无效选择，退出程序")
        return
    
    logger.info("\n🎉 操作完成！")

if __name__ == "__main__":
    main()