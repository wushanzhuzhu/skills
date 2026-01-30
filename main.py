from mcp.server.fastmcp import FastMCP
from utils.audit import ArcherAudit
from utils.tools.Str import to_https_url, is_https_url, is_ip_address
from Instances import Instances
from Hosts import Hosts
from Images import Images
import threading
import time
from sshcommand import ssh_execute_command
from volumes import Volumes
from utils.tools.Str import to_ipv4_address
from Dbclient import MySQLClient
from tools import register_all_tools

# Create an MCP server
mcp = FastMCP("Demo",host="0.0.0.0", port=8080, json_response=True)
register_all_tools(mcp)

class GlobalState:
    """
    === 工具功能描述 ===
    单例模式实现全局状态管理，线程安全，支持延迟初始化。
    存储认证信息、镜像管理、主机管理、实例管理、存储管理、数据库连接等全局状态。
    
    === 上下文依赖规则 ===
    - 通过getSession方法初始化所有管理对象
    - 各工具函数通过global_state实例访问全局状态
    - 线程安全设计，支持多线程环境下的状态管理
    
    === 版本信息 ===
    v1.0（2024-01更新）：新增线程安全锁机制
    """
    _instance = None
    _lock = threading.Lock()  # 多线程场景需解锁

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.audit = None
        self.host = None
        self.image = None
        self.instances = None
        self.volumes = None
        self.db = None

# 创建单例实例（在服务器启动时初始化）
global_state = GlobalState.get_instance()

