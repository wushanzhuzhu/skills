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
from env_disk_creator import EnvironmentAwareDiskCreator

class ContinueDiskCreator:
    """继续磁盘创建器"""
    
    def __init__(self, session_id: str = None):
        self.env_creator = EnvironmentAwareDiskCreator()
        self.session_id = session_id
        if session_id:
            logger.info(f"🔑 使用指定会话ID: {session_id}")
    
    def create_remaining_disks(self, start_num: int = 210, end_num: int = 1000, disk_size: int = 10) -> dict:
        """创建剩余的磁盘"""
        
        total_disks = end_num - start_num + 1
        logger.info(f"🚀 继续磁盘创建任务")
        logger.info(f"📊 磁盘范围: batch-{start_num:04d} 到 batch-{end_num:04d}")
        logger.info(f"💾 每个大小: {disk_size}GB")
        logger.info(f"🎯 总计: {total_disks}个磁盘")
        logger.info("=" * 80)
        
        # 选择环境（使用自动选择，优先生产环境）
        env_id = self.env_creator.auto_select_environment("production")
        if not env_id:
            logger.error("❌ 无法选择合适的环境")
            return {"success": False}
            
        # 验证环境
        if not self.env_creator.check_environment(env_id):
            logger.error("❌ 环境验证失败")
            return {"success": False}
        
        # 如果有指定session_id，设置到audit对象中
        if self.session_id:
            from utils.audit import ArcherAudit
            # 获取audit实例
            audit = ArcherAudit("admin", "Admin@123", "https://172.118.57.100")
            # 手动设置sessionId
            audit.session.cookies.set("sessionId", self.session_id)
            logger.info(f"🔑 已设置会话ID: {self.session_id}")
        
        start_time = time.time()
        results = []
        success_count = 0
        failed_count = 0
        
        for i in range(start_num, end_num + 1):
            disk_name = f"batch-{i:04d}"
            progress = i - start_num + 1
            logger.info(f"\n📁 创建磁盘 {progress}/{total_disks}: {disk_name}")
            
            try:
                from smart_disk_creator import SmartDiskCreator
                disk_creator = SmartDiskCreator("admin", "Admin@123", "https://172.118.57.100")
                
                # 智能配置
                config_result = disk_creator.create_disk_smart(
                    disk_size_gb=disk_size,
                    use_case="standard"
                )
                
                if not config_result["success"]:
                    logger.error(f"❌ {disk_name} 配置失败: {config_result['error']}")
                    failed_count += 1
                    results.append({
                        'disk_name': disk_name,
                        'disk_num': i,
                        'success': False,
                        'error': config_result['error']
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
                
                # 每创建50个磁盘显示一次进度
                if progress % 50 == 0:
                    logger.info(f"\n📊 进度报告 (已完成{progress}个磁盘):")
                    logger.info(f"✅ 成功: {success_count}")
                    logger.error(f"❌ 失败: {failed_count}")
                    logger.info(f"📈 成功率: {success_count/progress*100:.1f}%")
                    logger.info(f"💾 已创建容量: {success_count * disk_size}GB")
                
                # 添加延迟，避免API频率限制
                if i < end_num:
                    logger.info("⏳ 等待1秒后继续...")
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"❌ {disk_name} 创建出错: {e}")
                failed_count += 1
                results.append({
                    'disk_name': disk_name,
                    'disk_num': i,
                    'success': False,
                    'error': str(e)
                })
        
        # 显示最终结果
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"\n" + "=" * 80)
        logger.info(f"🎉 继续磁盘创建任务完成!")
        logger.info("=" * 80)
        logger.info(f"⏱️  总耗时: {duration/60:.1f} 分钟")
        logger.info(f"📊 总磁盘数: {total_disks}个")
        logger.info(f"✅ 成功创建: {success_count}个")
        logger.error(f"❌ 创建失败: {failed_count}个")
        logger.info(f"📈 成功率: {success_count/total_disks*100:.1f}%")
        logger.info(f"💾 成功总容量: {success_count * disk_size}GB")
        logger.info(f"🌐 目标环境: {self.env_creator.connection_info['name']}")
        
        # 显示失败的磁盘
        if failed_count > 0:
            logger.info(f"\n❌ 失败的磁盘 (前10个):")
            failed_disks = [r for r in results if not r['success']][:10]
            for result in failed_disks:
                error_info = f" - {result.get('error', '未知错误')}"
                logger.info(f"   {result['disk_name']}: 创建失败{error_info}")
            if failed_count > 10:
                logger.info(f"   ... 还有 {failed_count - 10} 个磁盘失败")
        
        # 生成报告
        report = {
            "task_summary": {
                "start_num": start_num,
                "end_num": end_num,
                "total_disks": total_disks,
                "disk_size_gb": disk_size,
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": duration,
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": success_count/total_disks*100,
                "total_capacity_gb": success_count * disk_size,
                "environment": self.env_creator.connection_info['name']
            },
            "results": results
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
    logger.info("🔥 继续磁盘创建器")
    logger.info("从batch-210到batch-1000创建剩余的791个10GB磁盘")
    logger.info("=" * 60)
    
    # 使用指定的session_id继续任务
    creator = ContinueDiskCreator(session_id="ses_3ebafbd55ffei9GHXwTLk2IRae")
    
    # 创建剩余磁盘
    result = creator.create_remaining_disks(
        start_num=210,
        end_num=1000,
        disk_size=10
    )
    
    if result.get("success", True):
        logger.info("\n🎉 任务成功完成!")
    else:
        logger.info("\n❌ 任务执行失败!")

if __name__ == "__main__":
    main()