#!/usr/bin/env python3
"""
VM配置模板系统
提供预定义的VM配置模板和智能推荐
"""

import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

import os
from typing import Dict, List, Optional
from vm_analyzer import VMAnalyzer

class VMConfigTemplates:
    """VM配置模板管理器"""
    
    def __init__(self):
        self.analyzer = VMAnalyzer()
        self.templates = self._load_default_templates()
        self.custom_templates = {}
        
    def _load_default_templates(self) -> Dict:
        """加载默认模板"""
        return {
            "basic": {
                "name": "basic-vm-{num}",
                "hostname": "basic-{num}",
                "description": "基础办公型VM",
                "videoModel": "virtio",
                "haEnable": False,
                "cpu": 2,
                "sockets": 1,
                "memory": 4,
                "size": 80,
                "cloneType": "LINK",
                "priority": 1,
                "vmActive": False,
                "numaEnable": False,
                "bigPageEnable": False,
                "balloonSwitch": False,
                "audioType": "ich6",
                "vncPwd": "",
                "rebuildPriority": 3,
                "use_case": "办公开发、轻量服务",
                "tags": ["office", "basic", "light"],
                "estimated_deploy_time": "3-5分钟",
                "resource_cost": "低"
            },
            
            "web_server": {
                "name": "web-vm-{num}",
                "hostname": "web-{num}",
                "description": "Web服务器型VM",
                "videoModel": "virtio",
                "haEnable": True,
                "cpu": 4,
                "sockets": 1,
                "memory": 8,
                "size": 100,
                "cloneType": "LINK",
                "priority": 2,
                "vmActive": True,
                "numaEnable": True,
                "bigPageEnable": False,
                "balloonSwitch": False,
                "audioType": "ich6",
                "vncPwd": "",
                "rebuildPriority": 2,
                "use_case": "Web应用、API服务",
                "tags": ["web", "server", "production"],
                "estimated_deploy_time": "5-8分钟",
                "resource_cost": "中"
            },
            
            "database": {
                "name": "db-vm-{num}",
                "hostname": "db-{num}",
                "description": "数据库型VM",
                "videoModel": "qxl",
                "haEnable": True,
                "cpu": 8,
                "sockets": 2,
                "memory": 16,
                "size": 200,
                "cloneType": "LINK",
                "priority": 3,
                "vmActive": True,
                "numaEnable": True,
                "bigPageEnable": True,
                "balloonSwitch": False,
                "audioType": "ich6",
                "vncPwd": "",
                "rebuildPriority": 1,
                "use_case": "MySQL、PostgreSQL数据库",
                "tags": ["database", "server", "production", "high_performance"],
                "estimated_deploy_time": "8-12分钟",
                "resource_cost": "高"
            },
            
            "development": {
                "name": "dev-vm-{num}",
                "hostname": "dev-{num}",
                "description": "开发测试型VM",
                "videoModel": "virtio",
                "haEnable": False,
                "cpu": 2,
                "sockets": 1,
                "memory": 4,
                "size": 60,
                "cloneType": "LINK",
                "priority": 1,
                "vmActive": True,
                "numaEnable": False,
                "bigPageEnable": False,
                "balloonSwitch": False,
                "audioType": "ich6",
                "vncPwd": "dev123",
                "rebuildPriority": 3,
                "use_case": "代码开发、功能测试",
                "tags": ["development", "test", "temporary"],
                "estimated_deploy_time": "2-4分钟",
                "resource_cost": "低"
            },
            
            "high_performance": {
                "name": "hp-vm-{num}",
                "hostname": "hp-{num}",
                "description": "高性能计算VM",
                "videoModel": "virtio",
                "haEnable": True,
                "cpu": 16,
                "sockets": 2,
                "memory": 32,
                "size": 500,
                "cloneType": "FULL",
                "priority": 5,
                "vmActive": True,
                "numaEnable": True,
                "bigPageEnable": True,
                "balloonSwitch": True,
                "audioType": "ich6",
                "vncPwd": "",
                "rebuildPriority": 1,
                "use_case": "大数据处理、AI计算",
                "tags": ["performance", "compute", "research"],
                "estimated_deploy_time": "15-20分钟",
                "resource_cost": "极高"
            },
            
            "container_host": {
                "name": "container-vm-{num}",
                "hostname": "container-{num}",
                "description": "容器宿主机VM",
                "videoModel": "virtio",
                "haEnable": True,
                "cpu": 8,
                "sockets": 1,
                "memory": 16,
                "size": 150,
                "cloneType": "LINK",
                "priority": 3,
                "vmActive": True,
                "numaEnable": True,
                "bigPageEnable": False,
                "balloonSwitch": True,
                "audioType": "ich6",
                "vncPwd": "",
                "rebuildPriority": 2,
                "use_case": "Docker、Kubernetes节点",
                "tags": ["container", "orchestration", "devops"],
                "estimated_deploy_time": "8-12分钟",
                "resource_cost": "高"
            }
        }
    
    def get_template(self, template_name: str) -> Optional[Dict]:
        """获取指定模板"""
        return self.templates.get(template_name)
    
    def list_templates(self) -> List[Dict]:
        """列出所有可用模板"""
        template_list = []
        for name, config in self.templates.items():
            template_info = {
                "name": name,
                "description": config["description"],
                "cpu": config["cpu"],
                "memory": config["memory"],
                "size": config["size"],
                "ha": config["haEnable"],
                "use_case": config["use_case"],
                "tags": config["tags"],
                "deploy_time": config["estimated_deploy_time"],
                "cost": config["resource_cost"]
            }
            template_list.append(template_info)
        return template_list
    
    def search_templates(self, keyword: str) -> List[Dict]:
        """搜索模板"""
        results = []
        keyword = keyword.lower()
        
        for name, config in self.templates.items():
            if (keyword in name.lower() or 
                keyword in config["description"].lower() or
                keyword in config["use_case"].lower() or
                any(keyword in tag.lower() for tag in config["tags"])):
                results.append({"name": name, **config})
        
        return results
    
    def generate_vm_config(self, template_name: str, vm_num: int = 1, 
                          custom_overrides: Dict = None) -> Dict:
        """生成VM配置"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")
        
        # 复制模板配置
        config = template.copy()
        
        # 替换占位符
        config["name"] = config["name"].format(num=vm_num)
        config["hostname"] = config["hostname"].format(num=vm_num)
        
        # 应用自定义覆盖
        if custom_overrides:
            config.update(custom_overrides)
        
        return config
    
    def recommend_template(self, use_case: str, performance_requirement: str = "standard") -> Dict:
        """智能推荐模板"""
        
        recommendation_matrix = {
            "office": {
                "low": "basic",
                "standard": "basic", 
                "high": "development"
            },
            "development": {
                "low": "development",
                "standard": "development",
                "high": "web_server"
            },
            "web": {
                "low": "web_server",
                "standard": "web_server",
                "high": "database"
            },
            "database": {
                "low": "database",
                "standard": "database",
                "high": "high_performance"
            },
            "compute": {
                "low": "high_performance",
                "standard": "high_performance",
                "high": "high_performance"
            },
            "container": {
                "low": "container_host",
                "standard": "container_host",
                "high": "high_performance"
            }
        }
        
        # 获取推荐模板名
        recommended_name = recommendation_matrix.get(use_case, {}).get(performance_requirement, "basic")
        
        template = self.get_template(recommended_name)
        reasoning = f"基于用例'{use_case}'和性能要求'{performance_requirement}'推荐"
        
        return {
            "template_name": recommended_name,
            "template": template,
            "reasoning": reasoning,
            "alternatives": self._get_alternative_templates(use_case, performance_requirement)
        }
    
    def _get_alternative_templates(self, use_case: str, performance_requirement: str) -> List[str]:
        """获取替代模板推荐"""
        alternatives = []
        
        if use_case == "office":
            alternatives = ["development", "basic"]
        elif use_case == "development":
            alternatives = ["basic", "web_server"]
        elif use_case == "web":
            alternatives = ["basic", "database"]
        elif use_case == "database":
            alternatives = ["web_server", "high_performance"]
        elif use_case == "compute":
            alternatives = ["database", "container_host"]
        else:
            alternatives = ["basic", "web_server"]
        
        return alternatives[:2]  # 最多返回2个替代方案
    
    def validate_template_customization(self, template_name: str, 
                                     custom_overrides: Dict) -> Dict:
        """验证模板自定义"""
        template = self.get_template(template_name)
        if not template:
            return {"valid": False, "errors": [f"模板不存在: {template_name}"]}
        
        # 合并配置
        config = template.copy()
        config.update(custom_overrides)
        
        # 使用分析器验证
        return self.analyzer.validate_vm_config(config)
    
    def calculate_resource_requirements(self, configs: List[Dict]) -> Dict:
        """计算资源需求"""
        total_cpu = sum(config.get("cpu", 0) for config in configs)
        total_memory = sum(config.get("memory", 0) for config in configs)
        total_storage = sum(config.get("size", 0) for config in configs)
        ha_count = sum(1 for config in configs if config.get("haEnable", False))
        
        return {
            "total_cpu": total_cpu,
            "total_memory_gb": total_memory,
            "total_storage_gb": total_storage,
            "ha_instances": ha_count,
            "instance_count": len(configs),
            "estimated_deploy_time": f"{len(configs) * 3}-{len(configs) * 8}分钟"
        }
    
    def export_template(self, template_name: str, filename: str):
        """导出模板到文件"""
        template = self.get_template(template_name)
        if not template:
            logger.error(f"❌ 模板不存在: {template_name}")
            return False
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({template_name: template}, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 模板已导出到: {filename}")
            return True
        except Exception as e:
            logger.error(f"❌ 导出失败: {e}")
            return False
    
    def import_template(self, filename: str) -> bool:
        """从文件导入模板"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported = json.load(f)
            
            for name, config in imported.items():
                # 验证模板格式
                required_fields = ["name", "hostname", "cpu", "memory", "size"]
                if all(field in config for field in required_fields):
                    self.custom_templates[name] = config
                    logger.info(f"✅ 已导入模板: {name}")
                else:
                    logger.error(f"❌ 模板格式不正确: {name}")
            
            return True
        except Exception as e:
            logger.error(f"❌ 导入失败: {e}")
            return False
    
    def display_templates_table(self, templates: List[Dict] = None):
        """显示模板表格"""
        if templates is None:
            templates = self.list_templates()
        
        if not templates:
            logger.info("📭 没有可用的模板")
            return
        
        logger.info("\n🎯 VM配置模板列表:")
        logger.info("=" * 80)
        logger.info(f"{'模板名称':<15} {'CPU':<4} {'内存':<6} {'磁盘':<8} {'HA':<3} {'用途':<20} {'成本':<8}")
        logger.info("-" * 80)
        
        for template in templates:
            ha = "是" if template["ha"] else "否"
            logger.info(f"{template['name']:<15} {template['cpu']:<4} "
                  f"{template['memory']:<6} {template['size']:<8} "
                  f"{ha:<3} {template['use_case'][:18]:<20} {template['cost']:<8}")
        
        logger.info("=" * 80)

