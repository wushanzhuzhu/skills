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
安超平台宿主机管理工具
提供系统信息查看、IPMI管理、节点清单和批量操作功能

使用方式:
    python host_manager.py --env production --sysinfo
    python host_manager.py --env production --ipmi-list
    python host_manager.py --env production --power-status
    python host_manager.py --env production --power-on --nodes node1,node2
"""

import sys
import json
import time
import argparse
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

class HostManager:
    """宿主机管理器"""
    
    def __init__(self):
        # 使用主项目的环境配置文件
        env_config_path = str(Path(__file__).resolve().parents[3] / "environments.json")
        self.env_manager = EnvironmentManager(env_config_path)
        self.current_env = None
        self.ssh_key_path = "/root/myskills/SKILLS/id_rsa_cloud"
        self.ssh_user = "cloud"
        
    def parse_hosts_file(self, hosts_content: str) -> List[Dict]:
        """解析hosts文件内容"""
        nodes = []
        for line in hosts_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # 解析IP和主机名
            if ' ansible_host=' in line:
                parts = line.split()
                node_info = {}
                
                for part in parts:
                    if 'ansible_host=' in part:
                        node_info['mgmt_ip'] = part.split('=')[1]
                    elif part.startswith('node'):
                        node_info['hostname'] = part
                    elif 'ipmi_ip=' in part:
                        node_info['ipmi_ip'] = part.split('=')[1]
                    elif 'ipmi_username=' in part:
                        node_info['ipmi_username'] = part.split('=')[1]
                    elif 'ipmi_password=' in part:
                        node_info['ipmi_password'] = part.split('=')[1]
                
                if 'hostname' in node_info and 'mgmt_ip' in node_info:
                    nodes.append(node_info)
        
        return nodes
    
    def get_nodes_from_hosts(self, env_name: str) -> List[Dict]:
        """从hosts文件获取节点信息"""
        try:
            # 使用第一个controller节点来获取hosts文件内容
            env = self.env_manager.get_environment(env_name)
            if not env:
                return []
            
            # 这里应该从实际的hosts文件读取，暂时使用模拟数据
            hosts_file = "/usr/local/cloudos-lcm_libs/CloudOs/inventory/hosts"
            
            # 执行SSH命令读取hosts文件
            result = ssh_execute_command(
                hostname=env['url'].replace('https://', '').replace('http://', ''),
                port=22,
                username=self.ssh_user,
                key_path=self.ssh_key_path,
                command=f"cat {hosts_file}"
            )
            
            if result:
                return self.parse_hosts_file(result)
            
        except Exception as e:
            logger.error(f"❌ 获取节点信息失败: {e}")
        
        return []
    
    def get_system_info(self, node_ip: str) -> Dict:
        """获取系统信息"""
        try:
            result = ssh_execute_command(
                hostname=node_ip,
                port=22,
                username=self.ssh_user,
                key_path=self.ssh_key_path,
                command="cat /etc/system-info"
            )
            
            return {
                "status": "success",
                "system_info": result.strip() if result else "无法获取系统信息"
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e)
            }
    
    def get_ipmi_ip(self, node_ip: str) -> str:
        """获取节点IPMI IP地址"""
        try:
            result = ssh_execute_command(
                hostname=node_ip,
                port=22,
                username=self.ssh_user,
                key_path=self.ssh_key_path,
                command="ipmitool -I open lan print 1 | awk '/IP Address[[:space:]]*:[[:space:]]*/ {print $NF}'"
            )
            
            return result.strip() if result else ""
        except Exception as e:
            logger.error(f"❌ 获取IPMI IP失败: {e}")
            return ""
    
    def check_power_status(self, ipmi_ip: str) -> Dict:
        """检查IPMI电源状态"""
        try:
            result = subprocess.run([
                "ipmitool", 
                "-H", ipmi_ip,
                "-I", "lanplus", 
                "-U", "root",
                "-P", "Admin@123",
                "chassis", "status"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout
                if "System Power" in output and "on" in output.lower():
                    return {"status": "on"}
                else:
                    return {"status": "off"}
            else:
                return {"status": "error", "error": result.stderr}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def power_control(self, ipmi_ip: str, action: str) -> Dict:
        """电源控制（on/off/status）"""
        try:
            result = subprocess.run([
                "ipmitool",
                "-H", ipmi_ip,
                "-I", "lanplus",
                "-U", "root", 
                "-P", "Admin@123",
                "power", action
            ], capture_output=True, text=True, timeout=30)
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout if result.returncode == 0 else result.stderr
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def execute_on_node(self, node: Dict, operation: str) -> Dict:
        """在单个节点执行操作"""
        node_ip = node.get('mgmt_ip', '')
        hostname = node.get('hostname', 'unknown')
        
        result = {
            "hostname": hostname,
            "mgmt_ip": node_ip,
            "operation": operation
        }
        
        if operation == "system_info":
            result.update(self.get_system_info(node_ip))
        elif operation == "ipmi_ip":
            ipmi_ip = self.get_ipmi_ip(node_ip)
            result["ipmi_ip"] = ipmi_ip
            result["status"] = "success" if ipmi_ip else "error"
        elif operation == "power_status":
            ipmi_ip = node.get('ipmi_ip', '') or self.get_ipmi_ip(node_ip)
            if ipmi_ip:
                result.update(self.check_power_status(ipmi_ip))
                result["ipmi_ip"] = ipmi_ip
            else:
                result["status"] = "error"
                result["error"] = "无法获取IPMI IP"
        else:
            result["status"] = "error"
            result["error"] = f"不支持的操作: {operation}"
        
        return result
    
    def execute_parallel(self, nodes: List[Dict], operation: str) -> List[Dict]:
        """并行执行操作"""
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_node = {
                executor.submit(self.execute_on_node, node, operation): node 
                for node in nodes
            }
            
            for future in as_completed(future_to_node):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    node = future_to_node[future]
                    results.append({
                        "hostname": node.get('hostname', 'unknown'),
                        "status": "error",
                        "error": str(e),
                        "operation": operation
                    })
        
        return results
    
    def show_inventory(self, env_name: str) -> Dict:
        """显示完整的节点清单"""
        nodes = self.get_nodes_from_hosts(env_name)
        
        # 获取所有节点的详细信息
        results = self.execute_parallel(nodes, "system_info")
        
        # 合并节点信息和系统信息
        inventory = []
        for i, node in enumerate(nodes):
            node_detail = node.copy()
            if i < len(results):
                node_detail.update(results[i])
            inventory.append(node_detail)
        
        return {
            "environment": env_name,
            "total_nodes": len(inventory),
            "nodes": inventory
        }
    
    def main(self):
        parser = argparse.ArgumentParser(description="安超平台宿主机管理工具")
        parser.add_argument("--env", required=True, help="环境名称")
        parser.add_argument("--sysinfo", action="store_true", help="查看系统信息")
        parser.add_argument("--ipmi-list", action="store_true", help="获取IPMI IP列表")
        parser.add_argument("--power-status", action="store_true", help="检查电源状态")
        parser.add_argument("--power-on", action="store_true", help="远程开机")
        parser.add_argument("--power-off", action="store_true", help="远程关机")
        parser.add_argument("--nodes", help="指定节点名，用逗号分隔")
        parser.add_argument("--inventory", action="store_true", help="显示完整节点清单")
        parser.add_argument("--format", choices=["json", "table"], default="table", help="输出格式")
        
        args = parser.parse_args()
        
        # 获取节点信息
        nodes = self.get_nodes_from_hosts(args.env)
        if not nodes:
            logger.error(f"❌ 无法获取环境 {args.env} 的节点信息")
            return 1
        
        # 过滤指定节点
        if args.nodes:
            node_names = args.nodes.split(',')
            nodes = [n for n in nodes if n.get('hostname', '') in node_names]
            if not nodes:
                logger.error(f"❌ 未找到指定节点: {args.nodes}")
                return 1
        
        # 执行相应操作
        if args.sysinfo:
            results = self.execute_parallel(nodes, "system_info")
        elif args.ipmi_list:
            results = self.execute_parallel(nodes, "ipmi_ip")
        elif args.power_status:
            results = self.execute_parallel(nodes, "power_status")
        elif args.power_on or args.power_off:
            action = "on" if args.power_on else "off"
            results = []
            for node in nodes:
                ipmi_ip = node.get('ipmi_ip', '') or self.get_ipmi_ip(node.get('mgmt_ip', ''))
                if ipmi_ip:
                    result = self.power_control(ipmi_ip, action)
                    result["hostname"] = node.get('hostname', 'unknown')
                    result["ipmi_ip"] = ipmi_ip
                    results.append(result)
                else:
                    results.append({
                        "hostname": node.get('hostname', 'unknown'),
                        "status": "error",
                        "error": "无法获取IPMI IP"
                    })
        elif args.inventory:
            result = self.show_inventory(args.env)
            if args.format == "json":
                logger.info(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                logger.info(f"\n📋 {args.env} 环境节点清单")
                logger.info("=" * 80)
                logger.info(f"{'主机名':<15} {'管理IP':<15} {'IPMI IP':<15} {'状态':<10}")
                logger.info("-" * 80)
                for node in result["nodes"]:
                    logger.info(f"{node.get('hostname', 'N/A'):<15} "
                          f"{node.get('mgmt_ip', 'N/A'):<15} "
                          f"{node.get('ipmi_ip', 'N/A'):<15} "
                          f"{node.get('status', 'N/A'):<10}")
            return 0
        else:
            logger.error("❌ 请指定要执行的操作")
            return 1
        
        # 输出结果
        if args.format == "json":
            logger.info(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            logger.info(f"\n🖥️ {args.env} 环境操作结果")
            logger.info("=" * 80)
            logger.info(f"{'主机名':<15} {'IP地址':<15} {'状态':<10} {'详细信息':<30}")
            logger.info("-" * 80)
            
            for result in results:
                hostname = result.get('hostname', 'N/A')
                ip = result.get('mgmt_ip', 'N/A') 
                status = result.get('status', 'N/A')
                detail = ""
                
                if args.sysinfo:
                    detail = result.get('system_info', 'N/A')[:27] + "..." if len(result.get('system_info', '')) > 30 else result.get('system_info', 'N/A')
                elif args.ipmi_list:
                    detail = result.get('ipmi_ip', 'N/A')
                elif args.power_status:
                    detail = f"电源: {result.get('status', 'N/A')}"
                
                logger.info(f"{hostname:<15} {ip:<15} {status:<10} {detail:<30}")
        
        return 0

if __name__ == "__main__":
    sys.exit(HostManager().main())