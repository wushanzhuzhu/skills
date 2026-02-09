#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的磁盘创建调用脚本
直接使用volume-creator skill实现
"""

import argparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

import json
from datetime import datetime


def call_skill(params):
    """调用volume-creator skill"""
    skill_call = f'''
import sys
sys.path.append('/root/myskills/wushanskills')

# 加载volume-creator skill
from opencode import skill

# 调用skill
volume_skill = skill('volume-creator')

# 使用skill创建磁盘
result = volume_skill.create_volumes(
    env_url="{params['env_url']}",
    username="{params['username']}",
    password="{params['password']}",
    size={params['size']},
    count={params['count']},
    name_prefix="{params['name_prefix']}",
    template="{params['template']}"
)

logger.info("Skill Result:", result)
'''
    
    # 创建临时执行文件
    temp_file = "/tmp/skill_call.py"
    with open(temp_file, 'w') as f:
        f.write(skill_call)
    
    # 执行skill调用
    import subprocess
    try:
        result = subprocess.run([sys.executable, temp_file], 
                              capture_output=True, text=True, cwd="/root/myskills/wushanskills")
        return result.stdout, result.stderr, result.returncode
    finally:
        # 清理临时文件
        try:
            import os
            os.remove(temp_file)
        except:
            pass


def list_templates():
    """列出可用模板"""
    logger.info("📋 volume-creator skill 可用磁盘配置模板:")
    logger.info("=" * 60)
    
    templates = {
        'basic': {
            'description': '基础配置 - 适用于测试环境',
            'pageSize': '4K',
            'compression': 'Disabled',
            'iops': 100,
            'bandwidth': 100,
            'readCache': True
        },
        'performance': {
            'description': '高性能配置 - 适用于数据库',
            'pageSize': '8K',
            'compression': 'LZ4',
            'iops': 5000,
            'bandwidth': 300,
            'readCache': True
        },
        'storage': {
            'description': '存储优化配置 - 适用于文件存储',
            'pageSize': '16K',
            'compression': 'Gzip_opt',
            'iops': 1000,
            'bandwidth': 150,
            'readCache': True
        },
        'database': {
            'description': '数据库专用配置 - 高性能无压缩',
            'pageSize': '8K',
            'compression': 'Disabled',
            'iops': 10000,
            'bandwidth': 400,
            'readCache': True
        }
    }
    
    for name, config in templates.items():
        logger.info(f"\n🎯 {name.upper()} 模板:")
        logger.info(f"   💬 {config['description']}")
        for key, value in config.items():
            if key != 'description':
                logger.info(f"   ⚙️ {key}: {value}")
    
    logger.info("\n" + "=" * 60)
    logger.info("💡 使用示例:")
    logger.info("   python simple_disk_creator.py --env https://172.118.13.100 --template performance")
    logger.info("   python simple_disk_creator.py --env 172.118.13.100 --size 50 --count 5")


def main():
    parser = argparse.ArgumentParser(
        description="使用volume-creator skill创建虚拟磁盘",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用高性能模板创建3个20GB磁盘
  python simple_disk_creator.py --env https://172.118.13.100 --template performance --size 20 --count 3
  
  # 快速创建测试磁盘
  python simple_disk_creator.py --env 172.118.13.100 --count 5
  
  # 使用自定义前缀
  python simple_disk_creator.py --env https://172.118.13.100 --name my-disk --size 100
        """
    )
    
    parser.add_argument("--env", required=True, help="环境URL或IP地址 (例: https://172.118.13.100 或 172.118.13.100)")
    parser.add_argument("--username", default="admin", help="平台用户名 (默认: admin)")
    parser.add_argument("--password", default="Admin@123", help="平台密码 (默认: Admin@123)")
    parser.add_argument("--size", type=int, default=10, help="磁盘大小GB (默认: 10)")
    parser.add_argument("--count", type=int, default=1, help="创建数量 (默认: 1)")
    parser.add_argument("--name", default="disk", help="磁盘命名前缀 (默认: disk)")
    parser.add_argument("--template", default="basic", 
                       choices=["basic", "performance", "storage", "database"],
                       help="配置模板 (默认: basic)")
    parser.add_argument("--list-templates", action="store_true", help="列出所有可用模板")
    
    args = parser.parse_args()
    
    if args.list_templates:
        list_templates()
        return
    
    # 准备参数
    params = {
        'env_url': args.env,
        'username': args.username,
        'password': args.password,
        'size': args.size,
        'count': args.count,
        'name_prefix': args.name,
        'template': args.template
    }
    
    logger.info("🚀 调用volume-creator skill创建磁盘")
    logger.info("=" * 50)
    logger.info(f"📍 目标环境: {params['env_url']}")
    logger.info(f"👤 用户: {params['username']}")
    logger.info(f"💾 磁盘规格: {params['count']}个 x {params['size']}GB")
    logger.info(f"🏷️ 命名前缀: {params['name_prefix']}")
    logger.info(f"⚙️ 配置模板: {params['template']}")
    logger.info("=" * 50)
    
    # 调用skill
    stdout, stderr, returncode = call_skill(params)
    
    if stdout:
        logger.info("📤 Skill输出:")
        logger.info(stdout)
    
    if stderr:
        logger.info("⚠️ 错误信息:")
        logger.info(stderr)
    
    if returncode == 0:
        logger.info("✅ 磁盘创建完成")
        
        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"skill_disk_creation_{timestamp}.txt"
        
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write(f"volume-creator skill 磁盘创建结果\n")
                f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"环境: {params['env_url']}\n")
                f.write(f"规格: {params['count']} x {params['size']}GB\n")
                f.write(f"模板: {params['template']}\n")
                f.write("-" * 40 + "\n")
                f.write("Skill输出:\n")
                f.write(stdout)
                if stderr:
                    f.write("\n错误信息:\n")
                    f.write(stderr)
            
            logger.info(f"📄 结果已保存到: {result_file}")
        except Exception as e:
            logger.warning(f"⚠️ 保存结果文件失败: {e}")
    else:
        logger.error("❌ 磁盘创建失败")
    
    return returncode


if __name__ == "__main__":
    import sys
    sys.exit(main())