# 🚀 MCP Client Skill - 实际使用完整指南

## 🎯 快速开始

### 方法1: 命令行直接使用

```bash
# 1. 进入技能目录
cd /root/myskills/wushanskills/.opencode/skills/mcp-client-skill

# 2. 查看可用命令和帮助
python mcp_client_skill.py --command info

# 3. 检查系统状态
python mcp_client_skill.py --command health

# 4. 查看资源信息
python mcp_client_skill.py --command resources

# 5. 进入交互模式（推荐）
python mcp_client_skill.py --command interactive
```

### 方法2: Python代码使用

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from mcp_client_skill import MCPClientSkill

# 创建技能实例
skill = MCPClientSkill(env_id="production")

# 创建虚拟磁盘
disk_config = {
    "storageManageId": "your-storage-id",
    "pageSize": "4K", 
    "compression": "Disabled",
    "name": f"my-disk-{int(time.time())}",
    "size": 20,  # 20GB
    "iops": 2000,
    "bandwidth": 150,
    "count": 1,
    "readCache": True,
    "zoneId": "your-zone-id"
}

result = skill.disk_management_operation("create", **disk_config)

if result["success"]:
    print(f"✅ 磁盘创建成功! ID: {result['disk_info']}")
else:
    print(f"❌ 磁盘创建失败: {result['error']}")
```

## 📋 环境配置

### 1. 启动MCP服务器

```bash
cd /root/myskills/wushanskills
python main.py
```

### 2. 配置环境文件

创建 `environments.json`:

```json
{
  "environments": {
    "production": {
      "url": "https://your-archeros-platform.com",
      "username": "admin",
      "password": "your-password", 
      "description": "生产环境"
    },
    "test": {
      "url": "https://test-platform.com",
      "username": "admin", 
      "password": "test-password",
      "description": "测试环境"
    }
  }
}
```

## 🎯 实际使用场景

### 场景1: 创建单个虚拟磁盘

```python
from mcp_client_skill import MCPClientSkill

skill = MCPClientSkill(env_id="production")

# 获取可用存储
resources = skill.resource_management_overview()
storage = resources['resources']['storage']['details'][0]

# 创建磁盘
disk_config = {
    "storageManageId": storage['storageManageId'],
    "pageSize": "4K",
    "compression": "LZ4",
    "name": f"data-disk-{int(time.time())}",
    "size": 50,
    "iops": 3000,
    "bandwidth": 200,
    "count": 1,
    "readCache": True,
    "zoneId": storage.get('zoneId', 'default-zone')
}

result = skill.disk_management_operation("create", **disk_config)
print(f"创建结果: {result['success']}")
```

### 场景2: 批量创建虚拟机

```python
from mcp_client_skill import MCPClientSkill

skill = MCPClientSkill(env_id="production")

# VM基础配置
vm_config = {
    "name": "web-server",
    "hostname": "web-01",
    "videoModel": "virtio",
    "storname": "basic-replica2",
    "cpu": 2,
    "memory": 4,
    "size": 40,
    "haEnable": True
}

# 批量创建3个VM
result = skill.smart_vm_creation(vm_config, count=3)

print(f"创建成功: {result['successful_creations']}/{result['total_requested']}")
print(f"成功率: {result['success_rate']}%")

# 查看创建的VM
for vm in result['creation_results']:
    if vm['success']:
        print(f"✅ {vm['name']}: {vm['vm_id']}")
    else:
        print(f"❌ {vm['name']}: {vm['error']}")
```

### 场景3: 系统健康检查和报告

```python
from mcp_client_skill import MCPClientSkill
import json
import time

skill = MCPClientSkill()

# 系统健康检查
health_report = skill.system_health_check()

# 资源概览
resources = skill.resource_management_overview()

# 生成综合报告
report = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "system_health": {
        "status": health_report['overall_status'],
        "issues": health_report['issues'],
        "components": health_report['component_status']
    },
    "resources": {
        "storage_locations": resources['resources']['storage']['total_locations'],
        "available_images": resources['resources']['images']['total_images'],
        "total_instances": resources['resources']['instances']['total_instances'],
        "total_volumes": resources['resources']['volumes']['total_volumes']
    }
}