@mcp.tool()
def sshexecute_command(hostip, command, port: int=22, username:str="cloud", key_path:str="./id_rsa_cloud"):
    """
    === 工具功能描述 ===
    通过SSH密钥执行远程命令，支持sudo权限。使用非对称加密进行身份验证，通过加密隧道执行命令。
    建议将私钥文件权限设置为600（-rw-------）。
    
    === 参数说明 ===
    :param hostip (str): 远程主机IP或域名（支持IPv4/IPv6）
    :param command (str): 要执行的Shell命令（支持多行命令用分号分隔）
    :param port (int): SSH服务端口，默认22
    :param username (str): 登录用户名，默认"cloud"
    :param key_path (str): 私钥文件路径（相对当前工作目录），建议使用绝对路径避免路径解析问题，默认"./id_rsa_cloud"
    
    :return dict: 包含执行结果的字典
        - "stdout": 命令标准输出（字符串）
        - "stderr": 命令错误输出（字符串）
        - "exit_code": 命令退出状态码（整数）
    
    === 上下文依赖规则 ===
    - 依赖paramiko库实现SSH连接和命令执行
    - 执行敏感命令时建议添加超时参数（需在实现中处理）
    - 配合系统防火墙配置（如开放对应端口）
    
    === 使用示例 ===
    >>> sshexecute_command("192.168.1.10", "ls -l /var/log", 
            username="admin", key_path="/home/admin/.ssh/id_rsa")
    {"stdout": "total 1024\n...", "stderr": "", "exit_code": 0}
    
    === 异常处理 ===
    - ConnectionRefusedError: 连接超时或服务未运行
    - AuthenticationFailed: 密钥验证失败或用户无权限
    - FileNotFoundError: 私钥文件不存在或路径错误
    - PermissionError: 私钥文件权限过宽（建议600）
    
    === 关联命令 ===
    安超平台底层(archeros,也可以简称平台，云管，上层，环境等)常用命令行参考：
        宿主机层面：
            cat/etc/system-info  显示安超平台(archeros)系统信息
            /var/log/haihe/resource/resource.log 云管平台的资源服务日志位置
            ipmitool -I open lan print 1 | awk '/IP Address[[:space:]]*:[[:space:]]*/ {print $NF}' 显示宿主机的IPMI IP地址，这里面的参数1是固定的，调用时不要当做是节点编号
            cat  /usr/local/cloudos-lcm_libs/CloudOs/inventory/hosts |grep  ipmi_ip 显示所有节点的IPMI IP地址列表
            cat  /usr/local/cloudos-lcm_libs/CloudOs/inventory/hosts |grep  ansible_host 显示所有节点的管理IP地址列表
            cat  /usr/local/cloudos-lcm_libs/CloudOs/inventory/hosts  |grep  ipmi_ 显示所有节点的IPMI帐号密码列表
            ipmitool -H ip -I lanplus -U root -P Admin@123 power on 通过IPMI远程开机，参数根据实际情况修改,-H 后的ip替换成实际IP地址,帐号密码参考下面说明
            ipmitool -H ip -I lanplus -U root -P Admin@123 power off 通过IPMI远程关机，参数根据实际情况修改,-H 后的ip替换成实际IP地址,帐号密码参考下面说明
            ipmitool -H ip -I lanplus -U root -P Admin@123 chassis status 通过IPMI查看电源状态，参数根据实际情况修改 ,-H 后的ip替换成实际IP地址,帐号密码参考下面说明
        存储集群/服务层面(别名vstor存储，arstor存储)：
            docker exec -it mxsp  zklist -c 显示arstor存储的zookeeper集群信息
            docker exec -it mxsp  showInodes --stale 显示arstor存储有没有不可访问的盘，返回空是没有，有内容则表示有不可访问的盘
            docker exec -it mxsp  mxServices -n 5 -L 显示节点5的磁盘占用情况，其中节点5是存储节点ID，可以通过命令docker exec -it mxsp  zklist -c查看
        stack 层面，也是虚拟化层面的命令行，基于openstack（无须进入容器，直接在节点执行）：
            arcompute hypervisor-list 显示虚拟化节点列表，包括节点ID、名称、State（服务状态）、Status(是否被禁用)
            arcompute  hypervisor-show 3 显示ID为3的计算节点详细信息，包括cpu超分比，虚拟化下内存使用情况，3是计算节点ID，可以通过hypervisor-list查看，执行前需要确认该节点存在
            arcompute service-list 显示计算服务列表，包括服务类型、主机名、状态等信息
            arcompute  list 显示所有虚拟机实例列表，包括ID、名称、状态等信息
            arcompute  show <vm-id> 显示指定虚拟机实例的详细信息，<vm-id>替换为实际的虚拟机ID，例如arcompute show 12345678-1234-1234-1234-1234567890ab
            arblock delete <volume-id> 删除指定的虚拟磁盘，<volume-id>替换为实际的磁盘ID，例如arblock delete 87654321-4321-4321-4321-ba0987654321
        以上命令需要使用有权限的用户登录，例如cloud用户，且该用户需要有sudo权限 
    
    === 版本信息 ===
    v1.0（2024-01更新）：新增IPMI远程开机/关机/状态查询支持
    """
    print("sshexecute_command input:", hostip, port, username, key_path, command)
    rs = ssh_execute_command(hostip, port, username, key_path, command)
    print("sshexecute_command rs:", rs)
    return rs

@mcp.tool()
def get_audit() -> tuple:
    """
    === 工具功能描述 ===
    获取当前安超平台交互权限的详细信息，包括平台地址、用户名、密码、认证token等。
    
    === 参数说明 ===
    无参数，依赖全局状态中的audit对象
    
    :return tuple: 包含交互权限信息的元组
        - base_url: 平台基础URL
        - username: 用户名
        - password: 
        - auth_token: 认证token
    
    === 上下文依赖规则 ===
    - 必须先调用getSession方法初始化audit对象
    - 返回信息包含认证所需的全部凭证
    
    === 使用示例 ===
    >>> get_audit()
    ("https://archeros.example.com", "admin", "Admin@123", "auth_token_value", "https://archeros.example.com")
    
    === 异常处理 ===
    - 未初始化时返回提示信息："当前会话中未保存交互权限信息，请先调用getSession方法获取安超平台的交互会话."
    
    === 关联工具 ===
    - 必须与getSession配合使用
    
    === 版本信息 ===
    v1.0（2024-01更新）：新增token信息返回
    """
    return global_state.audit.base_url, global_state.audit.username, global_state.audit.password, global_state.audit.auth_token, global_state.audit.base_url if global_state.audit else "当前会话中未保存交互权限信息，请先调用getSession方法获取安超平台的交互会话."

