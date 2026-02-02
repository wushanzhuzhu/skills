#!/usr/bin/env python3
"""
VM API分析工具
分析Instances.createInstance_noNet()的参数签名和约束
"""

import inspect
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class VMAnalyzer:
    """VM API分析器"""
    
    def __init__(self):
        self.parameter_constraints = {}
        self.default_values = {}
        self.vm_templates = {}
        
    def analyze_vm_api(self):
        """分析VM创建API"""
        print("🔍 VM API分析报告")
        print("=" * 50)
        
        try:
            from Instances import Instances
            
            # 获取createInstance_noNet方法的签名
            method = getattr(Instances, 'createInstance_noNet', None)
            if method:
                sig = inspect.signature(method)
                print(f"📝 createInstance_noNet{sig}")
                
                # 分析参数
                params = sig.parameters
                print(f"\n📋 参数列表 ({len(params)} 个):")
                for param_name, param in params.items():
                    param_info = {
                        'name': param_name,
                        'type': param.annotation if param.annotation != inspect.Parameter.empty else 'Any',
                        'default': param.default if param.default != inspect.Parameter.empty else 'Required',
                        'kind': param.kind.name
                    }
                    print(f"   {param_name}: {param_info}")
                
                return params
            else:
                print("❌ 未找到createInstance_noNet方法")
                return None
                
        except Exception as e:
            print(f"❌ API分析失败: {e}")
            return None
    
    def analyze_parameter_constraints(self):
        """分析参数约束"""
        print("\n🎯 参数约束分析")
        print("=" * 50)
        
        constraints = {
            # 必需参数
            'name': {
                'type': str,
                'description': 'VM名称',
                'constraints': '长度1-64字符，支持字母数字下划线',
                'examples': ['vm-web-01', 'database-01', 'dev-machine-01']
            },
            'hostname': {
                'type': str,
                'description': '主机名',
                'constraints': '标准主机名格式',
                'examples': ['web-01', 'db-01', 'dev-01']
            },
            'videoModel': {
                'type': str,
                'description': '视频模型',
                'options': ['VGA', 'QXL', 'virtio'],
                'default': 'virtio',
                'recommendations': {
                    'desktop': 'QXL',
                    'server': 'virtio',
                    'legacy': 'VGA'
                }
            },
            'haEnable': {
                'type': bool,
                'description': '是否启用高可用',
                'options': [True, False],
                'default': False,
                'scenarios': {
                    'production': True,
                    'development': False,
                    'testing': False
                }
            },
            'cpu': {
                'type': int,
                'description': 'CPU核心数',
                'range': '1-32',
                'default': 2,
                'recommendations': {
                    'basic': 2,
                    'web_server': 4,
                    'database': 8,
                    'high_performance': 16
                }
            },
            'sockets': {
                'type': int,
                'description': 'CPU插槽数',
                'range': '1-4',
                'default': 1
            },
            'memory': {
                'type': int,
                'description': '内存大小(GB)',
                'range': '1-256',
                'default': 4,
                'recommendations': {
                    'basic': 2,
                    'standard': 4,
                    'web_server': 8,
                    'database': 16,
                    'memory_intensive': 32
                }
            },
            'zoneId': {
                'type': str,
                'description': '区域ID',
                'constraints': '有效的区域UUID',
                'source': 'Hosts.zone'
            },
            'storageType': {
                'type': str,
                'description': '存储类型',
                'options': ['ISCSI', 'LOCAL', 'NFS'],
                'default': 'ISCSI',
                'source': 'Hosts.getStorsbyDiskType()'
            },
            'storageManageId': {
                'type': str,
                'description': '存储管理ID',
                'constraints': '有效的存储管理UUID',
                'source': 'Hosts.getStorsbyDiskType()'
            },
            'diskType': {
                'type': str,
                'description': '磁盘类型ID',
                'constraints': '有效的磁盘类型UUID',
                'source': 'Hosts.getStorsbyDiskType()'
            },
            'imageId': {
                'type': str,
                'description': '镜像ID',
                'constraints': '有效的镜像UUID',
                'source': 'Images.getImagebystorageManageId()'
            },
            'adminPassword': {
                'type': str,
                'description': '管理员密码',
                'constraints': '8-32字符，包含字母数字特殊字符',
                'security_tip': '使用强密码，避免默认密码'
            }
        }
        
        # 可选参数
        optional_constraints = {
            'size': {
                'type': int,
                'description': '系统磁盘大小(GB)',
                'range': '10-2000',
                'default': 80,
                'recommendations': {
                    'basic': 80,
                    'web_server': 100,
                    'database': 200,
                    'data_intensive': 500
                }
            },
            'rebuildPriority': {
                'type': int,
                'description': '重建优先级',
                'range': '1-10',
                'default': 3
            },
            'numaEnable': {
                'type': bool,
                'description': 'NUMA启用',
                'default': False,
                'scenarios': {
                    'high_performance': True,
                    'standard': False
                }
            },
            'vmActive': {
                'type': bool,
                'description': '创建后是否启动',
                'default': False
            },
            'vncPwd': {
                'type': str,
                'description': 'VNC密码',
                'default': ''
            },
            'bigPageEnable': {
                'type': bool,
                'description': '大页内存启用',
                'default': False
            },
            'balloonSwitch': {
                'type': bool,
                'description': '气球内存开关',
                'default': False
            },
            'audioType': {
                'type': str,
                'description': '音频类型',
                'options': ['ich6', 'ac97', 'hda'],
                'default': 'ich6'
            },
            'cloneType': {
                'type': str,
                'description': '克隆类型',
                'options': ['LINK', 'FULL'],
                'default': 'LINK'
            },
            'priority': {
                'type': int,
                'description': '优先级',
                'range': '1-10',
                'default': 1
            }
        }
        
        all_constraints = {**constraints, **optional_constraints}
        
        print("📋 必需参数:")
        for param, info in constraints.items():
            print(f"   {param}:")
            print(f"     类型: {info['type']}")
            print(f"     描述: {info['description']}")
            if 'options' in info:
                print(f"     选项: {info['options']}")
            if 'range' in info:
                print(f"     范围: {info['range']}")
            if 'default' in info:
                print(f"     默认值: {info['default']}")
            print()
        
        print("📋 可选参数:")
        for param, info in optional_constraints.items():
            print(f"   {param}: {info['description']} (默认: {info['default']})")
        
        self.parameter_constraints = all_constraints
        return all_constraints
    
    def create_vm_templates(self):
        """创建VM配置模板"""
        print("\n🎯 VM配置模板设计")
        print("=" * 50)
        
        templates = {
            "basic": {
                "name": "basic-vm-{num}",
                "hostname": "basic-{num}",
                "description": "基础办公型VM",
                "videoModel": "virtio",
                "haEnable": False,
                "cpu": 2,
                "memory": 4,
                "size": 80,
                "cloneType": "LINK",
                "priority": 1,
                "use_case": "办公开发、轻量服务"
            },
            "web_server": {
                "name": "web-vm-{num}",
                "hostname": "web-{num}",
                "description": "Web服务器型VM",
                "videoModel": "virtio",
                "haEnable": True,
                "cpu": 4,
                "memory": 8,
                "size": 100,
                "cloneType": "LINK",
                "priority": 2,
                "numaEnable": True,
                "use_case": "Web应用、API服务"
            },
            "database": {
                "name": "db-vm-{num}",
                "hostname": "db-{num}",
                "description": "数据库型VM",
                "videoModel": "qxl",
                "haEnable": True,
                "cpu": 8,
                "memory": 16,
                "size": 200,
                "cloneType": "LINK",
                "priority": 3,
                "numaEnable": True,
                "bigPageEnable": True,
                "use_case": "MySQL、PostgreSQL数据库"
            },
            "development": {
                "name": "dev-vm-{num}",
                "hostname": "dev-{num}",
                "description": "开发测试型VM",
                "videoModel": "virtio",
                "haEnable": False,
                "cpu": 2,
                "memory": 4,
                "size": 60,
                "cloneType": "LINK",
                "priority": 1,
                "vmActive": True,
                "use_case": "代码开发、功能测试"
            },
            "high_performance": {
                "name": "hp-vm-{num}",
                "hostname": "hp-{num}",
                "description": "高性能计算VM",
                "videoModel": "virtio",
                "haEnable": True,
                "cpu": 16,
                "memory": 32,
                "size": 500,
                "cloneType": "FULL",
                "priority": 5,
                "numaEnable": True,
                "bigPageEnable": True,
                "use_case": "大数据处理、AI计算"
            }
        }
        
        print("📋 预定义模板:")
        for template_name, config in templates.items():
            print(f"   {template_name}: {config['description']}")
            print(f"     CPU: {config['cpu']}核, 内存: {config['memory']}GB, 磁盘: {config['size']}GB")
            print(f"     HA: {config['haEnable']}, 用途: {config['use_case']}")
            print()
        
        self.vm_templates = templates
        return templates
    
    def validate_vm_config(self, config):
        """验证VM配置"""
        print("\n✅ VM配置验证")
        print("=" * 50)
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }
        
        # 检查必需参数
        required_params = ['name', 'hostname', 'videoModel', 'haEnable', 'cpu', 
                          'memory', 'zoneId', 'storageType', 'storageManageId', 
                          'diskType', 'imageId', 'adminPassword']
        
        for param in required_params:
            if param not in config:
                validation_result["valid"] = False
                validation_result["errors"].append(f"缺少必需参数: {param}")
        
        # 验证参数值
        if 'cpu' in config:
            cpu = config['cpu']
            if not isinstance(cpu, int) or cpu < 1 or cpu > 32:
                validation_result["errors"].append(f"CPU核心数必须在1-32之间")
        
        if 'memory' in config:
            memory = config['memory']
            if not isinstance(memory, int) or memory < 1 or memory > 256:
                validation_result["errors"].append(f"内存大小必须在1-256GB之间")
        
        if 'size' in config:
            size = config['size']
            if not isinstance(size, int) or size < 10 or size > 2000:
                validation_result["errors"].append(f"磁盘大小必须在10-2000GB之间")
        
        if 'videoModel' in config:
            video = config['videoModel']
            if video not in ['VGA', 'QXL', 'virtio']:
                validation_result["errors"].append(f"视频模型必须是: VGA, QXL, virtio")
        
        # 性能建议
        if config.get('cpu', 0) >= 8 and not config.get('numaEnable', False):
            validation_result["recommendations"].append("8核以上CPU建议启用NUMA")
        
        if config.get('memory', 0) >= 16 and not config.get('bigPageEnable', False):
            validation_result["recommendations"].append("16GB以上内存建议启用大页内存")
        
        return validation_result
    
    def recommend_optimal_config(self, use_case, vm_count=1):
        """推荐最优配置"""
        print(f"\n🎯 为用例 '{use_case}' 推荐配置 (数量: {vm_count})")
        print("=" * 50)
        
        recommendations = {
            "office": {
                "template": "basic",
                "reasoning": "办公场景对性能要求不高，基础配置即可"
            },
            "web": {
                "template": "web_server",
                "reasoning": "Web服务需要稳定的性能和HA保障"
            },
            "database": {
                "template": "database",
                "reasoning": "数据库需要高性能和可靠性"
            },
            "development": {
                "template": "development",
                "reasoning": "开发环境需要快速部署和调试"
            },
            "compute": {
                "template": "high_performance",
                "reasoning": "计算密集型任务需要最强性能"
            }
        }
        
        recommendation = recommendations.get(use_case.lower(), recommendations["office"])
        template_config = self.vm_templates.get(recommendation["template"], self.vm_templates["basic"])
        
        print(f"📋 推荐模板: {recommendation['template']}")
        print(f"📝 理由: {recommendation['reasoning']}")
        print(f"⚙️ 配置: CPU:{template_config['cpu']}核, 内存:{template_config['memory']}GB, 磁盘:{template_config['size']}GB")
        print(f"🛡️ 高可用: {'是' if template_config['haEnable'] else '否'}")
        
        return {
            "template": recommendation["template"],
            "config": template_config,
            "reasoning": recommendation["reasoning"]
        }

