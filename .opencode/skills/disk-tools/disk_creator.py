#!/usr/bin/env python3
"""
ArcherOSS 虚拟磁盘创建工具
支持多环境、多模板的磁盘批量创建

使用方式:
    python disk_creator.py --env production --size 10 --count 1 --name my-disk
    python disk_creator.py --list-env
    python disk_creator.py --list-templates
"""

import sys
import json
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加主项目路径
main_project_path = str(Path(__file__).resolve().parents[3])
sys.path.insert(0, main_project_path)

# 使用主项目的模块
from utils.audit import ArcherAudit
from Hosts import Hosts
from volumes import Volumes
from env_manager import EnvironmentManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class DiskCreator:
    """虚拟磁盘创建器"""
    
    # 配置模板
    TEMPLATES = {
        "basic": {
            "name": "基础模板",
            "description": "办公开发、轻量服务，低配置",
            "pageSize": "4K",
            "compression": "Disabled",
            "iops": 100,
            "bandwidth": 50,
            "readCache": False
        },
        "standard": {
            "name": "标准模板",
            "description": "Web应用、标准业务，均衡配置",
            "pageSize": "8K",
            "compression": "LZ4",
            "iops": 400,
            "bandwidth": 40,
            "readCache": True
        },
        "performance": {
            "name": "高性能模板",
            "description": "数据库、高性能计算，高IOPS",
            "pageSize": "8K",
            "compression": "LZ4",
            "iops": 2000,
            "bandwidth": 200,
            "readCache": True
        },
        "storage": {
            "name": "存储模板",
            "description": "文件存储、备份，优化压缩",
            "pageSize": "16K",
            "compression": "Gzip_opt",
            "iops": 500,
            "bandwidth": 100,
            "readCache": True
        }
    }
    
    def __init__(self):
        # 使用主项目的环境配置文件
        env_config_path = str(Path(__file__).resolve().parents[3] / "environments.json")
        self.env_manager = EnvironmentManager(env_config_path)
        self.current_env = None
        self.connection = None
        
    def list_environments(self):
        """列出所有可用环境"""
        environments = self.env_manager.list_environments()
        
        logger.info("\n🌐 可用环境列表:")
        logger.info("=" * 80)
        logger.info(f"{'ID':<12} {'名称':<15} {'地址':<20} {'存储后端':<10} {'描述':<20}")
        logger.info("-" * 80)
        
        for env in environments:
            logger.info(f"{env['id']:<12} {env['name']:<15} {env['url']:<20} "
                  f"{env.get('storage_backend', 'N/A'):<10} {env['description'][:18]:<20}")
        
        logger.info("=" * 80)
        return environments
    
    def list_templates(self):
        """列出所有配置模板"""
        logger.info("\n📋 可用配置模板:")
        logger.info("=" * 80)
        logger.info(f"{'模板ID':<12} {'名称':<15} {'描述':<25} {'页面大小':<8} {'压缩':<10} {'IOPS':<8} {'带宽':<8}")
        logger.info("-" * 80)
        
        for template_id, template in self.TEMPLATES.items():
            logger.info(f"{template_id:<12} {template['name']:<15} {template['description']:<25} "
                  f"{template['pageSize']:<8} {template['compression']:<10} "
                  f"{template['iops']:<8} {template['bandwidth']:<8}")
        
        logger.info("=" * 80)
        return self.TEMPLATES
    
    def connect_to_environment(self, env_id: str) -> bool:
        """连接到指定环境"""
        env_info = self.env_manager.get_connection_info(env_id)
        
        if not env_info:
            logger.error(f"❌ 环境 '{env_id}' 不存在")
            return False
        
        try:
            logger.info(f"🔗 正在连接到环境: {env_info['name']} ({env_info['url']})")
            
            # 初始化连接
            audit = ArcherAudit(env_info['username'], env_info['password'], env_info['url'])
            audit.setSession()
            host = Hosts(env_info['username'], env_info['password'], env_info['url'], audit)
            volumes = Volumes(audit, host)
            
            self.current_env = env_info
            self.connection = {
                'audit': audit,
                'host': host,
                'volumes': volumes
            }
            
            logger.info("✅ 环境连接成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 连接环境失败: {str(e)}")
            return False
    
    def get_storage_info(self) -> Optional[Dict]:
        """获取存储资源信息"""
        if not self.connection:
            logger.error("❌ 请先连接到环境")
            return None
        
        try:
            logger.info("📊 获取存储资源信息...")
            stors = self.connection['host'].getStorsbyDiskType()
            
            if not stors:
                logger.error("❌ 无法获取存储资源")
                return None
            
            storage_info = stors[0]  # 使用第一个存储资源
            zone_id = self.connection['host'].zone
            
            logger.info(f"✅ 存储资源: {storage_info['stackName']}")
            logger.info(f"   存储ID: {storage_info['storageManageId'][:8]}...")
            logger.info(f"   区域ID: {zone_id[:8]}...")
            
            return {
                'storage': storage_info,
                'zone_id': zone_id
            }
            
        except Exception as e:
            logger.error(f"❌ 获取存储信息失败: {str(e)}")
            return None
    
    def create_disk(self, 
                    size: int,
                    count: int = 1,
                    name: Optional[str] = None,
                    template: str = "standard",
                    env: str = "production",
                    **kwargs) -> Dict[str, Any]:
        """
        创建虚拟磁盘
        
        Args:
            size: 磁盘大小(GB)
            count: 创建数量 (支持1-10000)
            name: 磁盘名称前缀
            template: 配置模板
            env: 目标环境
            **kwargs: 覆盖模板参数
        
        Returns:
            创建结果字典
        """
        # 验证数量范围
        if count < 1 or count > 10000:
            logger.error(f"❌ 创建数量 {count} 超出支持范围 (1-10000)")
            return {"success": False, "error": f"创建数量超出范围，支持1-10000"}
        
        logger.info(f"🚀 开始创建磁盘: {count}个{size}GB磁盘 (环境: {env}, 模板: {template})")
        
        # 1. 连接环境
        if not self.connect_to_environment(env):
            return {"success": False, "error": "环境连接失败"}
        
        # 2. 获取存储信息
        storage_info = self.get_storage_info()
        if not storage_info:
            return {"success": False, "error": "存储信息获取失败"}
        
        # 3. 准备配置
        if template not in self.TEMPLATES:
            logger.warning(f"❌ 模板 '{template}' 不存在，使用标准模板")
            template = "standard"
        
        config = self.TEMPLATES[template].copy()
        config.update(kwargs)  # 允许覆盖模板参数
        
        # 4. 生成磁盘名称
        if not name:
            name = f"disk-{template}"
        
        # 5. 批量创建
        results = {
            "success": True,
            "total": count,
            "created": 0,
            "failed": 0,
            "disks": [],
            "errors": [],
            "env": env,
            "template": template,
            "config": config,
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            for i in range(count):
                disk_name = f"{name}-{int(time.time())}-{i:03d}"
                
                disk_config = {
                    "storageManageId": storage_info['storage']['storageManageId'],
                    "pageSize": config["pageSize"],
                    "compression": config["compression"],
                    "name": disk_name,
                    "size": size,
                    "iops": config["iops"],
                    "bandwidth": config["bandwidth"],
                    "count": 1,
                    "readCache": config["readCache"],
                    "zoneId": storage_info['zone_id']
                }
                
                # 对于大批量创建，显示更紧凑的进度
                if count <= 50:
                    logger.debug(f"\n📦 创建磁盘 {i+1}/{count}: {disk_name}")
                    logger.debug(f"   配置: {disk_config['pageSize']}, {disk_config['compression']}, "
                          f"IOPS={disk_config['iops']}, 带宽={disk_config['bandwidth']}MB/s")
                else:
                    # 每10个或最后一批显示进度
                    if (i + 1) % 10 == 0 or i == count - 1:
                        logger.info(f"📦 进度: {i+1}/{count} 磁盘已创建 ({name}-{int(time.time())}-{i:03d})")
                
                # 调用创建API
                if self.connection and 'volumes' in self.connection and self.connection['volumes']:
                    create_result = self.connection['volumes'].createDisk_vstor(**disk_config)
                else:
                    create_result = {"error": "Volumes connection not available"}
                
                # 检查创建结果 - 成功响应包含data字段且data是列表
                if (isinstance(create_result, dict) and 
                    'data' in create_result and 
                    isinstance(create_result['data'], list) and 
                    len(create_result['data']) > 0):
                    disk_info = create_result['data'][0]
                    if count <= 50:
                        logger.debug(f"   ✅ 创建成功: ID={disk_info.get('id', 'N/A')[:8]}...")
                    results["disks"].append(disk_info)
                    results["created"] += 1
                else:
                    if count <= 50:
                        logger.error(f"   ❌ 创建失败: {create_result}")
                    else:
                        logger.error(f"   ❌ 创建失败: {disk_name}")
                    results["failed"] += 1
                    results["errors"].append({
                        "name": disk_name,
                        "error": create_result
                    })
                
                # 强制1秒间隔防止API请求过快
                if i < count - 1:  # 不是最后一个
                    time.sleep(1)
        
        except Exception as e:
            logger.error(f"❌ 创建过程中发生异常: {str(e)}")
            results["success"] = False
            results["error"] = str(e)
        
        finally:
            results["duration"] = time.time() - start_time
        
        # 6. 对于大批量创建，显示简化结果
        if count > 50:
            logger.info(f"\n{'='*60}")
            logger.info(f"📊 大批量磁盘创建完成汇总")
            logger.info('='*60)
            logger.info(f"环境: {results['env']}")
            logger.info(f"模板: {results['template']}")
            logger.info(f"总数: {results['total']} 个")
            logger.info(f"成功: {results['created']} 个")
            logger.info(f"失败: {results['failed']} 个")
            logger.info(f"总耗时: {results['duration']:.2f} 秒")
            logger.info(f"平均耗时: {results['duration']/results['total']:.2f} 秒/磁盘")
            if results['created'] > 0:
                logger.info(f"✅ 首个成功磁盘: {results['disks'][0].get('name')} (ID: {results['disks'][0].get('id', 'N/A')[:8]}...)")
            logger.info('='*60)
        else:
            # 6. 输出详细结果
            self._print_results(results)
        
        return results
    
    def _print_results(self, results: Dict[str, Any]):
        """打印创建结果"""
        logger.info(f"\n{'='*60}")
        logger.info("📊 磁盘创建结果汇总")
        logger.info('='*60)
        logger.info(f"环境: {results['env']}")
        logger.info(f"模板: {results['template']}")
        logger.info(f"总计: {results['total']} 个")
        logger.info(f"成功: {results['created']} 个")
        logger.info(f"失败: {results['failed']} 个")
        logger.info(f"耗时: {results['duration']:.2f} 秒")
        
        if results["disks"]:
            if len(results["disks"]) <= 10:
                logger.info(f"\n✅ 成功创建的磁盘:")
                for i, disk in enumerate(results["disks"], 1):
                    logger.info(f"   {i}. {disk.get('name')} "
                          f"(ID: {disk.get('id', 'N/A')[:8]}..., "
                          f"大小: {disk.get('size', 'N/A')}GB)")
            else:
                logger.info(f"\n✅ 成功创建磁盘示例 (前5个):")
                for i, disk in enumerate(results["disks"][:5], 1):
                    logger.info(f"   {i}. {disk.get('name')} "
                          f"(ID: {disk.get('id', 'N/A')[:8]}..., "
                          f"大小: {disk.get('size', 'N/A')}GB)")
                logger.info(f"   ... 还有 {len(results['disks'])-5} 个磁盘")
        
        if results["errors"]:
            if len(results["errors"]) <= 5:
                logger.error(f"\n❌ 创建失败的磁盘:")
                for error in results["errors"]:
                    logger.error(f"   {error['name']}: {error['error']}")
            else:
                logger.error(f"\n❌ 创建失败磁盘示例 (前5个):")
                for error in results["errors"][:5]:
                    logger.error(f"   {error['name']}: {error['error']}")
                logger.error(f"   ... 还有 {len(results['errors'])-5} 个失败磁盘")
        
        logger.info('='*60)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ArcherOSS 虚拟磁盘创建工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --list-env                    # 列出所有环境
  %(prog)s --list-templates               # 列出所有模板
  %(prog)s --env production --size 10      # 在生产环境创建10GB磁盘
  %(prog)s --env test --size 50 --count 3 --template performance
  %(prog)s --env dev --size 20 --name my-disk --template storage
        """
    )
    
    # 基本参数
    parser.add_argument('--env', default='production', 
                       help='目标环境 (默认: production)')
    parser.add_argument('--size', type=int, required=False,
                       help='磁盘大小(GB)')
    parser.add_argument('--count', type=int, default=1,
                       help='创建数量 (支持1-10000, 默认: 1)')
    parser.add_argument('--name', 
                       help='磁盘名称前缀')
    parser.add_argument('--template', default='standard',
                       choices=['basic', 'standard', 'performance', 'storage'],
                       help='配置模板 (默认: standard)')
    
    # 信息查询参数
    parser.add_argument('--list-env', action='store_true',
                       help='列出所有可用环境')
    parser.add_argument('--list-templates', action='store_true',
                       help='列出所有配置模板')
    
    # 高级参数 (覆盖模板)
    parser.add_argument('--page-size', choices=['4K', '8K', '16K', '32K'],
                       help='页面大小 (覆盖模板)')
    parser.add_argument('--compression', choices=['Disabled', 'LZ4', 'Gzip_opt', 'Gzip_high'],
                       help='压缩方式 (覆盖模板)')
    parser.add_argument('--iops', type=int,
                       help='IOPS (覆盖模板)')
    parser.add_argument('--bandwidth', type=int,
                       help='带宽(MB/s) (覆盖模板)')
    parser.add_argument('--read-cache', action='store_true',
                       help='启用读缓存 (覆盖模板)')
    parser.add_argument('--no-read-cache', action='store_true',
                       help='禁用读缓存 (覆盖模板)')
    
    args = parser.parse_args()
    
    # 创建磁盘创建器
    creator = DiskCreator()
    
    # 处理信息查询
    if args.list_env:
        creator.list_environments()
        return
    
    if args.list_templates:
        creator.list_templates()
        return
    
    # 检查必需参数
    if not args.size:
        logger.error("❌ 请指定磁盘大小 --size 参数")
        parser.print_help()
        sys.exit(1)
    
    # 检查数量范围
    if args.count < 1 or args.count > 10000:
        logger.error(f"❌ 创建数量 {args.count} 超出支持范围 (1-10000)")
        logger.warning("💡 提示: 大批量创建(>100)将显示简化进度以提升性能")
        sys.exit(1)
    
    # 准备覆盖参数
    override_params = {}
    if args.page_size:
        override_params['pageSize'] = args.page_size
    if args.compression:
        override_params['compression'] = args.compression
    if args.iops:
        override_params['iops'] = args.iops
    if args.bandwidth:
        override_params['bandwidth'] = args.bandwidth
    if args.read_cache:
        override_params['readCache'] = True
    elif args.no_read_cache:
        override_params['readCache'] = False
    
    # 执行创建
    result = creator.create_disk(
        size=args.size,
        count=args.count,
        name=args.name,
        template=args.template,
        env=args.env,
        **override_params
    )
    
    # 根据结果设置退出码
    sys.exit(0 if result.get("success") else 1)

if __name__ == "__main__":
    main()