@mcp.tool()
def get_clusterStor() -> tuple:
    """
    === 工具功能描述 ===
    获取当前安超平台集群的相关信息，包括区域ID、集群ID、存储信息等。
    
    === 参数说明 ===
    无参数，依赖全局状态中的host对象
    
    :return tuple: 包含主机信息的元组
        - zoneId: 区域ID
        - clusterId: 集群ID
        - storageInfo: 存储信息
    
    === 上下文依赖规则 ===
    - 必须先调用getSession方法初始化host对象
    
    === 使用示例 ===
    >>> get_clusterStor()
    ("zoneId_value", "clusterId_value", "storageInfo_value")
    
    === 异常处理 ===
    - 未初始化时返回提示信息："当前会话中未保存主机信息，请先调用getSession方法获取安超平台的交互会话."
    
    === 关联工具 ===
    - 必须与getSession配合使用
    
    === 版本信息 ===
    v1.0（2024-01更新）：新增存储信息返回
    """
    return global_state.host.zone, global_state.host.clusterId, global_state.host.storageInfo if global_state.host else "当前会话中未保存主机信息，请先调用getSession方法获取安超平台的交互会话."

@mcp.tool()
def get_image() -> list:
    """
    === 工具功能描述 ===
    获取当前安超平台镜像相关信息，包括镜像列表等。
    
    === 参数说明 ===
    无参数，依赖全局状态中的image对象
    
    :return list: 包含镜像信息的列表，元素为字典
        - imageId: 镜像ID
        - imageName: 镜像名称
        - storageManageId: 存储管理ID
    
    === 上下文依赖规则 ===
    - 必须先调用getSession方法初始化image对象
    
    === 使用示例 ===
    >>> get_image()
    [{"imageId": "id1", "imageName": "name1", "storageManageId": "smid1"}, ...]
    
    === 异常处理 ===
    - 未初始化时返回提示信息："当前会话中未保存镜像信息，请先调用getSession方法获取安超平台的交互会话."
    
    === 关联工具 ===
    - 必须与getSession配合使用
    
    === 版本信息 ===
    v1.0（2024-01更新）：新增镜像信息返回
    """
    return global_state.image.images if global_state.image else "当前会话中未保存镜像信息，请先调用getSession方法获取安超平台的交互会话."

@mcp.tool()
def get_instances():
    """
    === 工具功能描述 ===
    获取当前会话下创建的虚拟机实例信息。
    
    === 参数说明 ===
    无参数，依赖全局状态中的instances对象
    
    :return list: 虚拟机实例信息列表
    
    === 上下文依赖规则 ===
    - 必须先调用getSession方法初始化instances对象
    
    === 使用示例 ===
    >>> get_instances()
    [{"instanceId": "id1", "name": "vm1", ...}, ...]
    
    === 异常处理 ===
    - 未初始化时返回提示信息："当前会话中未保存虚拟机实例信息，请先调用getSession方法获取安超平台的交互会话."
    
    === 关联工具 ===
    - 必须与getSession配合使用
    
    === 版本信息 ===
    v1.0（2024-01更新）：新增实例信息返回
    """
    return global_state.instances.instances if global_state.instances else "当前会话中未保存虚拟机实例信息，请先调用getSession方法获取安超平台的交互会话."

@mcp.tool()
def get_volumes():
    """
    === 工具功能描述 ===
    获取当前会话下创建的虚拟磁盘信息。
    
    === 参数说明 ===
    无参数，依赖全局状态中的volumes对象
    
    :return list: 虚拟磁盘信息列表
    
    === 上下文依赖规则 ===
    - 必须先调用getSession方法初始化volumes对象
    
    === 使用示例 ===
    >>> get_volumes()
    [{"diskId": "disk1", "size": 100, ...}, ...]
    
    === 异常处理 ===
    - 未初始化时返回提示信息："当前会话中未保存虚拟磁盘信息，请先调用getSession方法获取安超平台的交互会话."
    
    === 关联工具 ===
    - 必须与getSession配合使用
    
    === 版本信息 ===
    v1.0（2024-01更新）：新增磁盘信息返回
    """
    return global_state.volumes.disks if global_state.volumes else "当前会话中未保存虚拟磁盘信息，请先调用getSession方法获取安超平台的交互会话."

