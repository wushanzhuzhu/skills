#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于opencode agent skills的虚拟磁盘创建脚本
使用volume-creator skill实现智能磁盘创建
"""

import sys
import os
import argparse
import json
import logging
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import global_state, getSession, getStorinfo, createDisk_vstor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class VolumeCreatorSkill:
    """使用volume-creator skill的磁盘创建器"""
    
    def __init__(self):
        self.templates = {
            'basic': {
                'pageSize': '4K',
                'compression': 'Disabled',
                'iops': 100,
                'bandwidth': 100,
                'readCache': True
            },
            'performance': {
                'pageSize': '8K',
                'compression': 'LZ4',
                'iops': 5000,
                'bandwidth': 300,
                'readCache': True
            },
            'storage': {
                'pageSize': '16K',
                'compression': 'Gzip_opt',
                'iops': 1000,
                'bandwidth': 150,
                'readCache': True
            },
            'database': {
                'pageSize': '8K',
                'compression': 'Disabled',
                'iops': 10000,
                'bandwidth': 400,
                'readCache': True
            }
        }
    
    def create_volumes(self, env_url: str, username: str = "admin", password: str = "Admin@123",
                      size: int = 10, count: int = 1, name_prefix: str = "disk",
                      template: str = "basic", **kwargs):
        """
        使用volume-creator skill创建虚拟磁盘
        
        Args:
            env_url: 环境URL
            username: 用户名
            password: 密码
            size: 磁盘大小(GB)
            count: 创建数量
            name_prefix: 命名前缀
            template: 配置模板
            **kwargs: 其他参数覆盖
        """
        logger.info(f"🚀 启动volume-creator skill创建磁盘...")
        logger.info(f"📍 环境: {env_url}")
        logger.info(f"📊 规模: {count}个磁盘 x {size}GB")
        logger.info(f"🎯 模板: {template}")
        
        # 1. 获取会话
        logger.info("\n📡 步骤1: 获取平台会话...")
        session_result = getSession(env_url, username, password)
        if "成功" not in session_result:
            logger.error(f"❌ 会话建立失败: {session_result}")
            return {"success": False, "error": session_result}
        logger.info("✅ 会话建立成功")
        
        # 2. 获取存储信息
        logger.info("\n💾 步骤2: 获取存储信息...")
        stor_info = getStorinfo()
        if not stor_info or isinstance(stor_info, str):
            logger.error(f"❌ 获取存储信息失败: {stor_info}")
            return {"success": False, "error": "无法获取存储信息"}
        logger.info(f"✅ 获取到 {len(stor_info)} 个存储位置")
        
        # 选择第一个可用的存储位置
        storage = stor_info[0]
        storage_manage_id = storage.get("storageManageId")
        zone_id = storage.get("zoneId")
        storage_name = storage.get("stackName")
        logger.info(f"📍 选择存储: {storage_name} ({storage_manage_id})")
        
        # 3. 准备磁盘配置
        logger.info("\n⚙️ 步骤3: 准备磁盘配置...")
        config = self.templates.get(template, self.templates['basic'])
        
        # 允许参数覆盖
        config.update(kwargs)
        
        # 确保基本参数
        config.setdefault('pageSize', '4K')
        config.setdefault('compression', 'Disabled')
        config.setdefault('iops', 100)
        config.setdefault('bandwidth', 100)
        config.setdefault('readCache', True)
        
        logger.info(f"📋 磁盘配置:")
        for key, value in config.items():
            logger.info(f"   {key}: {value}")
        
        # 4. 批量创建磁盘
        logger.info(f"\n🔨 步骤4: 开始创建 {count} 个磁盘...")
        results = []
        success_count = 0
        failed_count = 0
        
        for i in range(count):
            disk_name = f"{name_prefix}-{i:03d}"
            
            # 检查磁盘命名冲突（简单版本）
            # TODO: 可以添加更复杂的命名检查逻辑
            
            logger.info(f"   创建磁盘 {i+1}/{count}: {disk_name}...")
            
            try:
                disk_result = createDisk_vstor(
                    storageManageId=storage_manage_id,
                    pageSize=config['pageSize'],
                    compression=config['compression'],
                    name=disk_name,
                    size=size,
                    iops=config['iops'],
                    bandwidth=config['bandwidth'],
                    count=1,  # 单个创建
                    readCache=config['readCache'],
                    zoneId=zone_id
                )
                
                if isinstance(disk_result, dict) and disk_result.get('code') == 0:
                    disk_info = disk_result.get('data', [])
                    if disk_info:
                        results.extend(disk_info)
                        success_count += 1
                        logger.info(f"   ✅ 成功: {disk_info[0].get('diskId', 'N/A')}")
                    else:
                        logger.info(f"   ⚠️ 成功但无返回数据")
                        failed_count += 1
                else:
                    logger.info(f"   ❌ 失败: {disk_result}")
                    failed_count += 1
                    
            except Exception as e:
                logger.info(f"   ❌ 异常: {str(e)}")
                failed_count += 1
            
            # 避免API频率限制
            if i < count - 1:
                import time
                time.sleep(1)
        
        # 5. 生成结果报告
        logger.info(f"\n📊 创建完成!")
        logger.info(f"✅ 成功: {success_count}")
        logger.error(f"❌ 失败: {failed_count}")
        logger.info(f"📈 成功率: {success_count/count*100:.1f}%")
        
        if results:
            logger.info(f"\n📋 磁盘详情:")
            for disk in results:
                logger.info(f"   • {disk.get('name')}: {disk.get('diskId')} ({disk.get('size')}GB)")
        
        return {
            "success": success_count > 0,
            "total": count,
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
            "config": config,
            "storage_info": storage
        }


def list_templates():
    """列出可用模板"""
    creator = VolumeCreatorSkill()
    logger.info("📋 可用磁盘配置模板:")
    logger.info("-" * 50)
    
    for name, config in creator.templates.items():
        logger.info(f"\n🎯 {name.upper()} 模板:")
        for key, value in config.items():
            logger.info(f"   {key}: {value}")
    
    logger.info("\n💡 使用示例:")
    logger.info("   python disk_creator_skill.py --env https://172.118.13.100 --template performance --size 50 --count 3")


def main():
    parser = argparse.ArgumentParser(description="基于volume-creator skill的磁盘创建脚本")
    parser.add_argument("--env", required=True, help="环境URL或IP地址")
    parser.add_argument("--username", default="admin", help="用户名")
    parser.add_argument("--password", default="Admin@123", help="密码")
    parser.add_argument("--size", type=int, default=10, help="磁盘大小(GB)")
    parser.add_argument("--count", type=int, default=1, help="创建数量")
    parser.add_argument("--name", default="disk", help="磁盘命名前缀")
    parser.add_argument("--template", default="basic", choices=["basic", "performance", "storage", "database"], help="配置模板")
    parser.add_argument("--list-templates", action="store_true", help="列出可用模板")
    
    # 高级参数
    parser.add_argument("--page-size", choices=["4K", "8K", "16K", "32K"], help="覆盖页面大小")
    parser.add_argument("--compression", choices=["Disabled", "LZ4", "Gzip_opt", "Gzip_high"], help="覆盖压缩方式")
    parser.add_argument("--iops", type=int, help="覆盖IOPS")
    parser.add_argument("--bandwidth", type=int, help="覆盖带宽(MB/s)")
    parser.add_argument("--read-cache", type=bool, help="覆盖读缓存设置")
    
    args = parser.parse_args()
    
    if args.list_templates:
        list_templates()
        return
    
    # 准备覆盖参数
    overrides = {}
    if args.page_size:
        overrides['pageSize'] = args.page_size
    if args.compression:
        overrides['compression'] = args.compression
    if args.iops:
        overrides['iops'] = args.iops
    if args.bandwidth:
        overrides['bandwidth'] = args.bandwidth
    if args.read_cache is not None:
        overrides['readCache'] = args.read_cache
    
    # 创建磁盘
    creator = VolumeCreatorSkill()
    result = creator.create_volumes(
        env_url=args.env,
        username=args.username,
        password=args.password,
        size=args.size,
        count=args.count,
        name_prefix=args.name,
        template=args.template,
        **overrides
    )
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = f"disk_creation_result_{timestamp}.json"
    
    try:
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"\n💾 结果已保存到: {result_file}")
    except Exception as e:
        logger.info(f"\n⚠️ 保存结果文件失败: {e}")
    
    # 退出状态
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()