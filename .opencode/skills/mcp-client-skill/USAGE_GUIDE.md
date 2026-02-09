# 🚀 MCP Client Skill 实际使用指南

## 📋 概述

MCP Client Skill 是一个**Skill驱动、MCP支撑**的智能客户端，允许您通过调用MCP Server的方法来管理安超平台资源。

## 🎯 使用场景示例

### 场景1: 创建虚拟磁盘

#### 📋 方法1: 命令行使用

```bash
# 进入技能目录
cd /root/myskills/wushanskills/.opencode/skills/mcp-client-skill

# 查看使用示例
python usage_examples.py
```

#### 📋 方法2: Python代码使用

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from mcp_client_skill import MCPClientSkill

# 1. 创建技能实例
skill = MCPClientSkill(env_id="production")

# 2. 准备磁盘配置
disk_config = {
    "storageManageId": "your-storage-id",  # 从资源信息中获取
    "pageSize": "4K",
    "compression": "Disabled",
    "name": "my-disk-001",
    "size": 10,  # GB
    "iops": 1000,
    "bandwidth": 100,  # MB/s
    "count": 1,
    "readCache": True,
    "zoneId": "your-zone-id"  # 从资源信息中获取
}

# 3. 创建磁盘
result = skill.disk_management_operation("create", **disk_config)

if result["success"]:
    print(f"✅ 磁盘创建成功!")
    print(f"磁盘ID: {result['disk_info']}")
else:
    print(f"❌ 磁盘创建失败: {result['error']}")
```

#### 📋 方法3: 交互式使用

```bash
# 进入交互模式
python mcp_client_skill.py --command interactive

# 在交互模式中输入:
> help              # 查看帮助
> resources         # 查看资源信息
> vm-create         # 交互式创建虚拟机
```

### 场景2: 创建虚拟机

```python
from mcp_client_skill import MCPClientSkill

# 创建技能实例
skill = MCPClientSkill(env_id="production")

# VM配置
vm_config = {
    "name": "web-server",
    "hostname": "web-01",
    "videoModel": "virtio",
    "storname": "basic-replica2",  # 存储位置名称
    "cpu": 4,
    "memory": 8,
    "size": 100,  # 磁盘大小(GB)
    "haEnable": True,
    "priority": 2,
    "imageId": "your-image-id"  # 镜像ID
}

# 创建单个VM
result = skill.smart_vm_creation(vm_config, count=1)
print(f"创建结果: {result['success']}")
print(f"VM ID: {result['creation_results'][0]['vm_id']}")

# 批量创建3个VM
batch_result = skill.smart_vm_creation(vm_config, count=3)
print(f"成功创建: {batch_result['successful_creations']}/{batch_result['total_requested']}")
```

### 场景3: 系统健康检查

```python
from mcp_client_skill import MCPClientSkill

skill = MCPClientSkill()

# 执行系统健康检查
health_report = skill.system_health_check()

print(f"系统状态: {health_report['overall_status']}")
print(f"检查时间: {health_report['check_time']}")

# 查看各组件状态
for component, status in health_report['component_status'].items():
    print(f"- {component}: {status['status']}")
    
if health_report['issues']:
    print("发现的问题:")
    for issue in health_report['issues']:
        print(f"  - {issue}")
```

## 🔧 实际使用步骤

### 步骤1: 环境准备

#### 1.1 启动MCP服务器
```bash
# 确保MCP服务器运行在8080端口
cd /root/myskills/wushanskills
python main.py
```

#### 1.2 配置环境信息
创建 `environments.json` 文件:
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
      "url": "https://test-archeros-platform.com", 
      "username": "admin",
      "password": "test-password",
      "description": "测试环境"
    }
  }
}
```

### 步骤2: 获取资源信息

```python
from mcp_client_skill import MCPClientSkill

skill = MCPClientSkill(env_id="production")

# 获取资源概览
resources = skill.resource_management_overview()

# 查看可用存储
storage_list = resources['resources']['storage']['details']
print("可用存储:")
for storage in storage_list:
    print(f"  - {storage['stackName']}: {storage['storageBackend']}")

# 查看可用镜像
image_list = resources['resources']['images']['details']  
print("可用镜像:")
for image in image_list[:5]:  # 显示前5个
    print(f"  - {image['imageName']}: {image['imageId']}")
```

### 步骤3: 执行实际操作

```python
# 使用实际的存储ID和镜像ID创建VM
vm_config = {
    "name": "production-web",
    "hostname": "web-01", 
    "videoModel": "virtio",
    "storname": storage_list[0]['stackName'],  # 使用第一个存储
    "imageId": image_list[0]['imageId'],       # 使用第一个镜像
    "cpu": 2,
    "memory": 4,
    "size": 50,
    "haEnable": True
}

result = skill.smart_vm_creation(vm_config, count=1)

if result["success"]:
    vm_id = result['creation_results'][0]['vm_id']
    print(f"✅ VM创建成功! ID: {vm_id}")
    
    # 可以通过MCP方法验证创建结果
    instances = skill.mcp_client.call_method("get_instances")
    print(f"当前VM数量: {len(instances.data) if instances.success else 0}")
```

