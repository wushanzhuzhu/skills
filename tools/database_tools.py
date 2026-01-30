from mcp.server.fastmcp import FastMCP
import models.mysql_schema as mysql_schema

# 数据库工具,获取数据库表结构定义
dba=mysql_schema.db_schema_manager

def register_database_tools(mcp: FastMCP):
    @mcp.tool()
    def get_db_schema(table_name: str = "virtual_machine") -> str:
        """
        获取数据库表结构定义
        :param table_name: 表名，默认为virtual_machine
        :return: 表结构的Markdown格式描述
        """
        return dba.get_table_markdown(table_name)
    
    @mcp.tool()
    def list_db_tables() -> list:
        """
        列出所有可用的数据库表
        :return: 表名列表
        """
        return list(dba.get_all_schemas().keys())
    
    @mcp.tool()
    def get_column_info(table_name: str, column_name: str) -> dict:
        """
        获取指定表中某一列的信息
        :param table_name: 表名
        :param column_name: 列名
        :return: 列信息字典
        """
        schema = dba.get_schema(table_name)
        if not schema:
            return {"error": f"表 '{table_name}' 不存在"}
        
        for col in schema['columns']:
            if col['name'] == column_name:
                return col
        
        return {"error": f"列 '{column_name}' 在表 '{table_name}' 中不存在"}
    
    @mcp.tool()
    def search_columns_by_type(data_type: str) -> list:
        """
        根据数据类型搜索所有匹配的列
        :param data_type: 数据类型，如 'varchar(128)', 'datetime' 等
        :return: 匹配的列信息列表
        """
        results = []
        all_schemas = dba.get_all_schemas()
        
        for table_name, schema in all_schemas.items():
            for col in schema['columns']:
                if data_type.lower() in col['type'].lower():
                    results.append({
                        "table": table_name,
                        "column": col['name'],
                        "type": col['type'],
                        "nullable": col['nullable'],
                        "key": col['key'],
                        "default": col['default']
                    })
        
        return results
    
    return get_db_schema, list_db_tables, get_column_info, search_columns_by_type