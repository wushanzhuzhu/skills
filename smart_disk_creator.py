#!/usr/bin/env python3
"""
智能磁盘创建器 - 基于API分析，避免试错
精准参数匹配和配置生成
"""

import sys
import os
import inspect
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class SmartDiskCreator:
    def __init__(self, username, password, url):
        self.username = username
        self.password = password
        self.url = url
        self.audit = None
        self.host = None
        self.volumes = None
        
    def validate_parameters(self, config):
        """基于API签名验证参数"""
        from utils.audit import ArcherAudit
        
        # 获取createDisk_vstor的参数要求
        required_params = {
            'storageManageId': str,
            'pageSize': str,
            'compression': str, 
            'name': str,
            'size': int,
            'iops': int,
            'bandwidth': int,
            'count': int,
            'readCache': bool,
            'zoneId': str
        }
        
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 检查必需参数
        for param, param_type in required_params.items():
            if param not in config:
                validation_results["valid"] = False
                validation_results["errors"].append(f"缺少必需参数: {param}")
            elif not isinstance(config[param], param_type):
                validation_results["valid"] = False
                validation_results["errors"].append(f"参数类型错误: {param} 应为 {param_type.__name__}")
        
        # 验证参数值范围
        if config.get('pageSize') not in ['4K', '8K', '16K', '32K']:
            validation_results["valid"] = False
            validation_results["errors"].append("pageSize 必须是: 4K, 8K, 16K, 32K")
            
        if config.get('compression') not in ['Disabled', 'LZ4', 'Gzip_opt', 'Gzip_high']:
            validation_results["valid"] = False
            validation_results["errors"].append("compression 必须是: Disabled, LZ4, Gzip_opt, Gzip_high")
            
        if not (75 <= config.get('iops', 0) <= 250000):
            validation_results["valid"] = False
            validation_results["errors"].append("iops 必须在 75-250000 范围内")
            
        if not (1 <= config.get('bandwidth', 0) <= 1000):
            validation_results["valid"] = False
            validation_results["errors"].append("bandwidth 必须在 1-1000 MB/s 范围内")
        
        return validation_results
    
    def get_storage_info(self):
        """获取存储资源信息"""
        try:
            from utils.audit import ArcherAudit
            from Hosts import Hosts
            
            # 初始化认证
            self.audit = ArcherAudit(self.username, self.password, self.url)
            if not self.audit.setSession():
                return {"success": False, "error": "认证失败"}
            
            # 获取存储信息
            self.host = Hosts(self.username, self.password, self.url, self.audit)
            storage_info = self.host.getStorsbyDiskType()
            
            if not storage_info:
                return {"success": False, "error": "无法获取存储信息"}
                
            return {
                "success": True,
                "storage_info": storage_info,
                "zone_id": self.host.zone
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_optimal_config(self, disk_size_gb, use_case="standard"):
        """基于存储能力和用例生成最优配置"""
        
        # 获取存储信息
        storage_result = self.get_storage_info()
        if not storage_result["success"]:
            return storage_result
        
        storage_info = storage_result["storage_info"][0]  # 使用第一个存储
        zone_id = storage_result["zone_id"]
        
        # 基于存储实际性能生成配置
        configs = {
            "test": {
                "description": "测试环境配置",
                "pageSize": "4K",
                "compression": "Disabled",
                "iops": 75,
                "bandwidth": 1,
                "readCache": False
            },
            "standard": {
                "description": "标准配置",
                "pageSize": "4K",
                "compression": "LZ4", 
                "iops": 400,  # 基于实际存储性能
                "bandwidth": 40,  # 基于实际存储性能
                "readCache": True
            },
            "performance": {
                "description": "高性能配置",
                "pageSize": "8K",
                "compression": "Disabled",  # 禁用压缩以获得最佳性能
                "iops": 1000,
                "bandwidth": 100,
                "readCache": True
            }
        }
        
        # 选择配置模板
        template = configs.get(use_case, configs["standard"])
        
        # 生成完整配置
        import uuid
        config = {
            "storageManageId": storage_info.get("storageManageId"),
            "pageSize": template["pageSize"],
            "compression": template["compression"],
            "name": f"disk-{disk_size_gb}gb-{str(uuid.uuid4())[:8]}",
            "size": disk_size_gb,
            "iops": template["iops"],
            "bandwidth": template["bandwidth"],
            "count": 1,
            "readCache": template["readCache"],
            "zoneId": zone_id
        }
        
        # 验证配置
        validation = self.validate_parameters(config)
        
        return {
            "success": True,
            "config": config,
            "validation": validation,
            "template_used": template["description"],
            "storage_backend": storage_info.get("storageBackend")
        }
    
    def create_disk_smart(self, disk_size_gb, use_case="standard"):
        """智能创建磁盘，避免试错"""
        
        print(f"🎯 开始智能创建 {disk_size_gb}GB 磁盘...")
        
        # 生成优化配置
        config_result = self.generate_optimal_config(disk_size_gb, use_case)
        
        if not config_result["success"]:
            print(f"❌ 配置生成失败: {config_result['error']}")
            return False
        
        config = config_result["config"]
        validation = config_result["validation"]
        
        # 检查验证结果
        if not validation["valid"]:
            print("❌ 配置验证失败:")
            for error in validation["errors"]:
                print(f"   • {error}")
            return False
        
        print(f"✅ 配置验证通过")
        print(f"📋 使用模板: {config_result['template_used']}")
        print(f"🔧 存储后端: {config_result['storage_backend']}")
        
        # 显示配置
        print(f"📝 磁盘配置:")
        print(f"   名称: {config['name']}")
        print(f"   大小: {config['size']}GB")
        print(f"   页面大小: {config['pageSize']}")
        print(f"   压缩: {config['compression']}")
        print(f"   IOPS: {config['iops']}")
        print(f"   带宽: {config['bandwidth']} MB/s")
        print(f"   读缓存: {'开启' if config['readCache'] else '关闭'}")
        
        # 创建磁盘
        try:
            from volumes import Volumes
            self.volumes = Volumes(self.audit, self.host)
            
            print("🚀 正在创建磁盘...")
            result = self.volumes.createDisk_vstor(**config)
            
            # 解析结果
            if isinstance(result, dict) and 'data' in result:
                if result['data'] and len(result['data']) > 0:
                    disk_info = result['data'][0]
                    print("✅ 磁盘创建成功!")
                    print(f"📁 磁盘ID: {disk_info['id']}")
                    print(f"📝 磁盘名称: {disk_info['name']}")
                    return True
                else:
                    print("❌ 创建失败: 返回数据为空")
                    print(f"响应: {result}")
                    return False
            else:
                print("❌ 创建失败: 意外的响应格式")
                print(f"响应: {result}")
                return False
                
        except Exception as e:
            print(f"❌ 创建过程中发生错误: {e}")
            return False

# 使用示例
if __name__ == "__main__":
    creator = SmartDiskCreator("admin", "Admin@123", "https://172.118.57.100")
    success = creator.create_disk_smart(10, "standard")
    
    if success:
        print("\n🎉 智能磁盘创建完成!")
    else:
        print("\n💥 创建失败")