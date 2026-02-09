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
安超平台监控工具
提供日志分析、资源监控、健康检查和性能分析功能

使用方式:
    python platform_monitor.py --env production --status
    python platform_monitor.py --env production --log-analysis
    python platform_monitor.py --env production --resource-monitor
    python platform_monitor.py --env production --health-check
"""

import sys
import json
import time
import argparse
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加主项目路径
main_project_path = str(Path(__file__).resolve().parents[3])
sys.path.insert(0, main_project_path)

# 使用主项目的模块
from utils.audit import ArcherAudit
from utils.tools.sshcommand import ssh_execute_command
from env_manager import EnvironmentManager

class PlatformMonitor:
    """平台监控器"""
    
    # 监控阈值配置
    DEFAULT_THRESHOLDS = {
        "cpu_percent": 80,
        "memory_percent": 85,
        "disk_percent": 90,
        "api_response_time": 1000,  # 毫秒
        "error_rate": 5  # 每小时错误数
    }
    
    def __init__(self):
        # 使用主项目的环境配置文件
        env_config_path = str(Path(__file__).resolve().parents[3] / "environments.json")
        self.env_manager = EnvironmentManager(env_config_path)
        self.current_env = None
        self.ssh_key_path = "/root/myskills/SKILLS/id_rsa_cloud"
        self.ssh_user = "cloud"
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()
        
    def get_monitoring_nodes(self, env_name: str) -> List[Dict]:
        """获取监控节点列表"""
        # 这里应该从实际环境配置中获取，暂时使用模拟数据
        monitoring_nodes = [
            {"hostname": "controller-01", "mgmt_ip": "172.118.57.100", "role": "controller"},
            {"hostname": "compute-01", "mgmt_ip": "172.118.57.101", "role": "compute"},
            {"hostname": "compute-02", "mgmt_ip": "172.118.57.102", "role": "compute"},
            {"hostname": "storage-01", "mgmt_ip": "172.118.57.103", "role": "storage"}
        ]
        return monitoring_nodes
    
    def execute_monitoring_command(self, node_ip: str, command: str) -> Dict:
        """在监控节点执行命令"""
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
    
    def get_system_resources(self, node_ip: str) -> Dict:
        """获取系统资源信息"""
        resources = {"node_ip": node_ip}
        
        # CPU使用率
        cpu_result = self.execute_monitoring_command(
            node_ip, 
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1"
        )
        if cpu_result["status"] == "success":
            try:
                resources["cpu_percent"] = float(cpu_result["output"])
            except ValueError:
                resources["cpu_percent"] = 0
        
        # 内存使用率
        mem_result = self.execute_monitoring_command(
            node_ip,
            "free -m | awk 'NR==2{printf \"%.2f\", $3*100/$2}'"
        )
        if mem_result["status"] == "success":
            try:
                resources["memory_percent"] = float(mem_result["output"])
            except ValueError:
                resources["memory_percent"] = 0
        
        # 磁盘使用率
        disk_result = self.execute_monitoring_command(
            node_ip,
            "df -h / | awk 'NR==2{print $5}' | cut -d'%' -f1"
        )
        if disk_result["status"] == "success":
            try:
                resources["disk_percent"] = float(disk_result["output"])
            except ValueError:
                resources["disk_percent"] = 0
        
        # 系统负载
        load_result = self.execute_monitoring_command(
            node_ip,
            "uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | cut -d',' -f1"
        )
        if load_result["status"] == "success":
            try:
                resources["load_average"] = float(load_result["output"])
            except ValueError:
                resources["load_average"] = 0
        
        return resources
    
    def analyze_platform_logs(self, node_ip: str, hours: int = 1) -> Dict:
        """分析平台日志"""
        log_path = "/var/log/haihe/resource/resource.log"
        
        # 获取最近N小时的日志
        since_time = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        command = f"journalctl -u haihe-resource --since '{since_time}' || tail -n 1000 {log_path}"
        
        log_result = self.execute_monitoring_command(node_ip, command)
        
        if log_result["status"] != "success":
            return log_result
        
        output = log_result["output"]
        analysis = {
            "log_lines": len(output.split('\n')),
            "errors": [],
            "warnings": [],
            "info_count": 0,
            "time_range": {"start": since_time, "end": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        }
        
        # 解析日志内容
        lines = output.split('\n')
        for line in lines:
            line_lower = line.lower()
            if "error" in line_lower or "fatal" in line_lower or "exception" in line_lower:
                analysis["errors"].append(line.strip())
            elif "warning" in line_lower or "warn" in line_lower:
                analysis["warnings"].append(line.strip())
            elif line.strip():
                analysis["info_count"] += 1
        
        # 计算错误率
        total_entries = len(analysis["errors"]) + len(analysis["warnings"]) + analysis["info_count"]
        if total_entries > 0:
            analysis["error_rate"] = round((len(analysis["errors"]) / total_entries) * 100, 2)
        else:
            analysis["error_rate"] = 0
        
        return {
            "status": "success",
            "log_analysis": analysis
        }
    
    def check_component_health(self, node_ip: str, component: str) -> Dict:
        """检查组件健康状态"""
        health_checks = {
            "api": self._check_api_health,
            "database": self._check_database_health,
            "message_queue": self._check_message_queue_health,
            "resource_service": self._check_resource_service_health
        }
        
        if component in health_checks:
            return health_checks[component](node_ip)
        else:
            return {
                "status": "error",
                "error": f"Unknown component: {component}"
            }
    
    def _check_api_health(self, node_ip: str) -> Dict:
        """检查API健康状态"""
        # 检查API服务状态
        api_result = self.execute_monitoring_command(
            node_ip,
            "systemctl is-active haihe-api || ps aux | grep haihe-api | grep -v grep"
        )
        
        if api_result["status"] == "success":
            is_active = "active" in api_result["output"] or len(api_result["output"].split()) > 0
            
            # 测试API响应时间
            response_time = 0
            if is_active:
                start_time = time.time()
                test_result = self.execute_monitoring_command(
                    node_ip,
                    "curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/health || echo '000'"
                )
                response_time = round((time.time() - start_time) * 1000, 2)  # 毫秒
            
            return {
                "status": "success",
                "component": "api",
                "is_active": is_active,
                "response_time_ms": response_time,
                "health_score": 100 if is_active and response_time < 1000 else 50
            }
        
        return {"status": "error", "component": "api", "error": api_result.get("error", "Unknown error")}
    
    def _check_database_health(self, node_ip: str) -> Dict:
        """检查数据库健康状态"""
        db_result = self.execute_monitoring_command(
            node_ip,
            "systemctl is-active mariadb || systemctl is-active mysql || ps aux | grep mariadb | grep -v grep"
        )
        
        if db_result["status"] == "success":
            is_active = "active" in db_result["output"] or len(db_result["output"].split()) > 0
            
            # 测试数据库连接
            connection_test = False
            if is_active:
                test_result = self.execute_monitoring_command(
                    node_ip,
                    "mysql -e 'SELECT 1;' 2>/dev/null || echo 'connection_failed'"
                )
                connection_test = "connection_failed" not in test_result.get("output", "")
            
            return {
                "status": "success",
                "component": "database",
                "is_active": is_active,
                "connection_ok": connection_test,
                "health_score": 100 if is_active and connection_test else 50
            }
        
        return {"status": "error", "component": "database", "error": db_result.get("error", "Unknown error")}
    
    def _check_message_queue_health(self, node_ip: str) -> Dict:
        """检查消息队列健康状态"""
        mq_result = self.execute_monitoring_command(
            node_ip,
            "systemctl is-active rabbitmq-server || systemctl is-active redis || ps aux | grep rabbitmq | grep -v grep"
        )
        
        if mq_result["status"] == "success":
            is_active = "active" in mq_result["output"] or len(mq_result["output"].split()) > 0
            
            return {
                "status": "success",
                "component": "message_queue",
                "is_active": is_active,
                "health_score": 100 if is_active else 0
            }
        
        return {"status": "error", "component": "message_queue", "error": mq_result.get("error", "Unknown error")}
    
    def _check_resource_service_health(self, node_ip: str) -> Dict:
        """检查资源服务健康状态"""
        rs_result = self.execute_monitoring_command(
            node_ip,
            "systemctl is-active haihe-resource || ps aux | grep haihe-resource | grep -v grep"
        )
        
        if rs_result["status"] == "success":
            is_active = "active" in rs_result["output"] or len(rs_result["output"].split()) > 0
            
            return {
                "status": "success",
                "component": "resource_service",
                "is_active": is_active,
                "health_score": 100 if is_active else 0
            }
        
        return {"status": "error", "component": "resource_service", "error": rs_result.get("error", "Unknown error")}
    
    def check_all_components(self, node_ip: str) -> Dict:
        """检查所有组件健康状态"""
        components = ["api", "database", "message_queue", "resource_service"]
        component_results = {}
        overall_score = 0
        
        for component in components:
            result = self.check_component_health(node_ip, component)
            component_results[component] = result
            
            if result["status"] == "success":
                overall_score += result.get("health_score", 0)
        
        # 计算总体健康分数
        if components:
            overall_score = round(overall_score / len(components), 2)
        
        return {
            "status": "success",
            "components": component_results,
            "overall_health_score": overall_score,
            "overall_status": "healthy" if overall_score >= 80 else "warning" if overall_score >= 60 else "critical"
        }
    
    def generate_alerts(self, resources: Dict, log_analysis: Dict, component_health: Dict) -> List[Dict]:
        """生成告警信息"""
        alerts = []
        
        # 资源使用告警
        for metric, threshold in self.thresholds.items():
            if metric in resources:
                current_value = resources[metric]
                if current_value > threshold:
                    severity = "critical" if current_value > threshold * 1.1 else "warning"
                    alerts.append({
                        "severity": severity,
                        "type": "resource",
                        "metric": metric,
                        "current_value": current_value,
                        "threshold": threshold,
                        "message": f"{metric.upper()} 使用率 {current_value}% 超过阈值 {threshold}%"
                    })
        
        # 日志错误告警
        if log_analysis.get("log_analysis"):
            error_count = len(log_analysis["log_analysis"].get("errors", []))
            if error_count > self.thresholds["error_rate"]:
                alerts.append({
                    "severity": "warning",
                    "type": "log",
                    "metric": "error_count",
                    "current_value": error_count,
                    "threshold": self.thresholds["error_rate"],
                    "message": f"日志错误数 {error_count} 超过阈值 {self.thresholds['error_rate']}"
                })
        
        # 组件健康告警
        if component_health.get("components"):
            for component, result in component_health["components"].items():
                if result.get("status") == "success" and not result.get("is_active", False):
                    alerts.append({
                        "severity": "critical",
                        "type": "component",
                        "metric": f"{component}_status",
                        "current_value": "down",
                        "threshold": "up",
                        "message": f"组件 {component.upper()} 状态异常"
                    })
        
        return alerts
    
    def get_platform_status(self, env_name: str) -> Dict:
        """获取平台整体状态"""
        monitoring_nodes = self.get_monitoring_nodes(env_name)
        controller_node = next((n for n in monitoring_nodes if n["role"] == "controller"), monitoring_nodes[0])
        
        status_report = {
            "environment": env_name,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "controller_node": controller_node["hostname"],
            "overall_status": "unknown",
            "health_score": 0,
            "alerts": []
        }
        
        # 获取系统资源
        resources = self.get_system_resources(controller_node["mgmt_ip"])
        status_report["resources"] = resources
        
        # 分析日志
        log_analysis = self.analyze_platform_logs(controller_node["mgmt_ip"])
        status_report["log_analysis"] = log_analysis
        
        # 检查组件健康
        component_health = self.check_all_components(controller_node["mgmt_ip"])
        status_report["component_health"] = component_health
        
        # 生成告警
        alerts = self.generate_alerts(resources, log_analysis, component_health)
        status_report["alerts"] = alerts
        
        # 计算总体状态
        if component_health.get("overall_health_score", 0) >= 80 and len(alerts) == 0:
            status_report["overall_status"] = "healthy"
            status_report["health_score"] = component_health["overall_health_score"]
        elif component_health.get("overall_health_score", 0) >= 60:
            status_report["overall_status"] = "warning"
            status_report["health_score"] = component_health["overall_health_score"]
        else:
            status_report["overall_status"] = "critical"
            status_report["health_score"] = component_health["overall_health_score"]
        
        return status_report
    
    def format_output(self, data: Dict, format_type: str = "table"):
        """格式化输出结果"""
        if format_type == "json":
            logger.info(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            # 表格格式输出
            logger.info(f"\n📊 {data.get('environment', 'Unknown')} 环境平台状态")
            logger.info("=" * 80)
            logger.info(f"时间: {data.get('timestamp', 'N/A')}")
            logger.info(f"控制节点: {data.get('controller_node', 'N/A')}")
            logger.info(f"总体状态: {data.get('overall_status', 'N/A')}")
            logger.info(f"健康分数: {data.get('health_score', 0)}/100")
            
            # 资源使用情况
            if "resources" in data:
                resources = data["resources"]
                logger.info(f"\n📈 资源使用情况")
                logger.info("-" * 40)
                logger.info(f"CPU使用率: {resources.get('cpu_percent', 0)}%")
                logger.info(f"内存使用率: {resources.get('memory_percent', 0)}%")
                logger.info(f"磁盘使用率: {resources.get('disk_percent', 0)}%")
                logger.info(f"系统负载: {resources.get('load_average', 0)}")
            
            # 组件健康状态
            if "component_health" in data and data["component_health"].get("components"):
                components = data["component_health"]["components"]
                logger.info(f"\n🔧 组件健康状态")
                logger.info("-" * 40)
                for component, result in components.items():
                    status_icon = "✅" if result.get("is_active", False) else "❌"
                    score = result.get("health_score", 0)
                    logger.info(f"{component.upper()}: {status_icon} (分数: {score}/100)")
            
            # 日志分析
            if "log_analysis" in data and data["log_analysis"].get("log_analysis"):
                log_info = data["log_analysis"]["log_analysis"]
                logger.info(f"\n📝 日志分析 (最近1小时)")
                logger.info("-" * 40)
                logger.info(f"总日志行数: {log_info.get('log_lines', 0)}")
                logger.info(f"错误数: {len(log_info.get('errors', []))}")
                logger.info(f"警告数: {len(log_info.get('warnings', []))}")
                logger.info(f"错误率: {log_info.get('error_rate', 0)}%")
            
            # 告警信息
            if "alerts" in data and data["alerts"]:
                alerts = data["alerts"]
                logger.info(f"\n⚠️ 告警信息 ({len(alerts)}条)")
                logger.info("-" * 60)
                for alert in alerts:
                    severity_icon = "🔴" if alert["severity"] == "critical" else "🟡"
                    logger.info(f"{severity_icon} {alert['message']}")
            else:
                logger.info(f"\n✅ 无告警信息")
    
    def main(self):
        parser = argparse.ArgumentParser(description="安超平台监控工具")
        parser.add_argument("--env", required=True, help="环境名称")
        parser.add_argument("--status", action="store_true", help="查看平台状态")
        parser.add_argument("--log-analysis", action="store_true", help="分析平台日志")
        parser.add_argument("--resource-monitor", action="store_true", help="监控资源使用")
        parser.add_argument("--health-check", action="store_true", help="执行健康检查")
        parser.add_argument("--component-check", help="检查指定组件 (api,database,message_queue,resource_service)")
        parser.add_argument("--daily-check", action="store_true", help="执行日常检查")
        parser.add_argument("--since", type=int, default=1, help="日志分析时间范围(小时)")
        parser.add_argument("--format", choices=["json", "table"], default="table", help="输出格式")
        
        args = parser.parse_args()
        
        monitoring_nodes = self.get_monitoring_nodes(args.env)
        if not monitoring_nodes:
            logger.error(f"❌ 无法获取环境 {args.env} 的监控节点")
            return 1
        
        controller_node = next((n for n in monitoring_nodes if n["role"] == "controller"), monitoring_nodes[0])
        node_ip = controller_node["mgmt_ip"]
        
        result = None
        
        # 执行相应操作
        if args.status or args.daily_check:
            result = self.get_platform_status(args.env)
        elif args.log_analysis:
            result = self.analyze_platform_logs(node_ip, args.since)
        elif args.resource_monitor:
            result = self.get_system_resources(node_ip)
        elif args.health_check:
            result = self.check_all_components(node_ip)
        elif args.component_check:
            result = self.check_component_health(node_ip, args.component_check)
        
        if result:
            self.format_output(result, args.format)
            return 0
        else:
            logger.error("❌ 请指定要执行的操作")
            return 1

if __name__ == "__main__":
    sys.exit(PlatformMonitor().main())