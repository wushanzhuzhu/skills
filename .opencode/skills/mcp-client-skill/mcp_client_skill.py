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
MCP Client Skill - 主要技能实现
遵循"Skill驱动、MCP支撑"的架构模式，作为执行者主动调用MCP Server方法
"""

import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加主项目路径
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from mcp_method_client import MCPMethodClient, MCPCallResult
from session_manager import SessionManager

class MCPClientSkill:
    """
    MCP Client Skill 主类
    
    作为Skill执行者，主动调用MCP Server的方法来处理业务逻辑：
    - 系统状态检查
    - 资源管理
    - 工作流编排
    - 故障诊断
    """
    
    def __init__(self, env_id: str = None, auto_session: bool = True):
        self.env_id = env_id
        self.auto_session = auto_session
        
        # 初始化组件
        self.mcp_client = MCPMethodClient(auto_session=auto_session)
        self.session_manager = SessionManager() if auto_session else None
        
        # 建立会话
        self._initialize_session()
    
    def _initialize_session(self):
        """初始化会话"""
        if not self.auto_session:
            return
        
        if self.env_id:
            result = self.session_manager.establish_session(env_id=self.env_id)
            if result.get('success'):
                logger.info(f"✅ 环境会话建立成功: {self.env_id}")
            else:
                logger.error(f"❌ 环境会话建立失败: {result.get('error')}")
        else:
            logger.info("🔧 使用默认会话配置")
    
    def system_health_check(self) -> Dict:
        """
        系统健康检查 - 调用多个MCP方法进行综合检查
        """
        logger.info("🔍 开始系统健康检查...")
        
        # 批量调用系统状态相关的MCP方法
        method_calls = [
            {"method": "get_audit", "params": {}},
            {"method": "get_clusterStor", "params": {}},
            {"method": "get_image", "params": {}},
            {"method": "get_instances", "params": {}},
            {"method": "get_volumes", "params": {}}
        ]
        
        results = self.mcp_client.batch_call(method_calls)
        
        # 分析结果
        health_report = self._analyze_health_results(results)
        
        return health_report
    
    def _analyze_health_results(self, results: List[MCPCallResult]) -> Dict:
        """分析健康检查结果"""
        report = {
            "check_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": "healthy",
            "component_status": {},
            "issues": [],
            "summary": {}
        }
        
        successful_checks = 0
        total_checks = len(results)
        
        for result in results:
            component = result.method_name.replace('get_', '').lower()
            
            if result.success:
                successful_checks += 1
                data = result.data
                
                if component == 'audit':
                    report["component_status"][component] = {
                        "status": "healthy",
                        "data": {
                            "session_active": True,
                            "base_url": data[0] if isinstance(data, tuple) and len(data) > 0 else "unknown"
                        }
                    }
                elif component == 'clusterstor':
                    report["component_status"][component] = {
                        "status": "healthy",
                        "data": {
                            "zone_id": data[0] if isinstance(data, tuple) and len(data) > 0 else "unknown",
                            "cluster_id": data[1] if isinstance(data, tuple) and len(data) > 1 else "unknown"
                        }
                    }
                elif component in ['image', 'instances', 'volumes']:
                    if isinstance(data, list):
                        report["component_status"][component] = {
                            "status": "healthy",
                            "data": {
                                "count": len(data),
                                "items": data[:3] if len(data) > 0 else []
                            }
                        }
                    else:
                        report["component_status"][component] = {
                            "status": "warning",
                            "data": {"message": "数据格式异常"}
                        }
                        report["issues"].append(f"{component}: 数据格式异常")
                else:
                    report["component_status"][component] = {
                        "status": "healthy",
                        "data": data
                    }
            else:
                report["component_status"][component] = {
                    "status": "error",
                    "error": result.error
                }
                report["issues"].append(f"{component}: {result.error}")
        
        # 计算总体状态
        success_rate = successful_checks / total_checks
        if success_rate >= 0.8:
            report["overall_status"] = "healthy"
        elif success_rate >= 0.5:
            report["overall_status"] = "warning"
        else:
            report["overall_status"] = "critical"
        
        # 生成摘要
        report["summary"] = {
            "total_checks": total_checks,
            "successful_checks": successful_checks,
            "failed_checks": total_checks - successful_checks,
            "success_rate": round(success_rate * 100, 1),
            "issues_count": len(report["issues"])
        }
        
        return report
    
    def resource_management_overview(self) -> Dict:
        """
        资源管理概览 - 获取并分析所有资源信息
        """
        logger.info("📊 开始资源管理概览...")
        
        # 获取详细资源信息
        method_calls = [
            {"method": "getStorinfo", "params": {}},
            {"method": "getImagebystorageManageId", "params": {}},
            {"method": "get_instances", "params": {}},
            {"method": "get_volumes", "params": {}}
        ]
        
        results = self.mcp_client.batch_call(method_calls)
        
        # 分析资源使用情况
        resource_overview = self._analyze_resource_overview(results)
        
        return resource_overview
    
    def _analyze_resource_overview(self, results: List[MCPCallResult]) -> Dict:
        """分析资源概览"""
        overview = {
            "analysis_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "resources": {},
            "recommendations": [],
            "statistics": {}
        }
        
        for result in results:
            if not result.success:
                continue
            
            resource_type = result.method_name.replace('get_', '').replace('imagebystorageManageId', 'images').lower()
            data = result.data
            
            if resource_type == 'storinfo':
                # 存储信息分析
                if isinstance(data, list):
                    storage_types = {}
                    for storage in data:
                        backend = storage.get('storageBackend', 'unknown')
                        storage_types[backend] = storage_types.get(backend, 0) + 1
                    
                    overview["resources"]["storage"] = {
                        "total_locations": len(data),
                        "storage_backends": storage_types,
                        "details": data
                    }
                    
                    if len(data) == 0:
                        overview["recommendations"].append("系统没有可用存储，建议检查存储配置")
            
            elif resource_type == 'images':
                # 镜像信息分析
                if isinstance(data, list):
                    overview["resources"]["images"] = {
                        "total_images": len(data),
                        "recent_images": data[:5],  # 显示最近5个镜像
                        "details": data
                    }
                    
                    if len(data) == 0:
                        overview["recommendations"].append("系统没有可用镜像，建议上传系统镜像")
            
            elif resource_type == 'instances':
                # 虚拟机实例分析
                if isinstance(data, list):
                    overview["resources"]["instances"] = {
                        "total_instances": len(data),
                        "details": data
                    }
            
            elif resource_type == 'volumes':
                # 磁盘分析
                if isinstance(data, list):
                    overview["resources"]["volumes"] = {
                        "total_volumes": len(data),
                        "details": data
                    }
        
        # 生成统计信息
        overview["statistics"] = {
            "total_resource_types": len(overview["resources"]),
            "recommendations_count": len(overview["recommendations"])
        }
        
        return overview
    
    def smart_vm_creation(self, vm_config: Dict, count: int = 1) -> Dict:
        """
        智能虚拟机创建 - 协调多个MCP方法创建VM
        """
        logger.info(f"🚀 开始智能创建 {count} 个虚拟机...")
        
        # 1. 获取资源信息用于验证
        resource_info = self.resource_management_overview()
        
        # 2. 验证配置
        validation_result = self._validate_vm_config(vm_config, resource_info)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": "配置验证失败",
                "validation_errors": validation_result["errors"]
            }
        
        # 3. 批量创建虚拟机
        creation_results = []
        for i in range(count):
            # 为每个VM生成唯一名称
            current_config = vm_config.copy()
            timestamp = int(time.time())
            current_config["name"] = f"{vm_config['name']}-{timestamp}-{i+1:03d}"
            current_config["hostname"] = f"{vm_config.get('hostname', 'vm')}-{i+1:03d}"
            
            logger.info(f"📝 创建第 {i+1}/{count} 个虚拟机: {current_config['name']}")
            
            # 调用MCP方法创建虚拟机
            result = self.mcp_client.call_method("createInstance_noNet", **current_config)
            
            if result.success:
                creation_results.append({
                    "index": i + 1,
                    "name": current_config["name"],
                    "vm_id": result.data[0] if isinstance(result.data, (tuple, list)) else None,
                    "parameters": result.data[1] if isinstance(result.data, (tuple, list)) and len(result.data) > 1 else {},
                    "success": True
                })
                logger.info(f"✅ 虚拟机创建成功: {current_config['name']}")
            else:
                creation_results.append({
                    "index": i + 1,
                    "name": current_config["name"],
                    "success": False,
                    "error": result.error
                })
                logger.error(f"❌ 虚拟机创建失败: {result.error}")
            
            # 添加延迟避免API频率限制
            if i < count - 1:
                time.sleep(2)
        
        # 4. 生成创建报告
        success_count = sum(1 for r in creation_results if r["success"])
        
        return {
            "success": success_count > 0,
            "total_requested": count,
            "successful_creations": success_count,
            "failed_creations": count - success_count,
            "success_rate": round(success_count / count * 100, 1),
            "creation_results": creation_results,
            "vm_configs_used": [r["parameters"] for r in creation_results if r.get("parameters")]
        }
    
    def _validate_vm_config(self, vm_config: Dict, resource_info: Dict) -> Dict:
        """验证虚拟机配置"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 检查必需参数
        required_params = ['name', 'hostname', 'videoModel', 'imageId', 'storname', 'cpu', 'memory']
        for param in required_params:
            if param not in vm_config or vm_config[param] is None:
                validation["valid"] = False
                validation["errors"].append(f"缺少必需参数: {param}")
        
        # 检查存储配置
        storage_info = resource_info.get("resources", {}).get("storage", {})
        if storage_info and storage_info.get("total_locations", 0) > 0:
            available_storages = [s.get("stackName") for s in storage_info.get("details", [])]
            if vm_config.get("storname") not in available_storages:
                validation["errors"].append(f"存储位置 '{vm_config.get('storname')}' 不存在，可用存储: {available_storages}")
        
        # 检查硬件配置
        if vm_config.get("cpu", 0) < 1:
            validation["errors"].append("CPU数量必须大于0")
        
        if vm_config.get("memory", 0) < 1:
            validation["errors"].append("内存大小必须大于0")
        
        # 检查视频模型
        valid_video_models = ["cirrus", "qxl", "virtio", "vga"]
        if vm_config.get("videoModel") not in valid_video_models:
            validation["errors"].append(f"无效的视频模型，支持: {valid_video_models}")
        
        return validation
    
    def disk_management_operation(self, operation: str, **params) -> Dict:
        """
        磁盘管理操作 - 创建或删除磁盘
        """
        logger.info(f"💾 开始磁盘管理操作: {operation}")
        
        if operation == "create":
            return self._create_disk_operation(**params)
        elif operation == "delete":
            return self._delete_disk_operation(**params)
        else:
            return {
                "success": False,
                "error": f"不支持的操作: {operation}"
            }
    
    def _create_disk_operation(self, **disk_params) -> Dict:
        """创建磁盘操作"""
        required_params = ['storageManageId', 'pageSize', 'compression', 'name', 'size', 'iops', 'bandwidth', 'count', 'readCache', 'zoneId']
        
        # 验证参数
        for param in required_params:
            if param not in disk_params or disk_params[param] is None:
                return {
                    "success": False,
                    "error": f"缺少必需参数: {param}"
                }
        
        # 调用MCP方法创建磁盘
        result = self.mcp_client.call_method("createDisk_vstor", **disk_params)
        
        if result.success:
            return {
                "success": True,
                "disk_info": result.data,
                "parameters_used": disk_params
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "parameters_used": disk_params
            }
    
    def _delete_disk_operation(self, disk_ids: List[str] = None) -> Dict:
        """删除磁盘操作"""
        if not disk_ids:
            return {
                "success": False,
                "error": "必须指定要删除的磁盘ID列表"
            }
        
        # 调用MCP方法删除磁盘
        result = self.mcp_client.call_method("deleteDisk", diskId=disk_ids)
        
        if result.success:
            return {
                "success": True,
                "deleted_disk_ids": disk_ids,
                "deletion_result": result.data
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "disk_ids": disk_ids
            }
    
    def get_mcp_client_info(self) -> Dict:
        """获取MCP客户端信息"""
        return {
            "available_methods": list(self.mcp_client.get_available_methods().keys()),
            "call_statistics": self.mcp_client.get_call_statistics(),
            "session_info": self.session_manager.get_session_summary() if self.session_manager else "会话管理未启用"
        }
    
    def interactive_mode(self):
        """交互式模式"""
        logger.info("🎮 MCP Client Skill 交互模式")
        logger.info("输入 'help' 查看可用命令，输入 'quit' 退出")
        
        while True:
            try:
                command = input("\n> ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    logger.info("👋 退出交互模式")
                    break
                
                if command.lower() == 'help':
                    self._show_help()
                elif command == 'health':
                    self._execute_and_show('system_health_check')
                elif command == 'resources':
                    self._execute_and_show('resource_management_overview')
                elif command == 'info':
                    self._execute_and_show('get_mcp_client_info')
                elif command.startswith('vm-create'):
                    self._interactive_vm_create(command)
                else:
                    logger.error(f"❌ 未知命令: {command}")
                    logger.info("输入 'help' 查看可用命令")
                    
            except KeyboardInterrupt:
                logger.info("\n👋 退出交互模式")
                break
            except Exception as e:
                logger.error(f"❌ 执行命令时发生错误: {e}")
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
🎮 MCP Client Skill 交互模式 - 帮助信息

📋 可用命令:
  help                 - 显示此帮助信息
  health               - 系统健康检查
  resources            - 资源管理概览
  info                 - MCP客户端信息
  vm-create <config>   - 交互式创建虚拟机
  
📝 示例:
  vm-create            - 使用交互式向导创建虚拟机
  vm-create name=test-vm cpu=2 memory=4 - 快速创建配置

🚀 退出:
  quit, exit, q       - 退出交互模式
        """
        logger.info(help_text)
    
    def _execute_and_show(self, method_name: str):
        """执行方法并显示结果"""
        logger.info(f"\n🔧 执行: {method_name}")
        logger.info("-" * 50)
        
        try:
            method = getattr(self, method_name)
            result = method()
            
            logger.info(json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error(f"❌ 执行失败: {e}")
    
    def _interactive_vm_create(self, command: str):
        """交互式虚拟机创建"""
        # 简单的VM创建向导
        base_config = {
            "name": "interactive-vm",
            "hostname": "int-vm",
            "videoModel": "virtio",
            "storname": "basic-replica2",  # 默认值
            "cpu": 2,
            "memory": 4,
            "size": 40,
            "haEnable": True,
            "priority": 1
        }
        
        logger.info("🚀 交互式虚拟机创建向导")
        logger.info("使用当前配置创建1个虚拟机，或输入自定义配置")
        logger.info(f"默认配置: {base_config}")
        
        confirm = input("是否使用默认配置? (y/n): ").strip().lower()
        
        if confirm == 'y':
            result = self.smart_vm_creation(base_config, count=1)
            logger.info(f"\n📊 创建结果:")
            logger.info(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            logger.info("💡 自定义配置功能开发中，请使用默认配置")


def main():
    """主函数 - 命令行入口"""
    parser = argparse.ArgumentParser(description="MCP Client Skill - 智能MCP方法调用客户端")
    parser.add_argument("--env", help="环境ID")
    parser.add_argument("--command", choices=["health", "resources", "info", "interactive"], 
                       help="要执行的命令")
    parser.add_argument("--auto-session", action="store_true", default=True,
                       help="自动管理会话")
    
    args = parser.parse_args()
    
    # 创建技能实例
    skill = MCPClientSkill(env_id=args.env, auto_session=args.auto_session)
    
    if args.command == "health":
        result = skill.system_health_check()
        logger.info(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.command == "resources":
        result = skill.resource_management_overview()
        logger.info(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.command == "info":
        result = skill.get_mcp_client_info()
        logger.info(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.command == "interactive":
        skill.interactive_mode()
    else:
        # 默认进入交互模式
        skill.interactive_mode()


if __name__ == "__main__":
    main()