print(f"系统状态: {report['system_health']['status']}")
print(f"存储位置: {report['resources']['storage_locations']}")
print(f"可用镜像: {report['resources']['available_images']}")
print(f"虚拟机: {report['resources']['total_instances']}")
print(f"磁盘: {report['resources']['total_volumes']}")

# 保存报告
with open(f"system_report_{int(time.time())}.json", 'w') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
```

## 🔧 交互模式使用

```bash
python mcp_client_skill.py --command interactive
```

交互模式中的常用命令：

```
> help                    # 查看帮助
> health                  # 系统健康检查
> resources               # 资源概览
> info                    # MCP客户端信息
> vm-create                # 交互式创建虚拟机
> quit                    # 退出
```

## 🛠️ 常见问题解决

### 问题1: "无法导入MCP模块"

**原因**: MCP服务器未运行或路径问题
**解决**:
```bash
cd /root/myskills/wushanskills
python main.py  # 启动MCP服务器
```

### 问题2: "环境配置不存在"

**原因**: environments.json文件不存在或配置错误
**解决**:
```bash
# 检查配置文件
ls -la environments.json

# 创建或修复配置文件
cat > environments.json << EOF
{
  "environments": {
    "production": {
      "url": "https://your-platform.com",
      "username": "admin", 
      "password": "your-password"
    }
  }
}
EOF
```

### 问题3: "存储位置不存在"

**原因**: 使用了不存在的存储名称
**解决**:
```python
# 先获取可用存储
resources = skill.resource_management_overview()
storage_list = resources['resources']['storage']['details']

# 使用实际的存储名称
for storage in storage_list:
    print(f"可用存储: {storage['stackName']}")
```

## 📊 高级功能

### 1. 自定义错误处理

```python
from mcp_client_skill import MCPClientSkill
from utils.error_handler import ErrorHandler

skill = MCPClientSkill()
error_handler = ErrorHandler()

# 执行带错误处理的操作
def safe_operation():
    try:
        result = skill.disk_management_operation("create", **disk_config)
        return result
    except Exception as e:
        return error_handler.handle_error(e, {"operation": "disk_creation"})

result = safe_operation()
```

### 2. 批量操作控制

```python
import time

def batch_disk_creation(disk_configs, delay=2):
    """批量创建磁盘，控制频率"""
    skill = MCPClientSkill()
    results = []
    
    for i, config in enumerate(disk_configs, 1):
        print(f"创建第 {i}/{len(disk_configs)} 个磁盘")
        
        result = skill.disk_management_operation("create", **config)
        results.append(result)
        
        # 避免API频率限制
        if i < len(disk_configs):
            time.sleep(delay)
    
    return results
```

### 3. 资源验证

```python
def validate_resources_before_operation():
    """操作前验证资源可用性"""
    skill = MCPClientSkill()
    
    # 检查系统状态
    health = skill.system_health_check()
    if health['overall_status'] != 'healthy':
        print("⚠️ 系统状态不健康，建议检查后再操作")
        return False
    
    # 检查资源
    resources = skill.resource_management_overview()
    
    if resources['resources']['storage']['total_locations'] == 0:
        print("❌ 没有可用存储位置")
        return False
    
    if resources['resources']['images']['total_images'] == 0:
        print("❌ 没有可用镜像")
        return False
    
    print("✅ 资源验证通过")
    return True
```

## 🎯 最佳实践

1. **操作前检查**: 每次重要操作前执行健康检查
2. **资源验证**: 获取并验证资源ID后再使用
3. **错误处理**: 检查所有返回结果并处理错误
4. **批量控制**: 大批量操作时控制并发和频率
5. **日志记录**: 保存操作日志用于审计和调试

## 🚀 现在开始使用

1. **准备环境**: 启动MCP服务器，配置环境文件
2. **选择方式**: 命令行或Python代码
3. **验证资源**: 获取可用资源信息
4. **执行操作**: 创建VM、磁盘等资源
5. **监控结果**: 检查操作结果和系统状态

**恭喜！您现在可以使用MCP Client Skill管理您的安超平台资源了！** 🎉