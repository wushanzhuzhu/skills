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
批量磁盘创建脚本 - 创建1000个10GB磁盘，分10批执行
每批100个磁盘，使用batch-001到batch-1000命名规则
"""

import sys
import os
import time
from env_disk_creator import EnvironmentAwareDiskCreator

class MassiveDiskCreator:
    """大规模磁盘创建器"""
    
    def __init__(self):
        self.env_creator = EnvironmentAwareDiskCreator()
        
    def create_single_batch(self, batch_num: int, total_disks: int = 100, disk_size: int = 10) -> dict:
        """创建单个批次的磁盘"""
        
        start_index = (batch_num - 1) * total_disks + 1
        end_index = batch_num * total_disks
        
        logger.info(f"🚀 开始创建第 {batch_num}/10 批磁盘")
        logger.info(f"📁 磁盘编号: {start_index:04d} - {end_index:04d}")
        logger.info(f"💾 每个大小: {disk_size}GB")
        logger.info(f"🎯 本批总数: {total_disks}个")
        logger.info("=" * 60)
        
        # 选择环境（使用自动选择，优先生产环境）
        env_id = self.env_creator.auto_select_environment("production")
        if not env_id:
            logger.error("❌ 无法选择合适的环境")
            return {"success": False, "batch_num": batch_num}
            
        # 验证环境
        if not self.env_creator.check_environment(env_id):
            logger.error("❌ 环境验证失败")
            return {"success": False, "batch_num": batch_num}
        
        results = []
        success_count = 0
        failed_count = 0
        
        for i in range(start_index, end_index + 1):
            disk_name = f"batch-{i:04d}"
            logger.info(f"\n📁 创建磁盘 {i:04d}/1000: {disk_name}")
            
            try:
                from smart_disk_creator import SmartDiskCreator
                
                # 每次创建新的连接
                disk_creator = SmartDiskCreator(
                    self.env_creator.connection_info['username'],
                    self.env_creator.connection_info['password'],
                    self.env_creator.connection_info['url']
                )
                
                # 生成配置并设置自定义名称
                config_result = disk_creator.generate_optimal_config(disk_size, "standard")
                
                if not config_result["success"]:
                    logger.error(f"❌ 配置生成失败: {config_result['error']}")
                    failed_count += 1
                    results.append({
                        'disk_name': disk_name,
                        'disk_num': i,
                        'success': False,
                        'error': '配置生成失败'
                    })
                    continue
                
                # 更新磁盘名称
                config_result["config"]["name"] = disk_name
                
                # 验证配置
                validation = disk_creator.validate_parameters(config_result["config"])
                if not validation["valid"]:
                    logger.error("❌ 配置验证失败:")
                    for error in validation["errors"]:
                        logger.info(f"   • {error}")
                    failed_count += 1
                    results.append({
                        'disk_name': disk_name,
                        'disk_num': i,
                        'success': False,
                        'error': '配置验证失败'
                    })
                    continue
                
                # 创建磁盘
                logger.info(f"🔧 创建配置: 大小={disk_size}GB, IOPS={config_result['config']['iops']}, 带宽={config_result['config']['bandwidth']}MB/s")
                
                from volumes import Volumes
                volumes = Volumes(disk_creator.audit, disk_creator.host)
                result = volumes.createDisk_vstor(**config_result["config"])
                
                # 解析结果
                if isinstance(result, dict) and 'data' in result:
                    if result['data'] and len(result['data']) > 0:
                        disk_info = result['data'][0]
                        logger.info(f"✅ {disk_name} 创建成功! ID: {disk_info['id']}")
                        success_count += 1
                        results.append({
                            'disk_name': disk_name,
                            'disk_num': i,
                            'success': True,
                            'disk_id': disk_info['id']
                        })
                    else:
                        logger.error(f"❌ {disk_name} 创建失败: 返回数据为空")
                        failed_count += 1
                        results.append({
                            'disk_name': disk_name,
                            'disk_num': i,
                            'success': False,
                            'error': '返回数据为空'
                        })
                else:
                    logger.error(f"❌ {disk_name} 创建失败: 意外响应格式")
                    failed_count += 1
                    results.append({
                        'disk_name': disk_name,
                        'disk_num': i,
                        'success': False,
                        'error': '意外响应格式'
                    })
                
                # 添加延迟，避免API频率限制
                if i < end_index:
                    logger.info("⏳ 等待2秒后继续...")
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"❌ {disk_name} 创建出错: {e}")
                failed_count += 1
                results.append({
                    'disk_name': disk_name,
                    'disk_num': i,
                    'success': False,
                    'error': str(e)
                })
        
        # 显示批次结果
        logger.info(f"\n" + "=" * 70)
        logger.info(f"📊 第 {batch_num} 批次创建结果汇总")
        logger.info("=" * 70)
        logger.info(f"✅ 成功创建: {success_count}/{total_disks}")
        logger.error(f"❌ 创建失败: {failed_count}/{total_disks}")
        logger.info(f"📈 成功率: {success_count/total_disks*100:.1f}%")
        logger.info(f"💾 成功容量: {success_count * disk_size}GB")
        logger.info(f"🌐 目标环境: {self.env_creator.connection_info['name']}")
        
        # 显示失败的磁盘
        if failed_count > 0:
            logger.info(f"\n❌ 失败的磁盘:")
            for result in results:
                if not result['success']:
                    error_info = f" - {result.get('error', '未知错误')}"
                    logger.info(f"   {result['disk_name']}: 创建失败{error_info}")
        
        logger.info(f"\n🎉 第 {batch_num} 批次创建完成!")
        
        return {
            "batch_num": batch_num,
            "total_disks": total_disks,
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": success_count/total_disks*100,
            "total_capacity_gb": success_count * disk_size,
            "environment": self.env_creator.connection_info['name'],
            "results": results
        }
    
    def create_all_batches(self, total_batches: int = 10, disks_per_batch: int = 100, disk_size: int = 10):
        """创建所有批次的磁盘"""
        
        logger.info("🔥 大规模磁盘创建任务")
        logger.info("=" * 70)
        logger.info(f"🎯 总批次数: {total_batches}")
        logger.info(f"📁 每批磁盘: {disks_per_batch}个")
        logger.info(f"💾 磁盘大小: {disk_size}GB")
        logger.info(f"📊 总磁盘数: {total_batches * disks_per_batch}个")
        logger.info(f"💾 总容量: {total_batches * disks_per_batch * disk_size}GB")
        logger.info(f"🏷️ 命名规则: batch-001 到 batch-{total_batches * disks_per_batch:04d}")
        logger.info("=" * 70)
        
        # 自动确认执行（非交互式环境）
        logger.info(f"\n⚠️  即将创建 {total_batches * disks_per_batch} 个磁盘，自动确认执行...")
        # confirm = input(f"\n⚠️  即将创建 {total_batches * disks_per_batch} 个磁盘，确认执行? (yes/no): ")
        # if confirm.lower() != 'yes':
        #     logger.error("❌ 操作已取消")
        #     return
        
        start_time = time.time()
        all_results = []
        total_success = 0
        total_failed = 0
        
        for batch_num in range(1, total_batches + 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"🚀 开始执行第 {batch_num}/{total_batches} 批次")
            logger.info(f"{'='*80}")
            
            batch_result = self.create_single_batch(batch_num, disks_per_batch, disk_size)
            all_results.append(batch_result)
            
            total_success += batch_result["success_count"]
            total_failed += batch_result["failed_count"]
            
            # 显示累计进度
            completed_disks = batch_num * disks_per_batch
            logger.info(f"\n📊 累计进度: {completed_disks}/{total_batches * disks_per_batch} 磁盘")
            logger.info(f"✅ 累计成功: {total_success}")
            logger.error(f"❌ 累计失败: {total_failed}")
            logger.info(f"📈 累计成功率: {total_success/completed_disks*100:.1f}%")
            
            # 如果不是最后一批，等待一段时间再继续
            if batch_num < total_batches:
                logger.info(f"\n⏳ 第 {batch_num} 批次完成，等待5秒后继续下一批...")
                time.sleep(5)
        
        # 显示最终结果
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🎉 大规模磁盘创建任务完成!")
        logger.info(f"{'='*80}")
        logger.info(f"⏱️  总耗时: {duration/60:.1f} 分钟")
        logger.info(f"📊 总磁盘数: {total_batches * disks_per_batch}个")
        logger.info(f"✅ 总成功: {total_success}个")
        logger.error(f"❌ 总失败: {total_failed}个")
        logger.info(f"📈 总成功率: {total_success/(total_batches * disks_per_batch)*100:.1f}%")
        logger.info(f"💾 成功总容量: {total_success * disk_size}GB")
        logger.info(f"🌐 目标环境: {all_results[0]['environment'] if all_results else 'N/A'}")
        
        # 生成详细报告
        report = {
            "task_summary": {
                "total_batches": total_batches,
                "disks_per_batch": disks_per_batch,
                "total_disks": total_batches * disks_per_batch,
                "disk_size_gb": disk_size,
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": duration,
                "total_success": total_success,
                "total_failed": total_failed,
                "success_rate": total_success/(total_batches * disks_per_batch)*100,
                "total_capacity_gb": total_success * disk_size
            },
            "batch_results": all_results
        }
        
        # 保存报告
        report_file = f"disk_creation_report_{int(start_time)}.json"
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"📄 详细报告已保存: {report_file}")
        
        return report

def main():
    """命令行界面"""
    creator = MassiveDiskCreator()
    
    logger.info("🔥 大规模磁盘创建器")
    logger.info("创建1000个10GB磁盘，分10批执行")
    logger.info("=" * 50)
    
    # 创建所有批次
    creator.create_all_batches(
        total_batches=10,
        disks_per_batch=100,
        disk_size=10
    )

if __name__ == "__main__":
    main()