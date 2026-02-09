# 虚拟机创建架构和前提条件

## 创建虚拟机的前提条件

### 1. 基础环境要求
- **安超平台连接**：有效的用户名、密码和API地址
- **认证会话**：通过ArcherAudit建立认证会话
- **网络连通性**：能够访问安超平台的API端点

### 2. 存储资源要求
- **存储管理ID**：有效的storageManageId
- **区域ID**：zoneId必须匹配存储所在区域
- **磁盘类型**：diskType需与存储后端兼容
- **存储容量**：足够的存储空间用于创建虚拟磁盘

### 3. 镜像要求
- **有效镜像ID**：imageId必须存在且可用
- **镜像格式兼容**：支持ISO、QCOW2、RAW等格式
- **架构匹配**：镜像架构需与主机架构一致（x86/ARM）

### 4. 资源配额要求
- **CPU资源**：足够的CPU核心数
- **内存资源**：足够的内存容量
- **许可证**：有效的平台许可证

## 组件关系图

```
集群 (clusterId)
├── 区域 (zoneId)
│   ├── 存储池 (storageManageId)
│   │   ├── 存储后端 (storageBackend)
│   │   └── 磁盘类型 (diskType)
│   │       └── 虚拟磁盘 (虚拟磁盘ID)
│   ├── 镜像 (imageId)
│   │   └── 存储关联 (storageManageId)
│   └── 主机 (Host)
│       └── 虚拟机 (VM实例)
│           ├── 系统磁盘 (基于镜像)
│           ├── 数据磁盘 (独立创建)
│           └── 网络接口 (可选)
```

## 核心关系说明

1. **集群ID → 区域ID**：集群包含多个区域，区域是资源隔离的基本单位

2. **区域ID → 存储管理ID**：每个区域内有多个存储池，存储管理ID标识具体存储池

3. **存储管理ID + 镜像ID**：镜像必须存储在特定存储池中，创建VM时两者需匹配

4. **存储管理ID + 磁盘类型ID → 虚拟磁盘**：虚拟磁盘创建依赖特定的存储池和磁盘类型

5. **虚拟机 → 虚拟磁盘**：VM可以挂载系统磁盘（基于镜像）和数据磁盘（独立创建）

## 关键验证点

- 存储管理ID存在性验证 (vm_manager.py:231-246)
- 镜像ID存在性验证  
- 资源配额充足性验证
- 架构兼容性验证 (Hosts.py:61-84)

## 相关代码文件

- **VM创建管理**：vm_manager.py, batch_vm_creator.py
- **存储管理**：volumes.py, Hosts.py
- **镜像管理**：Images.py
- **实例管理**：Instances.py
- **配置管理**：config.py, env_manager.py

## API调用流程

1. **认证**：ArcherAudit.setSession()
2. **获取区域信息**：Hosts.listHost() -> zoneId
3. **获取存储信息**：Hosts.getStorsbyDiskType() -> storageManageId, diskType
4. **获取镜像列表**：Images.getImagebystorageManageId() -> imageId
5. **创建虚拟磁盘**：Volumes.createDisk_vstor() -> 虚拟磁盘ID
6. **创建虚拟机**：Instances.createInstance_noNet() -> VM实例ID

## 最佳实践建议

1. **资源预检**：在创建VM前验证所有依赖资源是否存在
2. **错误处理**：实现完善的错误捕获和重试机制
3. **资源清理**：提供资源删除和清理功能
4. **配置模板**：使用预定义配置模板简化创建流程
5. **批量操作**：支持批量创建和状态跟踪

这个架构遵循了典型的云平台资源层次结构，确保资源隔离和管理灵活性。