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
安超平台版本查询工具
专门用于查询指定IP节点的安超版本信息

使用方式:
    python get_archeros_version.py [IP地址]
    python get_archeros_version.py 172.118.57.100
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# 导入现有模块
main_project_path = str(Path(__file__).resolve().parents[3])
sys.path.insert(0, main_project_path)
from utils.tools.sshcommand import ssh_execute_command

def get_archeros_version(target_ip: str) -> Dict[str, Any]:
    """获取安超平台版本信息"""
    try:
        # 执行版本查询命令
        result = ssh_execute_command(
            hostname=target_ip,
            port=22,
            username="cloud",
            key_path="/root/myskills/SKILLS/id_rsa_cloud",
            command="cat /etc/system-info"
        )
        
        if result and result.strip():
            return {
                "status": "success",
                "ip": target_ip,
                "version_info": result.strip()
            }
        else:
            return {
                "status": "no_output",
                "ip": target_ip,
                "error": "命令执行成功但没有输出"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "ip": target_ip,
            "error": str(e)
        }

def format_output(result: Dict[str, Any]) -> str:
    """格式化输出为纯文本格式"""
    if result["status"] == "success":
        output = []
        output.append(f"✅ 成功获取 {result['ip']} 的安超版本信息:")
        output.append("=" * 50)
        output.append(result["version_info"])
        output.append("=" * 50)
        return "\n".join(output)
    else:
        output = []
        output.append(f"❌ 获取 {result['ip']} 版本信息失败:")
        output.append(f"错误: {result.get('error', '未知错误')}")
        return "\n".join(output)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="安超平台版本查询工具")
    parser.add_argument("ip", nargs="?", default="172.118.57.100", 
                       help="目标IP地址 (默认: 172.118.57.100)")
    
    args = parser.parse_args()
    target_ip = args.ip
    
    logger.info(f"🔍 正在查询 {target_ip} 的安超平台版本信息...")
    
    # 获取版本信息
    result = get_archeros_version(target_ip)
    
    # 格式化并输出结果
    formatted_output = format_output(result)
    logger.info(formatted_output)
    
    # 根据状态返回退出码
    return 0 if result["status"] == "success" else 1

if __name__ == "__main__":
    sys.exit(main())