@mcp.tool()
def getSession(url: str,name: str="admin", password: str="") -> str:
    """
    === 工具功能描述 ===
    安超平台交互session获取工具
    建立/获取与安超平台的交互会话session，获取API操作权限。必须先调用此方法才能和安超平台进行交互。
    支持IP地址和HTTPS URL两种格式输入，自动转换为标准HTTPS URL。
    
    === 参数说明 ===
    :param url (str): 安超平台基础地址（支持IP地址或HTTPS URL格式）
    :param name (str): 平台用户名，默认"admin"
    :param password (str): 平台密码，默认"Admin@123"
    
    :return str: 会话建立结果说明
        - 成功："成功获取了安超平台的交互会话.并初始化平台上下文"
        - 失败："未能正确获取到安超平台交互会话，请检查平台地址是否正确."
    
    === 上下文依赖规则 ===
    - 自动初始化以下全局状态对象：
        global_state.audit: 认证信息
        global_state.image: 镜像管理
        global_state.host: 主机管理
        global_state.instances: 实例管理
        global_state.volumes: 存储管理
        global_state.db: 数据库连接
    
    === 使用示例 ===
    >>> getSession("172.118.13.100", "admin", "Admin@123")
    "成功获取了安超平台的交互会话.并初始化平台上下文"
    
    >>> getSession("https://archeros.example.com", "admin", "Admin@123")
    "成功获取了安超平台的交互会话.并初始化平台上下文"
    
    === 异常处理 ===
    - 地址格式错误："请提供正确的安超平台地址，格式应为IP地址或HTTPS URL格式。"
    - 认证失败：返回原始认证错误信息
    - 初始化失败：返回具体组件初始化失败信息
    
    === 关联工具 ===
    - 必须优先调用此方法后才能使用：
        createInstance_noNet, createDisk_vstor, getImagebystorageManageId 等
    
    === 版本信息 ===
    v2.0（2024-01更新）：新增MySQL数据库连接初始化支持
    """
    if is_ip_address(url):
        url = to_https_url(url)
    elif not is_https_url(url):
        return "请提供正确的安超平台地址，格式应为IP地址或HTTPS URL格式。"
    global_state.audit = ArcherAudit(name, password, url)
    global_state.image = Images(global_state.audit.username, global_state.audit.password, global_state.audit.base_url, global_state.audit)
    global_state.host = Hosts(global_state.audit.username, global_state.audit.password, global_state.audit.base_url, global_state.audit)
    global_state.instances = Instances(global_state.audit.username, global_state.audit.password, global_state.audit.base_url, global_state.audit)
    global_state.volumes = Volumes(global_state.audit, global_state.host)
    ipv4_address = to_ipv4_address(url)
    try:
        Dba = MySQLClient(ipv4_address, "root", "cloudadmin#Passw0rd")
        global_state.db = Dba
    except Exception as e:
        print(f"MySQLClient initialization failed: {e}")
        global_state.db = None
    if global_state.audit.setSession():
        return "成功获取了安超平台的交互会话.并初始化平台上下文"
    else:
        return "未能正确获取到安超平台交互会话，请检查平台地址是否正确."

