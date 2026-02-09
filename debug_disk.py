#!/usr/bin/env python3
"""
调试磁盘创建 - 检查现有磁盘配置和参数
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

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from utils.audit import ArcherAudit
from Hosts import Hosts
from volumes import Volumes
from env_manager import EnvironmentManager

def debug_disk_creation():
    """调试磁盘创建问题"""
    logger.info("🔍 调试磁盘创建...")
    
    # 1. 加载环境配置
    env_manager = EnvironmentManager()
    env_info = env_manager.get_connection_info("production")
    
    try:
        # 2. 初始化连接
        audit = ArcherAudit(env_info['username'], env_info['password'], env_info['url'])
        audit.setSession()
        host = Hosts(env_info['username'], env_info['password'], env_info['url'], audit)
        volumes = Volumes(audit, host)
        
        # 3. 查看现有磁盘
        logger.info("\n📊 查看现有磁盘配置...")
        existing_disks = volumes.listAllDisks()
        
        if existing_disks:
            logger.info(f"✅ 找到 {len(existing_disks)} 个现有磁盘:")
            for i, disk in enumerate(existing_disks[:3]):  # 只显示前3个
                logger.info(f"\n磁盘 {i+1}:")
                logger.info(f"   名称: {disk.get('name')}")
                logger.info(f"   大小: {disk.get('size')}GB")
                logger.info(f"   IOPS: {disk.get('iops')}")
                logger.info(f"   带宽: {disk.get('bandwidth')}")
                logger.info(f"   页面大小: {disk.get('pageSize')}")
                logger.info(f"   压缩方式: {disk.get('compression')}")
                logger.info(f"   读缓存: {disk.get('readCache')}")
                logger.info(f"   状态: {disk.get('status')}")
                if 'storageManageId' in disk:
                    logger.info(f"   存储ID: {disk['storageManageId'][:8]}...")
        else:
            logger.info("📭 没有找到现有磁盘")
        
        # 4. 获取存储信息详情
        logger.info("\n🏗️ 存储详细信息...")
        stors = host.getStorsbyDiskType()
        if stors:
            stor = stors[0]
            logger.info(f"存储名称: {stor['stackName']}")
            logger.info(f"存储ID: {stor['storageManageId']}")
            logger.info(f"区域ID: {stor['zoneId']}")
            logger.info(f"存储后端: {stor['storageBackend']}")
        
        # 5. 尝试用基础参数创建磁盘
        logger.info("\n🧪 尝试使用基础参数创建磁盘...")
        zone_id = host.zone
        
        # 使用更基础的参数
        basic_config = {
            "storageManageId": stors[0]['storageManageId'],
            "pageSize": "4K",        # 使用更基础的页面大小
            "compression": "Disabled", # 禁用压缩避免问题
            "name": f"basic-test-disk-{int(time.time())}",
            "size": 10,
            "iops": 100,             # 使用较低的IOPS
            "bandwidth": 50,          # 使用较低的带宽
            "count": 1,
            "readCache": False,       # 禁用读缓存
            "zoneId": zone_id
        }
        
        logger.info("基础配置:")
        for key, value in basic_config.items():
            logger.info(f"   {key}: {value}")
        
        result = volumes.createDisk_vstor(**basic_config)
        logger.info(f"\n基础配置创建结果: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 调试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import time
    debug_disk_creation()