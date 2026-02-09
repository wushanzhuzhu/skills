---
name: stack-tools
description: 安超平台虚拟化管理专家，提供计算节点管理、服务状态监控、虚拟机管理和存储卷操作功能
license: MIT
compatibility: opencode
metadata:
  audience: vm-admins
  workflow: virtualization-management
  version: "1.0"
  author: "OpenCode Assistant"
---

## 核心功能

### 🖥️ 计算节点管理
- **hypervisor列表**: `arcompute hypervisor-list` 显示所有计算节点信息
- **hypervisor详情**: `arcompute hypervisor-show <id>` 显示指定计算节点详细信息
- **资源监控**: CPU、内存、虚拟机数量等资源使用情况
- **节点状态**: 服务状态、启用状态、运行状态

### 🔄 服务状态监控
- **计算服务**: `arcompute service-list` 显示计算服务状态
- **服务健康**: 监控nova、neutron、cinder等服务组件
- **故障检测**: 自动识别服务异常和故障节点

### 💻 虚拟机管理
- **虚拟机列表**: `arcompute list` 显示所有虚拟机实例
- **虚拟机详情**: `arcompute show <vm-id>` 显示指定虚拟机详细信息
- **状态监控**: 虚拟机运行状态、主机分布、资源使用
- **批量操作**: 支持批量查询和管理

### 💾 存储卷管理
- **存储卷删除**: `arblock delete <volume-id>` 删除指定虚拟磁盘
- **存储信息**: 卷状态、挂载信息、容量使用
- **存储清理**: 批量清理无效或孤立的存储卷

## 使用方式

### 本地脚本执行（推荐）
```bash
# 查看所有计算节点
python .opencode/skills/stack-tools/virtualization_manager.py --env production --hypervisor-list

# 查看虚拟机列表
python .opencode/skills/stack-tools/virtualization_manager.py --env production --vm-list

# 检查服务状态
python .opencode/skills/stack-tools/virtualization_manager.py --env production --service-status

# 查看指定虚拟机详情
python .opencode/skills/stack-tools/virtualization_manager.py --env production --vm-show <vm-id>

# 删除指定存储卷
python .opencode/skills/stack-tools/virtualization_manager.py --env production --volume-delete <volume-id>

# 完整虚拟化状态检查
python .opencode/skills/stack-tools/virtualization_manager.py --env production --check-all
```

### Skill交互式使用
- 询问具体需求（节点管理/虚拟机查询/存储操作）
- 智能选择查询范围和操作类型
- 提供详细的虚拟化资源报告



## 安全配置

### OpenStack认证
- **认证方式**: 使用环境中的OpenStack客户端
- **权限要求**: 需要admin或适当的角色权限
- **安全上下文**: 在安全的认证环境中执行

### SSH认证
- **密钥文件**: `/root/myskills/SKILLS/id_rsa_cloud`
- **用户名**: `cloud` (具有OpenStack客户端权限)
- **连接方式**: RSA密钥认证

---

**开始使用：直接告诉我您需要查询或管理的虚拟化资源，我将为您提供专业的虚拟化管理服务！**