@mcp.tool()
def createInstance_noNet(name: str, hostname: str,  videoModel: str, imageId: str, storname: str, cpu: int, 
                         balloonSwitch: bool=False,size: int=80,rebuildPriority: int=3,numaEnable: bool=False,vncPwd="", bigPageEnable: bool=False,
                         vmActive: bool=False, cloneType: str="LINK", audioType: str="ich6", memory: int = "2", adminPassword: str="Admin@123", 
                         haEnable: bool=True, priority: int=1) -> list:
    """
    === 工具功能描述 ===
    通过安超API创建一个无网卡的虚拟机实例。根据用户提供的storname查找对应的存储管理ID和磁盘类型ID，并使用这些信息来创建虚拟机实例。
    
    === 参数说明 ===
    :param name (str): 虚拟机名称，前缀"AI_niuma_"
    :param hostname (str): 虚拟机主机名，不超过10个字符
    :param videoModel (str): 显卡类型，必须是cirrus/qxl/virtio/vga其中一个
    :param imageId (str): 镜像ID
    :param storname (str): 存储位置名称
    :param cpu (int): CPU数量
    :param memory (int): 内存大小，单位GB
    :param balloonSwitch (bool): 是否启用内存气球技术，默认False
    :param size (int): 磁盘大小，单位GB，默认80
    :param rebuildPriority (int): 磁盘重建优先级，整数值，通常为1-10之间，默认3
    :param numaEnable (bool): 是否启用NUMA，默认False
    :param vncPwd (str): VNC密码，只能是6位数字字符串，默认""
    :param bigPageEnable (bool): 是否启用大页内存，默认False
    :param vmActive (bool): 虚拟机创建后是否立即启动，默认False
    :param cloneType (str): 克隆类型，LINK或FULL，默认"LINK"
    :param audioType (str): 音频类型，默认"ich6"
    :param adminPassword (str): 虚拟机管理员密码，默认"Admin@123"
    :param haEnable (bool): 是否启用高可用，默认True
    :param priority (int): 虚拟机疏散的调度优先级，默认1
    
    :return tuple: 包含虚拟机ID和详细参数的元组
        - vm_id: 虚拟机ID
        - params: 创建参数字典
    
    === 上下文依赖规则 ===
    - 必须先调用getSession方法初始化相关对象
    - 根据storname查找存储管理ID和磁盘类型ID
    - 如果用户没有指定镜像名称，则默认选择第一个镜像
    
    === 使用示例 ===
    >>> createInstance_noNet("test", "test-host", "virtio", "img1", "basic-replica2", 2, 4, True, 80, 3, False, "", False, False, "LINK", "ich6", 2, "Admin@123", True, 1)
    ("vm-uuid-12345", {"name": "test_20240101120000", ...})
    
    === 异常处理 ===
    - 未初始化时返回提示信息："请先调用getSession方法获取安超平台的交互会话."
    - 存储位置不存在："未能找到名称为{storname}的存储信息，请确认该存储名称是否正确。"
    - 镜像不可用："镜像ID {imageId} 在存储位置 {storname} 中不可用，请重新选择正确的镜像ID。"
    
    === 关联工具 ===
    - 必须与getSession配合使用
    - 创建后可通过get_instances查看实例列表
    
    === 版本信息 ===
    v1.0（2024-01更新）：新增无网卡虚拟机创建支持
    """
    storageManageId = ""
    diskType = ""
    storageType = ""
    if global_state.audit is None:
        return "请先调用getSession方法获取安超平台的交互会话."
    if global_state.host is None:
        return "请先调用getSession方法获取安超平台的交互会话."
    if global_state.image is None:
        return "请先调用getSession方法获取安超平台的交互会话."
    instance_manager = global_state.instances
    storinfo = global_state.host.getStorsbyDiskType()
    print("createInstance_noNet storinfo:", storinfo)
    for stor in storinfo:
        if stor.get("stackName").upper() == storname.upper():
            storageManageId = stor.get("storageManageId")
            diskType = stor.get("diskType")
            storageType = stor.get("storageBackend")
            print("createInstance_noNet storinfo:", storageManageId, diskType, storageType)
    print("createInstance_noNet storageManageId, diskType, storageType:", storageManageId, diskType, storageType)
    if storageManageId == "" or diskType == "" or storageType == "":
        return f"未能找到名称为{storname}的存储信息，请确认该存储名称是否正确。"
    image_list = global_state.image.getImagebystorageManageId(global_state.host)
    print("createInstance_noNet image_list:", image_list)
    if len(image_list) == 0:
        return "当前安超平台没有可用的镜像，请先上传镜像。"
    if imageId =="" or imageId is None:
        imageId = image_list[0].get("imageId")
    else:
        checkimageId = False
        for img in image_list:
            if img.get("imageId") == imageId and img.get("storageManageId") == storageManageId:
                imageId = img.get("imageId")
                checkimageId = True
        if checkimageId == False:
            return f"镜像ID {imageId} 在存储位置 {storname} 中不可用，请重新选择正确的镜像ID。"
    print("createInstance_noNet imageId:", imageId)
    name = name + time.strftime("_%Y%m%d%H%M%S", time.localtime())
    name = name[:40]  # 限制名称长度不超过40个字符
    print("createInstance_noNet final all:", name, hostname, videoModel, haEnable, cpu, 1, memory, global_state.host.zone,
          storageType, storageManageId, diskType, imageId, adminPassword,size,rebuildPriority,numaEnable,vmActive,vncPwd,bigPageEnable,balloonSwitch,audioType,cloneType,priority)
    vm_id = instance_manager.createInstance_noNet(name, hostname, videoModel, haEnable, cpu, 1, memory, global_state.host.zone,
                                                   storageType, storageManageId, diskType, imageId, adminPassword, size=size,
                                                   rebuildPriority=rebuildPriority, numaEnable=numaEnable,
                                                   vmActive=vmActive,
                                                   vncPwd=vncPwd, bigPageEnable=bigPageEnable,
                                                   balloonSwitch=balloonSwitch,
                                                   audioType=audioType,
                                                   cloneType=cloneType,
                                                   priority=priority)
    return vm_id, {
        "name": name,
        "hostname": hostname,
        "videoModel": videoModel,
        "haEnable": haEnable,
        "cpu": cpu,
        "sockets": 1,
        "memory": memory,
        "zoneId": global_state.host.zone,
        "storageType": storageType,
        "storageManageId": storageManageId,
        "diskType": diskType,
        "imageId": imageId,
        "adminPassword": adminPassword,
        "size": size,
        "rebuildPriority": rebuildPriority,
        "numaEnable": numaEnable,
        "vmActive": vmActive,
        "vncPwd": vncPwd,
        "bigPageEnable": bigPageEnable,
        "balloonSwitch": balloonSwitch,
        "audioType": audioType,
        "cloneType": cloneType,
        "priority": priority
    }

