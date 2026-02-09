---
name: node-tools
description: 安超平台宿主机管理专家，提供系统信息查看、IPMI管理、节点清单和批量操作功能
license: MIT
compatibility: opencode
metadata:
  audience: system-admins
  workflow: host-management
  version: "1.0"
  author: "OpenCode Assistant"
---

## 核心功能

### 🔍 系统信息查看
- **平台信息**: `cat /etc/system-info` 显示安超平台版本和系统信息
- **节点识别**: 自动识别所有管理节点和存储节点
- **硬件信息**: CPU、内存、磁盘等硬件配置

### 🌐 IPMI管理
- **IPMI地址获取**: `ipmitool -I open lan print 1` 获取节点IPMI IP
- **电源控制**: 
  - `ipmitool -H <ip> -I lanplus -U root -P Admin@123 power on` 远程开机
  - `ipmitool -H <ip> -I lanplus -U root -P Admin@123 power off` 远程关机
  - `ipmitool -H <ip> -I lanplus -U root -P Admin@123 chassis status` 电源状态

### 📋 节点清单管理
- **管理IP列表**: 从hosts文件提取所有节点管理IP
- **IPMI账户**: 获取所有节点的IPMI账户信息
- **角色识别**: 自动识别controller、compute、storage角色

### 🔧 批量操作
- **并行执行**: 在多个节点同时执行命令
- **状态同步**: 批量检查所有节点状态
- **配置推送**: 批量应用系统配置

## 使用方式

### 本地脚本执行（推荐）
```bash
# 查看系统信息
python .opencode/skills/node-tools/host_manager.py --env production --sysinfo

# 获取所有节点IPMI地址
python .opencode/skills/node-tools/host_manager.py --env production --ipmi-list

# 检查所有节点电源状态
python .opencode/skills/node-tools/host_manager.py --env production --power-status

# 批量开机
python .opencode/skills/node-tools/host_manager.py --env production --power-on --nodes node1,node2

# 完整节点清单
python .opencode/skills/node-tools/host_manager.py --env production --inventory
```

### Skill交互式使用
- 询问具体需求（系统信息/节点管理/IPMI操作）
- 智能选择目标节点和操作类型
- 提供详细执行结果和状态报告



## 安全配置

### SSH认证
- **密钥文件**: `/root/myskills/SKILLS/id_rsa_cloud`
- **用户名**: `cloud` (具有sudo权限)
- **连接方式**: RSA密钥认证

### IPMI认证
- **默认用户**: `root`
- **默认密码**: `Admin@123`
- **连接协议**: LANplus

---

**开始使用：直接告诉我您需要查看的宿主机信息，我将为您提供专业的管理服务！**