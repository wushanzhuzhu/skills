#!/usr/bin/env python3
"""
批量创建随机参数虚拟磁盘
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
import random
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from unified_disk_creator import UnifiedDiskCreator

class RandomDiskCreator:
    def __init__(self):
        self.creator = UnifiedDiskCreator()
        self.use_cases = ['test', 'standard', 'performance']
        
    def generate_random_disk_config(self, max_size_gb: int = 20) -> dict:
        """生成随机磁盘配置"""
        # 随机大小 1-max_size_gb
        size = random.randint(1, max_size_gb)
        
        # 随机用例，根据大小调整概率
        if size <= 5:
            # 小磁盘倾向于测试环境
            use_case = random.choices(
                self.use_cases, 
                weights=[0.7, 0.2, 0.1], 
                k=1
            )[0]
        elif size <= 15:
            # 中等磁盘倾向于标准环境
            use_case = random.choices(
                self.use_cases, 
                weights=[0.3, 0.5, 0.2], 
                k=1
            )[0]
        else:
            # 大磁盘倾向于高性能环境
            use_case = random.choices(
                self.use_cases, 
                weights=[0.1, 0.3, 0.6], 
                k=1
            )[0]
        
        return {
            'size': size,
            'use_case': use_case,
            'description': self.get_use_case_description(use_case)
        }
    
    def get_use_case_description(self, use_case: str) -> str:
        """获取用例描述"""
        descriptions = {
            'test': '测试环境配置 - 低IOPS和带宽',
            'standard': '标准配置 - 平衡性能和成本',
            'performance': '高性能配置 - 高IOPS和带宽'
        }
        return descriptions.get(use_case, '标准配置')
    
    def create_random_disks(self, count: int, max_size_gb: int = 20, 
                           env_id: str = None, skip_confirm: bool = False) -> dict:
        """批量创建随机参数的磁盘"""
        logger.info(f"🎲 批量创建 {count} 个随机参数磁盘 (最大 {max_size_gb}GB)")
        logger.info("=" * 70)
        
        # 生成随机配置
        logger.info("\n📋 生成随机磁盘配置...")
        disk_configs = []
        
        for i in range(count):
            config = self.generate_random_disk_config(max_size_gb)
            disk_configs.append(config)
            logger.info(f"   磁盘 {i+1}: {config['size']}GB - {config['description']}")
        
        # 显示配置统计
        logger.info(f"\n📊 配置统计:")
        size_distribution = {}
        use_case_distribution = {}
        
        for config in disk_configs:
            size = config['size']
            use_case = config['use_case']
            
            # 大小分布（按范围）
            size_range = f"{size}GB"
            size_distribution[size_range] = size_distribution.get(size_range, 0) + 1
            
            # 用例分布
            use_case_distribution[use_case] = use_case_distribution.get(use_case, 0) + 1
        
        logger.info(f"   大小分布:")
        for size_range, count in sorted(size_distribution.items()):
            logger.info(f"     {size_range}: {count} 个")
        
        logger.info(f"   用例分布:")
        for use_case, count in use_case_distribution.items():
            desc = self.get_use_case_description(use_case)
            logger.info(f"     {use_case}: {count} 个 ({desc})")
        
        # 确认创建
        if not skip_confirm:
            confirm = input(f"\n🤔 确认创建这 {count} 个随机磁盘? (y/n): ").strip().lower()
            if confirm != 'y':
                logger.error("❌ 操作已取消")
                return {"success": False, "error": "用户取消"}
        else:
            logger.info(f"\n✅ 跳过确认，开始创建 {count} 个随机磁盘...")
        
        # 执行创建
        logger.info(f"\n🚀 开始创建...")
        return self.creator.batch_create_disks(disk_configs, env_id)
    
    def display_results_summary(self, results: dict):
        """显示创建结果摘要"""
        logger.info("\n" + "=" * 70)
        logger.info("📊 批量创建结果摘要")
        logger.info("=" * 70)
        
        success_count = len(results.get('success', []))
        failed_count = len(results.get('failed', []))
        total = results.get('total', 0)
        
        logger.info(f"✅ 成功创建: {success_count}/{total}")
        logger.error(f"❌ 创建失败: {failed_count}/{total}")
        logger.info(f"📈 成功率: {success_count/total*100:.1f}%" if total > 0 else "📈 成功率: 0%")
        logger.info(f"🌐 目标环境: {results.get('environment', '未知')}")
        
        # 成功的磁盘详情
        if success_count > 0:
            logger.info(f"\n✅ 成功创建的磁盘:")
            for disk in results['success']:
                logger.info(f"   磁盘 {disk['disk_num']}: {disk['size']}GB ({disk['use_case']})")
        
        # 失败的磁盘详情
        if failed_count > 0:
            logger.info(f"\n❌ 失败的磁盘:")
            for disk in results.get('failed', []):
                logger.info(f"   磁盘 {disk['disk_num']}: {disk.get('size', '?')}GB - {disk.get('error', '未知错误')}")
        
        # 容量统计
        if success_count > 0:
            total_capacity = sum(disk['size'] for disk in results['success'])
            logger.info(f"\n💾 容量统计:")
            logger.info(f"   总容量: {total_capacity}GB")
            logger.info(f"   平均大小: {total_capacity/success_count:.1f}GB")
        
        logger.info("\n🎉 批量创建任务完成!")

def main():
    """命令行界面"""
    parser = argparse.ArgumentParser(description='批量创建随机参数虚拟磁盘')
    parser.add_argument('--count', type=int, default=10,
                       help='磁盘数量 (默认: 10)')
    parser.add_argument('--max-size', type=int, default=20,
                       help='最大磁盘大小GB (默认: 20)')
    parser.add_argument('--env', help='指定环境ID')
    parser.add_argument('--yes', action='store_true',
                       help='跳过确认，直接创建')
    
    args = parser.parse_args()
    
    creator = RandomDiskCreator()
    
    # 验证参数
    if args.count <= 0:
        logger.error("❌ 磁盘数量必须大于0")
        return
    
    if args.max_size <= 0:
        logger.error("❌ 最大磁盘大小必须大于0")
        return
    
    # 批量创建
    results = creator.create_random_disks(
        count=args.count,
        max_size_gb=args.max_size,
        env_id=args.env,
        skip_confirm=args.yes
    )
    
    # 显示结果
    if results.get('success') is not False:  # 不是用户取消
        creator.display_results_summary(results)

if __name__ == "__main__":
    main()