@mcp.tool()
def createDisk_vstor(storageManageId: str, pageSize: str, compression: str, name: str, size: int, iops: int, bandwidth: int, count: int, readCache: bool, zoneId: str) -> dict:
    """
    === 工具功能描述 ===
    通过安超API创建虚拟磁盘。根据存储管理ID和区域ID创建指定参数的虚拟磁盘。
    
    === 参数说明 ===
    :param storageManageId (str): 存储管理ID
    :param pageSize (str): 磁盘页面大小，4K/8K/16K/32K
    :param compression (str): 数据压缩方式，"Disabled"/"LZ4"/"Gzip_opt"/"Gzip_high"
    :param name (str): 磁盘名称
    :param size (int): 磁盘大小，单位GB
    :param iops (int): 磁盘IOPS，范围75-250000
    :param bandwidth (int): 磁盘带宽，单位MB/s，范围1-1000
    :param count (int): 创建数量，批量创建磁盘设定此值
    :param readCache (bool): 是否启用读缓存
    :param zoneId (str): 区域ID
    
    :return dict: 虚拟磁盘信息字典
        - diskId: 磁盘ID
        - name: 磁盘名称
        - size: 磁盘大小
    
    === 上下文依赖规则 ===
    - 必须先调用getSession方法初始化相关对象
    - storageManageId和zoneId可通过getStorinfo获取
    
    === 使用示例 ===
    >>> createDisk_vstor("smid1", "4K", "Disabled", "disk1", 100, 1000, 100, 1, True, "zoneId1")
    {"diskId": "disk-uuid-12345", "name": "disk1", "size": 100, ...}
    
    === 异常处理 ===
    - 未初始化时返回提示信息："请先调用getSession方法获取安超平台的交互会话."
    
    === 关联工具 ===
    - 必须与getSession配合使用
    - 创建后可通过get_volumes查看磁盘列表
    
    === 版本信息 ===
    v1.0（2024-01更新）：新增虚拟磁盘创建支持
    """
    if global_state.audit is None:
        return "请先调用getSession方法获取安超平台的交互会话."
    if global_state.host is None:
        return "请先调用getSession方法获取安超平台的交互会话."
    volume_manager = global_state.volumes
    global_state.volumes.disks.append(volume_manager)
    print("mcp createDisk_vstor input:", storageManageId, pageSize, compression, name, size, iops, bandwidth, count, readCache, zoneId)
    disk_info = volume_manager.createDisk_vstor(storageManageId, pageSize, compression, name, size, iops, bandwidth, count, readCache, zoneId)
    return disk_info

