#!/usr/bin/env python3
"""
磁盘创建进度监控器
实时监控batch磁盘创建进度
"""

import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

import subprocess
import json
from datetime import datetime

def monitor_progress():
    """监控磁盘创建进度"""
    
    logger.info("🔍 磁盘创建进度监控器")
    logger.info("=" * 50)
    
    start_time = time.time()
    last_count = 0
    
    try:
        while True:
            # 检查当前磁盘数量
            result = subprocess.run(['python3', 'check_disk_status.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                # 解析输出获取batch磁盘数量
                lines = result.stdout.split('\n')
                batch_count = 0
                
                for line in lines:
                    if 'Batch磁盘数:' in line:
                        batch_count = int(line.split(':')[1].strip())
                        break
                
                current_time = datetime.now().strftime("%H:%M:%S")
                elapsed = int(time.time() - start_time)
                hours = elapsed // 3600
                minutes = (elapsed % 3600) // 60
                seconds = elapsed % 60
                
                # 计算创建速度
                new_disks = batch_count - last_count
                rate = new_disks / 60 if new_disks > 0 else 0  # 每分钟创建数
                
                # 估算剩余时间（假设目标是1000个磁盘）
                remaining = 1000 - batch_count
                eta_minutes = remaining / rate if rate > 0 else 999999
                eta_hours = eta_minutes // 60
                eta_minutes_remaining = int(eta_minutes % 60)
                
                logger.info(f"[{current_time}] 进度: {batch_count}/1000 | "
                      f"新增: +{new_disks} | "
                      f"速度: {rate:.1f}/min | "
                      f"剩余: {remaining} | "
                      f"预计: {eta_hours}h{eta_minutes_remaining}m | "
                      f"耗时: {hours:02d}:{minutes:02d}:{seconds:02d}")
                
                last_count = batch_count
                
                # 如果达到1000个，停止监控
                if batch_count >= 1000:
                    logger.info("\n🎉 恭喜！已完成1000个磁盘的创建！")
                    break
                    
            # 等待60秒再次检查
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("\n👋 监控已停止")
        
    except Exception as e:
        logger.info(f"\n❌ 监控出错: {e}")

if __name__ == "__main__":
    monitor_progress()