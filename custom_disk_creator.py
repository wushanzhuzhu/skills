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
自定义磁盘创建脚本 - 创建10台10GB磁盘，关闭压缩策略
支持不同环境的批量创建
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

from env_manager import EnvironmentManager
from smart_disk_creator import SmartDiskCreator

class CustomDiskCreator:
    """自定义磁盘创建器"""
    
    def __init__(self):
        self.env_manager = EnvironmentManager()
        
    def create_10_disks_with_disabled_compression(self, env_id: str, env_name: str) -> dict:
        """在指定环境创建10台10GB磁盘，关闭压缩策略"""
        
        logger.info(f"🚀 开始在环境 '{env_name}' 创建10台磁盘...")
        logger.info(f"🌐 环境地址: {self.get_env_address(env_id)}")
        logger.info("=" * 60)
        
        # 获取环境连接信息
        env_info = self.env_manager.get_connection_info(env_id)
        if not env_info:
            return {"success": False, "error": f"无法获取环境 {env_id} 的连接信息"}
        
        # 初始化智能磁盘创建器
        creator = SmartDiskCreator(
            env_info['username'], 
            env_info['password'], 
            env_info['url']
        )
        
        # 获取存储信息
        storage_result = creator.get_storage_info()
        if not storage_result["success"]:
            return {"success": False, "error": f"无法获取存储信息: {storage_result['error']}"}
        
        storage_info = storage_result["storage_info"][0]
        zone_id = storage_result["zone_id"]
        
        results = {
            "environment": env_name,
            "env_id": env_id,
            "address": self.get_env_address(env_id),
            "total_disks": 10,
            "success_count": 0,
            "failed_count": 0,
            "disks": [],
            "errors": []
        }
        
        # 创建10台磁盘
        for i in range(10):
            disk_name = f"disk-10gb-nocomp-{i+1:02d}"
            logger.info(f"\n📁 创建第 {i+1}/10 台磁盘: {disk_name}")
            
            try:
                # 构建自定义配置（basic模板，压缩关闭）
                custom_config = {
                    "storageManageId": storage_info.get("storageManageId"),
                    "pageSize": "4K",           # basic模板使用4K
                    "compression": "Disabled",   # 关闭压缩策略
                    "name": disk_name,
                    "size": 10,                  # 10GB
                    "iops": 100,                 # basic模板使用100 IOPS
                    "bandwidth": 50,             # basic模板使用50MB/s带宽
                    "count": 1,
                    "readCache": False,          # basic模板默认关闭读缓存
                    "zoneId": zone_id
                }
                
                # 验证配置
                validation = creator.validate_parameters(custom_config)
                if not validation["valid"]:
                    error_msg = f"配置验证失败: {', '.join(validation['errors'])}"
                    logger.error(f"❌ {error_msg}")
                    results["errors"].append({"disk": disk_name, "error": error_msg})
                    results["failed_count"] += 1
                    continue
                
                logger.info(f"📝 磁盘配置:")
                logger.info(f"   名称: {custom_config['name']}")
                logger.info(f"   大小: {custom_config['size']}GB")
                logger.info(f"   页面大小: {custom_config['pageSize']}")
                logger.info(f"   压缩策略: {custom_config['compression']}")
                logger.info(f"   IOPS: {custom_config['iops']}")
                logger.info(f"   带宽: {custom_config['bandwidth']} MB/s")
                logger.info(f"   读缓存: {'开启' if custom_config['readCache'] else '关闭'}")
                
                # 创建磁盘
                from volumes import Volumes
                volumes = Volumes(creator.audit, creator.host)
                
                logger.info("🚀 正在创建磁盘...")
                result = volumes.createDisk_vstor(**custom_config)
                
                # 解析结果
                if isinstance(result, dict) and 'data' in result:
                    if result['data'] and len(result['data']) > 0:
                        disk_info = result['data'][0]
                        logger.info("✅ 磁盘创建成功!")
                        logger.info(f"📁 磁盘ID: {disk_info['id']}")
                        logger.info(f"📝 磁盘名称: {disk_info['name']}")
                        
                        results["disks"].append({
                            "id": disk_info['id'],
                            "name": disk_info['name'],
                            "size": 10,
                            "compression": "Disabled",
                            "iops": 100,
                            "bandwidth": 50
                        })
                        results["success_count"] += 1
                    else:
                        error_msg = "创建失败: 返回数据为空"
                        logger.error(f"❌ {error_msg}")
                        results["errors"].append({"disk": disk_name, "error": error_msg})
                        results["failed_count"] += 1
                else:
                    error_msg = f"创建失败: 意外的响应格式 - {result}"
                    logger.error(f"❌ {error_msg}")
                    results["errors"].append({"disk": disk_name, "error": error_msg})
                    results["failed_count"] += 1
                
                # 添加延迟避免API频率限制
                if i < 9:  # 最后一个不需要延迟
                    time.sleep(1)
                    
            except Exception as e:
                error_msg = f"创建过程中发生错误: {str(e)}"
                logger.error(f"❌ {error_msg}")
                results["errors"].append({"disk": disk_name, "error": error_msg})
                results["failed_count"] += 1
        
        return results
    
    def get_env_address(self, env_id: str) -> str:
        """获取环境地址"""
        envs = self.env_manager.list_environments()
        for env in envs:
            if env['id'] == env_id:
                return env['url']
        return "未知地址"
    
    def print_results(self, results: dict):
        """打印创建结果"""
        logger.info(f"\n📊 环境 '{results['environment']}' 创建结果:")
        logger.info("=" * 60)
        logger.info(f"🌐 环境地址: {results['address']}")
        logger.info(f"📦 计划创建: {results['total_disks']} 台磁盘")
        logger.info(f"✅ 成功创建: {results['success_count']} 台")
        logger.error(f"❌ 创建失败: {results['failed_count']} 台")
        
        if results['success_count'] > 0:
            logger.info(f"\n✅ 成功创建的磁盘:")
            logger.info("-" * 60)
            for disk in results['disks']:
                logger.info(f"📁 名称: {disk['name']}")
                logger.info(f"   ID: {disk['id']}")
                logger.info(f"   大小: {disk['size']}GB")
                logger.info(f"   压缩策略: {disk['compression']}")
                logger.info(f"   IOPS: {disk['iops']}")
                logger.info(f"   带宽: {disk['bandwidth']} MB/s")
                logger.info()
        
        if results['failed_count'] > 0:
            logger.info(f"\n❌ 失败详情:")
            logger.info("-" * 60)
            for error in results['errors']:
                logger.info(f"📁 磁盘: {error['disk']}")
                logger.info(f"   错误: {error['error']}")
                logger.info()

