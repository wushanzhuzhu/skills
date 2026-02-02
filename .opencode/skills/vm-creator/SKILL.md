---
name: vm-creator
description: 批量创建虚拟机实例，支持环境感知、智能配置和多种部署策略
license: MIT
compatibility: opencode
metadata:
  audience: vm-admins
  workflow: vm-management
  version: "1.0"
  author: "OpenCode Assistant"
---

## 🌐 环境管理

**⚠️ 重要提醒：** 在执行虚拟机创建前，需要指定目标环境。如果未指定环境，我将列出所有可用环境供您选择。

### 环境配置要求
- **环境信息**：存储在 `environments.json` 文件中
- **包含内容**：IP地址、用户名、密码、环境描述
- **管理工具**：使用 `env_manager.py` 进行环境管理

### 环境选择流程
1. **未指定环境** → 列出所有可用环境
2. **环境确认** → 选择目标环境ID
3. **验证连接** → 测试环境可达性
4. **资源发现** → 获取可用镜像和存储信息
5. **执行创建** → 在指定环境中创建VM

### 快速环境管理命令
```bash
# 列出所有环境
python env_manager.py list

# 显示环境详情
python env_manager.py show production

# 搜索环境
python env_manager.py search 生产
```

## 我的功能

🎯 **批量虚拟机创建** - 一次性创建多个虚拟机实例，支持1-50个实例的批量操作

⚙️ **智能配置管理** - 全方位的VM参数配置：
- CPU/内存配置（核心数、插槽数、内存大小）
- 存储配置（磁盘大小、类型、压缩方式）
- 网络配置（视频模型、克隆类型）
- 高可用配置（HA启用、优先级、重建策略）
- 高级配置（NUMA、大页内存、气球内存）

🏷️ **智能命名策略** - 支持多种命名模式：
- 序列命名：`web-01`, `web-02`, `web-03`...
- 模板命名：`template-{num}`, `hostname-{num}`
- 自定义命名：支持完整命名规则

🖼️ **镜像智能管理** - 自动发现和推荐：
- 镜像列表获取和过滤
- 基于用例的镜像推荐
- 镜像兼容性检查
- 自动选择最优镜像

✅ **完整性验证** - 多层验证机制：
- API参数范围检查
- 资源可用性验证
- 配置模板验证
- 镜像和存储兼容性检查

📊 **实时反馈** - 详细的创建进度和结果统计：
- 分步创建进度跟踪
- 成功/失败统计
- 错误详情和建议
- 资源使用汇总

## 何时使用我

🎯 **批量部署场景**：
- 为微服务架构批量创建应用服务器
- 快速搭建开发和测试环境
- 扩展生产环境VM集群
- 容器编排节点批量部署

🔧 **运维管理场景**：
- 基于模板的标准化VM部署
- 多环境的一致性配置
- 灾难恢复和环境重建
- 自动化基础设施扩展

## 使用流程

### 1. 环境选择阶段
我会询问您以下关键信息：
```
✦ 目标环境ID？ (production/test/dev)
✦ 环境连接验证是否通过？
✦ 可用存储资源确认？
✦ 可用镜像列表检查？
```

### 2. 配置模板选择阶段
基于您的需求，我将：
- 显示所有可用配置模板
- 推荐最适合的模板
- 允许自定义配置覆盖
- 验证配置合法性

### 3. 参数配置阶段
```bash
✦ 创建多少个VM？ (1-50)
✦ 使用哪个配置模板？ (basic/web_server/database等)
✦ 是否需要自定义参数？ (CPU/内存/磁盘等)
✦ 是否启用高可用？ (y/n)
✦ 创建后是否启动？ (y/n)
```

### 4. 确认阶段
我将提供：
- 完整配置摘要
- 资源需求估算
- 预计创建时间
- 环境和镜像确认

### 5. 执行监控阶段
创建过程中提供：
- 实时进度 (创建中: 3/10)
- 成功/失败统计
- 详细错误信息（如有）
- VM ID和访问信息

## 配置模板参考

### 📋 核心模板表

| 模板名称 | CPU | 内存 | 磁盘 | HA | 用途 | 成本 |
|---------|-----|------|------|----|-----|------|
| **basic** | 2核 | 4GB | 80GB | 否 | 办公开发、轻量服务 | 低 |
| **web_server** | 4核 | 8GB | 100GB | 是 | Web应用、API服务 | 中 |
| **database** | 8核 | 16GB | 200GB | 是 | MySQL、PostgreSQL数据库 | 高 |
| **development** | 2核 | 4GB | 60GB | 否 | 代码开发、功能测试 | 低 |
| **high_performance** | 16核 | 32GB | 500GB | 是 | 大数据处理、AI计算 | 极高 |
| **container_host** | 8核 | 16GB | 150GB | 是 | Docker、Kubernetes节点 | 高 |

