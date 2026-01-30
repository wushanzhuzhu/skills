from .database_tools import register_database_tools

def register_all_tools(mcp):
    """注册所有工具函数"""
    register_database_tools(mcp) 