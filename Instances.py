from utils.audit import ArcherAudit
from utils.tools.sshcommand import ssh_execute_command
from utils.tools.Str import  convert_policy_string_to_dict
import  urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Instances:
    def __init__(self, username, password, url, audit:ArcherAudit=None):
        if audit is None:
            audit = ArcherAudit(username, password, url)
            audit.setSession()
        self.session = audit.session
        self.base_url = url
        self.instances = []

    def createInstance_noNet(self, name, hostname, videoModel, haEnable, cpu, sockets, memory, zoneId, storageType,
                              storageManageId, diskType, imageId, adminPassword,size=80,rebuildPriority=3,numaEnable=False,
                            vmActive=False,vncPwd="",bigPageEnable=False,balloonSwitch=False,audioType="ich6",cloneType="LINK",priority=1) -> list:
        """
        通过安超API创建一个无网卡的虚拟机实例
        :return: 创建的结果，返回的是一个列表，包含创建的虚拟机IDs
        创建之前请确保所选的镜像ID是存在的，并且存储后端和存储管理ID是正确配置的。
        name: 虚拟机名称
        hostname: 虚拟机主机名
        videoModel: 视频模型，例如"VGA"或"QXL"
        haEnable: 是否启用高可用，True或False
        cpu: CPU数量
        sockets: CPU插槽数
        memory: 内存大小，单位GB
        zoneId: 所属区域ID
        storageType: 存储类型
        storageManageId: 存储管理ID
        imageId: 镜像ID
        adminPassword: 虚拟机管理员密码
        diskType: 磁盘类型ID
        """
        print("Instance createInstance_noNet:","进入方法体")
        url = f"{self.base_url}/api/resource/createVirtualMachine"
        payload = {"name":name,"hostname":hostname,"folderId":"100e4de3-1b8a-8cbe-e505-bc49edbb8503",
                    "videoModel":videoModel,"vmHaConfig":{"ftEnable":False,"haEnable":haEnable},
                    "type":"NORMAL","cpuMode":"host-passthrough","cpu":cpu,"sockets":sockets,"memory":memory,"zoneId":zoneId,
                    "count":1,"storageType":storageType.upper(),
                    "disk":[{"storageManageId":storageManageId,"size":size,"ioThread":True,
                            "turboEnable":False,"compression":"LZ4","diskType":diskType,
                            "pageSize":"4K","readCache":True,"rebuildPriority":rebuildPriority,"isSystem":True}],"isMemMonopoly":False,
                            "numaEnable":numaEnable,"balloonSwitch":balloonSwitch,"audioType":audioType,"clock":"utc","cloneType":cloneType,
                            "vmActive":vmActive,"vncPwd":vncPwd,"bigPageEnable":bigPageEnable,"cpuLimitEnabled":False,"cpuLimit":None,
                            "cpuShareLevel":"MID","cpuShare":None,"tagIds":[],"isTemplate":False,"usbType":"3.0",
                            "storageManageId":storageManageId,"priority":priority,"createVmType":"SYSTEMDEFAULT",
                            "imageId":imageId,"adminPassword":adminPassword,"script":[None],"interface":[]}
        print("Instance createInstance_noNet payload:", payload)
        response = self.session.post(url, json=payload, verify=False)
        print("Instance createInstance_noNet:", response.json())
        if response.status_code == 200 and response.json().get('code') == 0:
            self.instances.extend(response.json().get('data').get('ids'))
        return response.json().get('data').get('ids')
    
    def getVminfobyid(self, vmId: str) -> dict:
        """
        通过虚拟机ID获取对应的虚拟机信息
        :return: 返回虚拟机信息的字典
        """
        url = f"{self.base_url}/api/resource/getVirtualMachine"
        payload = {"id":vmId}
        response = self.session.post(url, json=payload, verify=False)
        print("Instance getVminfobyid response:", response.json())
        if response.status_code == 200 and response.json().get('code') == 0:
            return response.json().get('data')
        else:
            return "获取虚拟机信息失败,请检查虚拟机ID是否正确。"

    def deleteInstance_byId(self, vmId: str) -> bool:
        """
        通过虚拟机ID删除对应的虚拟机实例
        :return: 删除成功返回True，失败返回False
        """
        url = f"{self.base_url}/api/resource/deleteVirtualMachine"
        payload = {"ids":[vmId]}
        response = self.session.post(url, json=payload, verify=False)
        print("Instance deleteInstance_byId response:", response.json())
        if response.status_code == 200 and response.json().get('code') == 0:
            return True
        else:
            return False