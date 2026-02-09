#!/usr/bin/env python3
"""
智能VM创建器
集成环境感知、镜像发现、参数验证和批量创建
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
import json
import time
from typing import Dict, List, Optional
from vm_analyzer import VMAnalyzer
from vm_config_templates import VMConfigTemplates
from env_manager import EnvironmentManager

class VMManager:
    """智能VM管理器"""
    
    def __init__(self):
        self.env_manager = EnvironmentManager()
        self.analyzer = VMAnalyzer()
        self.templates = VMConfigTemplates()
        self.current_env = None
        self.connection_info = None
        self.available_images = []
        self.storage_info = []
        
    def select_environment_interactive(self) -> str:
        """交互式环境选择"""
        environments = self.env_manager.list_environments()
        
        if not environments:
            logger.error("❌ 没有配置的环境")
            return None
        
        logger.info("\n🌐 可用环境列表:")
        logger.info("=" * 70)
        logger.info(f"{'序号':<4} {'环境ID':<12} {'名称':<15} {'地址':<25} {'描述':<20}")
        logger.info("-" * 70)
        
        for i, env in enumerate(environments, 1):
            logger.info(f"{i:<4} {env['id']:<12} {env['name']:<15} "
                  f"{env['url']:<25} {env['description'][:18]:<20}")
        
        logger.info("=" * 70)
        
        while True:
            try:
                choice = input(f"\n请选择环境 (1-{len(environments)}) 或输入环境ID: ").strip()
                
                # 尝试按序号选择
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(environments):
                        selected_env = environments[idx]
                        return selected_env['id']
                
                # 尝试按ID选择
                for env in environments:
                    if env['id'] == choice:
                        return env['id']
                
                logger.error("❌ 无效选择，请重新输入")
                
            except KeyboardInterrupt:
                logger.info("\n👋 操作已取消")
                return None
    
    def auto_select_environment(self, env_hint: str = None) -> str:
        """自动环境选择"""
        if not env_hint:
            environments = self.env_manager.list_environments()
            for env in environments:
                if 'prod' in env.get('tags', []) or '生产' in env.get('name', ''):
                    return env['id']
            return environments[0]['id'] if environments else None
        
        results = self.env_manager.search_environments(env_hint)
        if len(results) == 1:
            return results[0]['id']
        elif len(results) > 1:
            logger.info(f"🔍 找到 {len(results)} 个匹配环境，请手动选择:")
            return self.select_environment_interactive()
        else:
            logger.error(f"❌ 没有找到匹配 '{env_hint}' 的环境")
            return self.select_environment_interactive()
    
    def check_environment(self, env_id: str) -> bool:
        """检查环境可用性"""
        self.connection_info = self.env_manager.get_connection_info(env_id)
        
        if not self.connection_info:
            logger.error(f"❌ 环境不存在: {env_id}")
            return False
        
        logger.info(f"🔗 正在连接环境: {self.connection_info['name']}")
        logger.info(f"📡 地址: {self.connection_info['url']}")
        
        # 测试连接
        try:
            from utils.audit import ArcherAudit
            from Hosts import Hosts
            from Images import Images
            
            audit = ArcherAudit(
                self.connection_info['username'],
                self.connection_info['password'], 
                self.connection_info['url']
            )
            
            if audit.setSession():
                logger.info(f"✅ 环境连接成功: {self.connection_info['name']}")
                self.current_env = env_id
                
                # 初始化管理器
                host = Hosts(
                    self.connection_info['username'],
                    self.connection_info['password'],
                    self.connection_info['url'],
                    audit=audit
                )
                
                # 获取资源信息
                self.storage_info = host.getStorsbyDiskType()
                images_manager = Images(
                    self.connection_info['username'],
                    self.connection_info['password'],
                    self.connection_info['url'],
                    audit=audit
                )
                self.available_images = images_manager.getImagebystorageManageId(host)
                
                return True
            else:
                logger.error(f"❌ 环境连接失败: {self.connection_info['name']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 连接测试失败: {e}")
            return False
    
    def discover_resources(self):
        """发现可用资源"""
        logger.info("\n🔍 资源发现结果:")
        logger.info("=" * 50)
        
        # 存储信息
        if self.storage_info:
            logger.info(f"💾 可用存储: {len(self.storage_info)} 个")
            for i, storage in enumerate(self.storage_info[:3], 1):  # 显示前3个
                logger.info(f"   {i}. {storage.get('stackName')} - {storage.get('storageBackend')}")
        else:
            logger.error("❌ 未发现存储资源")
        
        # 镜像信息
        if self.available_images:
            logger.info(f"🖼️ 可用镜像: {len(self.available_images)} 个")
            for i, image in enumerate(self.available_images[:3], 1):  # 显示前3个
                logger.info(f"   {i}. {image.get('imageName')} - {image.get('imageId')[:8]}...")
        else:
            logger.error("❌ 未发现可用镜像")
        
        return bool(self.storage_info and self.available_images)
    
    def get_image_recommendations(self, use_case: str = "general") -> List[Dict]:
        """获取镜像推荐"""
        if not self.available_images:
            return []
        
        recommendations = {
            "office": ["ubuntu", "windows", "centos"],
            "development": ["ubuntu", "debian", "fedora"],
            "web": ["centos", "ubuntu", "alpine"],
            "database": ["centos", "ubuntu", "oracle"],
            "general": ["ubuntu", "centos"]
        }
        
        keywords = recommendations.get(use_case, recommendations["general"])
        recommended_images = []
        
        for image in self.available_images:
            image_name = image.get('imageName', '').lower()
            for keyword in keywords:
                if keyword in image_name:
                    recommended_images.append(image)
                    break
        
        return recommended_images[:3] if recommended_images else self.available_images[:3]
    
    def prepare_vm_config(self, template_name: str, use_case: str = "general",
                          custom_overrides: Dict = None) -> Dict:
        """准备VM配置"""
        
        # 获取模板
        template = self.templates.get_template(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")
        
        # 获取存储信息
        if not self.storage_info:
            raise ValueError("存储信息不可用")
        
        storage = self.storage_info[0]  # 使用第一个存储
        storage_config = {
            "zoneId": storage.get('zoneId'),
            "storageType": storage.get('storageBackend'),
            "storageManageId": storage.get('storageManageId'),
            "diskType": storage.get('diskType')
        }
        
        # 生成VM配置
        vm_num = 1  # 单个VM编号
        config = self.templates.generate_vm_config(template_name, vm_num, custom_overrides)
        config.update(storage_config)
        
        # 设置镜像ID
        image_recs = self.get_image_recommendations(use_case)
        if image_recs:
            config["imageId"] = image_recs[0].get('imageId')
            logger.info(f"🖼️ 推荐镜像: {image_recs[0].get('imageName')}")
        else:
            config["imageId"] = self.available_images[0].get('imageId') if self.available_images else ""
            logger.info(f"🖼️ 使用镜像: {self.available_images[0].get('imageName') if self.available_images else '无'}")
        
        # 设置管理员密码（如果未提供）
        if not config.get("adminPassword"):
            config["adminPassword"] = "VM@2024!"  # 默认密码
        
        return config
    
    def validate_vm_config(self, config: Dict) -> Dict:
        """验证VM配置"""
        validation = self.analyzer.validate_vm_config(config)
        
        # 额外的环境特定验证
        if self.storage_info:
            storage_ids = [s.get('storageManageId') for s in self.storage_info]
            if config.get('storageManageId') not in storage_ids:
                validation["errors"].append(f"存储管理ID不存在: {config.get('storageManageId')}")
        
        if self.available_images:
            image_ids = [img.get('imageId') for img in self.available_images]
            if config.get('imageId') not in image_ids:
                validation["errors"].append(f"镜像ID不存在: {config.get('imageId')}")
        
        return validation
    
    def create_single_vm(self, config: Dict) -> Dict:
        """创建单个VM"""
        try:
            from utils.audit import ArcherAudit
            from Hosts import Hosts
            from Instances import Instances
            
            # 初始化连接
            audit = ArcherAudit(
                self.connection_info['username'],
                self.connection_info['password'],
                self.connection_info['url']
            )
            
            if not audit.setSession():
                return {"success": False, "error": "认证失败"}
            
            host = Hosts(
                self.connection_info['username'],
                self.connection_info['password'],
                self.connection_info['url'],
                audit=audit
            )
            
            instances = Instances(
                self.connection_info['username'],
                self.connection_info['password'],
                self.connection_info['url'],
                audit=audit
            )
            
            logger.info(f"🚀 正在创建VM: {config['name']}")
            
            # 调用创建API
            vm_ids = instances.createInstance_noNet(**config)
            
            if vm_ids and len(vm_ids) > 0:
                return {
                    "success": True,
                    "vm_id": vm_ids[0],
                    "vm_name": config['name'],
                    "config": config
                }
            else:
                return {"success": False, "error": "创建失败"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_batch_vms(self, template_name: str, vm_count: int,
                        use_case: str = "general", custom_overrides: Dict = None) -> Dict:
        """批量创建VM"""
        
        logger.info(f"🔥 开始批量创建 {vm_count} 个VM (模板: {template_name})")
        logger.info("=" * 60)
        
        results = {
            "total": vm_count,
            "success": [],
            "failed": [],
            "start_time": time.time()
        }
        
        for i in range(1, vm_count + 1):
            logger.info(f"\n📁 创建第 {i}/{vm_count} 个VM...")
            
            try:
                # 准备配置
                config = self.prepare_vm_config(template_name, use_case, custom_overrides)
                config["name"] = config["name"].format(num=i)
                config["hostname"] = config["hostname"].format(num=i)
                
                # 验证配置
                validation = self.validate_vm_config(config)
                if not validation["valid"]:
                    error_msg = f"配置验证失败: {', '.join(validation['errors'])}"
                    results["failed"].append({
                        "vm_num": i,
                        "vm_name": config["name"],
                        "error": error_msg
                    })
                    logger.error(f"❌ 第 {i} 个VM配置验证失败")
                    continue
                
                # 创建VM
                result = self.create_single_vm(config)
                
                if result["success"]:
                    results["success"].append({
                        "vm_num": i,
                        "vm_id": result["vm_id"],
                        "vm_name": result["vm_name"]
                    })
                    logger.info(f"✅ 第 {i} 个VM创建成功: {result['vm_name']}")
                else:
                    results["failed"].append({
                        "vm_num": i,
                        "vm_name": config["name"],
                        "error": result["error"]
                    })
                    logger.error(f"❌ 第 {i} 个VM创建失败: {result['error']}")
                
                # 添加延迟避免API频率限制
                if i < vm_count:
                    logger.info("⏳ 等待3秒后继续...")
                    time.sleep(3)
                    
            except Exception as e:
                results["failed"].append({
                    "vm_num": i,
                    "vm_name": f"vm-{i}",
                    "error": str(e)
                })
                logger.error(f"❌ 第 {i} 个VM创建出错: {e}")
        
        results["end_time"] = time.time()
        results["duration"] = results["end_time"] - results["start_time"]
        
        return self.generate_batch_report(results)
    
    def generate_batch_report(self, results: Dict) -> Dict:
        """生成批量创建报告"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 批量VM创建结果汇总")
        logger.info("=" * 60)
        
        success_count = len(results["success"])
        failed_count = len(results["failed"])
        
        logger.info(f"✅ 成功创建: {success_count}/{results['total']}")
        logger.error(f"❌ 创建失败: {failed_count}/{results['total']}")
        logger.info(f"📈 成功率: {success_count/results['total']*100:.1f}%")
        logger.info(f"⏱️ 总耗时: {results['duration']:.1f}秒")
        logger.info(f"🌐 目标环境: {self.connection_info['name']}")
        
        # 成功的VM列表
        if results["success"]:
            logger.info(f"\n✅ 成功创建的VM:")
            for vm in results["success"]:
                logger.info(f"   {vm['vm_num']}. {vm['vm_name']} (ID: {vm['vm_id'][:8]}...)")
        
        # 失败的VM列表
        if results["failed"]:
            logger.info(f"\n❌ 失败的VM:")
            for vm in results["failed"]:
                logger.info(f"   {vm['vm_num']}. {vm['vm_name']}: {vm['error']}")
        
        # 资源统计
        if results["success"]:
            cpu_total = len(results["success"]) * 2  # 假设每个VM 2核
            memory_total = len(results["success"]) * 4  # 假设每个VM 4GB
            logger.info(f"\n💾 资源统计:")
            logger.info(f"   总CPU: {cpu_total} 核")
            logger.info(f"   总内存: {memory_total} GB")
        
        logger.info("\n🎉 批量创建任务完成!")
        return results
    
    def get_vm_info(self, vm_id: str) -> Dict:
        """获取VM信息"""
        try:
            from utils.audit import ArcherAudit
            from Instances import Instances
            
            audit = ArcherAudit(
                self.connection_info['username'],
                self.connection_info['password'],
                self.connection_info['url']
            )
            
            if audit.setSession():
                instances = Instances(
                    self.connection_info['username'],
                    self.connection_info['password'],
                    self.connection_info['url'],
                    audit=audit
                )
                
                vm_info = instances.getVminfobyid(vm_id)
                return vm_info
            else:
                return {"error": "认证失败"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def delete_vm(self, vm_id: str) -> bool:
        """删除VM"""
        try:
            from utils.audit import ArcherAudit
            from Instances import Instances
            
            audit = ArcherAudit(
                self.connection_info['username'],
                self.connection_info['password'],
                self.connection_info['url']
            )
            
            if audit.setSession():
                instances = Instances(
                    self.connection_info['username'],
                    self.connection_info['password'],
                    self.connection_info['url'],
                    audit=audit
                )
                
                success = instances.deleteInstance_byId(vm_id)
                return success
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ 删除VM失败: {e}")
            return False

def main():
    """命令行界面"""
    import sys
    
    manager = VMManager()
    
    if len(sys.argv) < 2:
        logger.info("🔧 智能VM管理器")
        logger.info("python vm_manager.py [命令] [参数]")
        logger.info("\n命令:")
        logger.info("  create <template> <count> [env_hint]  - 批量创建VM")
        logger.info("  single <template> [env_hint]        - 创建单个VM")
        logger.info("  env-list                           - 列出环境")
        logger.info("  templates                          - 列出模板")
        logger.info("  images <env_id>                     - 列出镜像")
        return
    
    command = sys.argv[1]
    
    if command == "create":
        if len(sys.argv) < 4:
            logger.error("❌ 请提供模板名称和VM数量")
            return
        
        template = sys.argv[2]
        count = int(sys.argv[3])
        env_hint = sys.argv[4] if len(sys.argv) > 4 else None
        
        # 环境选择
        if env_hint:
            env_id = manager.auto_select_environment(env_hint)
        else:
            env_id = manager.select_environment_interactive()
        
        if not env_id or not manager.check_environment(env_id):
            logger.error("❌ 环境选择或连接失败")
            return
        
        # 资源发现
        if not manager.discover_resources():
            logger.error("❌ 资源发现失败")
            return
        
        # 批量创建
        results = manager.create_batch_vms(template, count)
        
    elif command == "single":
        if len(sys.argv) < 3:
            logger.error("❌ 请提供模板名称")
            return
        
        template = sys.argv[2]
        env_hint = sys.argv[3] if len(sys.argv) > 3 else None
        
        # 环境选择和创建逻辑类似...
        logger.info("单个VM创建功能待实现")
        
    elif command == "env-list":
        manager.env_manager.display_environments_table()
        
    elif command == "templates":
        manager.templates.display_templates_table()
        
    elif command == "images":
        if len(sys.argv) < 3:
            logger.error("❌ 请提供环境ID")
            return
        
        env_id = sys.argv[2]
        if manager.check_environment(env_id):
            manager.discover_resources()
    
    else:
        logger.error(f"❌ 未知命令: {command}")

if __name__ == "__main__":
    main()