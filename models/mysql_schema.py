from mcp.server.fastmcp import FastMCP
from typing import Dict, List, Optional
import json

class DatabaseSchemaManager:
    """数据库模式管理器"""
    
    def __init__(self):
        self.mcp = FastMCP(name="xu_resource_assistant")
        self._schemas = {}
        self._initialize_schemas()
    
    def _initialize_schemas(self):
        """初始化数据库表结构定义"""
        self._schemas = {
            "virtual_machine": self._get_virtual_machine_schema(),
            "virtual_disk": self._get_virtual_disk_schema(),  # 示例其他表
        }
    
    def _get_virtual_machine_schema(self) -> Dict:
        """获取虚拟机表结构定义"""
        return {
            "table_name": "virtual_machine",
            "description": "虚拟机表,它属于xu_resource数据库",
            "columns": [
                {"name": "id", "type": "varchar(128)", "nullable": False, "key": "PRI", "default": None},
                {"name": "ref", "type": "varchar(64)", "nullable": True, "key": "MUL", "default": None},
                {"name": "name", "type": "varchar(256)", "nullable": True, "key": "", "default": None},
                {"name": "source", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "description", "type": "varchar(255)", "nullable": True, "key": "", "default": None},
                {"name": "host_id", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "image_id", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "flavor_id", "type": "varchar(128)", "nullable": False, "key": "", "default": None},
                {"name": "cluster_id", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "user_name", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "password", "type": "varchar(256)", "nullable": True, "key": "", "default": None},
                {"name": "status", "type": "varchar(128)", "nullable": False, "key": "", "default": None},
                {"name": "task_status", "type": "varchar(128)", "nullable": False, "key": "", "default": "NONE"},
                {"name": "create_time", "type": "datetime", "nullable": False, "key": "", "default": "current_timestamp()"},
                {"name": "update_time", "type": "datetime", "nullable": False, "key": "", "default": "current_timestamp()"},
                {"name": "create_user_id", "type": "varchar(128)", "nullable": False, "key": "", "default": None},
                {"name": "run_time", "type": "bigint(20)", "nullable": True, "key": "", "default": None},
                {"name": "hot_resize", "type": "smallint(6)", "nullable": True, "key": "", "default": None},
                {"name": "usb_ref", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "zone_id", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "cpu_host_resize", "type": "tinyint(4)", "nullable": True, "key": "", "default": 0},
                {"name": "memory_host_resize", "type": "tinyint(4)", "nullable": True, "key": "", "default": 0},
                {"name": "type", "type": "varchar(16)", "nullable": True, "key": "", "default": None},
                {"name": "is_new", "type": "tinyint(4)", "nullable": True, "key": "", "default": 1},
                {"name": "createvm_type", "type": "varchar(32)", "nullable": True, "key": "", "default": None},
                {"name": "pay_type", "type": "varchar(16)", "nullable": True, "key": "", "default": None},
                {"name": "product_status", "type": "varchar(256)", "nullable": True, "key": "", "default": None},
                {"name": "virtual_machine_snapshot_id", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "image_iso_id", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "os", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "is_agent_alive", "type": "smallint(6)", "nullable": True, "key": "", "default": None},
                {"name": "is_in_recycle_bin", "type": "tinyint(4)", "nullable": True, "key": "", "default": 0},
                {"name": "delete_time", "type": "datetime", "nullable": True, "key": "", "default": None},
                {"name": "arstor_status", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "storage_type", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "priority", "type": "smallint(6)", "nullable": True, "key": "", "default": None},
                {"name": "is_restorable", "type": "tinyint(4)", "nullable": True, "key": "", "default": 0},
                {"name": "aggregate_id", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "gpu_count", "type": "tinyint(255)", "nullable": True, "key": "", "default": None},
                {"name": "instance_name", "type": "varchar(64)", "nullable": True, "key": "", "default": None},
                {"name": "policy_id", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "cpu_limit_enabled", "type": "tinyint(4)", "nullable": True, "key": "", "default": None},
                {"name": "cpu_limit", "type": "double(6,2)", "nullable": True, "key": "", "default": None},
                {"name": "cpu_share", "type": "int(11)", "nullable": True, "key": "", "default": None},
                {"name": "cpu_share_level", "type": "varchar(64)", "nullable": True, "key": "", "default": None},
                {"name": "storage_manage_id", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "is_mem_monopoly", "type": "tinyint(4)", "nullable": True, "key": "", "default": None},
                {"name": "compatibility_mode", "type": "tinyint(4)", "nullable": True, "key": "", "default": None},
                {"name": "backup_id", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "locked", "type": "tinyint(4)", "nullable": True, "key": "", "default": None},
                {"name": "root_vm_id", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "server_hostname", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "hw_firmware_type", "type": "varchar(20)", "nullable": True, "key": "", "default": None},
                {"name": "video_model", "type": "varchar(32)", "nullable": True, "key": "", "default": None},
                {"name": "ha_level", "type": "varchar(64)", "nullable": True, "key": "", "default": None},
                {"name": "ft_status", "type": "varchar(64)", "nullable": True, "key": "", "default": None},
                {"name": "vm_ha_enable", "type": "smallint(6)", "nullable": True, "key": "", "default": None},
                {"name": "is_open_agent", "type": "tinyint(4)", "nullable": True, "key": "", "default": None},
                {"name": "start_delay_time", "type": "smallint(5) unsigned", "nullable": True, "key": "", "default": None},
                {"name": "stop_delay_time", "type": "int(4)", "nullable": True, "key": "", "default": None},
                {"name": "start_order", "type": "int(4)", "nullable": True, "key": "", "default": None},
                {"name": "cpu_mode", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "qga_os", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "usb_controller", "type": "tinyint(4)", "nullable": True, "key": "", "default": None},
                {"name": "multi_queue_enabled", "type": "smallint(6)", "nullable": True, "key": "", "default": None},
                {"name": "cpu_model", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "clone_type", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "clock", "type": "varchar(16)", "nullable": True, "key": "", "default": None},
                {"name": "balloon_switch", "type": "smallint(2)", "nullable": True, "key": "", "default": None},
                {"name": "balloon_level", "type": "smallint(6)", "nullable": True, "key": "", "default": None},
                {"name": "cpu_qos_down", "type": "tinyint(1)", "nullable": True, "key": "", "default": None},
                {"name": "release_status", "type": "varchar(32)", "nullable": True, "key": "", "default": None},
                {"name": "vm_faultcheck_enable", "type": "smallint(6)", "nullable": True, "key": "", "default": None},
                {"name": "vmtools_version", "type": "varchar(32)", "nullable": True, "key": "", "default": None},
                {"name": "batch_num", "type": "bigint(20)", "nullable": True, "key": "", "default": None},
                {"name": "protect_enable", "type": "smallint(6)", "nullable": True, "key": "", "default": 0},
                {"name": "kubernetes_source", "type": "smallint(6)", "nullable": True, "key": "", "default": None},
                {"name": "bus_type", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "display_number", "type": "int(11)", "nullable": True, "key": "", "default": None},
                {"name": "in_recycle_bin_source", "type": "varchar(32)", "nullable": True, "key": "", "default": None},
                {"name": "is_enable_vnc", "type": "smallint(6)", "nullable": True, "key": "", "default": None},
                {"name": "audio_type", "type": "varchar(32)", "nullable": True, "key": "", "default": None},
                {"name": "vnc_pwd", "type": "varchar(256)", "nullable": True, "key": "", "default": None},
                {"name": "boot_order", "type": "varchar(100)", "nullable": True, "key": "", "default": None},
                {"name": "irq_enable", "type": "varchar(100)", "nullable": True, "key": "", "default": None},
                {"name": "tool_id", "type": "varchar(128)", "nullable": True, "key": "", "default": None},
                {"name": "is_template", "type": "smallint(6)", "nullable": True, "key": "", "default": 0},
                {"name": "template_enabled", "type": "smallint(6)", "nullable": True, "key": "", "default": 1},
                {"name": "template_vm_id", "type": "varchar(100)", "nullable": True, "key": "", "default": None},
                {"name": "temp_cpu", "type": "bigint(20)", "nullable": True, "key": "", "default": None},
                {"name": "temp_memory", "type": "bigint(20)", "nullable": True, "key": "", "default": None},
                {"name": "temp_socket", "type": "bigint(20)", "nullable": True, "key": "", "default": None},
                {"name": "device_bus_type", "type": "varchar(64)", "nullable": True, "key": "", "default": "virtio"},
                {"name": "temp_numa_enable", "type": "smallint(6)", "nullable": True, "key": "", "default": None},
                {"name": "temp_numa_node_nums", "type": "int(11)", "nullable": True, "key": "", "default": None},
                {"name": "temp_numa_bond", "type": "varchar(32)", "nullable": True, "key": "", "default": None},
                {"name": "immediate", "type": "smallint(6)", "nullable": True, "key": "", "default": None},
                {"name": "exact_clock", "type": "smallint(6)", "nullable": True, "key": "", "default": None},
                {"name": "kvm_hidden", "type": "smallint(6)", "nullable": True, "key": "", "default": None},
                {"name": "hyperv", "type": "smallint(6)", "nullable": True, "key": "", "default": None},
                {"name": "dynamic", "type": "tinyint(4)", "nullable": True, "key": "", "default": None},
                {"name": "dynamic_gpu", "type": "varchar(32)", "nullable": True, "key": "", "default": None},
                {"name": "dynamic_vgpu", "type": "varchar(32)", "nullable": True, "key": "", "default": None},
                {"name": "vtpm_enable", "type": "tinyint(4)", "nullable": True, "key": "", "default": None},
                {"name": "encrypt", "type": "smallint(6)", "nullable": True, "key": "", "default": 0},
                {"name": "nic_type", "type": "varchar(32)", "nullable": True, "key": "", "default": None},
                {"name": "usb_type", "type": "varchar(32)", "nullable": True, "key": "", "default": None},
                {"name": "temp_balloon_switch", "type": "smallint(6)", "nullable": True, "key": "", "default": None},
                {"name": "cpu_set", "type": "varchar(512)", "nullable": True, "key": "", "default": None},
                {"name": "old_host_id", "type": "varchar(64)", "nullable": True, "key": "", "default": None},
            ]
        }
    
    def _get_virtual_disk_schema(self) -> Dict:
        """获取虚拟磁盘表结构定义"""
        return {
            "table_name": "virtual_disk",
            "description": "虚拟磁盘表",
            "columns": [
                {"name": "id", "type": "varchar(128)", "nullable": False, "key": "PRI", "default": None},
                {"name": "vm_id", "type": "varchar(128)", "nullable": True, "key": "MUL", "default": None},
                {"name": "disk_name", "type": "varchar(256)", "nullable": True, "key": "", "default": None},
                {"name": "size_gb", "type": "int", "nullable": True, "key": "", "default": 0},
                {"name": "status", "type": "varchar(64)", "nullable": True, "key": "", "default": "available"},
                {"name": "create_time", "type": "datetime", "nullable": False, "key": "", "default": "current_timestamp()"},
                {"name": "update_time", "type": "datetime", "nullable": False, "key": "", "default": "current_timestamp()"},
            ]
        }
    
    def get_schema(self, table_name: str) -> Optional[Dict]:
        """获取指定表的结构定义"""
        return self._schemas.get(table_name)
    
    def get_all_schemas(self) -> Dict[str, Dict]:
        """获取所有表的结构定义"""
        return self._schemas.copy()
    
    def add_schema(self, table_name: str, schema: Dict):
        """添加新的表结构定义"""
        self._schemas[table_name] = schema
    
    def get_table_markdown(self, table_name: str) -> str:
        """获取表结构的Markdown格式"""
        schema = self.get_schema(table_name)
        if not schema:
            return f"表 '{table_name}' 不存在"
        
        markdown = f"# {schema['description']}\n\n"
        markdown += f"## 表: {table_name}\n"
        markdown += "| 字段名 | 类型 | 允许空 | 键 | 默认值 | 额外信息 |\n"
        markdown += "|-------|------|--------|----|--------|----------|\n"
        
        for col in schema['columns']:
            name = col['name']
            col_type = col['type']
            nullable = "YES" if col['nullable'] else "NO"
            key = col['key'] if col['key'] else ""
            default = str(col['default']) if col['default'] is not None else "NULL"
            extra = ""
            
            markdown += f"| {name} | {col_type} | {nullable} | {key} | {default} | {extra} |\n"
        
        return markdown
    
    def register_resources(self):
        """注册MCP资源"""
        for table_name, schema in self._schemas.items():
            @self.mcp.resource(
                f"doc://db/schema/{table_name}",
                mime_type="text/markdown",
                title=f"{table_name} 数据库表结构",
                description=f"包含{table_name}表完整字段定义"
            )
            def get_schema_doc(table=table_name):
                return self.get_table_markdown(table)
        
        return self.mcp

# 全局实例
db_schema_manager = DatabaseSchemaManager()