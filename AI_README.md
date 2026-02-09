# AI参考文档索引

本目录包含为AI助手优化的结构化文档，便于快速理解和操作项目。

## 核心文档

### [VM_Architecture_Guide.md](./VM_Architecture_Guide.md)
**虚拟机创建架构和前提条件** - 完整的系统架构说明，包括：
- 创建VM的前提条件
- 组件关系图和依赖关系
- API调用流程
- 最佳实践建议

## 关键代码模块

### 虚拟机管理
- **vm_manager.py** - 智能VM管理器，支持环境选择、模板配置、批量创建
- **batch_vm_creator.py** - 批量VM创建脚本，支持多种创建模式
- **Instances.py** - VM实例管理，创建、查询、删除操作

### 资源管理
- **volumes.py** - 虚拟磁盘管理，创建、查询、删除
- **Images.py** - 镜像管理，列表查询、上传操作
- **Hosts.py** - 主机和存储管理，获取zoneId、storageManageId等

### 工具和配置
- **config.py** - 项目配置文件，包含默认值和常量
- **env_manager.py** - 环境管理，多环境配置和切换
- **utils/audit.py** - 认证和会话管理

## 快速参考

### 创建VM的核心步骤
1. **认证**：ArcherAudit.setSession()
2. **获取区域**：Hosts.listHost() → zoneId
3. **获取存储**：Hosts.getStorsbyDiskType() → storageManageId, diskType
4. **获取镜像**：Images.getImagebystorageManageId() → imageId
5. **创建VM**：Instances.createInstance_noNet() → VM实例

### 关键ID关系
```
clusterId → zoneId → storageManageId → diskType → 虚拟磁盘
                          ↓
                      imageId → VM实例
```

### 验证要点
- 存储管理ID存在性 (vm_manager.py:231-246)
- 镜像ID存在性
- 资源配额充足性
- 架构兼容性 (Hosts.py:61-84)

## 使用示例

### 虚拟机创建
```bash
# 交互式创建VM
python vm_manager.py create web_server 3

# 快速批量创建
python batch_vm_creator.py quick basic 5 production

# 场景化创建
python batch_vm_creator.py scenario

# 从配置文件创建
python batch_vm_creator.py config vm_config.json
```

### 虚拟磁盘创建
```bash
# 统一磁盘创建器（推荐 - 支持环境选择）
python unified_disk_creator.py create --size 10
python unified_disk_creator.py create --size 20 --use-case performance --env production
python unified_disk_creator.py batch
python unified_disk_creator.py env-list

# 传统磁盘创建器（注意：部分脚本缺少环境选择）
python env_disk_creator.py create 10 standard production  # 有环境选择
python create_10g_disk.py                                  # 硬编码环境
python create_disk.py                                      # 硬编码环境
```

## 重要提醒

### 环境选择问题
项目中的磁盘创建脚本存在环境选择不一致的问题：

- ✅ **推荐使用**：`unified_disk_creator.py` - 完整的环境选择功能
- ✅ **有环境选择**：`env_disk_creator.py` - 交互式环境选择
- ⚠️ **硬编码环境**：`create_10g_disk.py`, `create_disk.py` - 需要修改代码才能切换环境
- ⚠️ **需要传参**：`smart_disk_creator.py` - 需要在初始化时传入环境信息

### AI助手使用提示

当需要处理此项目时，请：
1. 首先阅读VM_Architecture_Guide.md了解整体架构
2. **优先使用统一磁盘创建器**：`unified_disk_creator.py`
3. 避免使用硬编码环境的脚本，除非明确环境地址
4. 根据具体需求查看对应的代码模块
5. 遵循已有的代码风格和命名规范
6. 使用配置文件中的默认值和常量
7. 确保所有API调用都有适当的错误处理
8. **询问用户目标环境**，不要假设使用默认环境

---

*最后更新：2026-02-02*