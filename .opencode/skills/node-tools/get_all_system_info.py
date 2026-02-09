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
获取所有节点的系统信息
"""

import sys
from pathlib import Path
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# 导入现有模块
sys.path.insert(0, '/root/myskills/SKILLS')
from utils.tools.sshcommand import ssh_execute_command

# 从hosts文件中解析的节点信息
NODES = {
    "node001": {"ip": "172.118.57.10", "role": "Controller/Compute"},
    "node002": {"ip": "172.118.57.11", "role": "Controller/Compute"},
    "node003": {"ip": "172.118.57.12", "role": "Controller/Compute"},
    "node004": {"ip": "172.118.57.15", "role": "Storage/vStor"},
    "node005": {"ip": "172.118.57.16", "role": "Storage/vStor"},
    "node006": {"ip": "172.118.57.17", "role": "Storage/vStor"}
}

def get_node_system_info(node_name: str, node_info: Dict) -> Dict[str, Any]:
    """获取单个节点的系统信息"""
    ip = node_info["ip"]
    role = node_info["role"]
    
    try:
        result = ssh_execute_command(
            hostname=ip,
            port=22,
            username="cloud",
            key_path="/root/myskills/SKILLS/id_rsa_cloud",
            command="cat /etc/system-info"
        )
        
        if result and result.strip():
            return {
                "status": "success",
                "node_name": node_name,
                "ip": ip,
                "role": role,
                "system_info": result.strip()
            }
        else:
            return {
                "status": "no_output",
                "node_name": node_name,
                "ip": ip,
                "role": role,
                "error": "命令执行成功但没有输出"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "node_name": node_name,
            "ip": ip,
            "role": role,
            "error": str(e)
        }

def format_system_info(results: list) -> None:
    """格式化输出所有节点的系统信息"""
    logger.info("🖥️ 安超平台集群系统信息报告")
    logger.info("=" * 80)
    
    successful_nodes = []
    failed_nodes = []
    
    for result in results:
        if result["status"] == "success":
            successful_nodes.append(result)
        else:
            failed_nodes.append(result)
    
    # 显示成功获取信息的节点
    if successful_nodes:
        for i, node in enumerate(successful_nodes, 1):
            logger.info(f"\n📋 节点 {i}: {node['node_name']} ({node['role']})")
            logger.info(f"📍 IP地址: {node['ip']}")
            logger.info(f"📝 系统信息:")
            logger.info("-" * 40)
            logger.info(node['system_info'])
            logger.info("-" * 40)
    
    # 显示失败的节点
    if failed_nodes:
        logger.info(f"\n❌ 获取信息失败的节点 ({len(failed_nodes)}个):")
        for node in failed_nodes:
            logger.info(f"  • {node['node_name']} ({node['ip']}): {node.get('error', '未知错误')}")
    
    # 汇总信息
    logger.info(f"\n📊 汇总统计:")
    logger.info(f"  • 总节点数: {len(results)}")
    logger.info(f"  • 成功获取: {len(successful_nodes)}")
    logger.info(f"  • 获取失败: {len(failed_nodes)}")
    
    if successful_nodes:
        logger.info(f"  • 成功率: {round((len(successful_nodes)/len(results))*100, 1)}%")

def main():
    """主函数"""
    logger.info("🔍 正在获取所有节点的安超平台系统信息...")
    
    # 并行获取所有节点的系统信息
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_node = {
            executor.submit(get_node_system_info, node_name, node_info): node_name
            for node_name, node_info in NODES.items()
        }
        
        for future in as_completed(future_to_node):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                node_name = future_to_node[future]
                results.append({
                    "status": "error",
                    "node_name": node_name,
                    "error": f"执行异常: {str(e)}"
                })
    
    # 按节点名排序
    results.sort(key=lambda x: x.get('node_name', ''))
    
    # 格式化输出
    format_system_info(results)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())