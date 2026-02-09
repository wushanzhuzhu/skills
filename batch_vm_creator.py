#!/usr/bin/env python3
"""
批量VM创建脚本
支持环境选择、模板配置、批量创建和结果追踪
"""

from vm_manager import VMManager
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

import time

def create_vm_batch_with_env_selection():
    """带环境选择的批量VM创建"""
    
    logger.info("🚀 智能批量VM创建器")
    logger.info("=" * 60)
    
    manager = VMManager()
    
    # 环境选择
    logger.info("\n🌐 选择目标环境:")
    env_id = manager.select_environment_interactive()
    
    if not env_id:
        logger.error("❌ 未选择环境，操作取消")
        return False
    
    # 环境验证
    if not manager.check_environment(env_id):
        logger.error("❌ 环境连接失败，无法执行批量创建")
        return False
    
    # 资源发现
    if not manager.discover_resources():
        logger.error("❌ 资源发现失败")
        return False
    
    # 模板选择
    logger.info("\n🎯 可用模板:")
    manager.templates.display_templates_table()
    
    template_options = list(manager.templates.templates.keys())
    logger.info(f"\n请选择模板: {', '.join(template_options)}")
    
    while True:
        template_choice = input("模板名称: ").strip()
        if template_choice in template_options:
            break
        logger.error("❌ 无效模板，请重新输入")
    
    # 数量输入
    while True:
        try:
            vm_count = int(input("创建数量 (1-10): ").strip())
            if 1 <= vm_count <= 10:
                break
            logger.error("❌ 数量必须在1-10之间")
        except ValueError:
            logger.error("❌ 请输入有效数字")
    
    # 高级配置（可选）
    logger.info("\n⚙️ 高级配置 (可选，直接回车跳过):")
    
    custom_overrides = {}
    
    # CPU自定义
    cpu_input = input("CPU核心数 (回车使用模板默认): ").strip()
    if cpu_input:
        try:
            custom_overrides["cpu"] = int(cpu_input)
        except ValueError:
            logger.info("⚠️ CPU输入无效，使用默认值")
    
    # 内存自定义
    memory_input = input("内存大小GB (回车使用模板默认): ").strip()
    if memory_input:
        try:
            custom_overrides["memory"] = int(memory_input)
        except ValueError:
            logger.info("⚠️ 内存输入无效，使用默认值")
    
    # 磁盘大小自定义
    size_input = input("磁盘大小GB (回车使用模板默认): ").strip()
    if size_input:
        try:
            custom_overrides["size"] = int(size_input)
        except ValueError:
            logger.info("⚠️ 磁盘大小输入无效，使用默认值")
    
    # 高可用设置
    ha_input = input("启用高可用 (y/n, 回车使用模板默认): ").strip().lower()
    if ha_input in ['y', 'yes', 'n', 'no']:
        custom_overrides["haEnable"] = ha_input in ['y', 'yes']
    
    # 创建后启动设置
    active_input = input("创建后启动VM (y/n, 默认n): ").strip().lower()
    if active_input in ['y', 'yes']:
        custom_overrides["vmActive"] = True
    elif active_input in ['n', 'no', '']:
        custom_overrides["vmActive"] = False
    
    # 确认创建
    logger.info(f"\n📋 创建配置确认:")
    logger.info(f"   环境: {manager.connection_info['name']}")
    logger.info(f"   模板: {template_choice}")
    logger.info(f"   数量: {vm_count}")
    if custom_overrides:
        logger.info(f"   自定义配置: {custom_overrides}")
    
    confirm = input("\n确认创建? (y/n): ").strip().lower()
    if confirm != 'y':
        logger.error("❌ 操作已取消")
        return False
    
    # 执行批量创建
    logger.info(f"\n🔥 开始批量创建 {vm_count} 个VM...")
    results = manager.create_batch_vms(
        template_choice, 
        vm_count, 
        "general", 
        custom_overrides
    )
    
    return results

