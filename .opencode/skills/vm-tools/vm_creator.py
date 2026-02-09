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
ArcherOSS 虚拟机创建工具
支持多环境、多模板的虚拟机批量创建

使用方式:
    python vm_creator.py --help
    python vm_creator.py --list-env
    python vm_creator.py --list-templates
    python vm_creator.py --list-images
    python vm_creator.py --env production --count 1 --name my-vm
    python vm_creator.py --env test --count 3 --template performance
"""

import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加主项目路径
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# 使用主项目的模块
from utils.audit import ArcherAudit
from Hosts import Hosts
from Instances import Instances
from Images import Images
from env_manager import EnvironmentManager

class VMCreator:
    """虚拟机创建器"""
    
    # 配置模板
    TEMPLATES = {
        "basic": {
            "name": "基础模板",
            "description": "办公开发、轻量服务，低配置",
            "cpu": 2,
            "sockets": 1,
            "memory": 4,
            "videoModel": "VGA",
            "haEnable": False,
            "diskSize": 40,
            "priority": 1,
            "numaEnable": False,
            "balloonSwitch": False,
            "bigPageEnable": False,
            "vncPwd": "",
            "cloneType": "LINK"
        },
        "standard": {
            "name": "标准模板",
            "description": "Web应用、标准业务，均衡配置",
            "cpu": 4,
            "sockets": 2,
            "memory": 8,
            "videoModel": "QXL",
            "haEnable": True,
            "diskSize": 80,
            "priority": 2,
            "numaEnable": True,
            "balloonSwitch": True,
            "bigPageEnable": True,
            "vncPwd": "",
            "cloneType": "LINK"
        },
        "performance": {
            "name": "高性能模板",
            "description": "数据库、高性能计算，高配置",
            "cpu": 8,
            "sockets": 4,
            "memory": 16,
            "videoModel": "QXL",
            "haEnable": True,
            "diskSize": 200,
            "priority": 3,
            "numaEnable": True,
            "balloonSwitch": True,
            "bigPageEnable": True,
            "vncPwd": "",
            "cloneType": "FULL"
        },
        "storage": {
            "name": "存储模板",
            "description": "文件存储、备份，优化配置",
            "cpu": 2,
            "sockets": 1,
            "memory": 2,
            "videoModel": "VGA",
            "haEnable": False,
            "diskSize": 500,
            "priority": 1,
            "numaEnable": False,
            "balloonSwitch": False,
            "bigPageEnable": False,
            "vncPwd": "",
            "cloneType": "LINK"
        }
    }
    
    def __init__(self):
        # 使用主项目的环境配置文件
        env_config_path = str(Path(__file__).resolve().parents[3] / "environments.json")
        self.env_manager = EnvironmentManager(env_config_path)
        self.current_env = None
        self.connection = None
        self.images = []
        
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
        logger.info("\n🔧 可用配置模板:")
        logger.info("=" * 100)
        logger.info(f"{'模板ID':<12} {'名称':<15} {'描述':<30} {'CPU':<8} {'内存':<8} {'磁盘':<8} {'视频':<8} {'HA':<5}")
        logger.info("-" * 100)
        
        for template_id, template in self.TEMPLATES.items():
            memory_str = f"{template['memory']}GB"
            disk_str = f"{template['diskSize']}GB"
            logger.info(f"{template_id:<12} {template['name']:<15} {template['description']:<30} "
                  f"{template['cpu']:<8} {memory_str:<8} {disk_str:<8} {template['videoModel']:<8} "
                  f"{str(template['haEnable']):<5}")
        
        logger.info("=" * 100)
        return self.TEMPLATES
    
    def list_images(self, env_id: str = "production"):
        """列出可用镜像"""
        logger.info(f"\n📷 列出环境 '{env_id}' 的可用镜像:")
        
        # 连接环境
        if not self.connect_to_environment(env_id):
            return []
        
        try:
            logger.info("🔍 获取镜像信息...")
            # 使用真实的Images类获取镜像列表
            if not self.connection:
                logger.info("😈 连接不可用")
                return []
                
            images_client = self.connection.get('images')
            if not images_client:
                logger.info("😈 无法获取Images客户端")
                return []
            
            host_client = self.connection.get('host')
            if not host_client:
                logger.info("😈 无法获取Host客户端")
                return []
                
            real_images = images_client.getImagebystorageManageId(host_client)
            
            # 转换为统一格式
            sample_images = []
            for img in real_images:
                sample_images.append({
                    "id": img.get("imageId", ""),
                    "name": img.get("imageName", ""),
                    "description": "可用镜像",
                    "size": "N/A",
                    "os": img.get("imageName", "")
                })
            
            if not sample_images:
                logger.info("😈 未找到可用镜像，使用示例数据")
                sample_images = [
                    {"id": "default-img", "name": "默认镜像", "description": "默认镜像", "size": "N/A", "os": "Linux"}
                ]
            
            self.images = sample_images
            
            logger.info("\n📂 可用镜像列表:")
            logger.info("=" * 80)
            logger.info(f"{'ID':<12} {'名称':<20} {'操作系统':<15} {'大小':<10} {'描述':<20}")
            logger.info("-" * 80)
            
            for img in sample_images:
                logger.info(f"{img['id']:<12} {img['name']:<20} {img['os']:<15} {img['size']:<10} {img['description'][:18]:<20}")
            
            logger.info("=" * 80)
            return sample_images
            
        except Exception as e:
            logger.info(f"😈 获取镜像列表失败: {str(e)}")
            return []
    
    def connect_to_environment(self, env_id: str) -> bool:
        """连接到指定环境"""
        env_info = self.env_manager.get_connection_info(env_id)
        
        if not env_info:
            logger.info(f"🛑 环境 '{env_id}' 不存在")
            return False
        
        try:
            logger.info(f"🐾 正在连接到环境: {env_info['name']} ({env_info['url']})")
            
            # 初始化连接
            audit = ArcherAudit(env_info['username'], env_info['password'], env_info['url'])
            audit.setSession()
            host = Hosts(env_info['username'], env_info['password'], env_info['url'], audit)
            instances = Instances(env_info['username'], env_info['password'], env_info['url'], audit)
            
            images = Images(env_info['username'], env_info['password'], env_info['url'], audit)
            
            self.current_env = env_info
            self.connection = {
                'audit': audit,
                'host': host,
                'instances': instances,
                'images': images
            }
            
            logger.info("✅ 环境连接成功")
            return True
            
        except Exception as e:
            logger.info(f"🛑 连接环境失败: {str(e)}")
            return False
    
    def get_storage_info(self) -> Optional[Dict]:
        """获取存储资源信息"""
        if not self.connection:
            logger.info("🛑 请先连接到环境")
            return None
        
        try:
            logger.info("📊 获取存储资源信息...")
            stors = self.connection['host'].getStorsbyDiskType()
            
            if not stors:
                logger.info("🛑 无法获取存储资源")
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
            logger.info(f"🛑 获取存储信息失败: {str(e)}")
            return None
    
    def create_vm(self, 
                  count: int = 1,
                  name: Optional[str] = None,
                  template: str = "standard",
                  env: str = "production",
                  image_id: Optional[str] = None,
                  hostname: Optional[str] = None,
                  **kwargs) -> Dict[str, Any]:
        """
        创建虚拟机
        
        Args:
            count: 创建数量
            name: 虚拟机名称前缀
            template: 配置模板
            env: 目标环境
            image_id: 镜像ID
            hostname: 主机名
            **kwargs: 覆盖模板参数
        
        Returns:
            创建结果字典
        """
        logger.info(f"🚀 开始创建虚拟机: {count}个虚拟机 (环境: {env}, 模板: {template})")
        
        # 1. 连接环境
        connection_success = self.connect_to_environment(env)
        if not connection_success:
            return {"success": False, "error": "环境连接失败"}
        
        # 2. 获取存储信息
        storage_info = self.get_storage_info()
        if not storage_info:
            return {"success": False, "error": "存储信息获取失败"}
        
        # 3. 获取镜像信息
        if not image_id:
            logger.info("❓ 未指定镜像ID，列出可用镜像...")
            images = self.list_images(env)
            if not images:
                return {"success": False, "error": "无可用镜像"}
            
            # 使用第一个镜像
            image_id = images[0]['id']
            logger.info(f"✅ 使用镜像: {images[0]['name']} (ID: {image_id})")
        
        # 4. 准备配置
        if template not in self.TEMPLATES:
            logger.info(f"🛑 模板 '{template}' 不存在，使用标准模板")
            template = "standard"
        
        config = self.TEMPLATES[template].copy()
        config.update(kwargs)  # 允许覆盖模板参数
        
        # 5. 生成虚拟机名称
        if not name:
            name = f"vm-{template}"
        
        # 6. 生成主机名
        if not hostname:
            hostname = name
        
        # 7. 批量创建
        results = {
            "success": True,
            "total": count,
            "created": 0,
            "failed": 0,
            "vms": [],
            "errors": [],
            "env": env,
            "template": template,
            "config": config,
            "duration": 0,
            "image_id": image_id
        }
        
        start_time = time.time()
        
        try:
            for i in range(count):
                vm_name = f"{name}-{int(time.time())}-{i:03d}"
                
                # 生成管理密码 (临时使用静态密码，实际应用中应该设置更安全的密码)
                admin_password = "Admin@123456"
                
                logger.info(f"\n💻 创建虚拟机 {i+1}/{count}: {vm_name}")
                logger.info(f"   配置: CPU={config['cpu']} 核, 内存={config['memory']}GB, 磁盘={config['diskSize']}GB")
                logger.info(f"   模板: {config['name']}, HA={'启用' if config['haEnable'] else '禁用'}")
                
                # 8. 调用创建API
                if not self.connection or not self.connection.get('instances'):
                    logger.info("   🛑 无法获取Instances客户端")
                    results["failed"] += 1
                    results["errors"].append({
                        "name": vm_name,
                        "error": "Instances客户端不可用"
                    })
                    continue
                    
                instances_client = self.connection.get('instances')
                if not instances_client:
                    logger.info("   🛑 无法获取Instances客户端")
                    results["failed"] += 1
                    results["errors"].append({
                        "name": vm_name,
                        "error": "Instances客户端不可用"
                    })
                    continue
                    
                create_result = instances_client.createInstance_noNet(
                    name=vm_name,
                    hostname=hostname,
                    videoModel="cirrus",  # 使用固定值 cirrus
                    haEnable=config['haEnable'],
                    cpu=config['cpu'],
                    sockets=config['sockets'],
                    memory=config['memory'],
                    zoneId=storage_info['zone_id'],
                    storageType=storage_info['storage']['stackName'],
                    storageManageId=storage_info['storage']['storageManageId'],
                    diskType=storage_info['storage']['diskType'],
                    imageId=image_id,
                    adminPassword=admin_password,
                    size=config['diskSize'],
                    priority=config['priority'],
                    numaEnable=config['numaEnable'],
                    balloonSwitch=config['balloonSwitch'],
                    bigPageEnable=config['bigPageEnable'],
                    vncPwd=config['vncPwd'],
                    cloneType=config['cloneType']
                )
                
                # 验证创建结果
                if isinstance(create_result, list) and len(create_result) > 0:
                    vm_id = create_result[0]
                    logger.info(f"   ✅ 创建成功: ID={vm_id[:8]}...")
                    results["vms"].append({
                        "name": vm_name,
                        "id": vm_id,
                        "image_id": image_id,
                        "template": template
                    })
                    results["created"] += 1
                elif create_result is None:
                    logger.info(f"   🛑 创建失败: API返回None")
                    results["failed"] += 1
                    results["errors"].append({
                        "name": vm_name,
                        "error": "API返回None"
                    })
                else:
                    logger.info(f"   🛑 创建失败: {create_result}")
                    results["failed"] += 1
                    results["errors"].append({
                        "name": vm_name,
                        "error": str(create_result)
                    })
                
                # 避免API频率限制
                if i < count - 1:
                    time.sleep(1)
            
        except Exception as e:
            logger.info(f"🛑 创建过程中发生异常: {str(e)}")
            results["success"] = False
            results["error"] = str(e)
        
        finally:
            results["duration"] = time.time() - start_time
        
        # 9. 输出结果
        self._print_results(results)
        
        return results
    
    def _print_results(self, results: Dict[str, Any]):
        """打印创建结果"""
        logger.info(f"\n{'='*80}")
        logger.info("📊 虚拟机创建结果汇总")
        logger.info('='*80)
        logger.info(f"环境: {results['env']}")
        logger.info(f"模板: {results['template']}")
        logger.info(f"镜像: {results['image_id']}")
        logger.info(f"总计: {results['total']} 个")
        logger.info(f"成功: {results['created']} 个")
        logger.info(f"失败: {results['failed']} 个")
        logger.info(f"耗时: {results['duration']:.2f} 秒")
        
        if results["vms"]:
            logger.info(f"\n✅ 成功创建的虚拟机:")
            for i, vm in enumerate(results["vms"], 1):
                logger.info(f"   {i}. {vm['name']} "
                      f"(ID: {vm['id'][:8]}..., "
                      f"镜像: {vm['image_id']}, "
                      f"模板: {vm['template']})")
        
        if results["errors"]:
            logger.info(f"\n🛑 创建失败的虚拟机:")
            for error in results["errors"]:
                logger.info(f"   {error['name']}: {error['error']}")
        
        logger.info('='*80)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="ArcherOSS 虚拟机创建工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --list-env                    # 列出所有环境
  %(prog)s --list-templates               # 列出所有模板
  %(prog)s --list-images                  # 列出可用镜像
  %(prog)s --env production --count 1     # 在生产环境创建1个虚拟机
  %(prog)s --env test --count 3 --template performance
  %(prog)s --env dev --count 2 --name dev-vm --template storage
        """
    )
    
    # 基本参数
    parser.add_argument('--env', default='production', 
                       help='目标环境 (默认: production)')
    parser.add_argument('--count', type=int, default=1,
                       help='创建数量 (默认: 1)')
    parser.add_argument('--name', 
                       help='虚拟机名称前缀')
    parser.add_argument('--template', default='standard',
                       choices=['basic', 'standard', 'performance', 'storage'],
                       help='配置模板 (默认: standard)')
    parser.add_argument('--image-id', 
                       help='镜像ID')
    parser.add_argument('--hostname', 
                       help='主机名')
    
    # 信息查询参数
    parser.add_argument('--list-env', action='store_true',
                       help='列出所有可用环境')
    parser.add_argument('--list-templates', action='store_true',
                       help='列出所有配置模板')
    parser.add_argument('--list-images', action='store_true',
                       help='列出可用镜像')
    
    # 高级参数 (覆盖模板)
    parser.add_argument('--cpu', type=int,
                       help='CPU核数 (覆盖模板)')
    parser.add_argument('--sockets', type=int,
                       help='CPU插槽数 (覆盖模板)')
    parser.add_argument('--memory', type=int,
                       help='内存大小(GB) (覆盖模板)')
    parser.add_argument('--video-model', choices=['VGA', 'QXL'],
                       help='视频模型 (覆盖模板)')
    parser.add_argument('--ha-enable', action='store_true',
                       help='启用高可用 (覆盖模板)')
    parser.add_argument('--disk-size', type=int,
                       help='磁盘大小(GB) (覆盖模板)')
    parser.add_argument('--priority', type=int,
                       help='优先级 (覆盖模板)')
    
    args = parser.parse_args()
    
    # 创建虚拟机创建器
    creator = VMCreator()
    
    # 处理信息查询
    if args.list_env:
        creator.list_environments()
        return
    
    if args.list_templates:
        creator.list_templates()
        return
    
    if args.list_images:
        creator.list_images(args.env)
        return
    
    # 准备覆盖参数
    override_params = {}
    if args.cpu:
        override_params['cpu'] = args.cpu
    if args.sockets:
        override_params['sockets'] = args.sockets
    if args.memory:
        override_params['memory'] = args.memory
    if args.video_model:
        override_params['videoModel'] = args.video_model
    if args.ha_enable:
        override_params['haEnable'] = True
    if args.disk_size:
        override_params['diskSize'] = args.disk_size
    if args.priority:
        override_params['priority'] = args.priority
    
    # 执行创建
    result = creator.create_vm(
        count=args.count,
        name=args.name,
        template=args.template,
        env=args.env,
        image_id=args.image_id,
        hostname=args.hostname,
        **override_params
    )
    
    # 根据结果设置退出码
    sys.exit(0 if result.get("success") else 1)

if __name__ == "__main__":
    main()