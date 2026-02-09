import logging
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
from utils.audit import ArcherAudit
from utils.tools.sshcommand import ssh_execute_command
from utils.tools.Str import  convert_policy_string_to_dict 
from Hosts import Hosts
import  urllib3
import time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Volumes:
    def __init__(self, audit:ArcherAudit, host:Hosts):
        self.audit = audit
        self.host = host
        self.disks = []

    def createDisk_vstor(self, storageManageId: str, pageSize: str, 
                         compression: str, name: str, size: int, iops: int, bandwidth: int, 
                         count: int, readCache: bool, zoneId: str) -> dict:
        """
        调用archeross平台API创建虚拟磁盘
        :param storageManageId: 存储管理ID
        :param pageSize: 磁盘页面大小 4K/8K/16K/32K
        :param compression: 数据落盘时的压缩方式， "Disabled" --禁用 , "LZ4" -- "Gzip_opt"   "Gzip_high"
        :param name: 磁盘名称
        :param size: 磁盘大小，单位GB
        :param iops: 磁盘IOPS  入参范围75-250000
        :param count: 创建数量，如果创建多个磁盘，则返回磁盘列表
        :param readCache: 读缓存 True/False
        :param bandwidth: 磁盘带宽，单位MB/s，接受参数范围 1-1000
        :param zoneId: 区域ID
        :return: 创建成功返回虚拟磁盘信息，创建失败返回错误信息
        """
        url = f"{self.audit.base_url}/api/resource/createDisk"
        payload = {"storageManageId": storageManageId, "pageSize": pageSize, "compression": compression, "name": name, "size": size, "iops": iops, "bandwidth": bandwidth, "count": count, "readCache": readCache, "zoneId": zoneId}
        logger.info("Volumes createDisk payload:", payload)
        response = self.audit.session.post(url, json=payload, verify=False)
        logger.info("Volumes createDisk response:", response.json())
        if response.status_code == 200 and response.json().get('code') == 0:
            self.disks.extend(response.json().get('data'))
            return response.json().get('data')
        else:
            return response.json()


    def deleteDisk(self, diskId: list) -> dict:
        """
        调用archeross平台API删除虚拟磁盘
        :param diskId: 虚拟磁盘ID
        :return: 删除成功返回成功信息，删除失败返回错误信息
        """
        url = f"{self.audit.base_url}/api/resource/removeDisk"
        payload = {"ids":diskId}
        logger.info("Volumes deleteDisk payload:", payload)
        response = self.audit.session.post(url, json=payload, verify=False)
        logger.info("Volumes deleteDisk response:", response.json())
        return response.json()

    def getDiskbyName(self,name: str) -> list:
        """
        只是一个模糊的查询，结果是个一个列表
        调用archeross平台API查询虚拟磁盘
        :param name: 虚拟磁盘名称
        :return: 查询成功返回虚拟磁盘信息，查询失败返回错误信息
        此方法返回一个列表，列表中包含多个虚拟磁盘信息，磁盘信息是一个字典，包含虚拟磁盘ID，名称，大小等信息
        """
        url = f"{self.audit.base_url}/api/resource/listDisk"
        payload = {"name":name}
        logger.info("Volumes getDiskbyName payload:", payload)
        response = self.audit.session.post(url, json=payload, verify=False)
        return response.json().get("data",[])
    
    def getDiskbyName_exact(self,name: str) -> dict:
        """
        一个精确的查询，结果是一个字典
        调用archeross平台,根据磁盘名称，精确查询出一个虚拟磁盘信息
        :param name: 虚拟磁盘名称
        :return: 查询成功返回虚拟磁盘信息，查询失败返回错误信息
        此方法返回一个字典，包含虚拟磁盘ID，名称，大小等信息
        方法返回只包含一个虚拟磁盘信息，磁盘信息是一个字典，包含虚拟磁盘ID，名称，大小等信息
        """
        disk = {}
        url = f"{self.audit.base_url}/api/resource/listDisk"
        payload = {"name":name}
        logger.info("Volumes getDiskbyName payload:", payload)
        response = self.audit.session.post(url, json=payload, verify=False)
        disks = response.json().get("data",[])
        for disk_item in disks:
            if disk_item.get("name") == name:
                return disk_item
        return {}
    
    def listAllDisks(self) -> list:
        """
        调用archeross平台API查询所有虚拟磁盘
        :return: 查询成功返回虚拟磁盘信息列表，查询失败返回空列表
        """
        url = f"{self.audit.base_url}/api/resource/listDisk"
        payload = {}  # 空载荷获取所有磁盘
        logger.info("Volumes listAllDisks payload:", payload)
        response = self.audit.session.post(url, json=payload, verify=False)
        logger.info("Volumes listAllDisks response:", response.json())
        return response.json().get("data", [])
    

if __name__ == "__main__":
    audit = ArcherAudit("admin", "Admin@123", "https://172.118.57.100")
    audit.setSession()
    host = Hosts("admin", "Admin@123", "https://172.118.57.100")
    stors=host.getStorsbyDiskType()
    zoneid=host.zone
    volumes = Volumes(audit, host)
    i = 0
    while i < 2:
        volumes.createDisk_vstor(stors[0].get("storageManageId"), "4K", "Disabled", f"DStest-{i}", 10, 100, 100, 1, True, zoneid)
        i = i+1
        time.sleep(1)