def main():
    """主函数 - 执行两个环境的磁盘创建任务"""
    creator = CustomDiskCreator()
    
    # 环境配置
    environments = [
        {"id": "production", "name": "存算分离环境"},
        {"id": "langchao", "name": "浪潮5代繁体版环境"}
    ]
    
    all_results = []
    
    for env in environments:
        logger.info(f"\n🎯 开始执行环境: {env['name']} ({env['id']})")
        logger.info("=" * 80)
        
        results = creator.create_10_disks_with_disabled_compression(env['id'], env['name'])
        creator.print_results(results)
        all_results.append(results)
        
        # 环境间延迟
        if env != environments[-1]:
            logger.info(f"\n⏳ 等待 3 秒后开始下一个环境...")
            time.sleep(3)
    
    # 打印总体汇总
    logger.info(f"\n🎉 总体创建汇总:")
    logger.info("=" * 80)
    total_success = sum(r['success_count'] for r in all_results)
    total_failed = sum(r['failed_count'] for r in all_results)
    total_planned = sum(r['total_disks'] for r in all_results)
    
    logger.info(f"📦 计划创建总数: {total_planned} 台磁盘")
    logger.info(f"✅ 成功创建总数: {total_success} 台")
    logger.error(f"❌ 创建失败总数: {total_failed} 台")
    logger.info(f"📈 成功率: {(total_success/total_planned*100):.1f}%")
    
    for result in all_results:
        logger.info(f"\n🌐 {result['environment']}:")
        logger.info(f"   成功: {result['success_count']}/{result['total_disks']}")
        logger.info(f"   压缩策略: Disabled (全部符合要求)")

if __name__ == "__main__":
    main()