## 🎯 常见操作模板

### 模板1: 磁盘管理

```python
def manage_disks():
    """磁盘管理完整流程"""
    skill = MCPClientSkill()
    
    # 1. 查看现有磁盘
    volumes_result = skill.mcp_client.call_method("get_volumes")
    if volumes_result.success:
        print(f"现有磁盘数量: {len(volumes_result.data)}")
    
    # 2. 创建新磁盘
    disk_config = {
        "storageManageId": "your-storage-id",
        "pageSize": "4K", 
        "compression": "LZ4",
        "name": f"data-disk-{int(time.time())}",
        "size": 100,
        "iops": 5000,
        "bandwidth": 200,
        "count": 1,
        "readCache": True,
        "zoneId": "your-zone-id"
    }
    
    result = skill.disk_management_operation("create", **disk_config)
    
    if result["success"]:
        print(f"✅ 磁盘创建成功: {result['disk_info']}")
        
        # 3. 如需删除磁盘
        # disk_ids = [result['disk_info']['diskId']]
        # delete_result = skill.disk_management_operation("delete", disk_ids=disk_ids)
```

### 模板2: VM批量管理

```python
def batch_vm_management():
    """批量VM管理"""
    skill = MCPClientSkill()
    
    # VM模板配置
    base_config = {
        "name": "app-server",
        "hostname": "app",
        "videoModel": "virtio", 
        "storname": "basic-replica2",
        "cpu": 2,
        "memory": 4,
        "size": 50,
        "haEnable": True
    }
    
    # 获取资源信息验证
    resources = skill.resource_management_overview()
    
    if resources['resources']['storage']['total_locations'] > 0:
        # 批量创建5个VM
        result = skill.smart_vm_creation(base_config, count=5)
        
        print(f"创建结果: {result['success']}")
        print(f"成功: {result['successful_creations']}")
        print(f"失败: {result['failed_creations']}")
        
        # 显示创建的VM信息
        for vm in result['creation_results']:
            if vm['success']:
                print(f"✅ {vm['name']}: {vm['vm_id']}")
            else:
                print(f"❌ {vm['name']}: {vm['error']}")
```

### 模板3: 系统监控

```python
def system_monitoring():
    """系统监控和报告"""
    skill = MCPClientSkill()
    
    # 1. 健康检查
    health = skill.system_health_check()
    print(f"系统状态: {health['overall_status']}")
    
    # 2. 资源统计
    resources = skill.resource_management_overview()
    print(f"存储位置: {resources['resources']['storage']['total_locations']}")
    print(f"可用镜像: {resources['resources']['images']['total_images']}")
    print(f"虚拟机: {resources['resources']['instances']['total_instances']}")
    print(f"磁盘: {resources['resources']['volumes']['total_volumes']}")
    
    # 3. 生成报告
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "health_status": health['overall_status'],
        "resource_summary": {
            "storage": resources['resources']['storage']['total_locations'],
            "images": resources['resources']['images']['total_images'], 
            "instances": resources['resources']['instances']['total_instances'],
            "volumes": resources['resources']['volumes']['total_volumes']
        },
        "issues": health['issues']
    }
    
    # 保存报告
    with open(f"system_report_{int(time.time())}.json", 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("📊 系统报告已生成")
```

## 🛠️ 故障排除

### 常见问题1: 会话建立失败
```
错误: "会话建立失败或会话不健康"
解决: 
1. 检查MCP服务器是否运行: python main.py
2. 检查网络连接和URL是否正确
3. 验证用户名和密码是否正确
```

### 常见问题2: 资源不存在
```
错误: "存储位置不存在" 或 "镜像ID不可用"
解决:
1. 先调用 resource_management_overview() 获取可用资源
2. 使用返回的实际ID和名称
3. 确认资源状态正常
```

### 常见问题3: 权限不足
```
错误: "权限不足" 或 "认证失败"
解决:
1. 检查用户权限设置
2. 确认账号有相应操作权限
3. 联系管理员分配权限
```

## 🎯 最佳实践

1. **操作前检查**: 每次操作前先执行健康检查
2. **资源验证**: 获取并验证资源ID后再使用
3. **批量控制**: 大批量操作时控制并发数量
4. **错误处理**: 检查返回结果并处理错误
5. **日志记录**: 保存操作日志用于审计

## 🚀 开始使用

```bash
# 1. 进入技能目录
cd /root/myskills/wushanskills/.opencode/skills/mcp-client-skill

# 2. 查看可用命令
python mcp_client_skill.py --command info

# 3. 检查系统状态
python mcp_client_skill.py --command health

# 4. 进入交互模式
python mcp_client_skill.py --command interactive
```

现在您可以开始使用MCP Client Skill管理您的安超平台资源了！