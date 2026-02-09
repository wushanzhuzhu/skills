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
实际磁盘创建脚本 - 简化版本
演示如何通过MCP Client Skill创建虚拟磁盘
"""

import sys
import json
import time
from pathlib import Path

def simple_disk_creation_example():
    """简化的磁盘创建示例"""
    
    logger.info("💾 磁盘创建实际操作示例")
    logger.info("=" * 50)
    
    logger.info("📋 在实际环境中，您需要:")
    logger.info("1. 启动MCP服务器: python main.py")
    logger.info("2. 配置environments.json文件")
    logger.info("3. 运行以下代码:")
    
    # 实际代码示例
    example_code = '''
#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from mcp_client_skill import MCPClientSkill

def create_disk_example():
    """创建磁盘的完整示例"""
    
    # 1. 创建技能实例
    skill = MCPClientSkill(env_id="production")
    
    # 2. 获取存储信息
    logger.info("🔍 获取存储资源信息...")
    resources = skill.resource_management_overview()
    
    if not resources.get('resources', {}).get('storage', {}).get('details'):
        logger.error("❌ 没有可用的存储资源")
        return
    
    storage_list = resources['resources']['storage']['details']
    logger.info(f"✅ 找到 {len(storage_list)} 个存储位置")
    
    # 选择第一个存储
    storage = storage_list[0]
    logger.info(f"📁 使用存储: {storage['stackName']}")
    
    # 3. 创建磁盘
    disk_config = {
        "storageManageId": storage['storageManageId'],
        "pageSize": "4K",
        "compression": "Disabled",
        "name": f"data-disk-{int(time.time())}",
        "size": 20,  # 20GB
        "iops": 2000,
        "bandwidth": 150,  # MB/s
        "count": 1,
        "readCache": True,
        "zoneId": storage.get('zoneId', 'default-zone')
    }
    
    logger.info(f"💾 创建磁盘: {disk_config['name']}")
    
    # 4. 执行创建
    result = skill.disk_management_operation("create", **disk_config)
    
    if result["success"]:
        logger.info("✅ 磁盘创建成功!")
        logger.info(f"   磁盘信息: {result['disk_info']}")
        return True
    else:
        logger.error(f"❌ 磁盘创建失败: {result['error']}")
        return False

if __name__ == "__main__":
    create_disk_example()
'''
    
    logger.info("📝 完整代码:")
    logger.info(example_code)
    
    logger.info("\n🎯 实际使用步骤:")
    logger.info("1. 将上述代码保存为 create_my_disk.py")
    logger.info("2. 修改 env_id 为您的环境ID")
    logger.info("3. 运行: python create_my_disk.py")
    
    logger.info("\n🔧 命令行快速使用:")
    logger.info("python mcp_client_skill.py --command interactive")
    logger.info("# 然后输入 'resources' 查看资源")
    logger.info("# 输入 'vm-create' 创建资源")

def batch_disk_creation_example():
    """批量磁盘创建示例"""
    
    logger.info("\n📦 批量磁盘创建示例")
    logger.info("=" * 50)
    
    batch_code = '''
#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from mcp_client_skill import MCPClientSkill

def batch_create_disks():
    """批量创建磁盘"""
    
    skill = MCPClientSkill(env_id="production")
    
    # 获取存储信息
    resources = skill.resource_management_overview()
    storage = resources['resources']['storage']['details'][0]
    
    # 批量配置
    disk_configs = []
    sizes = [10, 20, 30]  # 不同大小的磁盘
    
    for i, size in enumerate(sizes):
        config = {
            "storageManageId": storage['storageManageId'],
            "pageSize": "4K",
            "compression": "LZ4",
            "name": f"batch-disk-{int(time.time())}-{i+1}",
            "size": size,
            "iops": 1000 + i * 500,
            "bandwidth": 100 + i * 25,
            "count": 1,
            "readCache": True,
            "zoneId": storage.get('zoneId', 'default-zone')
        }
        disk_configs.append(config)
    
    logger.info(f"📦 准备创建 {len(disk_configs)} 个磁盘")
    
    # 批量创建
    results = []
    for i, config in enumerate(disk_configs, 1):
        logger.info(f"💾 创建第 {i}/{len(disk_configs)} 个磁盘: {config['name']}")
        
        result = skill.disk_management_operation("create", **config)
        results.append(result)
        
        if result["success"]:
            logger.info(f"   ✅ 创建成功")
        else:
            logger.info(f"   ❌ 创建失败: {result['error']}")
        
        # 避免API频率限制
        if i < len(disk_configs):
            time.sleep(2)
    
    # 统计结果
    success_count = sum(1 for r in results if r["success"])
    logger.info(f"\n📊 批量创建结果:")
    logger.info(f"   总数: {len(results)}")
    logger.info(f"   成功: {success_count}")
    logger.info(f"   失败: {len(results) - success_count}")
    logger.info(f"   成功率: {success_count/len(results)*100:.1f}%")

if __name__ == "__main__":
    batch_create_disks()
'''
    
    logger.info("📝 批量创建代码:")
    logger.info(batch_code)

def disk_management_workflow():
    """磁盘管理工作流示例"""
    
    logger.info("\n🔄 磁盘管理工作流示例")
    logger.info("=" * 50)
    
    workflow_code = '''
#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from mcp_client_skill import MCPClientSkill

def disk_management_workflow():
    """完整的磁盘管理工作流"""
    
    skill = MCPClientSkill(env_id="production")
    
    # 步骤1: 查看现有磁盘
    logger.info("🔍 步骤1: 查看现有磁盘")
    volumes_result = skill.mcp_client.call_method("get_volumes")
    
    if volumes_result.success:
        existing_disks = volumes_result.data
        logger.info(f"   当前磁盘数量: {len(existing_disks)}")
        
        # 显示前5个磁盘
        for disk in existing_disks[:5]:
            logger.info(f"   - {disk.get('name', 'unknown')}: {disk.get('size', 0)}GB")
    else:
        logger.info(f"   ❌ 获取磁盘信息失败: {volumes_result.error}")
    
    # 步骤2: 创建新磁盘
    logger.info("\\n💾 步骤2: 创建新磁盘")
    
    # 获取存储信息
    resources = skill.resource_management_overview()
    if not resources['resources']['storage']['details']:
        logger.info("   ❌ 没有可用存储")
        return
    
    storage = resources['resources']['storage']['details'][0]
    
    disk_config = {
        "storageManageId": storage['storageManageId'],
        "pageSize": "4K",
        "compression": "Disabled",
        "name": f"workflow-disk-{int(time.time())}",
        "size": 50,
        "iops": 3000,
        "bandwidth": 200,
        "count": 1,
        "readCache": True,
        "zoneId": storage.get('zoneId', 'default-zone')
    }
    
    create_result = skill.disk_management_operation("create", **disk_config)
    
    if create_result["success"]:
        logger.info("   ✅ 磁盘创建成功")
        disk_info = create_result['disk_info']
        
        # 步骤3: 验证创建结果
        logger.info("\\n✅ 步骤3: 验证创建结果")
        
        # 重新获取磁盘列表
        new_volumes_result = skill.mcp_client.call_method("get_volumes")
        if new_volumes_result.success:
            new_disks = new_volumes_result.data
            logger.info(f"   更新后磁盘数量: {len(new_disks)}")
            
            # 查找新创建的磁盘
            found = False
            for disk in new_disks:
                if disk.get('name') == disk_config['name']:
                    logger.info(f"   ✅ 找到新磁盘: {disk}")
                    found = True
                    break
            
            if not found:
                logger.info("   ⚠️ 未找到新创建的磁盘（可能需要等待同步）")
        else:
            logger.info(f"   ❌ 验证失败: {new_volumes_result.error}")
        
        # 步骤4: 清理（可选）
        logger.info("\\n🗑️  步骤4: 清理示例（可选）")
        logger.info("   如需删除磁盘，使用:")
        logger.info(f"   skill.disk_management_operation('delete', disk_ids=['{disk_info.get('diskId', '')}')")
        
    else:
        logger.info(f"   ❌ 磁盘创建失败: {create_result['error']}")

if __name__ == "__main__":
    disk_management_workflow()
'''
    
    logger.info("📝 完整工作流代码:")
    logger.info(workflow_code)

def main():
    """主函数"""
    logger.info("🎯 MCP Client Skill 磁盘创建实际使用指南")
    logger.info("=" * 70)
    
    logger.info("📚 本指南包含:")
    logger.info("✅ 单个磁盘创建")
    logger.info("✅ 批量磁盘创建") 
    logger.info("✅ 完整工作流程")
    logger.info("✅ 实际可用代码")
    
    # 单个磁盘创建示例
    simple_disk_creation_example()
    
    # 批量创建示例
    batch_disk_creation_example()
    
    # 工作流示例
    disk_management_workflow()
    
    logger.info("\n🎯 关键要点:")
    logger.info("1. 📋 确保MCP服务器运行: python main.py")
    logger.info("2. 🔧 配置environments.json环境信息")
    logger.info("3. 🔍 先获取资源信息再进行操作")
    logger.info("4. 💾 使用正确的存储ID和区域ID")
    logger.info("5. ⚡ 批量操作时注意API频率限制")
    
    logger.info("\n🚀 现在您可以:")
    logger.info("1. 复制上述代码到您的项目中")
    logger.info("2. 修改环境配置和参数")
    logger.info("3. 运行代码创建磁盘")
    logger.info("4. 使用交互模式快速操作")

if __name__ == "__main__":
    main()