#!/usr/bin/env python3
"""
安超平台存储集群管理工具
提供Zookeeper监控、磁盘健康检查、存储使用分析和异常告警功能

使用方式:
    python storage_manager.py --env production --zk-status
    python storage_manager.py --env production --disk-health
    python storage_manager.py --env production --usage --node 5
    python storage_manager.py --env production --check-all
"""

import sys
import json
import time
import argparse
import logging
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class StorageManager:
    """存储集群管理器"""
    
    # 存储节点映射
    NODE_MAPPING = {
        1: "storage-01",
        2: "storage-02", 
        3: "storage-03",
        4: "storage-04",
        5: "storage-05"
    }
    
    def __init__(self):
        # 使用主项目的环境配置文件
        env_config_path = str(Path(__file__).resolve().parents[3] / "environments.json")
        self.env_manager = EnvironmentManager(env_config_path)
        self.current_env = None
        self.ssh_key_path = "/root/myskills/SKILLS/id_rsa_cloud"
        self.ssh_user = "cloud"
        
    def get_storage_nodes(self, env_name: str) -> List[Dict]:
        """获取存储节点列表"""
        # 这里应该从实际环境配置中获取，暂时使用模拟数据
        # 在实际实现中，可以从hosts文件或环境配置中读取
        storage_nodes = [
            {"node_id": 1, "hostname": "storage-01", "mgmt_ip": "172.118.57.101"},
            {"node_id": 2, "hostname": "storage-02", "mgmt_ip": "172.118.57.102"},
            {"node_id": 3, "hostname": "storage-03", "mgmt_ip": "172.118.57.103"},
            {"node_id": 4, "hostname": "storage-04", "mgmt_ip": "172.118.57.104"},
            {"node_id": 5, "hostname": "storage-05", "mgmt_ip": "172.118.57.105"}
        ]
        return storage_nodes
    
    def execute_docker_command(self, node_ip: str, command: str) -> Dict:
        """在存储节点执行Docker命令"""
        try:
            full_command = f"docker exec -it mxsp {command}"
            result = ssh_execute_command(
                hostname=node_ip,
                port=22,
                username=self.ssh_user,
                key_path=self.ssh_key_path,
                command=full_command
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
    
    def check_zookeeper_status(self, node_ip: str) -> Dict:
        """检查Zookeeper集群状态"""
        result = self.execute_docker_command(node_ip, "zklist -c")
        
        if result["status"] != "success":
            return result
        
        output = result["output"]
        zk_info = {
            "status": "unknown",
            "nodes": [],
            "leader": None,
            "followers": []
        }
        
        # 解析Zookeeper输出
        lines = output.split('\n')
        node_count = 0
        
        for line in lines:
            if 'leader' in line.lower():
                zk_info["status"] = "healthy"
                # 提取节点信息，例如: Node 1: 192.168.1.10:2181 (leader)
                match = re.search(r'Node (\d+):\s*([0-9.]+:\d+)\s*\((\w+)\)', line)
                if match:
                    node_id = match.group(1)
                    address = match.group(2)
                    role = match.group(3)
                    
                    node_info = {"id": node_id, "address": address, "role": role}
                    zk_info["nodes"].append(node_info)
                    
                    if role.lower() == "leader":
                        zk_info["leader"] = address
                        zk_info["followers"] = [n["address"] for n in zk_info["nodes"] if n["role"].lower() != "leader"]
                    
                    node_count += 1
        
        zk_info["node_count"] = node_count
        return {
            "status": "success",
            "zookeeper_info": zk_info
        }
    
    def check_stale_disks(self, node_ip: str) -> Dict:
        """检查不可访问的磁盘"""
        result = self.execute_docker_command(node_ip, "showInodes --stale")
        
        if result["status"] != "success":
            return result
        
        output = result["output"]
        
        # 空输出表示没有不可访问的磁盘
        if not output.strip():
            return {
                "status": "success",
                "stale_disks": [],
                "healthy": True
            }
        
        # 解析不可访问磁盘信息
        stale_disks = []
        lines = output.split('\n')
        for line in lines:
            if line.strip():
                # 这里需要根据实际的输出格式解析
                stale_disks.append({
                    "disk_info": line.strip(),
                    "status": "stale"
                })
        
        return {
            "status": "success",
            "stale_disks": stale_disks,
            "healthy": len(stale_disks) == 0
        }
    
    def get_disk_usage(self, node_ip: str, node_id: int) -> Dict:
        """获取节点磁盘使用情况"""
        result = self.execute_docker_command(node_ip, f"mxServices -n {node_id} -L")
        
        if result["status"] != "success":
            return result
        
        output = result["output"]
        usage_info = {
            "node_id": node_id,
            "hostname": self.NODE_MAPPING.get(node_id, f"node-{node_id}"),
            "disks": []
        }
        
        # 解析磁盘使用信息
        lines = output.split('\n')
        for line in lines:
            if 'Disk' in line and 'GB' in line:
                # 解析类似: Disk /dev/sda1: 1024GB used / 2048GB total (50%)
                match = re.search(r'Disk\s+([^\s:]+):\s*(\d+)GB\s+used\s*/\s*(\d+)GB\s+total\s*\((\d+)%\)', line)
                if match:
                    disk_info = {
                        "device": match.group(1),
                        "used_gb": int(match.group(2)),
                        "total_gb": int(match.group(3)),
                        "usage_percent": int(match.group(4))
                    }
                    usage_info["disks"].append(disk_info)
        
        # 计算总体使用情况
        if usage_info["disks"]:
            total_used = sum(d["used_gb"] for d in usage_info["disks"])
            total_capacity = sum(d["total_gb"] for d in usage_info["disks"])
            usage_info["total_used_gb"] = total_used
            usage_info["total_capacity_gb"] = total_capacity
            usage_info["overall_usage_percent"] = round((total_used / total_capacity) * 100, 2) if total_capacity > 0 else 0
        
        return {
            "status": "success",
            "usage_info": usage_info
        }
    
    def get_cluster_usage(self, env_name: str) -> Dict:
        """获取整个集群的存储使用情况"""
        storage_nodes = self.get_storage_nodes(env_name)
        cluster_usage = {
            "environment": env_name,
            "total_nodes": len(storage_nodes),
            "nodes": [],
            "cluster_summary": {
                "total_capacity_gb": 0,
                "total_used_gb": 0,
                "overall_usage_percent": 0
            }
        }
        
        for node in storage_nodes:
            result = self.get_disk_usage(node["mgmt_ip"], node["node_id"])
            if result["status"] == "success":
                usage_info = result["usage_info"]
                cluster_usage["nodes"].append(usage_info)
                
                # 累计计算集群总量
                if "total_capacity_gb" in usage_info:
                    cluster_usage["cluster_summary"]["total_capacity_gb"] += usage_info["total_capacity_gb"]
                    cluster_usage["cluster_summary"]["total_used_gb"] += usage_info["total_used_gb"]
        
        # 计算集群总体使用率
        if cluster_usage["cluster_summary"]["total_capacity_gb"] > 0:
            cluster_usage["cluster_summary"]["overall_usage_percent"] = round(
                (cluster_usage["cluster_summary"]["total_used_gb"] / cluster_usage["cluster_summary"]["total_capacity_gb"]) * 100, 2
            )
        
        return cluster_usage
    
    def check_all_nodes_health(self, env_name: str) -> Dict:
        """检查所有节点的健康状态"""
        storage_nodes = self.get_storage_nodes(env_name)
        health_report = {
            "environment": env_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "zk_status": None,
            "disk_health": {
                "total_nodes": len(storage_nodes),
                "healthy_nodes": 0,
                "unhealthy_nodes": 0,
                "node_details": []
            },
            "alerts": []
        }
        
        # 检查Zookeeper状态（使用第一个节点）
        if storage_nodes:
            zk_result = self.check_zookeeper_status(storage_nodes[0]["mgmt_ip"])
            health_report["zk_status"] = zk_result
        
        # 检查每个节点的磁盘健康状态
        for node in storage_nodes:
            node_health = {
                "node_id": node["node_id"],
                "hostname": node["hostname"],
                "mgmt_ip": node["mgmt_ip"]
            }
            
            # 检查不可访问磁盘
            stale_result = self.check_stale_disks(node["mgmt_ip"])
            node_health["disk_health"] = stale_result
            
            if stale_result["status"] == "success" and stale_result.get("healthy", False):
                health_report["disk_health"]["healthy_nodes"] += 1
                node_health["overall_health"] = "healthy"
            else:
                health_report["disk_health"]["unhealthy_nodes"] += 1
                node_health["overall_health"] = "unhealthy"
                
                # 添加告警
                if stale_result.get("stale_disks"):
                    health_report["alerts"].append({
                        "severity": "warning",
                        "node": node["hostname"],
                        "message": f"发现 {len(stale_result['stale_disks'])} 个不可访问的磁盘",
                        "details": stale_result["stale_disks"]
                    })
            
            health_report["disk_health"]["node_details"].append(node_health)
        
        # 生成总体健康状态
        health_report["overall_health"] = (
            "healthy" if (
                health_report["disk_health"]["unhealthy_nodes"] == 0 and
                health_report["zk_status"] and health_report["zk_status"]["zookeeper_info"]["status"] == "healthy"
            ) else "unhealthy"
        )
        
        return health_report
    
    def format_output(self, data: Dict, format_type: str = "table"):
        """格式化输出结果"""
        if format_type == "json":
            logger.info(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            # 表格格式输出
            if "zk_status" in data and data["zk_status"]:
                zk_info = data["zk_status"].get("zookeeper_info", {})
                logger.info(f"\n🐘 Zookeeper集群状态")
                logger.info("=" * 60)
                logger.info(f"状态: {zk_info.get('status', 'unknown')}")
                logger.info(f"节点数: {zk_info.get('node_count', 0)}")
                logger.info(f"Leader: {zk_info.get('leader', 'N/A')}")
                logger.info(f"Followers: {', '.join(zk_info.get('followers', []))}")
            
            if "disk_health" in data:
                disk_health = data["disk_health"]
                logger.info(f"\n💿 磁盘健康状态")
                logger.info("=" * 60)
                logger.info(f"总节点数: {disk_health.get('total_nodes', 0)}")
                logger.info(f"健康节点: {disk_health.get('healthy_nodes', 0)}")
                logger.info(f"异常节点: {disk_health.get('unhealthy_nodes', 0)}")
                
                if disk_health.get("node_details"):
                    logger.info(f"\n{'节点名':<12} {'状态':<10} {'磁盘详情':<30}")
                    logger.info("-" * 60)
                    for node in disk_health["node_details"]:
                        status = node.get("overall_health", "unknown")
                        details = "健康"
                        if node.get("disk_health", {}).get("stale_disks"):
                            details = f"{len(node['disk_health']['stale_disks'])} 个异常磁盘"
                        logger.info(f"{node.get('hostname', 'N/A'):<12} {status:<10} {details:<30}")
            
            if "cluster_summary" in data:
                summary = data["cluster_summary"]
                logger.info(f"\n📊 集群存储使用情况")
                logger.info("=" * 60)
                logger.info(f"总容量: {summary.get('total_capacity_gb', 0)}GB")
                logger.info(f"已使用: {summary.get('total_used_gb', 0)}GB")
                logger.info(f"使用率: {summary.get('overall_usage_percent', 0)}%")
    
    def main(self):
        parser = argparse.ArgumentParser(description="安超平台存储集群管理工具")
        parser.add_argument("--env", required=True, help="环境名称")
        parser.add_argument("--zk-status", action="store_true", help="检查Zookeeper状态")
        parser.add_argument("--disk-health", action="store_true", help="检查磁盘健康状态")
        parser.add_argument("--usage", action="store_true", help="查看存储使用情况")
        parser.add_argument("--node", type=int, help="指定存储节点ID")
        parser.add_argument("--check-all", action="store_true", help="执行完整健康检查")
        parser.add_argument("--format", choices=["json", "table"], default="table", help="输出格式")
        
        args = parser.parse_args()
        
        result = None
        
        # 执行相应操作
        if args.check_all:
            result = self.check_all_nodes_health(args.env)
        elif args.zk_status:
            storage_nodes = self.get_storage_nodes(args.env)
            if storage_nodes:
                result = self.check_zookeeper_status(storage_nodes[0]["mgmt_ip"])
        elif args.disk_health:
            storage_nodes = self.get_storage_nodes(args.env)
            if args.node:
                # 检查指定节点
                node = next((n for n in storage_nodes if n["node_id"] == args.node), None)
                if node:
                    result = self.check_stale_disks(node["mgmt_ip"])
            else:
                # 检查所有节点
                health_report = self.check_all_nodes_health(args.env)
                result = health_report.get("disk_health", {})
        elif args.usage:
            if args.node:
                # 查看指定节点使用情况
                storage_nodes = self.get_storage_nodes(args.env)
                node = next((n for n in storage_nodes if n["node_id"] == args.node), None)
                if node:
                    result = self.get_disk_usage(node["mgmt_ip"], args.node)
            else:
                # 查看整个集群使用情况
                result = self.get_cluster_usage(args.env)
        
        if result:
            self.format_output(result, args.format)
            return 0
        else:
            logger.error("❌ 请指定要执行的操作")
            return 1

if __name__ == "__main__":
    sys.exit(StorageManager().main())