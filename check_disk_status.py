#!/usr/bin/env python3
"""
磁盘创建状态检查器
检查已创建的batch-XXX磁盘状态
"""

from utils.audit import ArcherAudit
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

from Hosts import Hosts
from volumes import Volumes

def check_batch_disks():
    """检查已创建的batch磁盘"""
    
    logger.info("🔍 检查批量磁盘创建状态")
    logger.info("=" * 50)
    
    # 初始化连接
    audit = ArcherAudit("admin", "Admin@123", "https://172.118.57.100")
    if not audit.setSession():
        logger.error("❌ 连接失败")
        return
    
    host = Hosts("admin", "Admin@123", "https://172.118.57.100", audit)
    volumes = Volumes(audit, host)
    
    try:
        # 获取所有磁盘列表
        disks = volumes.listAllDisks()
        if not disks:
            logger.info("📭 没有找到任何磁盘")
            return
        
        # 筛选batch开头的磁盘
        batch_disks = []
        for disk in disks:
            if disk.get('name', '').startswith('batch-'):
                batch_disks.append(disk)
        
        logger.info(f"📊 磁盘状态汇总")
        logger.info(f"总磁盘数: {len(disks)}")
        logger.info(f"Batch磁盘数: {len(batch_disks)}")
        
        if batch_disks:
            logger.info(f"\n📁 Batch磁盘详情:")
            logger.info("-" * 80)
            logger.info(f"{'序号':<6} {'磁盘名称':<15} {'大小(GB)':<10} {'状态':<10} {'磁盘ID':<40}")
            logger.info("-" * 80)
            
            for i, disk in enumerate(batch_disks[:20], 1):  # 显示前20个
                name = disk.get('name', 'N/A')
                size = disk.get('size', 0)
                status = disk.get('status', 'N/A')
                disk_id = disk.get('id', 'N/A')
                
                logger.info(f"{i:<6} {name:<15} {size:<10} {status:<10} {disk_id:<40}")
            
            if len(batch_disks) > 20:
                logger.info(f"... 还有 {len(batch_disks) - 20} 个磁盘未显示")
        
        # 按批次统计
        batch_stats = {}
        for disk in batch_disks:
            name = disk.get('name', '')
            if name.startswith('batch-'):
                batch_num = name[6:9]  # 提取batch-XXX中的XXX
                batch_key = f"batch-{batch_num}"
                if batch_key not in batch_stats:
                    batch_stats[batch_key] = 0
                batch_stats[batch_key] += 1
        
        if batch_stats:
            logger.info(f"\n📈 批次统计:")
            logger.info("-" * 30)
            for batch, count in sorted(batch_stats.items())[:10]:  # 显示前10个批次
                logger.info(f"{batch}: {count}个磁盘")
            if len(batch_stats) > 10:
                logger.info(f"... 还有 {len(batch_stats) - 10} 个批次")
                
        logger.info(f"\n🎉 成功创建了 {len(batch_disks)} 个batch磁盘!")
        
    except Exception as e:
        logger.error(f"❌ 检查过程中发生错误: {e}")

if __name__ == "__main__":
    check_batch_disks()