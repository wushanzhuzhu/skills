#!/usr/bin/env python3
"""
继续磁盘创建脚本 - 从batch-210到batch-1000
创建剩余的791个虚拟磁盘，每个10GB
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
import time
from massive_disk_creator import MassiveDiskCreator

class ContinueMassiveDiskCreator(MassiveDiskCreator):
    """继承大规模磁盘创建器，继续创建剩余磁盘"""
    
    def __init__(self):
        super().__init__()
        
    def create_remaining_batches(self, start_batch: int = 3, end_batch: int = 10) -> dict:
        """创建剩余批次的磁盘 (3-10批 = batch-201到batch-1000)"""
        
        logger.info(f"🚀 继续大规模磁盘创建任务")
        logger.info(f"📊 批次范围: 第{start_batch}批 - 第{end_batch}批")
        logger.info(f"💾 每批100个磁盘，每个10GB")
        logger.info(f"🎯 总计: {(end_batch - start_batch + 1) * 100}个磁盘")
        logger.info(f"🏷️ 磁盘命名: batch-{((start_batch-1)*100+1):04d} 到 batch-{end_batch*100:04d}")
        logger.info("=" * 80)
        
        # 自动确认执行（非交互式环境）
        logger.info(f"\n⚠️  即将创建 {(end_batch - start_batch + 1) * 100} 个磁盘，自动确认执行...")
        
        start_time = time.time()
        all_results = []
        total_success = 0
        total_failed = 0
        
        for batch_num in range(start_batch, end_batch + 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"🚀 开始执行第 {batch_num}/10 批次")
            logger.info(f"{'='*80}")
            
            batch_result = self.create_single_batch(batch_num, 100, 10)
            all_results.append(batch_result)
            
            total_success += batch_result["success_count"]
            total_failed += batch_result["failed_count"]
            
            # 显示累计进度
            completed_disks = (batch_num - start_batch + 1) * 100
            total_target_disks = (end_batch - start_batch + 1) * 100
            logger.info(f"\n📊 累计进度: {completed_disks}/{total_target_disks} 磁盘")
            logger.info(f"✅ 累计成功: {total_success}")
            logger.error(f"❌ 累计失败: {total_failed}")
            logger.info(f"📈 累计成功率: {total_success/completed_disks*100:.1f}%")
            
            # 如果不是最后一批，等待一段时间再继续
            if batch_num < end_batch:
                logger.info(f"\n⏳ 第 {batch_num} 批次完成，等待5秒后继续下一批...")
                time.sleep(5)
        
        # 显示最终结果
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🎉 继续磁盘创建任务完成!")
        logger.info(f"{'='*80}")
        logger.info(f"⏱️  总耗时: {duration/60:.1f} 分钟")
        logger.info(f"📊 总磁盘数: {total_target_disks}个")
        logger.info(f"✅ 总成功: {total_success}个")
        logger.error(f"❌ 总失败: {total_failed}个")
        logger.info(f"📈 总成功率: {total_success/total_target_disks*100:.1f}%")
        logger.info(f"💾 成功总容量: {total_success * 10}GB")
        logger.info(f"🌐 目标环境: {all_results[0]['environment'] if all_results else 'N/A'}")
        
        # 生成详细报告
        report = {
            "task_summary": {
                "task_type": "continue_disk_creation",
                "start_batch": start_batch,
                "end_batch": end_batch,
                "total_batches": end_batch - start_batch + 1,
                "disks_per_batch": 100,
                "total_disks": total_target_disks,
                "disk_size_gb": 10,
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": duration,
                "total_success": total_success,
                "total_failed": total_failed,
                "success_rate": total_success/total_target_disks*100,
                "total_capacity_gb": total_success * 10
            },
            "batch_results": all_results
        }
        
        # 保存报告
        report_file = f"continue_disk_creation_report_{int(start_time)}.json"
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"📄 详细报告已保存: {report_file}")
        
        return report

def main():
    """命令行界面"""
    logger.info("🔥 继续大规模磁盘创建器")
    logger.info("从batch-210到batch-1000创建剩余的791个10GB磁盘")
    logger.info("=" * 60)
    
    # 创建继续磁盘创建器实例
    creator = ContinueMassiveDiskCreator()
    
    # 创建剩余批次 (第3批到第10批)
    result = creator.create_remaining_batches(
        start_batch=3,  # 从第3批开始 (batch-201-300)
        end_batch=10    # 到第10批结束 (batch-901-1000)
    )
    
    total_success = result["task_summary"]["total_success"]
    total_disks = result["task_summary"]["total_disks"]
    
    if total_success > 0:
        logger.info(f"\n🎉 任务成功完成! 成功创建了 {total_success}/{total_disks} 个磁盘")
    else:
        logger.info("\n❌ 任务执行失败!")

if __name__ == "__main__":
    main()