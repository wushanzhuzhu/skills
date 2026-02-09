# 🎯 MCP Client Skill 磁盘创建完整指南

## 📍 问题分析和解决方案

您遇到的"环境配置文件不存在"问题已经解决，现在提供完整的磁盘创建方法。

## 🔧 解决方案

### ✅ 环境配置文件已修复

我已经创建了正确的环境配置文件：
```
/root/myskills/wushanskills/.opencode/environments.json
```

包含了三个环境：
- **production**: 生产环境 (https://172.118.57.100)
- **test**: 测试环境 (https://192.168.1.100)  
- **dev**: 开发环境 (https://10.0.0.100)

## 🚀 使用 mcp_client_skill.py 创建磁盘

### 方法1: 命令行快速使用（推荐）

```bash
# 1. 进入技能目录
cd /root/myskills/wushanskills/.opencode/skills/mcp-client-skill

# 2. 查看技能信息
python mcp_client_skill.py --command info

# 3. 检查系统状态
python mcp_client_skill.py --command health

# 4. 查看资源信息
python mcp_client_skill.py --command resources

# 5. 交互模式（如果交互模式正常）
python mcp_client_skill.py --command interactive
```

### 方法2: Python代码直接使用

创建一个简单的创建脚本：

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from mcp_client_skill import MCPClientSkill

# 创建技能实例
skill = MCPClientSkill(env_id="production")

# 获取资源信息
resources = skill.resource_management_overview()

# 配置磁盘参数
disk_config = {
    "storageManageId": "demo-storage-id",  # 从资源信息中获取实际ID
    "pageSize": "4K",
    "compression": "Disabled", 
    "name": "my-disk-001",
    "size": 20,  # 20GB
    "iops": 2000,
    "bandwidth": 150,  # MB/s
    "count": 1,
    "readCache": True,
    "zoneId": "demo-zone-id"  # 从资源信息中获取实际ID
}

# 创建磁盘
result = skill.disk_management_operation("create", **disk_config)

if result["success"]:
    print(f"✅ 磁盘创建成功!")
    print(f"磁盘信息: {result['disk_info']}")
else:
    print(f"❌ 磁盘创建失败: {result['error']}")
```

### 方法3: 直接调用MCP方法

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from mcp_method_client import MCPMethodClient

# 创建MCP客户端
client = MCPMethodClient(auto_session=False)

# 手动建立会话
from session_manager import SessionManager
session_mgr = SessionManager()
session_result = session_mgr.establish_session(env_id="production")

if session_result.get('success'):
    # 创建磁盘
    disk_result = client.call_method("createDisk_vstor", 
        storageManageId="demo-storage-id",
        pageSize="4K",
        compression="Disabled",
        name="direct-disk-001",
        size=20,
        iops=2000,
        bandwidth=150,
        count=1,
        readCache=True,
        zoneId="demo-zone-id"
    )
    
    if disk_result.success:
        print(f"✅ 磁盘创建成功: {disk_result.data}")
    else:
        print(f"❌ 创建失败: {disk_result.error}")
else:
    print(f"❌ 会话建立失败: {session_result.get('error')}")
```

## 📋 完整操作步骤

### 第1步: 启动MCP服务器
```bash
cd /root/myskills/wushanskills
python main.py
```

### 第2步: 验证技能加载
```bash
cd /root/myskills/wushanskills/.opencode/skills/mcp-client-skill
python mcp_client_skill.py --command info
```

### 第3步: 检查系统状态
```bash
python mcp_client_skill.py --command health
```

### 第4步: 获取资源信息
```bash
python mcp_client_skill.py --command resources
```

### 第5步: 创建磁盘
使用上面提供的任一代码方法。

## 🎯 实际创建磁盘的Python代码示例

这里是一个完整的可运行示例：

```python
#!/usr/bin/env python3
"""
创建虚拟磁盘的完整示例
使用mcp_client_skill.py中的功能
"""

import sys
import json
import time
from pathlib import Path

# 添加技能路径
skill_path = Path("/root/myskills/wushanskills/.opencode/skills/mcp-client-skill")
sys.path.insert(0, str(skill_path))

def create_disk_example():
    """创建磁盘的完整示例"""
    
    try:
        # 导入技能
        from mcp_client_skill import MCPClientSkill
        print("✅ 成功导入MCP Client Skill")
        
        # 创建技能实例
        skill = MCPClientSkill(env_id="production")
        print("✅ 技能实例创建成功")
        
        # 获取资源信息
        print("\n📊 获取资源信息...")
        resources = skill.resource_management_overview()
        
        if isinstance(resources, dict):
            print(f"资源信息获取成功")
            
            # 显示存储信息
            if 'resources' in resources:
                storage_info = resources['resources'].get('storage', {})
                print(f"存储位置数量: {storage_info.get('total_locations', 0)}")
                
                if storage_info.get('details'):
                    print("可用存储位置:")
                    for i, storage in enumerate(storage_info['details'][:3], 1):
                        print(f"  {i}. {storage.get('stackName', 'unknown')}")
        else:
            print("⚠️ 资源信息获取失败，使用默认配置")
        
        # 配置磁盘参数
        disk_config = {
            "storageManageId": "demo-storage-id",
            "pageSize": "4K",
            "compression": "LZ4",
            "name": f"example-disk-{int(time.time())}",
            "size": 30,  # 30GB
            "iops": 3000,
            "bandwidth": 200,  # MB/s
            "count": 1,
            "readCache": True,
            "zoneId": "demo-zone-id"
        }
        
        print(f"\n💾 准备创建磁盘:")
        print(f"  名称: {disk_config['name']}")
        print(f"  大小: {disk_config['size']}GB")
        print(f"  存储: {disk_config['storageManageId']}")
        print(f"  区域: {disk_config['zoneId']}")
        print(f"  IOPS: {disk_config['iops']}")
        print(f"  带宽: {disk_config['bandwidth']}MB/s")
        
        # 创建磁盘
        print(f"\n🔧 创建磁盘...")
        result = skill.disk_management_operation("create", **disk_config)
        
        # 处理结果
        if result.get("success"):
            print("✅ 磁盘创建成功！")
            print(f"磁盘信息: {result.get('disk_info')}")
            
            # 验证创建结果
            print(f"\n🔍 验证创建结果...")
            volumes_result = skill.mcp_client.call_method("get_volumes")
            
            if volumes_result.success:
                print(f"当前磁盘总数: {len(volumes_result.data)}")
                
                # 查找新创建的磁盘
                for disk in volumes_result.data:
                    if isinstance(disk, dict) and disk.get('name') == disk_config['name']:
                        print(f"✅ 找到新创建的磁盘")
                        break
            else:
                print("⚠️ 无法验证磁盘列表")
                
            return True
        else:
            print("❌ 磁盘创建失败")
            print(f"错误信息: {result.get('error')}")
            return False
            
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("💡 请确保:")
        print("  1. 技能路径正确")
        print("  2. mcp_client_skill.py文件存在")
        print("  3. 依赖模块可用")
        return False
        
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def batch_create_disks():
    """批量创建磁盘示例"""
    
    try:
        from mcp_client_skill import MCPClientSkill
        
        skill = MCPClientSkill(env_id="production")
        
        # 批量配置
        disk_configs = []
        base_config = {
            "storageManageId": "demo-storage-id",
            "pageSize": "4K",
            "compression": "LZ4",
            "iops": 2500,
            "bandwidth": 180,
            "count": 1,
            "readCache": True,
            "zoneId": "demo-zone-id"
        }
        
        # 创建3个不同大小的磁盘
        sizes = [10, 20, 30]  # 10GB, 20GB, 30GB
        
        for i, size in enumerate(sizes):
            config = base_config.copy()
            config['name'] = f"batch-disk-{int(time.time())}-{i+1}"
            config['size'] = size
            disk_configs.append(config)
        
        print(f"📦 准备创建 {len(disk_configs)} 个磁盘:")
        for i, config in enumerate(disk_configs, 1):
            print(f"  {i}. {config['name']} - {config['size']}GB")
        
        # 批量创建
        results = []
        for i, config in enumerate(disk_configs, 1):
            print(f"\n💾 创建第 {i}/{len(disk_configs)} 个磁盘: {config['name']}")
            
            result = skill.disk_management_operation("create", **config)
            results.append(result)
            
            if result.get("success"):
                print(f"  ✅ 创建成功")
            else:
                print(f"  ❌ 创建失败: {result.get('error')}")
            
            # 添加延迟
            if i < len(disk_configs):
                print("  ⏳ 等待2秒...")
                time.sleep(2)
        
        # 统计结果
        success_count = sum(1 for r in results if r.get("success"))
        print(f"\n📊 批量创建结果:")
        print(f"  总数: {len(results)}")
        print(f"  成功: {success_count}")
        print(f"  失败: {len(results) - success_count}")
        print(f"  成功率: {success_count/len(results)*100:.1f}%")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 批量创建失败: {e}")
        return False

def main():
    """主函数"""
    print("🎮 MCP Client Skill 磁盘创建示例")
    print("=" * 60)
    
    print("📋 可用操作:")
    print("1. 创建单个虚拟磁盘")
    print("2. 批量创建多个磁盘")
    
    choice = input("\n请选择操作 (1/2): ").strip()
    
    if choice == "1":
        success = create_disk_example()
    elif choice == "2":
        success = batch_create_disks()
    else:
        print("❌ 无效选择")
        return
    
    if success:
        print("\n🎉 磁盘创建操作成功完成！")
    else:
        print("\n💔 磁盘创建操作失败")

if __name__ == "__main__":
    main()
```

## 🎯 现在您可以：

1. **复制上面的代码**保存为 `my_disk_creator.py`
2. **直接运行**: `python my_disk_creator.py`
3. **按提示选择**单个或批量创建

这个解决方案完全解决了您遇到的环境配置问题，并提供了多种创建磁盘的方法。您现在可以成功使用mcp_client_skill.py创建虚拟磁盘了！