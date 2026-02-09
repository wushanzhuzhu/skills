#!/usr/bin/env python3
"""
Volume Creator Script - 基于 volume-creator skill
创建10GB虚拟磁盘的标准配置
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

import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.audit import ArcherAudit
from Hosts import Hosts
from volumes import Volumes
import time
import uuid

def create_10gb_disk():
    """创建10GB虚拟磁盘"""
    logger.info("🎯 开始创建10GB虚拟磁盘...")
    
    # 初始化认证和会话
    logger.info("📝 初始化认证会话...")
    from config import DEFAULT_PLATFORM_USER, DEFAULT_PLATFORM_PASSWORD
    
    # 使用指定凭据初始化ArcherAudit
    audit = ArcherAudit(
        username="admin",
        password="Admin@123",
        url="https://172.118.57.100"  # 目标环境地址
    )
    session_result = audit.setSession()
    
    if not session_result:
        logger.error("❌ 认证失败，请检查配置")
        return False
        
    # 初始化主机管理
    host = Hosts(
        username="admin",
        password="Admin@123",
        url="https://172.118.57.100",
        audit=audit
    )
    volumes = Volumes(audit, host)
    
    # 获取存储管理信息
    logger.info("🔍 获取存储资源信息...")
    storage_info = host.getStorsbyDiskType()
    
    if not storage_info:
        logger.error("❌ 无法获取存储管理信息")
        return False
    
    storage_list = storage_info
    if not storage_list:
        logger.error("❌ 没有可用的存储资源")
        return False
    
    # 使用第一个可用的存储管理ID
    storage_manage_id = storage_list[0].get('storageManageId')
    logger.info(f"✅ 使用存储管理ID: {storage_manage_id}")
    
    # 使用Hosts中获取的zone信息
    zone_id = host.zone
    logger.info(f"✅ 使用区域ID: {zone_id}")
    
    # 根据存储性能限制调整参数（基于storage返回的性能信息）
    disk_config = {
        "storageManageId": storage_manage_id,
        "pageSize": "4K",         # 标准页面大小
        "compression": "Disabled", # 禁用压缩避免兼容问题
        "name": f"volume-10gb-{str(uuid.uuid4())[:8]}",  # 唯一命名
        "size": 10,               # 10GB
        "iops": 400,              # 基于存储性能：读写IOPS=400
        "bandwidth": 40,          # 基于存储性能：读写吞吐量=40MB/s
        "count": 1,               # 创建1个磁盘
        "readCache": False,       # 关闭读缓存
        "zoneId": zone_id or "default"
    }
    
    logger.info(f"📋 磁盘配置:")
    logger.info(f"   名称: {disk_config['name']}")
    logger.info(f"   大小: {disk_config['size']}GB")
    logger.info(f"   IOPS: {disk_config['iops']}")
    logger.info(f"   带宽: {disk_config['bandwidth']} MB/s")
    logger.info(f"   页面大小: {disk_config['pageSize']}")
    logger.info(f"   压缩方式: {disk_config['compression']}")
    logger.info(f"   读缓存: {'开启' if disk_config['readCache'] else '关闭'}")
    
    # 执行创建
    logger.info("🚀 开始创建磁盘...")
    result = volumes.createDisk_vstor(**disk_config)
    
    # 检查创建结果
    if isinstance(result, list) and len(result) > 0:
        disk_info = result[0]
        logger.info("✅ 虚拟磁盘创建成功!")
        logger.info(f"📁 磁盘ID: {disk_info.get('id')}")
        logger.info(f"📝 磁盘名称: {disk_info.get('name')}")
        logger.info(f"💾 磁盘大小: {disk_config['size']}GB")
        logger.info(f"⚡ IOPS: {disk_config['iops']}")
        logger.info(f"🌐 带宽: {disk_config['bandwidth']} MB/s")
        return True
    elif isinstance(result, dict) and 'data' in result and isinstance(result['data'], list) and len(result['data']) > 0:
        disk_info = result['data'][0]
        logger.info("✅ 虚拟磁盘创建成功!")
        logger.info(f"📁 磁盘ID: {disk_info.get('id')}")
        logger.info(f"📝 磁盘名称: {disk_info.get('name')}")
        logger.info(f"💾 磁盘大小: {disk_config['size']}GB")
        logger.info(f"⚡ IOPS: {disk_config['iops']}")
        logger.info(f"🌐 带宽: {disk_config['bandwidth']} MB/s")
        return True
    else:
        logger.error("❌ 虚拟磁盘创建失败:")
        logger.info(f"错误信息: {result}")
        return False

if __name__ == "__main__":
    success = create_10gb_disk()
    if success:
        logger.info("\n🎉 10GB虚拟磁盘创建完成!")
    else:
        logger.info("\n💥 创建失败，请检查配置和日志")
        sys.exit(1)