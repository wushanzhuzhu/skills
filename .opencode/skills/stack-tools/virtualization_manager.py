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
安超平台虚拟化管理工具
提供计算节点管理、服务状态监控、虚拟机管理和存储卷操作功能

使用方式:
    python virtualization_manager.py --env production --hypervisor-list
    python virtualization_manager.py --env production --vm-list
    python virtualization_manager.py --env production --service-status
    python virtualization_manager.py --env production --check-all
"""

import sys
import json
import time
import argparse
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加主项目路径
main_project_path = str(Path(__file__).resolve().parents[3])
sys.path.insert(0, main_project_path)

# 使用主项目的模块
from utils.audit import ArcherAudit
from utils.tools.sshcommand import ssh_execute_command
from env_manager import EnvironmentManager

class VirtualizationManager:
    """虚拟化管理器"""
    
    def __init__(self):
        # 使用主项目的环境配置文件
        env_config_path = str(Path(__file__).resolve().parents[3] / "environments.json")
        self.env_manager = EnvironmentManager(env_config_path)
        self.current_env = None
        self.ssh_key_path = "/root/myskills/wushanskills/id_rsa_cloud"
        self.ssh_user = "cloud"
        
    def get_controller_node(self, env_name: str) -> Dict:
        """获取控制节点信息"""
        # 这里应该从实际环境配置中获取，暂时使用模拟数据
        controller = {
            "hostname": "controller-01",
            "mgmt_ip": "172.118.57.100"
        }
        return controller
    
    def execute_ar_command(self, node_ip: str, command: str) -> Dict:
        """在控制节点执行ar命令"""
        try:
            result = ssh_execute_command(
                hostname=node_ip,
                port=22,
                username=self.ssh_user,
                key_path=self.ssh_key_path,
                command=command
            )
            
            return {
                "status": "success",
                "output": result.strip() if result else ""
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def parse_hypervisor_list(self, output: str) -> List[Dict]:
        """解析hypervisor列表输出"""
        hypervisors = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('+') and not line.startswith('| ID') and '|' in line:
                # 解析类似: | 1  | compute-01.localdomain| up      | enabled| 15    |
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 5:
                        try:
                            hypervisor = {
                                "id": int(parts[0]),
                                "host": parts[1],
                                "state": parts[2],
                                "status": parts[3],
                                "vms_count": int(parts[4]) if parts[4].replace('.', '').isdigit() else 0
                            }
                            hypervisors.append(hypervisor)
                        except (ValueError, IndexError):
                            continue
        
        return hypervisors
    
    def get_hypervisor_list(self, node_ip: str) -> Dict:
        """获取计算节点列表"""
        result = self.execute_ar_command(node_ip, "arcompute hypervisor-list")
        
        if result["status"] != "success":
            return result
        
        hypervisors = self.parse_hypervisor_list(result["output"])
        return {
            "status": "success",
            "hypervisors": hypervisors
        }
    
    def get_hypervisor_detail(self, node_ip: str, hypervisor_id: int) -> Dict:
        """获取指定计算节点详细信息"""
        result = self.execute_ar_command(node_ip, f"arcompute hypervisor-show {hypervisor_id}")
        
        if result["status"] != "success":
            return result
        
        output = result["output"]
        detail: Dict[str, Any] = {"id": hypervisor_id}
        
        # 解析详细信息
        lines = output.split('\n')
        for line in lines:
            if '| resource' in line.lower() or '| host' in line.lower():
                continue
            
            if '|' in line and len(line.split('|')) >= 3:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2:
                    key = parts[0].lower().replace(' ', '_')
                    value = parts[1]
                    
                    # 尝试转换数值
                    if value.isdigit():
                        detail[key] = int(value)
                    elif '.' in value and value.replace('.', '').isdigit():
                        detail[key] = float(value)
                    else:
                        detail[key] = str(value)
        
        return {
            "status": "success",
            "hypervisor_detail": detail
        }
    
    def parse_vm_list(self, output: str) -> List[Dict]:
        """解析虚拟机列表输出"""
        vms = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('+') and not line.startswith('| ID') and '|' in line:
                # 解析类似: | 12345678-... | web-01 | active | compute-01 |
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 4:
                    vm = {
                        "id": parts[0],
                        "name": parts[1],
                        "status": parts[2],
                        "host": parts[3] if len(parts) > 3 else "N/A"
                    }
                    vms.append(vm)
        
        return vms
    
    def get_vm_list(self, node_ip: str) -> Dict:
        """获取虚拟机列表"""
        result = self.execute_ar_command(node_ip, "arcompute list")
        
        if result["status"] != "success":
            return result
        
        vms = self.parse_vm_list(result["output"])
        return {
            "status": "success",
            "virtual_machines": vms
        }
    
    def get_vm_detail(self, node_ip: str, vm_id: str) -> Dict:
        """获取指定虚拟机详细信息"""
        result = self.execute_ar_command(node_ip, f"arcompute show {vm_id}")
        
        if result["status"] != "success":
            return result
        
        output = result["output"]
        detail: Dict[str, Any] = {"id": vm_id}
        
        # 解析详细信息
        lines = output.split('\n')
        for line in lines:
            if '|' in line and len(line.split('|')) >= 3:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2:
                    key = parts[0].lower().replace(' ', '_')
                    value = parts[1]
                    
                    # 特殊处理一些字段
                    if key == 'status':
                        detail['status'] = value
                    elif key == 'host':
                        detail['host'] = value
                    elif key == 'flavor':
                        detail['flavor'] = value
                    elif key == 'image':
                        detail['image'] = value
                    else:
                        detail[key] = value
        
        return {
            "status": "success",
            "vm_detail": detail
        }
    
    def parse_service_list(self, output: str) -> Dict:
        """解析服务列表输出"""
        services = {}
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('+') and '|' in line:
                # 解析类似: | nova-compute  | controller-01 | nova   | up     |
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 4:
                    service_name = parts[0]
                    host = parts[1]
                    service_type = parts[2]
                    status = parts[3]
                    
                    if service_type not in services:
                        services[service_type] = {}
                    services[service_type][host] = status
        
        return services
    
    def get_service_status(self, node_ip: str) -> Dict:
        """获取服务状态"""
        result = self.execute_ar_command(node_ip, "arcompute service-list")
        
        if result["status"] != "success":
            return result
        
        services = self.parse_service_list(result["output"])
        return {
            "status": "success",
            "services": services
        }
    
    def delete_volume(self, node_ip: str, volume_id: str) -> Dict:
        """删除指定存储卷"""
        result = self.execute_ar_command(node_ip, f"arblock delete {volume_id}")
        
        if result["status"] != "success":
            return result
        
        # 检查删除是否成功
        if "deleted" in result["output"].lower() or "删除" in result["output"]:
            return {
                "status": "success",
                "message": f"存储卷 {volume_id} 删除成功",
                "volume_id": volume_id
            }
        else:
            return {
                "status": "error",
                "error": result["output"],
                "volume_id": volume_id
            }
    
    def calculate_resource_usage(self, hypervisors: List[Dict], vms: List[Dict]) -> Dict:
        """计算虚拟化资源使用情况"""
        total_vcpus = sum(h.get('vcpus', 0) for h in hypervisors)
        total_memory = sum(h.get('memory_mb', 0) for h in hypervisors)
        total_local_gb = sum(h.get('local_gb', 0) for h in hypervisors)
        
        # 统计运行的虚拟机资源
        active_vms = [vm for vm in vms if vm.get('status') == 'active']
        used_vcpus = sum(vm.get('vcpus', 1) for vm in active_vms)
        used_memory = sum(vm.get('memory_mb', 2048) for vm in active_vms)
        
        return {
            "hypervisor_count": len(hypervisors),
            "total_vcpus": total_vcpus,
            "used_vcpus": used_vcpus,
            "vcpu_usage_percent": round((used_vcpus / total_vcpus) * 100, 2) if total_vcpus > 0 else 0,
            "total_memory_gb": total_memory // 1024,
            "used_memory_gb": used_memory // 1024,
            "memory_usage_percent": round((used_memory / total_memory) * 100, 2) if total_memory > 0 else 0,
            "total_storage_gb": total_local_gb,
            "vm_count": {
                "total": len(vms),
                "active": len(active_vms),
                "stopped": len([vm for vm in vms if vm.get('status') == 'shutoff'])
            }
        }
    
    def get_resource_overview(self, env_name: str) -> Dict:
        """获取虚拟化资源概览"""
        controller = self.get_controller_node(env_name)
        node_ip = controller["mgmt_ip"]
        
        overview = {
            "environment": env_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 获取hypervisor列表
        hv_result = self.get_hypervisor_list(node_ip)
        if hv_result["status"] == "success":
            overview["hypervisors"] = hv_result["hypervisors"]
        
        # 获取虚拟机列表
        vm_result = self.get_vm_list(node_ip)
        if vm_result["status"] == "success":
            overview["virtual_machines"] = vm_result["virtual_machines"]
        
        # 获取服务状态
        service_result = self.get_service_status(node_ip)
        if service_result["status"] == "success":
            overview["services"] = service_result["services"]
        
        # 计算资源使用情况
        if "hypervisors" in overview and "virtual_machines" in overview:
            hv_data = overview["hypervisors"]
            vm_data = overview["virtual_machines"]
            if isinstance(hv_data, list) and isinstance(vm_data, list):
                overview["resource_usage"] = self.calculate_resource_usage(hv_data, vm_data)
        
        return overview
    
    def format_output(self, data: Dict, format_type: str = "table"):
        """格式化输出结果"""
        if format_type == "json":
            logger.info(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            # 表格格式输出
            if "hypervisors" in data:
                hypervisors = data["hypervisors"]
                logger.info(f"\n🖥️ 计算节点列表")
                logger.info("=" * 80)
                logger.info(f"{'ID':<4} {'主机名':<25} {'状态':<8} {'启用状态':<10} {'虚拟机数':<8}")
                logger.info("-" * 80)
                for hv in hypervisors:
                    logger.info(f"{hv.get('id', 0):<4} {hv.get('host', 'N/A'):<25} "
                          f"{hv.get('state', 'N/A'):<8} {hv.get('status', 'N/A'):<10} "
                          f"{hv.get('vms_count', 0):<8}")
            
            if "virtual_machines" in data:
                vms = data["virtual_machines"]
                logger.info(f"\n💻 虚拟机列表 (显示前20个)")
                logger.info("=" * 80)
                logger.info(f"{'ID':<20} {'名称':<15} {'状态':<10} {'主机':<20}")
                logger.info("-" * 80)
                for vm in vms[:20]:  # 只显示前20个
                    logger.info(f"{vm.get('id', 'N/A')[:20]:<20} {vm.get('name', 'N/A'):<15} "
                          f"{vm.get('status', 'N/A'):<10} {vm.get('host', 'N/A'):<20}")
                if len(vms) > 20:
                    logger.info(f"... 还有 {len(vms) - 20} 个虚拟机")
            
            if "services" in data:
                services = data["services"]
                logger.info(f"\n🔄 服务状态")
                logger.info("=" * 60)
                for service_type, hosts in services.items():
                    logger.info(f"\n{service_type}:")
                    for host, status in hosts.items():
                        status_icon = "✅" if status.lower() == "up" else "❌"
                        logger.info(f"  {host}: {status} {status_icon}")
            
            if "resource_usage" in data:
                usage = data["resource_usage"]
                logger.info(f"\n📊 资源使用情况")
                logger.info("=" * 60)
                logger.info(f"计算节点数: {usage.get('hypervisor_count', 0)}")
                logger.info(f"CPU使用: {usage.get('used_vcpus', 0)}/{usage.get('total_vcpus', 0)} "
                      f"({usage.get('vcpu_usage_percent', 0)}%)")
                logger.info(f"内存使用: {usage.get('used_memory_gb', 0)}GB/{usage.get('total_memory_gb', 0)}GB "
                      f"({usage.get('memory_usage_percent', 0)}%)")
                logger.info(f"虚拟机数: 总计{usage.get('vm_count', {}).get('total', 0)} | "
                      f"运行{usage.get('vm_count', {}).get('active', 0)} | "
                      f"停止{usage.get('vm_count', {}).get('stopped', 0)}")
    
    def main(self):
        parser = argparse.ArgumentParser(description="安超平台虚拟化管理工具")
        parser.add_argument("--env", required=True, help="环境名称")
        parser.add_argument("--hypervisor-list", action="store_true", help="查看计算节点列表")
        parser.add_argument("--hypervisor-show", type=int, help="查看指定计算节点详情")
        parser.add_argument("--vm-list", action="store_true", help="查看虚拟机列表")
        parser.add_argument("--vm-show", help="查看指定虚拟机详情")
        parser.add_argument("--service-status", action="store_true", help="查看服务状态")
        parser.add_argument("--volume-delete", help="删除指定存储卷")
        parser.add_argument("--check-all", action="store_true", help="执行完整资源检查")
        parser.add_argument("--resource-overview", action="store_true", help="获取资源概览")
        parser.add_argument("--format", choices=["json", "table"], default="table", help="输出格式")
        
        args = parser.parse_args()
        
        controller = self.get_controller_node(args.env)
        node_ip = controller["mgmt_ip"]
        
        result = None
        
        # 执行相应操作
        if args.check_all or args.resource_overview:
            result = self.get_resource_overview(args.env)
        elif args.hypervisor_list:
            result = self.get_hypervisor_list(node_ip)
        elif args.hypervisor_show:
            result = self.get_hypervisor_detail(node_ip, args.hypervisor_show)
        elif args.vm_list:
            result = self.get_vm_list(node_ip)
        elif args.vm_show:
            result = self.get_vm_detail(node_ip, args.vm_show)
        elif args.service_status:
            result = self.get_service_status(node_ip)
        elif args.volume_delete:
            result = self.delete_volume(node_ip, args.volume_delete)
        
        if result:
            self.format_output(result, args.format)
            return 0
        else:
            logger.error("❌ 请指定要执行的操作")
            return 1

if __name__ == "__main__":
    sys.exit(VirtualizationManager().main())