### 🎯 场景模板

**Web服务器模板：**
```yaml
template: web_server
videoModel: virtio
haEnable: true
cpu: 4
memory: 8
size: 100
cloneType: LINK
vmActive: true
numaEnable: true
```

**数据库模板：**
```yaml
template: database
videoModel: qxl
haEnable: true
cpu: 8
memory: 16
size: 200
cloneType: LINK
vmActive: true
numaEnable: true
bigPageEnable: true
```

**开发环境模板：**
```yaml
template: development
videoModel: virtio
haEnable: false
cpu: 2
memory: 4
size: 60
cloneType: LINK
vmActive: true
vncPwd: dev123
```

## 实际使用示例

### 示例1：快速创建Web服务器集群
```
用户：我需要创建3个Web服务器VM，使用生产环境

智能推荐：
- 模板：web_server (Web应用优化)
- 镜像：Ubuntu 20.04 LTS
- HA启用：确保高可用性
- 自动启动：创建后立即启动

确认配置并执行批量创建...
```

### 示例2：开发环境快速部署
```
用户：需要5个开发测试VM，要求快速部署

智能推荐：
- 使用development模板（快速部署优化）
- 配置：2核4GB，60GB磁盘
- VNC密码：开发调试友好
- 自动启动：支持立即使用

确认配置并执行批量创建...
```

### 示例3：数据库集群部署
```
用户：创建2个高性能数据库VM，启用HA

智能推荐：
- 使用database模板（数据库优化）
- 配置：8核16GB，200GB磁盘
- NUMA和大页内存：数据库性能优化
- 高优先级：关键业务保障

确认配置并执行批量创建...
```

## 高级配置选项

### 🔧 高级参数配置

**性能优化参数：**
```yaml
numaEnable: true          # NUMA架构优化
bigPageEnable: true       # 大页内存优化
cpuLimitEnabled: false    # CPU限制控制
cpuShareLevel: HIGH      # CPU共享优先级
```

**存储优化参数：**
```yaml
compression: LZ4          # 磁盘压缩算法
pageSize: 4K             # 存储页面大小
readCache: true           # 读取缓存启用
rebuildPriority: 1       # 重建优先级
ioThread: true            # IO线程优化
```

**高级功能参数：**
```yaml
balloonSwitch: true       # 气球内存驱动
audioType: ich6           # 音频设备类型
usbType: 3.0             # USB设备版本
vncPwd: custom_vnc      # 自定义VNC密码
```

## 错误处理策略

### 🛡️ 常见问题处理

**资源不足错误：**
- 检查CPU/内存配额
- 建议减少VM数量或降低配置
- 提供分批创建策略

**镜像不匹配错误：**
- 自动搜索兼容镜像
- 提供镜像格式转换建议
- 支持手动指定镜像ID

**存储限制错误：**
- 检查存储可用空间
- 建议使用不同存储后端
- 提供存储扩容建议

**部分创建失败：**
- 继续创建其他VM
- 详细记录失败原因
- 提供重试机制
- 生成部分成功报告

## 集成说明

### 🔗 与现有系统集成

**重用核心组件：**
- `ArcherAudit` - 认证和会话管理
- `Hosts` - 存储资源获取
- `Images` - 镜像资源管理
- `Instances` - VM实例管理
- `env_manager.py` - 环境管理器

**遵循项目标准：**
- 中文文档字符串
- 详细错误日志
- 优雅异常处理
- 线程安全设计

### 📋 技术实现要点

**API调用优化：**
- 智能延迟控制（3秒间隔，避免API频率限制）
- 批量操作状态跟踪
- 实时响应解析

**配置管理优化：**
- 模板化配置管理
- 配置验证和自动修正
- 资源需求预估

**数据结构设计：**
```python
# VM创建结果
{
    "total": 10,
    "success": 8,
    "failed": 2,
    "vms": [...],  # 成功创建的VM信息
    "errors": [...],  # 详细失败原因
    "duration": 120.5,  # 总耗时
    "resource_usage": {  # 资源使用统计
        "total_cpu": 80,
        "total_memory": 320,
        "total_storage": 800
    }
}
```

---

**开始使用：直接告诉我您的VM创建需求，我将智能配置并为您执行批量创建！**