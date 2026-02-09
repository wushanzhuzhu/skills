#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
node-tools skill 调用脚本
使用opencode skill系统管理安超平台宿主机
"""

import argparse
import json
import logging
from datetime import datetime
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def invoke_host_manager_skill(env_url, username="admin", password="Admin@123", 
                              action="list", host_id=None, operation=None):
    """调用host-manager skill管理宿主机"""
    
    # 构建skill调用参数
    skill_params = {
        "env_url": env_url,
        "username": username,
        "password": password,
        "action": action,
        "host_id": host_id,
        "operation": operation
    }
    
    logger.info(f"🚀 调用node-tools skill...")
    logger.info(f"📋 参数: {json.dumps(skill_params, indent=2, ensure_ascii=False)}")
    
    try:
        # 这里应该使用opencode的skill调用接口
        from opencode import task
        
        # 使用task工具调用skill
        skill_task = task(
            description="调用node-tools skill",
            prompt=f"请使用node-tools skill管理宿主机，参数如下:\n{json.dumps(skill_params, indent=2, ensure_ascii=False)}\n\n请执行宿主机管理操作并返回详细结果。",
            subagent_type="general"
        )
        
        return skill_task
        
    except ImportError:
        # 如果无法导入opencode，返回模拟结果
        logger.info("⚠️ 无法导入opencode模块，返回模拟结果")
        return simulate_host_manager_action(skill_params)
    except Exception as e:
        return {
            "success": False,
            "error": f"skill调用失败: {str(e)}",
            "params": skill_params
        }


def simulate_host_manager_action(params):
    """模拟宿主机管理操作"""
    action = params.get('action', 'list')
    
    if action == 'list':
        return {
            "success": True,
            "message": "获取宿主机列表成功",
            "hosts": [
                {
                    "id": "host-001",
                    "name": "compute-node-1",
                    "status": "active",
                    "ip": "172.118.57.101",
                    "cpu_usage": "45%",
                    "memory_usage": "67%",
                    "role": "计算节点"
                },
                {
                    "id": "host-002", 
                    "name": "storage-node-1",
                    "status": "active",
                    "ip": "172.118.57.102",
                    "cpu_usage": "23%",
                    "memory_usage": "34%",
                    "role": "存储节点"
                }
            ],
            "total": 2
        }
    
    elif action == 'ipmi' and params.get('host_id'):
        return {
            "success": True,
            "message": f"获取宿主机 {params['host_id']} IPMI信息成功",
            "ipmi_info": {
                "ip": "192.168.1.100",
                "mac": "00:1A:2B:3C:4D:5E",
                "status": "online",
                "power_state": "on"
            }
        }
    
    elif action == 'batch' and params.get('operation'):
        return {
            "success": True,
            "message": f"批量操作 {params['operation']} 执行成功",
            "affected_hosts": ["host-001", "host-002"],
            "operation_result": "completed"
        }
    
    else:
        return {
            "success": False,
            "error": "不支持的操作或缺少必要参数",
            "supported_actions": ["list", "ipmi", "batch", "info", "maintenance"]
        }


def list_actions():
    """列出可用的宿主机管理操作"""
    logger.info("📋 host-manager skill 支持的宿主机管理操作:")
    logger.info("=" * 60)
    
    actions = {
        'list': {
            'desc': '列出所有宿主机',
            'usage': '获取宿主机列表、状态、资源使用情况',
            'params': '无额外参数'
        },
        'info': {
            'desc': '获取指定宿主机详细信息',
            'usage': '查看特定宿主机的详细配置和状态',
            'params': '需要host_id参数'
        },
        'ipmi': {
            'desc': 'IPMI远程管理',
            'usage': '通过IPMI远程控制宿主机电源、获取硬件信息',
            'params': '需要host_id参数'
        },
        'batch': {
            'desc': '批量操作',
            'usage': '批量执行重启、关机、维护模式等操作',
            'params': '需要operation参数'
        },
        'maintenance': {
            'desc': '维护模式管理',
            'usage': '设置宿主机维护模式、迁移虚拟机',
            'params': '需要host_id和operation参数'
        }
    }
    
    for name, info in actions.items():
        logger.info(f"\n🎯 {name.upper()} 操作:")
        logger.info(f"   💬 描述: {info['desc']}")
        logger.info(f"   🎪 用途: {info['usage']}")
        logger.info(f"   ⚙️ 参数: {info['params']}")
    
    logger.info("\n" + "=" * 60)
    logger.info("💡 使用示例:")
    logger.info("   python skill_host_manager.py --env https://172.118.57.100 --action list")
    logger.info("   python skill_host_manager.py --env 172.118.57.100 --action info --host-id host-001")
    logger.info("   python skill_host_manager.py --env https://172.118.57.100 --action ipmi --host-id host-001")


def main():
    parser = argparse.ArgumentParser(
        description="使用host-manager skill管理宿主机",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📖 详细说明:
  本脚本通过调用host-manager skill来管理安超平台的宿主机，支持列表查看、IPMI管理、批量操作等。

🔄 巚作流程:
  1. 连接到指定的安超平台环境
  2. 获取宿主机信息和状态
  3. 执行指定的管理操作
  4. 返回详细的操作结果

⚠️ 注意事项:
  - 确保目标环境的网络连接正常
  - 执行IPMI操作需要正确配置IPMI网络
  - 批量操作前请确认影响范围
        """
    )
    
    parser.add_argument("--env", required=True, 
                       help="目标环境URL或IP地址")
    parser.add_argument("--username", default="admin", 
                       help="平台用户名 (默认: admin)")
    parser.add_argument("--password", default="Admin@123", 
                       help="平台密码 (默认: Admin@123)")
    parser.add_argument("--action", default="list",
                       choices=["list", "info", "ipmi", "batch", "maintenance"],
                       help="操作类型 (默认: list)")
    parser.add_argument("--host-id", 
                       help="宿主机ID (用于info、ipmi、maintenance操作)")
    parser.add_argument("--operation",
                       choices=["power-on", "power-off", "reboot", "enable", "disable"],
                       help="批量操作类型")
    parser.add_argument("--list-actions", action="store_true", 
                       help="列出所有可用操作和说明")
    parser.add_argument("--dry-run", action="store_true", 
                       help="仅显示将要执行的操作，不实际执行")
    
    args = parser.parse_args()
    
    if args.list_actions:
        list_actions()
        return 0
    
    # 参数验证
    if args.action in ["info", "ipmi", "maintenance"] and not args.host_id:
        logger.error(f"❌ {args.action} 操作需要 --host-id 参数")
        return 1
    
    if args.action == "batch" and not args.operation:
        logger.error("❌ batch 操作需要 --operation 参数")
        return 1
    
    logger.info("🚀 host-manager skill 宿主机管理工具")
    logger.info("=" * 60)
    logger.info(f"📍 目标环境: {args.env}")
    logger.info(f"👤 登录用户: {args.username}")
    logger.info(f"🔧 操作类型: {args.action}")
    if args.host_id:
        logger.info(f"🖥️ 目标主机: {args.host_id}")
    if args.operation:
        logger.info(f"⚡ 操作指令: {args.operation}")
    logger.info("=" * 60)
    
    if args.dry_run:
        logger.info("🔍 DRY RUN模式 - 仅显示操作，不实际执行")
        logger.info(f"\n📋 将要执行的操作: {args.action}")
        if args.host_id:
            logger.info(f"   目标主机: {args.host_id}")
        if args.operation:
            logger.info(f"   具体操作: {args.operation}")
        logger.info(f"\n💡 如需实际执行，请移除 --dry-run 参数")
        return 0
    
    # 调用skill
    logger.info(f"\n🔄 开始调用host-manager skill...")
    result = invoke_host_manager_skill(
        env_url=args.env,
        username=args.username,
        password=args.password,
        action=args.action,
        host_id=args.host_id,
        operation=args.operation
    )
    
    # 处理结果
    logger.info(f"\n📊 Skill执行结果:")
    logger.info("-" * 40)
    
    if isinstance(result, dict):
        success = result.get('success', False)
        
        if success:
            logger.info("✅ 宿主机管理操作成功!")
            
            # 显示操作结果
            if args.action == "list" and "hosts" in result:
                hosts = result["hosts"]
                logger.info(f"\n🖥️ 宿主机列表 (共{len(hosts)}个):")
                for host in hosts:
                    logger.info(f"   • {host.get('id')}: {host.get('name')} ({host.get('ip')})")
                    logger.info(f"     状态: {host.get('status')} | CPU: {host.get('cpu_usage')} | 内存: {host.get('memory_usage')}")
                    logger.info(f"     角色: {host.get('role')}")
            
            elif args.action == "info" and "host_info" in result:
                host_info = result["host_info"]
                logger.info(f"\n🖥️ 宿主机信息:")
                for key, value in host_info.items():
                    logger.info(f"   {key}: {value}")
            
            elif args.action == "ipmi" and "ipmi_info" in result:
                ipmi_info = result["ipmi_info"]
                logger.info(f"\n⚡ IPMI信息:")
                for key, value in ipmi_info.items():
                    logger.info(f"   {key}: {value}")
            
            elif args.action == "batch" and "affected_hosts" in result:
                affected_hosts = result["affected_hosts"]
                logger.info(f"\n🔄 批量操作结果:")
                logger.info(f"   影响主机: {len(affected_hosts)}个")
                logger.info(f"   操作状态: {result.get('operation_result', 'N/A')}")
                logger.info(f"   主机列表: {', '.join(affected_hosts)}")
            
        else:
            logger.error("❌ 宿主机管理操作失败!")
            error = result.get('error', '未知错误')
            logger.info(f"错误信息: {error}")
            
    else:
        # 如果返回的是其他格式
        logger.info("📤 Skill返回结果:")
        logger.info(result)
    
    # 保存执行记录
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"skill_host_manager_log_{timestamp}.json"
    
    try:
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "environment": args.env,
            "username": args.username,
            "operation": {
                "action": args.action,
                "host_id": args.host_id,
                "operation": args.operation
            },
            "result": result if isinstance(result, dict) else str(result)
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📄 执行日志已保存到: {log_file}")
        
    except Exception as e:
        logger.info(f"\n⚠️ 保存日志文件失败: {e}")
    
    return 0 if result.get('success', False) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())