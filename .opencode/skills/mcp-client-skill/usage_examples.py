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
MCP Client Skill 磁盘创建示例
演示如何使用skill调用MCP方法创建虚拟磁盘
"""

import sys
import json
import time
from pathlib import Path

# 添加主项目路径
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

def example_create_disk():
    """演示创建虚拟磁盘的完整流程"""
    
    logger.info("🚀 MCP Client Skill 磁盘创建示例")
    logger.info("=" * 60)
    
    # 1. 导入技能
    try:
        from mcp_client_skill import MCPClientSkill
        logger.info("✅ 成功导入MCPClientSkill")
    except Exception as e:
        logger.error(f"❌ 导入失败: {e}")
        return
    
    # 2. 创建技能实例
    skill = MCPClientSkill(auto_session=True)
    
    # 3. 获取可用资源信息
    logger.info("\n📊 第一步：获取存储资源信息...")
    try:
        resource_result = skill.resource_management_overview()
        
        if isinstance(resource_result, dict) and 'resources' in resource_result:
            storage_info = resource_result['resources'].get('storage', {})
            logger.info(f"📁 存储位置数量: {storage_info.get('total_locations', 0)}")
            
            if storage_info.get('details'):
                logger.info("🗂️  可用存储位置:")
                for i, storage in enumerate(storage_info['details'][:3], 1):
                    logger.info(f"   {i}. {storage.get('stackName', 'unknown')} - {storage.get('storageBackend', 'unknown')}")
        else:
            logger.info("⚠️ 无法获取存储信息，使用默认配置")
            
    except Exception as e:
        logger.warning(f"⚠️ 获取资源信息失败: {e}")
        logger.info("💡 继续使用示例配置...")
    
    # 4. 演示磁盘创建参数
    logger.info("\n💾 第二步：准备磁盘创建参数...")
    
    # 磁盘配置示例
    disk_config = {
        "storageManageId": "demo-storage-id",  # 实际使用时需要从存储信息中获取
        "pageSize": "4K",
        "compression": "Disabled", 
        "name": f"mcp-demo-disk-{int(time.time())}",
        "size": 10,  # 10GB
        "iops": 1000,
        "bandwidth": 100,  # MB/s
        "count": 1,
        "readCache": True,
        "zoneId": "demo-zone-id"
    }
    
    logger.info("📋 磁盘创建配置:")
    for key, value in disk_config.items():
        logger.info(f"   {key}: {value}")
    
    # 5. 执行磁盘创建
    logger.info("\n🔧 第三步：执行磁盘创建...")
    try:
        # 使用磁盘管理功能
        creation_result = skill.disk_management_operation("create", **disk_config)
        
        logger.info(f"📊 磁盘创建结果:")
        logger.info(json.dumps(creation_result, indent=2, ensure_ascii=False))
        
        if creation_result.get('success'):
            logger.info("✅ 磁盘创建成功！")
        else:
            logger.error(f"❌ 磁盘创建失败: {creation_result.get('error')}")
            
    except Exception as e:
        logger.error(f"❌ 磁盘创建异常: {e}")
        logger.info("💡 这可能是因为:")
        logger.info("   1. MCP服务器未运行")
        logger.info("   2. 会话未建立")
        logger.info("   3. 存储ID或区域ID不存在")
    
    # 6. 演示批量创建
    logger.info("\n📦 第四步：演示批量磁盘创建配置...")
    
    batch_configs = []
    for i in range(3):
        config = disk_config.copy()
        config['name'] = f"batch-disk-{int(time.time())}-{i+1}"
        config['size'] = 5 + i * 5  # 5GB, 10GB, 15GB
        batch_configs.append(config)
    
    logger.info("📋 批量创建配置:")
    for i, config in enumerate(batch_configs, 1):
        logger.info(f"   磁盘{i}: {config['name']} ({config['size']}GB)")
    
    logger.info("\n💡 批量创建代码示例:")
    logger.info("```python")
    logger.info("# 批量创建磁盘")
    logger.info("results = []")
    logger.info("for config in batch_configs:")
    logger.info("    result = skill.disk_management_operation('create', **config)")
    logger.info("    results.append(result)")
    logger.info("    time.sleep(2)  # 避免API频率限制")
    logger.info("```")

def example_vm_creation():
    """演示虚拟机创建"""
    logger.info("\n🖥️  虚拟机创建示例")
    logger.info("=" * 60)
    
    # VM配置示例
    vm_config = {
        "name": "demo-vm",
        "hostname": "demo-vm",
        "videoModel": "virtio",
        "storname": "basic-replica2",  # 默认存储位置
        "cpu": 2,
        "memory": 4,
        "size": 40,
        "haEnable": True,
        "priority": 1
    }
    
    logger.info("📋 虚拟机配置:")
    for key, value in vm_config.items():
        logger.info(f"   {key}: {value}")
    
    logger.info("\n💡 创建单个VM代码:")
    logger.info("```python")
    logger.info("from mcp_client_skill import MCPClientSkill")
    logger.info("")
    logger.info("# 创建技能实例")
    logger.info("skill = MCPClientSkill()")
    logger.info("")
    logger.info("# 创建单个虚拟机")
    logger.info("result = skill.smart_vm_creation(vm_config, count=1)")
    logger.info("logger.info(result)")
    logger.info("```")
    
    logger.info("\n💡 批量创建VM代码:")
    logger.info("```python")
    logger.info("# 批量创建3个虚拟机")
    logger.info("result = skill.smart_vm_creation(vm_config, count=3)")
    logger.info("logger.info(f'成功创建: {result[\"successful_creations\"]}/{result[\"total_requested\"]}')")
    logger.info("```")

def main():
    """主函数"""
    logger.info("🎮 MCP Client Skill 实际使用指南")
    logger.info("=" * 80)
    
    logger.info("\n📚 本示例包含:")
    logger.info("1. 磁盘创建演示")
    logger.info("2. 虚拟机创建示例") 
    logger.info("3. 实际代码模板")
    logger.info("4. 常见问题解决")
    
    # 磁盘创建示例
    example_create_disk()
    
    # VM创建示例
    example_vm_creation()
    
    # 实际使用建议
    logger.info("\n🎯 实际使用建议:")
    logger.info("=" * 30)
    logger.info("1. 📋 预先检查环境:")
    logger.info("   - 确保MCP服务器运行在8080端口")
    logger.info("   - 配置environments.json文件")
    logger.info("   - 验证存储和镜像可用性")
    logger.info("")
    logger.info("2. 🔧 使用交互模式:")
    logger.info("   python mcp_client_skill.py --command interactive")
    logger.info("")
    logger.info("3. 📊 系统状态检查:")
    logger.info("   python mcp_client_skill.py --command health")
    logger.info("")
    logger.info("4. 📁 资源概览:")
    logger.info("   python mcp_client_skill.py --command resources")
    logger.info("")
    logger.info("5. 💻 Python代码集成:")
    logger.info("   from mcp_client_skill import MCPClientSkill")
    logger.info("   skill = MCPClientSkill(env_id='production')")
    logger.info("   result = skill.smart_vm_creation(config, count=5)")
    logger.info("")
    
    logger.info("🚀 开始使用MCP Client Skill吧！")

if __name__ == "__main__":
    main()