def create_vm_batch_quick(template_name: str, vm_count: int, 
                          env_hint: str = None, custom_overrides: dict = None):
    """快速批量创建VM"""
    
    manager = VMManager()
    
    # 自动环境选择
    if env_hint:
        env_id = manager.auto_select_environment(env_hint)
    else:
        env_id = manager.select_environment_interactive()
    
    if not env_id or not manager.check_environment(env_id):
        return False
    
    if not manager.discover_resources():
        return False
    
    logger.info(f"\n🚀 在环境 '{manager.connection_info['name']}' 中创建 {vm_count} 个VM...")
    
    results = manager.create_batch_vms(
        template_name,
        vm_count,
        "general",
        custom_overrides
    )
    
    return results

def create_scenario_vms():
    """场景化VM创建"""
    
    logger.info("🎯 场景化VM创建")
    logger.info("=" * 60)
    
    scenarios = {
        "1": {
            "name": "Web服务器集群",
            "description": "创建3个Web服务器VM",
            "template": "web_server",
            "count": 3,
            "overrides": {"vmActive": True}
        },
        "2": {
            "name": "数据库集群",
            "description": "创建2个数据库VM",
            "template": "database",
            "count": 2,
            "overrides": {"vmActive": True, "haEnable": True}
        },
        "3": {
            "name": "开发环境",
            "description": "创建5个开发测试VM",
            "template": "development",
            "count": 5,
            "overrides": {"vmActive": True, "vncPwd": "dev123"}
        },
        "4": {
            "name": "容器编排集群",
            "description": "创建3个Kubernetes节点",
            "template": "container_host",
            "count": 3,
            "overrides": {"vmActive": True, "haEnable": True}
        }
    }
    
    logger.info("📋 预定义场景:")
    for key, scenario in scenarios.items():
        logger.info(f"   {key}. {scenario['name']}")
        logger.info(f"      {scenario['description']}")
        logger.info(f"      模板: {scenario['template']}, 数量: {scenario['count']}")
        logger.info()
    
    choice = input("选择场景 (1-4): ").strip()
    
    if choice in scenarios:
        scenario = scenarios[choice]
        manager = VMManager()
        
        # 环境选择
        env_id = manager.select_environment_interactive()
        if not env_id or not manager.check_environment(env_id):
            return False
        
        if not manager.discover_resources():
            return False
        
        logger.info(f"\n🚀 执行场景: {scenario['name']}")
        
        results = manager.create_batch_vms(
            scenario["template"],
            scenario["count"],
            "general",
            scenario["overrides"]
        )
        
        return results
    else:
        logger.error("❌ 无效场景选择")
        return False

from typing import Dict, List

def create_vm_from_config_file(config_file: str):
    """从配置文件创建VM"""
    
    import json
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        logger.info(f"📁 从配置文件创建VM: {config_file}")
        logger.info("=" * 60)
        
        manager = VMManager()
        
        # 环境选择
        if "environment" in config:
            env_id = manager.auto_select_environment(config["environment"])
        else:
            env_id = manager.select_environment_interactive()
        
        if not env_id or not manager.check_environment(env_id):
            return False
        
        if not manager.discover_resources():
            return False
        
        # 从配置文件创建
        vm_configs = config.get("vms", [])
        if not vm_configs:
            logger.error("❌ 配置文件中没有VM配置")
            return False
        
        results = {
            "total": len(vm_configs),
            "success": [],
            "failed": [],
            "start_time": time.time()
        }
        
        logger.info(f"\n🔥 根据配置文件创建 {len(vm_configs)} 个VM...")
        
        for i, vm_config in enumerate(vm_configs, 1):
            logger.info(f"\n📁 创建第 {i}/{len(vm_configs)} 个VM: {vm_config.get('name', f'vm-{i}')}")
            
            try:
                # 准备完整配置
                full_config = manager.prepare_vm_config(
                    vm_config.get("template", "basic"),
                    vm_config.get("use_case", "general"),
                    vm_config.get("overrides", {})
                )
                full_config.update(vm_config.get("overrides", {}))
                
                # 验证配置
                validation = manager.validate_vm_config(full_config)
                if not validation["valid"]:
                    error_msg = f"配置验证失败: {', '.join(validation['errors'])}"
                    results["failed"].append({
                        "vm_num": i,
                        "vm_name": full_config.get("name", f"vm-{i}"),
                        "error": error_msg
                    })
                    logger.error(f"❌ 第 {i} 个VM配置验证失败")
                    continue
                
                # 创建VM
                result = manager.create_single_vm(full_config)
                
                if result["success"]:
                    results["success"].append({
                        "vm_num": i,
                        "vm_id": result["vm_id"],
                        "vm_name": result["vm_name"]
                    })
                    logger.info(f"✅ 第 {i} 个VM创建成功")
                else:
                    results["failed"].append({
                        "vm_num": i,
                        "vm_name": full_config.get("name", f"vm-{i}"),
                        "error": result["error"]
                    })
                    logger.error(f"❌ 第 {i} 个VM创建失败: {result['error']}")
                
                time.sleep(2)  # 避免API频率限制
                    
            except Exception as e:
                results["failed"].append({
                    "vm_num": i,
                    "vm_name": vm_config.get("name", f"vm-{i}"),
                    "error": str(e)
                })
                logger.error(f"❌ 第 {i} 个VM创建出错: {e}")
        
        results["end_time"] = time.time()
        results["duration"] = results["end_time"] - results["start_time"]
        
        # 生成报告
        return manager.generate_batch_report(results)
        
    except FileNotFoundError:
        logger.error(f"❌ 配置文件不存在: {config_file}")
        return False
    except json.JSONDecodeError:
        logger.error(f"❌ 配置文件格式错误: {config_file}")
        return False
    except Exception as e:
        logger.error(f"❌ 处理配置文件失败: {e}")
        return False