def main():
    """命令行界面"""
    import sys
    
    analyzer = VMAnalyzer()
    
    if len(sys.argv) < 2:
        print("🔧 VM API分析工具")
        print("python vm_analyzer.py [命令] [参数]")
        print("\n命令:")
        print("  analyze                    - 分析VM API")
        print("  constraints                - 显示参数约束")
        print("  templates                  - 显示配置模板")
        print("  validate <config_file>     - 验证配置文件")
        print("  recommend <use_case>       - 推荐配置")
        return
    
    command = sys.argv[1]
    
    if command == "analyze":
        analyzer.analyze_vm_api()
    
    elif command == "constraints":
        analyzer.analyze_parameter_constraints()
    
    elif command == "templates":
        analyzer.create_vm_templates()
    
    elif command == "recommend":
        if len(sys.argv) < 3:
            print("❌ 请提供用例: office, web, database, development, compute")
            return
        use_case = sys.argv[2]
        analyzer.recommend_optimal_config(use_case)
    
    elif command == "validate":
        if len(sys.argv) < 3:
            print("❌ 请提供配置文件路径")
            return
        config_file = sys.argv[2]
        try:
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
            result = analyzer.validate_vm_config(config)
            print("✅" if result["valid"] else "❌", "配置验证结果")
            for error in result["errors"]:
                print(f"   错误: {error}")
            for warning in result["warnings"]:
                print(f"   警告: {warning}")
            for rec in result["recommendations"]:
                print(f"   建议: {rec}")
        except Exception as e:
            print(f"❌ 读取配置文件失败: {e}")
    
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == "__main__":
    main()