#!/usr/bin/env python3
"""
创建10G虚拟磁盘脚本
使用production环境配置
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

def create_10g_disk():
    """在production环境创建10G虚拟磁盘"""
    logger.info("🚀 开始在production环境创建10G虚拟磁盘...")
    
    # 1. 加载环境配置
    env_manager = EnvironmentManager()
    env_info = env_manager.get_connection_info("production")
    
    if not env_info:
        logger.error("❌ 无法获取production环境配置")
        return False
    
    logger.info(f"✅ 环境配置加载完成: {env_info['name']}")
    logger.info(f"   URL: {env_info['url']}")
    logger.info(f"   存储后端: {env_info['storage_backend']}")
    
    try:
        # 2. 初始化连接
        logger.info("\n🔗 正在连接到ArcherOSS平台...")
        audit = ArcherAudit(env_info['username'], env_info['password'], env_info['url'])
        audit.setSession()
        host = Hosts(env_info['username'], env_info['password'], env_info['url'], audit)
        volumes = Volumes(audit, host)
        
        logger.info("✅ 平台连接成功")
        
        # 3. 获取存储资源信息
        logger.info("\n📊 正在获取存储资源信息...")
        stors = host.getStorsbyDiskType()
        zone_id = host.zone
        
        if not stors:
            logger.error("❌ 无法获取存储资源信息")
            return False
        
        logger.info(f"✅ 获取到 {len(stors)} 个存储资源:")
        for i, stor in enumerate(stors):
            logger.info(f"   {i+1}. {stor['stackName']} (ID: {stor['storageManageId'][:8]}...)")
        
        # 选择第一个存储资源
        storage_info = stors[0]
        storage_id = storage_info['storageManageId']
        
        # 4. 配置磁盘参数（生产环境优化配置）
        logger.info("\n⚙️ 配置磁盘参数（生产环境优化）...")
        disk_config = {
            "storageManageId": storage_id,
            "pageSize": "8K",       # 生产环境推荐8K页面大小
            "compression": "LZ4",   # 平衡性能和压缩率
            "name": f"prod-disk-{int(time.time())}",  # 时间戳命名
            "size": 10,             # 10GB
            "iops": 1000,           # 生产环境推荐IOPS
            "bandwidth": 150,       # 生产环境推荐带宽
            "count": 1,             # 创建1个磁盘
            "readCache": True,      # 启用读缓存
            "zoneId": zone_id
        }
        
        logger.info("📋 磁盘配置:")
        logger.info(f"   名称: {disk_config['name']}")
        logger.info(f"   大小: {disk_config['size']}GB")
        logger.info(f"   页面大小: {disk_config['pageSize']}")
        logger.info(f"   压缩方式: {disk_config['compression']}")
        logger.info(f"   IOPS: {disk_config['iops']}")
        logger.info(f"   带宽: {disk_config['bandwidth']}MB/s")
        logger.info(f"   读缓存: {'启用' if disk_config['readCache'] else '禁用'}")
        
        # 5. 执行磁盘创建
        logger.info("\n🎯 正在创建虚拟磁盘...")
        start_time = time.time()
        
        result = volumes.createDisk_vstor(**disk_config)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 6. 处理创建结果
        logger.info(f"\n⏱️ 创建耗时: {duration:.2f}秒")
        
        if isinstance(result, list) and len(result) > 0:
            disk_info = result[0]
            logger.info("🎉 虚拟磁盘创建成功!")
            logger.info("\n📋 磁盘详细信息:")
            logger.info(f"   ID: {disk_info.get('id', 'N/A')}")
            logger.info(f"   名称: {disk_info.get('name', 'N/A')}")
            logger.info(f"   大小: {disk_info.get('size', 'N/A')}GB")
            logger.info(f"   状态: {disk_info.get('status', 'N/A')}")
            logger.info(f"   创建时间: {disk_info.get('createTime', 'N/A')}")
            logger.info(f"   存储池: {disk_info.get('poolName', 'N/A')}")
            
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
            return {
                "success": False,
                "error": result,
                "duration": duration
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
    result = create_10g_disk()
    
    if result.get("success"):
        logger.info(f"\n🎊 任务完成！磁盘 '{result['disk_name']}' 已成功创建")
        logger.info(f"📌 磁盘ID: {result['disk_id']}")
        logger.info(f"💾 大小: {result['size']}GB")
    else:
        logger.info(f"\n💥 任务失败！错误: {result.get('error', '未知错误')}")
        sys.exit(1)