def main():
    """命令行界面"""
    import sys
    
    if len(sys.argv) < 2:
        logger.info("🔧 批量VM创建器")
        logger.info("python batch_vm_creator.py [命令] [参数]")
        logger.info("\n命令:")
        logger.info("  interactive                    - 交互式创建")
        logger.info("  quick <template> <count> [env] - 快速创建")
        logger.info("  scenario                      - 场景化创建")
        logger.info("  config <config_file>          - 从配置文件创建")
        logger.info("  example-config                 - 生成示例配置文件")
        return
    
    command = sys.argv[1]
    
    if command == "interactive":
        create_vm_batch_with_env_selection()
    
    elif command == "quick":
        if len(sys.argv) < 4:
            logger.error("❌ 请提供模板名称和VM数量")
            return
        
        template = sys.argv[2]
        count = int(sys.argv[3])
        env_hint = sys.argv[4] if len(sys.argv) > 4 else None
        
        create_vm_batch_quick(template, count, env_hint)
    
    elif command == "scenario":
        create_scenario_vms()
    
    elif command == "config":
        if len(sys.argv) < 3:
            logger.error("❌ 请提供配置文件路径")
            return
        
        config_file = sys.argv[2]
        create_vm_from_config_file(config_file)
    
    elif command == "example-config":
        generate_example_config()
    
    else:
        logger.error(f"❌ 未知命令: {command}")

def generate_example_config():
    """生成示例配置文件"""
    
    example_config = {
        "environment": "production",
        "description": "Web应用集群配置示例",
        "vms": [
            {
                "name": "web-frontend-01",
                "template": "web_server",
                "use_case": "web",
                "overrides": {
                    "cpu": 4,
                    "memory": 8,
                    "size": 100,
                    "vmActive": True,
                    "haEnable": True
                }
            },
            {
                "name": "web-backend-01", 
                "template": "web_server",
                "use_case": "web",
                "overrides": {
                    "cpu": 6,
                    "memory": 12,
                    "size": 150,
                    "vmActive": True,
                    "haEnable": True
                }
            },
            {
                "name": "database-01",
                "template": "database",
                "use_case": "database", 
                "overrides": {
                    "cpu": 8,
                    "memory": 16,
                    "size": 200,
                    "vmActive": True,
                    "haEnable": True,
                    "bigPageEnable": True
                }
            }
        ]
    }
    
    import json
    filename = "vm_batch_example.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(example_config, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ 示例配置文件已生成: {filename}")

if __name__ == "__main__":
    main()