@mcp.tool()
def deleteDisk(diskId: list) -> dict:
    """
    === 工具功能描述 ===
    通过安超API删除虚拟磁盘。删除指定磁盘ID列表中的虚拟磁盘。
    注意:这是删除虚拟磁盘，而不是删除镜像，也不是删除虚拟机。不要混用
    
    === 参数说明 ===
    :param diskId (list): 虚拟磁盘ID列表
    
    :return dict: 删除结果字典
        - success: 是否成功
        - message: 操作信息
    
    === 上下文依赖规则 ===
    - 必须先调用getSession方法初始化相关对象
    
    === 使用示例 ===
    >>> deleteDisk(["disk1", "disk2"])
    {"success": True, "message": "Disks deleted successfully."}
    
    === 异常处理 ===
    - 未初始化时返回提示信息："请先调用getSession方法获取安超平台的交互会话."
    
    === 关联工具 ===
    - 必须与getSession配合使用
    
    === 版本信息 ===
    v1.0（2024-01更新）：新增虚拟磁盘删除支持
    """
    if global_state.volumes is None:
        return "请先调用getSession方法获取安超平台的交互会话."
    delete_result = global_state.volumes.deleteDisk(diskId)
    return delete_result

@mcp.tool()
def getImagebystorageManageId() -> list:
    """
    === 工具功能描述 ===
    通过存储管理ID获取对应的镜像列表。返回镜像ID、镜像名称、storageManageId字典的列表。
    
    === 参数说明 ===
    无参数，依赖全局状态中的image和host对象
    
    :return list: 镜像信息列表，元素为字典
        - imageId: 镜像ID
        - imageName: 镜像名称
        - storageManageId: 存储管理ID
    
    === 上下文依赖规则 ===
    - 必须先调用getSession方法初始化image和host对象
    
    === 使用示例 ===
    >>> getImagebystorageManageId()
    [{"imageId": "id1", "imageName": "name1", "storageManageId": "smid1"}, ...]
    
    === 异常处理 ===
    - 未初始化时返回提示信息："请先调用getSession方法获取安超平台的交互会话."
    
    === 关联工具 ===
    - 必须与getSession配合使用
    
    === 版本信息 ===
    v1.0（2024-01更新）：新增镜像信息获取支持
    """
    if global_state.audit is None:
        return "请先调用getSession方法获取安超平台的交互会话."
    if global_state.host is None:
        return "请先调用getSession方法获取安超平台的交互会话."
    if global_state.image is None:
        return "请先调用getSession方法获取安超平台的交互会话."
    host = global_state.host
    image = global_state.image
    image_list = image.getImagebystorageManageId(host)
    return image_list

@mcp.tool()
def getStorinfo() -> list:
    """
    === 工具功能描述 ===
    获取平台全部的存储信息列表。返回存储位置名称、storageBackend、zoneId、storageManageId、diskType字典的列表。
    
    === 参数说明 ===
    无参数，依赖全局状态中的host对象
    
    :return list: 存储信息列表，元素为字典
        - stackName: 存储位置名称
        - zoneId: 区域ID
        - storageBackend: 存储后端类型
        - storageManageId: 存储管理ID
        - diskType: 磁盘类型ID
    
    === 上下文依赖规则 ===
    - 必须先调用getSession方法初始化host对象
    
    === 使用示例 ===
    >>> getStorinfo()
    [{'stackName': 'basic-replica2', 'zoneId': 'zoneId1', 'storageBackend': 'Arstor', 'storageManageId': 'smid1', 'diskType': 'dtid1'}, ...]
    
    === 异常处理 ===
    - 未初始化时返回提示信息："请先调用getSession方法获取安超平台的交互会话."
    
    === 关联工具 ===
    - 必须与getSession配合使用
    
    === 版本信息 ===
    v1.0（2024-01更新）：新增存储信息获取支持
    """
    if global_state.audit is None:
        return "请先调用getSession方法获取安超平台的交互会话."
    if global_state.host is None:
        return "请先调用getSession方法获取安超平台的交互会话."
    host = global_state.host
    storinfo = host.getStorsbyDiskType()
    return storinfo