def main():
    """命令行界面"""
    import sys
    
    templates = VMConfigTemplates()
    
    if len(sys.argv) < 2:
        logger.info("🔧 VM配置模板管理器")
        logger.info("python vm_config_templates.py [命令] [参数]")
        logger.info("\n命令:")
        logger.info("  list                      - 列出所有模板")
        logger.info("  show <template_name>     - 显示模板详情")
        logger.info("  search <keyword>          - 搜索模板")
        logger.info("  generate <template> <num> - 生成VM配置")
        logger.info("  recommend <use_case>      - 智能推荐模板")
        logger.info("  export <template> <file>  - 导出模板")
        logger.info("  import <file>             - 导入模板")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        templates.display_templates_table()
    
    elif command == "show":
        if len(sys.argv) < 3:
            logger.error("❌ 请提供模板名称")
            return
        template = templates.get_template(sys.argv[2])
        if template:
            logger.info(f"\n📋 模板详情: {sys.argv[2]}")
            logger.info("=" * 40)
            for key, value in template.items():
                logger.info(f"{key}: {value}")
        else:
            logger.error(f"❌ 模板不存在: {sys.argv[2]}")
    
    elif command == "search":
        if len(sys.argv) < 3:
            logger.error("❌ 请提供搜索关键词")
            return
        results = templates.search_templates(sys.argv[2])
        logger.info(f"\n🔍 搜索结果: '{sys.argv[2]}'")
        templates.display_templates_table([{"name": name, **config} for name, config in results.items()])
    
    elif command == "generate":
        if len(sys.argv) < 4:
            logger.error("❌ 请提供模板名称和VM编号")
            return
        template_name = sys.argv[2]
        vm_num = int(sys.argv[3])
        
        try:
            config = templates.generate_vm_config(template_name, vm_num)
            logger.info(f"\n📋 生成的VM配置 (模板: {template_name}, 编号: {vm_num}):")
            logger.info("=" * 50)
            logger.info(json.dumps(config, ensure_ascii=False, indent=2))
        except Exception as e:
            logger.error(f"❌ 生成配置失败: {e}")
    
    elif command == "recommend":
        if len(sys.argv) < 3:
            logger.error("❌ 请提供用例")
            return
        use_case = sys.argv[2]
        performance = sys.argv[3] if len(sys.argv) > 3 else "standard"
        
        result = templates.recommend_template(use_case, performance)
        logger.info(f"\n🎯 推荐结果:")
        logger.info("=" * 50)
        logger.info(f"推荐模板: {result['template_name']}")
        logger.info(f"推荐理由: {result['reasoning']}")
        logger.info(f"替代方案: {', '.join(result['alternatives'])}")
    
    elif command == "export":
        if len(sys.argv) < 4:
            logger.error("❌ 请提供模板名称和文件名")
            return
        templates.export_template(sys.argv[2], sys.argv[3])
    
    elif command == "import":
        if len(sys.argv) < 3:
            logger.error("❌ 请提供文件名")
            return
        templates.import_template(sys.argv[2])
    
    else:
        logger.error(f"❌ 未知命令: {command}")

if __name__ == "__main__":
    main()