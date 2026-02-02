#!/usr/bin/env python3
"""
磁盘创建状态检查器
检查已创建的batch-XXX磁盘状态
"""

from utils.audit import ArcherAudit
from Hosts import Hosts
from volumes import Volumes

def check_batch_disks():
    """检查已创建的batch磁盘"""
    
    print("🔍 检查批量磁盘创建状态")
    print("=" * 50)
    
    # 初始化连接
    audit = ArcherAudit("admin", "Admin@123", "https://172.118.57.100")
    if not audit.setSession():
        print("❌ 连接失败")
        return
    
    host = Hosts("admin", "Admin@123", "https://172.118.57.100", audit)
    volumes = Volumes(audit, host)
    
    try:
        # 获取所有磁盘列表
        disks = volumes.listAllDisks()
        if not disks:
            print("📭 没有找到任何磁盘")
            return
        
        # 筛选batch开头的磁盘
        batch_disks = []
        for disk in disks:
            if disk.get('name', '').startswith('batch-'):
                batch_disks.append(disk)
        
        print(f"📊 磁盘状态汇总")
        print(f"总磁盘数: {len(disks)}")
        print(f"Batch磁盘数: {len(batch_disks)}")
        
        if batch_disks:
            print(f"\n📁 Batch磁盘详情:")
            print("-" * 80)
            print(f"{'序号':<6} {'磁盘名称':<15} {'大小(GB)':<10} {'状态':<10} {'磁盘ID':<40}")
            print("-" * 80)
            
            for i, disk in enumerate(batch_disks[:20], 1):  # 显示前20个
                name = disk.get('name', 'N/A')
                size = disk.get('size', 0)
                status = disk.get('status', 'N/A')
                disk_id = disk.get('id', 'N/A')
                
                print(f"{i:<6} {name:<15} {size:<10} {status:<10} {disk_id:<40}")
            
            if len(batch_disks) > 20:
                print(f"... 还有 {len(batch_disks) - 20} 个磁盘未显示")
        
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
            print(f"\n📈 批次统计:")
            print("-" * 30)
            for batch, count in sorted(batch_stats.items())[:10]:  # 显示前10个批次
                print(f"{batch}: {count}个磁盘")
            if len(batch_stats) > 10:
                print(f"... 还有 {len(batch_stats) - 10} 个批次")
                
        print(f"\n🎉 成功创建了 {len(batch_disks)} 个batch磁盘!")
        
    except Exception as e:
        print(f"❌ 检查过程中发生错误: {e}")

if __name__ == "__main__":
    check_batch_disks()