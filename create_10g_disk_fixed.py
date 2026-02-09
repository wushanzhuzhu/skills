#!/usr/bin/env python3
"""
修正后的10G磁盘创建脚本 - 基于现有磁盘配置
"""

import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

import time
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from utils.audit import ArcherAudit
from Hosts import Hosts
from volumes import Volumes
from env_manager import EnvironmentManager

def create_10g_disk_fixed():
    """基于现有磁盘配置创建10G磁盘"""
    logger.info("🚀 使用修正参数在production环境创建10G虚拟磁盘...")
    
    # 1. 加载环境配置
    env_manager = EnvironmentManager()
    env_info = env_manager.get_connection_info("production")
    
    if not env_info:
        logger.error("❌ 无法获取production环境配置")
        return False
    
    try:
        # 2. 初始化连接
        logger.info("🔗 正在连接到ArcherOSS平台...")
        audit = ArcherAudit(env_info['username'], env_info['password'], env_info['url'])
        audit.setSession()
        host = Hosts(env_info['username'], env_info['password'], env_info['url'], audit)
        volumes = Volumes(audit, host)
        
        # 3. 获取存储资源
        stors = host.getStorsbyDiskType()
        zone_id = host.zone
        storage_info = stors[0]
        
        # 4. 使用与现有磁盘相同的配置格式
        logger.info("⚙️ 使用现有磁盘成功的配置格式...")
        
        # 基于现有磁盘配置：使用4K而不是4K，LZ4压缩，中等IOPS和带宽
        disk_config = {
            "storageManageId": storage_info['storageManageId'],
            "pageSize": "4K",           # 修正：使用4K而不是4K
            "compression": "LZ4",        # 使用LZ4压缩（现有磁盘使用的）
            "name": f"fixed-disk-{int(time.time())}", 
            "size": 10,
            "iops": 400,                 # 基于存储描述中的性能：读写IOPS=400
            "bandwidth": 40,             # 基于存储描述：读写吞吐量=40MB/s
            "count": 1,
            "readCache": True,           # 与现有磁盘一致
            "zoneId": zone_id
        }
        
        logger.info("📋 修正后的磁盘配置:")
        for key, value in disk_config.items():
            logger.info(f"   {key}: {value}")
        
        # 5. 执行创建
        logger.info("\n🎯 正在创建虚拟磁盘...")
        start_time = time.time()
        
        result = volumes.createDisk_vstor(**disk_config)
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"\n⏱️ 创建耗时: {duration:.2f}秒")
        
        # 6. 检查结果
        if isinstance(result, list) and len(result) > 0:
            disk_info = result[0]
            logger.info("🎉 虚拟磁盘创建成功!")
            logger.info("\n📋 磁盘详细信息:")
            logger.info(f"   ID: {disk_info.get('id', 'N/A')}")
            logger.info(f"   名称: {disk_info.get('name', 'N/A')}")
            logger.info(f"   大小: {disk_info.get('size', 'N/A')}GB")
            logger.info(f"   状态: {disk_info.get('status', 'N/A')}")
            logger.info(f"   创建时间: {disk_info.get('createTime', 'N/A')}")
            logger.info(f"   页面大小: {disk_info.get('pagesize', 'N/A')}")
            logger.info(f"   压缩方式: {disk_info.get('compression', 'N/A')}")
            logger.info(f"   读缓存: {disk_info.get('readCache', 'N/A')}")
            
            return {
                "success": True,
                "disk_id": disk_info.get('id'),
                "disk_name": disk_info.get('name'),
                "size": disk_info.get('size'),
                "status": disk_info.get('status'),
                "duration": duration
            }
        else:
            logger.error("❌ 虚拟磁盘创建失败!")
            logger.info(f"错误信息: {result}")
            
            # 7. 如果还是失败，尝试最小化参数
            logger.info("\n🔄 尝试最小化参数...")
            minimal_config = {
                "storageManageId": storage_info['storageManageId'],
                "pageSize": "4K",
                "compression": "LZ4",
                "name": f"minimal-disk-{int(time.time())}", 
                "size": 10,
                "iops": 75,                  # 最小IOPS
                "bandwidth": 1,              # 最小带宽
                "count": 1,
                "readCache": True,
                "zoneId": zone_id
            }
            
            logger.info("最小化配置:")
            for key, value in minimal_config.items():
                logger.info(f"   {key}: {value}")
            
            result2 = volumes.createDisk_vstor(**minimal_config)
            
            if isinstance(result2, list) and len(result2) > 0:
                disk_info = result2[0]
                logger.info("🎉 使用最小化参数创建成功!")
                return {
                    "success": True,
                    "disk_id": disk_info.get('id'),
                    "disk_name": disk_info.get('name'),
                    "method": "minimal_config"
                }
            else:
                logger.error(f"❌ 最小化参数也失败: {result2}")
                return {
                    "success": False,
                    "error_first": result,
                    "error_second": result2
                }
            
    except Exception as e:
        logger.error(f"❌ 创建过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    result = create_10g_disk_fixed()
    
    if result.get("success"):
        logger.info(f"\n🎊 任务完成！磁盘 '{result['disk_name']}' 已成功创建")
        logger.info(f"📌 磁盘ID: {result['disk_id']}")
        logger.info(f"💾 大小: {result.get('size', 'N/A')}GB")
        if result.get("method") == "minimal_config":
            logger.info("💡 提示：使用最小化参数配置")
    else:
        logger.info(f"\n💥 任务失败！")
        if result.get("error_first"):
            logger.info(f"第一次尝试错误: {result['error_first']}")
        if result.get("error_second"):
            logger.info(f"第二次尝试错误: {result['error_second']}")
        if result.get("error"):
            logger.info(f"异常错误: {result['error']}")
        sys.exit(1)