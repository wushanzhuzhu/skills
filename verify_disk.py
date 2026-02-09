#!/usr/bin/env python3
"""
验证磁盘创建结果
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

def verify_disk_creation():
    """验证磁盘创建结果"""
    logger.info("🔍 验证磁盘创建结果...")
    
    # 加载环境配置
    env_manager = EnvironmentManager()
    env_info = env_manager.get_connection_info("production")
    
    try:
        # 初始化连接
        audit = ArcherAudit(env_info['username'], env_info['password'], env_info['url'])
        audit.setSession()
        host = Hosts(env_info['username'], env_info['password'], env_info['url'], audit)
        volumes = Volumes(audit, host)
        
        # 检查刚才创建的磁盘
        logger.info("\n📋 检查最近创建的磁盘...")
        
        # 检查第一个磁盘
        disk1 = volumes.getDiskbyName_exact("fixed-disk-1770001706")
        if disk1:
            logger.info("✅ 找到磁盘 'fixed-disk-1770001706':")
            logger.info(f"   ID: {disk1.get('id')}")
            logger.info(f"   大小: {disk1.get('size')}GB")
            logger.info(f"   状态: {disk1.get('status')}")
            logger.info(f"   页面大小: {disk1.get('pagesize')}")
            logger.info(f"   压缩方式: {disk1.get('compression')}")
            logger.info(f"   读缓存: {disk1.get('readCache')}")
            logger.info(f"   创建时间: {disk1.get('createTime')}")
        else:
            logger.error("❌ 未找到磁盘 'fixed-disk-1770001706'")
        
        # 检查第二个磁盘
        disk2 = volumes.getDiskbyName_exact("minimal-disk-1770001706")
        if disk2:
            logger.info("\n✅ 找到磁盘 'minimal-disk-1770001706':")
            logger.info(f"   ID: {disk2.get('id')}")
            logger.info(f"   大小: {disk2.get('size')}GB")
            logger.info(f"   状态: {disk2.get('status')}")
            logger.info(f"   页面大小: {disk2.get('pagesize')}")
            logger.info(f"   压缩方式: {disk2.get('compression')}")
            logger.info(f"   读缓存: {disk2.get('readCache')}")
            logger.info(f"   创建时间: {disk2.get('createTime')}")
        else:
            logger.error("❌ 未找到磁盘 'minimal-disk-1770001706'")
        
        return disk1, disk2
        
    except Exception as e:
        logger.error(f"❌ 验证过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    disk1, disk2 = verify_disk_creation()
    
    if disk1:
        logger.info(f"\n🎉 第一个磁盘创建成功！")
        logger.info(f"📌 磁盘ID: {disk1.get('id')}")
        logger.info(f"💾 大小: {disk1.get('size')}GB")
    
    if disk2:
        logger.info(f"\n🎉 第二个磁盘创建成功！")
        logger.info(f"📌 磁盘ID: {disk2.get('id')}")
        logger.info(f"💾 大小: {disk2.get('size')}GB")
    
    if disk1 or disk2:
        logger.info("\n✅ 至少有一个10G磁盘创建成功！")
    else:
        logger.info("\n❌ 没有找到成功创建的磁盘")