@mcp.tool()
def db_query_simple(sql: str,database:str) -> list:
    """
    === 工具功能描述 ===
    查询云管平台数据库的SQL语句执行结果。
    
    === 参数说明 ===
    :param sql (str): SQL查询语句
    :param database (str): 数据库名称
    
    :return list: 查询结果列表，每行一个字典
    
    === 上下文依赖规则 ===
    - 必须先调用getSession方法初始化db对象
    - 支持所有标准SQL查询语句
    
    === 使用示例 ===
    >>> db_query_simple("SELECT * FROM virtual_machine", "xu_resource")
    [{"id": 1, "name": "vm1", ...}, ...]
    virtual_machine表属于xu_resource数据库
    === 异常处理 ===
    - 未初始化时返回提示信息："请先调用getSession方法获取安超平台的交互会话."
    
    === 关联工具 ===
    - 必须与getSession配合使用
    
    === 版本信息 ===
    v1.0（2024-01更新）：新增数据库查询支持
    """
    return global_state.db.query_simple(sql,database)

@mcp.tool()
def check_workflow_testcase001  (workflow_id: str) -> str:
    """
    === 测试用例描述 ===
    这是一个测试场景
    需要根据用例步骤描述，调用相关的tool 进行测试
    根据测试用例步骤描述，测试用例执行步骤。
    === 测试用例参数说明 ===
    :return str: 返回该测试用例的描述
    
    === 测试用例步骤描述 ===
    1. 获取平台session tool调用：getSession
    2.获取集群存储信息 tool调用：getStorinfo
    3.获取镜像信息 tool调用：getImagebystorageManageId
    4.创建虚拟机 tool调用：createInstance_noNet tool
    5.创建虚拟磁盘 -- tool调用: createDisk_vstor 强制要求：使用虚拟机名称作为磁盘名称

    === 测试用例异常处理 ===
    - 工作流执行异常时返回错误信息
    
    === 测试用例关联工具 ===
    - 必须与getSession配合使用
    
    === 测试用例版本信息 ===
    v1.0（2024-01更新）：新增工作流测试用例
    """
    return  """
    === 测试用例步骤描述 ===
    1. 获取平台session
    2.获取集群存储信息
    3.获取镜像信息
    4.创建虚拟机
    5.创建虚拟磁盘
    """

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """
    === 工具功能描述 ===
    获取个性化问候语。
    
    === 参数说明 ===
    :param name (str): 用户名称
    
    :return str: 个性化问候语
    
    === 使用示例 ===
    >>> get_greeting("Alice")
    "Hello, Alice!"
    
    === 版本信息 ===
    v1.0（2024-01更新）：新增多语言支持
    """
    return f"Hello, {name}!"

@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """
    === 工具功能描述 ===
    生成指定风格的个性化问候语。
    
    === 参数说明 ===
    :param name (str): 用户名称
    :param style (str): 问候风格，可选friendly/formal/casual，默认friendly
    
    :return str: 风格化问候语
    
    === 使用示例 ===
    >>> greet_user("Alice", "formal")
    "Please write a formal, professional greeting for someone named Alice."
    
    === 版本信息 ===
    v1.0（2024-01更新）：新增风格化问候支持
    """
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }
    return f"{styles.get(style, styles['friendly'])} for someone named {name}."

# Run with streamable HTTP transport
if __name__ == "__main__":
    mcp.run(transport="sse")