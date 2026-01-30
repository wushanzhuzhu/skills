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
#mcp = FastMCP("Demo", json_response=True)
register_all_tools(mcp)

class GlobalState:
    """
    单例模式实现全局状态管理
    线程安全，支持延迟初始化
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
    """通过SSH密钥执行远程命令
    加sudo去执行命令，
    使用非对称加密进行身份验证，通过加密隧道执行命令。
    建议将私钥文件权限设置为600（-rw-------）
    
    Args:
        hostip (str): 远程主机IP或域名（支持IPv4/IPv6）
        command (str): 要执行的Shell命令（支持多行命令用分号分隔）
        port (int, optional): SSH服务端口. Defaults to 22.
        username (str, optional): 登录用户名. Defaults to "cloud".
        key_path (str, optional): 私钥文件路径（相对当前工作目录）. 
        建议使用绝对路径避免路径解析问题. Defaults to "./id_rsa_cloud".
    
    Returns:
        dict: 包含执行结果的字典
            - "stdout": 命令标准输出（字符串）
            - "stderr": 命令错误输出（字符串）
            - "exit_code": 命令退出状态码（整数）
    
    Raises:
        ConnectionRefusedError: 连接超时或服务未运行
        AuthenticationFailed: 密钥验证失败或用户无权限
        FileNotFoundError: 私钥文件不存在或路径错误
        PermissionError: 私钥文件权限过宽（建议600）
    
    Example:
        >>> sshexecute_command("192.168.1.10", "ls -l /var/log", 
                                username="admin", key_path="/home/admin/.ssh/id_rsa")
        {"stdout": "total 1024\n...", "stderr": "", "exit_code": 0}
    
    Note:
        建议配合系统防火墙配置（如开放对应端口）
        长命令建议使用分号分隔或换行符（需服务端支持）
        执行敏感命令时建议添加超时参数（需在实现中处理）
        该方法依赖paramiko库实现SSH连接和命令执行。
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
    """
    print("sshexecute_command input:", hostip, port, username, key_path, command)
    rs = ssh_execute_command(hostip, port, username, key_path, command)
    print("sshexecute_command rs:", rs)
    return rs


@mcp.tool()
def get_audit() -> tuple:
    """
    获取当前安超平台交互权限的详细信息
    包括平台地址，用户名，密码，认证token等
    :return: 包含交互权限信息的元组
    例如: (base_url, username, password, auth_token, base_url)
    该方法依赖于先前调用的getSession方法来获取安超平台的交互会话。
    """
    return global_state.audit.base_url, global_state.audit.username, global_state.audit.password, global_state.audit.auth_token, global_state.audit.base_url if global_state.audit else "当前会话中未保存交互权限信息，请先调用getSession方法获取安超平台的交互会话."   

@mcp.tool()
def get_clusterStor() -> tuple:
    """
    获取当前安超平台集群的相关信息
    包括区域ID，集群ID，存储信息等
    :return: 包含主机信息的元组
    例如: (zoneId, clusterId, storageInfo)
    """
    return global_state.host.zone, global_state.host.clusterId, global_state.host.storageInfo if global_state.host else "当前会话中未保存主机信息，请先调用getSession方法获取安超平台的交互会话."

@mcp.tool()
def get_image() -> list:
    """
    获取当前安超平台镜像相关信息
    包括镜像列表等
    :return: 包含镜像信息的列表
    例如: [{"imageId": "id1", "imageName": "name1", "storageManageId": "smid1"}, ...]
    """
    return global_state.image.images if global_state.image else "当前会话中未保存镜像信息，请先调用getSession方法获取安超平台的交互会话."

@mcp.tool()
def get_instances():
    """
    获取当前会话下创建的虚拟机实例信息
    """
    return global_state.instances.instances if global_state.instances else "当前会话中未保存虚拟机实例信息，请先调用getSession方法获取安超平台的交互会话."
@mcp.tool()
def get_volumes():
    """
    获取当前会话下创建的虚拟磁盘信息
    """
    return global_state.volumes.disks if global_state.volumes else "当前会话中未保存虚拟磁盘信息，请先调用getSession方法获取安超平台的交互会话."

# 获取安超平台交互权限
@mcp.tool()
def getSession(url: str,name: str="admin", password: str="Admin@123") -> str:
    """
    当用户要求再某个ip下创建资源时，就是指这个ip对应的平台，那就需要调用此方法
    AI与平台的交换会话权限，想要调用平台的API，必须先获取session
    当用户询问是否能连接，是否能操作安超平台，是否能登录安超平台时，调用本方法确认
    当需要访问安超的平台时，首先要调用这个方式获取http session，才可以进行后续的操作;
    url: 安超平台的基础地址，例如：https://172.118.13.100
    该方法返回获取session的结果说明
    returns: str
    如果传入的是172.118.13.100这样的格式，则代码会添加https://前缀
    如果传入的既不是IP地址，也不是HTTPS URL格式，则返回错误提示
    name: str 安超平台用户名，默认admin
    password: str 安超平台密码，默认Admin@123
    如果切换了安超平台地址，请重新调用该方法获取session和初始化相关的对象。
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
    Dba=MySQLClient(ipv4_address,"root","cloudadmin#Passw0rd",)
    global_state.db = Dba
    if global_state.audit.setSession():
        return "成功获取了安超平台的交互会话.并初始化平台上下文"
    else:
        return "未能正确获取到安超平台交互会话，请检查平台地址是否正确."

