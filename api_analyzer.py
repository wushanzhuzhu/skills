#!/usr/bin/env python3
"""
API分析工具 - 精准分析类和方法签名
避免试错，提前了解API要求
"""

import inspect
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_api_signatures():
    """分析关键API的方法签名和参数要求"""
    
    print("🔍 API签名分析报告")
    print("=" * 50)
    
    # 1. 分析ArcherAudit
    try:
        from utils.audit import ArcherAudit
        audit_sig = inspect.signature(ArcherAudit.__init__)
        print(f"📝 ArcherAudit.__init__{audit_sig}")
        
        # 查看方法
        methods = [method for method in dir(ArcherAudit) if not method.startswith('_')]
        print(f"   可用方法: {methods}")
        
        # 分析setSession方法
        if hasattr(ArcherAudit, 'setSession'):
            session_sig = inspect.signature(ArcherAudit.setSession)
            print(f"   setSession{session_sig}")
        
    except Exception as e:
        print(f"❌ ArcherAudit分析失败: {e}")
    
    print("\n" + "-" * 50)
    
    # 2. 分析Hosts
    try:
        from Hosts import Hosts
        hosts_sig = inspect.signature(Hosts.__init__)
        print(f"🏠 Hosts.__init__{hosts_sig}")
        
        # 查看方法
        methods = [method for method in dir(Hosts) if not method.startswith('_')]
        print(f"   可用方法: {methods}")
        
        # 分析关键方法
        if hasattr(Hosts, 'getStorsbyDiskType'):
            stors_sig = inspect.signature(Hosts.getStorsbyDiskType)
            print(f"   getStorsbyDiskType{stors_sig}")
            
    except Exception as e:
        print(f"❌ Hosts分析失败: {e}")
    
    print("\n" + "-" * 50)
    
    # 3. 分析Volumes
    try:
        from volumes import Volumes
        volumes_sig = inspect.signature(Volumes.__init__)
        print(f"💾 Volumes.__init__{volumes_sig}")
        
        # 查看方法
        methods = [method for method in dir(Volumes) if not method.startswith('_')]
        print(f"   可用方法: {methods}")
        
        # 分析createDisk_vstor方法
        if hasattr(Volumes, 'createDisk_vstor'):
            create_sig = inspect.signature(Volumes.createDisk_vstor)
            print(f"   createDisk_vstor{create_sig}")
            
    except Exception as e:
        print(f"❌ Volumes分析失败: {e}")

def analyze_parameter_constraints():
    """分析参数约束和有效值"""
    
    print("\n🎯 参数约束分析")
    print("=" * 50)
    
    # 从代码中提取参数说明
    constraints = {
        "pageSize": {
            "options": ["4K", "8K", "16K", "32K"],  # 修正：代码显示4K/8K等，不是4KB
            "source": "volumes.py createDisk_vstor docstring"
        },
        "compression": {
            "options": ["Disabled", "LZ4", "Gzip_opt", "Gzip_high"],
            "source": "volumes.py createDisk_vstor docstring"
        },
        "iops": {
            "range": "75-250000",
            "source": "volumes.py createDisk_vstor docstring"
        },
        "bandwidth": {
            "range": "1-1000 MB/s",
            "source": "volumes.py createDisk_vstor docstring"
        }
    }
    
    for param, info in constraints.items():
        print(f"📋 {param}:")
        if "options" in info:
            print(f"   选项: {info['options']}")
        if "range" in info:
            print(f"   范围: {info['range']}")
        print(f"   来源: {info['source']}")

def create_optimized_config():
    """基于分析创建优化配置"""
    
    print("\n⚙️ 优化配置建议")
    print("=" * 50)
    
    # 基于存储性能限制的建议
    config_templates = {
        "test": {
            "description": "测试环境配置",
            "pageSize": "4K",
            "compression": "Disabled",
            "iops": 75,  # 最低值
            "bandwidth": 1,  # 最低值
            "readCache": False
        },
        "standard": {
            "description": "标准配置",
            "pageSize": "4K", 
            "compression": "LZ4",
            "iops": 400,  # 基于存储实际性能
            "bandwidth": 40,  # 基于存储实际性能
            "readCache": True
        }
    }
    
    for name, config in config_templates.items():
        print(f"🎯 {name}: {config['description']}")
        for key, value in config.items():
            if key != "description":
                print(f"   {key}: {value}")
        print()

if __name__ == "__main__":
    analyze_api_signatures()
    analyze_parameter_constraints()
    create_optimized_config()