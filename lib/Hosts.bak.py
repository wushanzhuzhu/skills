from utils.audit import ArcherAudit
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

from utils.tools.sshcommand import ssh_execute_command
from utils.tools.Str import  convert_policy_string_to_dict
import re
from TestCaseApp.licensemake1 import LicenseService

class Hosts:
    def __init__(self, username, password, url, audit:ArcherAudit=None):
        if audit is None:
            audit = ArcherAudit(username, password, url)
            audit.setSession()
        self.session = audit.session
        self.base_url = url
        self.zone = ""
        self.storageBacken = ""
        self.storageManageId = ""
        self.clusterId = ""

    def getHostStorInfo(self):

        """
        :return:
        返回一个列表[{zone,storageBacken ,storageManageId }，{zone,storageBacken ,storageManageId},.......]
        """
        hostInfo_rs = []
        url = f"{self.base_url}/api/resource/listHost"
        payload = {}
        listhost_rs = self.session.post(url, json=payload, verify=False)
        self.zone = listhost_rs.json().get('data', [])[0].get("zoneId")
        logger.info("getHostInfo self.zone:", self.zone)
        url = f"{self.base_url}/api/resource/listStorage"
        payload = {"zoneId":self.zone}
        rs = self.session.post(url, json=payload, verify=False)
        logger.info("getHostInfo listStorage rs:", rs.json().get('data', []))
        hostinfo = rs.json().get('data', [])
        for item in hostinfo:
            hostInfo_rs.append({"base_url": self.base_url, "zoneId": self.zone, "storageType": item.get("type"), "storageBacken": item.get("storageBackend"), "storageManageId": item.get("id")})
        logger.info("getHostInfo hostInfo_rs:", hostInfo_rs)
        return hostInfo_rs
    
    def getStorsbyDiskType(self):
        """
        :return:平台可以用的全部的存储信息，以字典的方式返回
        """


    def is_X86(self):
        """
        x86环境返回true，arm环境返回false
        如果ssh执行失败，则反回ERROR
        :return:
        """
        pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        match = re.search(pattern, self.base_url)
        hostname = match.group(1) if match else None
        logger.info("hostname", hostname)
        args = {
            "hostname": hostname,
            "port": 22,
            "username": "cloud",
            "key_path": "id_rsa_cloud",
            "command": '''sudo uname -r'''
        }

        sshresult = ssh_execute_command(**args)
        logger.info("Host is_X86 ssh:", sshresult)
        logger.info("is_X86 sshresult:", "x86" in sshresult)
        if sshresult == "":
            return "ERROR"
        return "x86" in sshresult

    def getClusterInfo(self):
        """
        :return:
        返回集群ID
        """
        hostInfo_rs = []
        url = f"{self.base_url}/api/resource/getLicense"
        payload = {}
        listhost_rs = self.session.post(url, json=payload, verify=False)
        self.clusterId = listhost_rs.json().get('data').get("clusterId")
        self.archType = listhost_rs.json().get('data').get("architecture")
        logger.info("Hosts getClusterId self.clusterId:", self.clusterId)
        logger.info("Hosts getClusterId self.archType", self.archType)
        logger.info({"clusterId" : self.clusterId, "archType" : self.archType})
        return {"clusterId" : self.clusterId, "archType" : self.archType}

    def updateLicense(self, license_text, license_id):
        """
                :return:
                返回集群ID
                """
        if license_id =="" or license_id ==None:
            license_id = "t2t2t124-t3t1-4ttt-9475-t97t3159t41t"
        url = f"{self.base_url}/api/resource/updateLicense"

        logger.info("app license_id:", license_id)
        logger.info("app license_text:", license_text)
        payload = {"licenseCode":license_text,"id":license_id}
        listhost_rs = self.session.post(url, json=payload, verify=False)
        logger.info("host updateLicense response", listhost_rs.json())
        return listhost_rs

    def getLicenseId(self):
        """
                :return:
                返回集群ID
                """
        url = f"{self.base_url}/api/resource/getLicense"
        payload = {}
        rs = self.session.post(url, json=payload, verify=False)
        license_id = rs.json().get("data").get("id")
        logger.info("hasLicense getLicenseId",license_id)
        return license_id

if __name__ == "__main__":
    server = Hosts("admin", "Admin@123", "https://172.118.13.201"                                  )
    logger.info(server.is_X86())
    #info = server.getClusterInfo()
    #licensetxt = LicenseService.get_permit_info(info.get("clusterId"), info.get("archType"), 100, 30, 100, 100, 100, "2026-12-31")