# 在安超平台创建虚拟机实例
@mcp.tool()
def createInstance_noNet(name: str, hostname: str,  videoModel: str, imageId: str, storname: str, cpu: int, 
                         balloonSwitch: bool=False,size: int=80,rebuildPriority: int=3,numaEnable: bool=False,vncPwd="", bigPageEnable: bool=False,
                         vmActive: bool=False, cloneType: str="LINK", audioType: str="ich6", memory: int = "2", adminPassword: str="Admin@123", 
                         haEnable: bool=True, priority: int=1) -> list:
    """
    将入参反馈给用户，方便用户确认参数正确性
    通过安超API创建一个无网卡的虚拟机实例
    :return: 创建的结果，返回的是虚拟机的id以及创建时的虚拟机参数信息
    创建之前请确保所选的镜像ID是存在的，并且存储后端和存储管理ID是正确配置的。
    name: 虚拟机名称,前缀“AI_niuma_”
    hostname: 虚拟机主机名，可以不设置，系统会自动生成，不超过10个字符
    videoModel: 必须是cirrus or qxl or virtio or vga其中一个
    haEnable: 是否启用高可用，True或False
    cpu: CPU数量
    sockets: CPU插槽数,cpu数量=sockets*coresPerSocket，coresPerSocket默认为1
    memory: 内存大小，单位GB,
    cpu和memory的配置，我们定义如下规则：
    - 小型配置：2 CPU，4 GB 内存
    - 中型配置：4 CPU，8 GB 内存
    - 大型配置：8 CPU，16 GB 内存
    - 超大型配置：16 CPU，32 GB 内存
    imageId: 镜像ID
    adminPassword: 虚拟机管理员密码
    diskType: 磁盘类型ID
    storname: 安超平台称之为存储位置，为用户选择用于创建虚拟机创建时使用的存储位置
    vncPwd: VNC密码，只能是6位数字字符串，例如"123456"，如果不设置则默认不启用VNC密码保护  
    cloneType: 克隆类型，LINK或FULL
    balloonSwitch: 是否启用内存气球技术，True或False
    bigPageEnable: 是否启用大页内存，True或False
    numaEnable: 是否启用NUMA，True或False
    rebuildPriority: 磁盘重建优先级，整数值，通常为1-10之间，当虚拟机磁盘数据出现问题时，按这个级别设定优先级进行重建
    vmActive: 虚拟机创建后是否立即启动，True或False
    priority: 虚拟机疏散的调度优先级，也可以称之为HA优先级，整数值，通常为1-10之间，数值越大优先级越高
    size: 磁盘大小，单位GB，默认为80GB
    该方法会根据用户提供的storname查找对应的存储管理ID和磁盘类型ID，并使用这些信息来创建虚拟机实例。
    如果用户没有指定imagename，则默认选择第一个镜像。
    该方法返回创建的虚拟机ID列表。
    例如：["vm-uuid-1", "vm-uuid-2"]
    该方法依赖于先前调用的getSession方法来获取安超平台的交互会话。
    如果批量创建虚拟机，请多次调用该方法，每次调用创建一个虚拟机实例。如果存在调用失败的情况，停止批量动作，并返回错误信息。
    如果用户没有指定镜像名称，则默认选择第一个镜像
    存储位置信息可以通过调用getStorinfo方法获取，为stackname那个字段
    镜像信息可以通过调用getImagebystorageManageId方法获取
    如果haEnable设置为True，请确保所选的主机支持高可用配置。
    如果haEnable设置为False，则虚拟机将不会启用高可用功能。并且priority参数需要传入0
    当要求疏散优先级是非0时，haEnable必须为True
    当要求疏散优先级是0时，haEnable必须为False
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
        #stor.get("stackName")转成大写和用户输入的对比
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
    # 如果用户没有指定镜像名称，则默认选择第一个镜像
    if imageId =="" or imageId is None:
        imageId = image_list[0].get("imageId")
    else:
        checkimageId = False
        for img in image_list:
            # 检查镜像名称和存储管理ID是否匹配
            if img.get("imageId") == imageId and img.get("storageManageId") == storageManageId:
                imageId = img.get("imageId")
                checkimageId = True
        if checkimageId == False:
            return f"镜像ID {imageId} 在存储位置 {storname} 中不可用，请重新选择正确的镜像ID。"
    print("createInstance_noNet imageId:", imageId)
    # 调用创建虚拟机实例的方法
    name = name + time.strftime("_%Y%m%d%H%M%S", time.localtime())
    name = name[:40]  # 限制名称长度不超过20个字符
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



#虚拟磁盘相关操作 disk相关操作

@mcp.tool()
def createDisk_vstor(storageManageId: str, pageSize: str, compression: str, name: str, size: int, iops: int, bandwidth: int, count: int, readCache: bool, zoneId: str) -> dict:
    """
    通过安超API创建虚拟磁盘
    :return: 创建的结果，返回的是虚拟磁盘的信息
    storageManageId: 存储管理ID
    pageSize: 磁盘页面大小 4K/8K/16K/32K
    compression: 数据落盘时的压缩方式， "Disabled" --禁用 , "LZ4" -- "Gzip_opt"   "Gzip_high"
    name: 磁盘名称
    size: 磁盘大小，单位GB
    iops: 磁盘IOPS  入参范围75-250000
    count: 创建数量，如果创建多个磁盘，则返回磁盘列表
    readCache: 读缓存 True/False
    bandwidth: 磁盘带宽，单位MB/s，接受参数范围 1-1000
    zoneId: 区域ID
    该方法返回创建的虚拟磁盘信息。
    例如：{"diskId": "disk-uuid", "name": "disk-name", "size": 100, ...}
    该方法依赖于先前调用的getSession方法来获取安超平台的交互会话。
    storageManageId和zoneId可以通过调用getStorinfo()方法获取。
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
    通过安超API删除虚拟磁盘
    这个是删除磁盘，并不是删除虚拟机
    :return: 删除的结果，返回的是删除操作的结果信息
    diskId: 虚拟磁盘ID列表
    该方法返回删除操作的结果信息。
    例如：{"success": True, "message": "Disks deleted successfully."}
    该方法依赖于先前调用的getSession方法来获取安超平台的交互会话。
    """
    if global_state.volumes is None:
        return "请先调用getSession方法获取安超平台的交互会话."
    delete_result = global_state.volumes.deleteDisk(diskId)
    return delete_result

# 返回平台全部的imges列表信息
@mcp.tool()
def getImagebystorageManageId() -> list:
    """
    通过存储管理ID获取对应的镜像列表
    返回镜像ID，镜像名称，storageManageId 字典的列表
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

# 返回平台全部的存储信息列表
@mcp.tool()
def getStorinfo() -> list:
    """
    获取平台全部的存储信息列表
    返回存储位置名称，storageBackend，zoneId，storageManageId，diskType 字典的列表,如[{'stackName': 'basic-replica2', 'zoneId': '4ce2e90e-6cc6-4c4b-b49f-bcd00d2064e9', 'storageBackend': 'Arstor', 'storageManageId': 'b3e11997-60ad-4110-8a7d-cfc74c7cb8e1',
 'diskType': 'ec6a6e03-1619-4380-a29f-93ba868dbdd2'}]
    必须完整的返回这些信息，以便用户选择正确的存储位置来创建虚拟机实例。
    """
    if global_state.audit is None:
        return "请先调用getSession方法获取安超平台的交互会话."
    if global_state.host is None:
        return "请先调用getSession方法获取安超平台的交互会话."
    host = global_state.host
    storinfo = host.getStorsbyDiskType()
    return storinfo


# @mcp.tool()
# def db_query(table: str,database:str, fields="*", condition: str = "") -> list:
#     """查询云管平台数据库的数据库表
#     :param table: 数据库表名
#     :param condition: 查询条件
#     :return: 查询结果
#     virtual_machine 为虚拟机表，它属于xu_resource数据库
#     表结构通过查询get_db_schema方法获取
#     """
#     return global_state.db.query(table,fields,condition,database)

@mcp.tool()
def db_query_simple(sql: str,database:str) -> list:
    """查询云管平台数据库的SQL语句
    :param sql: SQL语句
    :return: 查询结果
    """
    return global_state.db.query_simple(sql,database)

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# Add a prompt
@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."


# Run with streamable HTTP transport
if __name__ == "__main__":
    mcp.run(transport="sse")
    #mcp.run(transport="streamable-http")