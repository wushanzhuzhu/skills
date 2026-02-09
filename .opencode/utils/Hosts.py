from utils.audit import ArcherAudit
from utils.tools.sshcommand import ssh_execute_command
from utils.tools.Str import  convert_policy_string_to_dict
import re
import urllib3
from TestCaseApp.licensemake1 import LicenseService
import  ssl
# 全局禁用SSL验证
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Hosts:
    def __init__(self, username, password, url, audit:ArcherAudit=None):
        if audit is None:
            audit = ArcherAudit(username, password, url)
            audit.setSession()
        self.session = audit.session
        self.base_url = url
        self.zone = ""
        self.clusterId = ""
        self.storageInfo = []
        url = f"{self.base_url}/api/resource/listHost"
        payload = {}
        listhost_rs = self.session.post(url, json=payload, verify=False)
        self.zone = listhost_rs.json().get('data', [])[0].get("zoneId")



    def getStorsbyDiskType(self):
        """
        :return:平台可以用的全部的存储信息，以列表的方式返回,列表格式如下：
        返回的信息包括：
        stackname, zoneId, diskType, storageBackend, storageManageId
        例如：
       [{"stackname": "basic-replica2", "zoneId": "xxxx-xxxx-xxxx-xxxx", "diskType": "xxxx-xxxx-xxxx-xxxx", "storageBackend": "xxxx-xxxx-xxxx-xxxx", "storageManageId": "xxxx-xxxx-xxxx-xxxx"},......]
        其中stackname是存储名称，zoneId是区域ID，diskType是磁盘类型ID，storageBackend是存储后端类型，storageManageId是存储管理ID
        """
        stors_rs = []
        url = f"{self.base_url}/api/resource/listStorage"
        payload = {"zoneId":self.zone}
        rs = self.session.post(url, json=payload, verify=False)
        print("getStorsbyDiskType listStorage rs:", rs.json().get('data', []))
        storinfo = rs.json().get('data', [])
        for item in storinfo:
            stors_rs.append({"stackName": item.get("stackName"), "zoneId": self.zone, "storageBackend": item.get("storageBackend"), "storageManageId": item.get("id")})
        print("getStorsbyDiskType stors_rs:", stors_rs)
        url2 = f"{self.base_url}/api/resource/listDiskType"
        payload2 = {"zoneId": self.zone}
        rs2 = self.session.post(url2, json=payload2, verify=False)
        print("getStorsbyDiskType listDiskType rs:", rs2.json().get('data', []))
        disktypeinfo = rs2.json().get('data', [])
        for dtitem in disktypeinfo:
            for stor in stors_rs:
                if dtitem.get("name") == stor.get("stackName"):
                    stor["diskType"] = dtitem.get("id")
        print("getStorsbyDiskType final stors_rs:", stors_rs)
        self.storageInfo = stors_rs
        return stors_rs


    def is_X86(self):
        """
        x86环境返回true，arm环境返回false
        如果ssh执行失败，则反回ERROR
        :return:
        """
        pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        match = re.search(pattern, self.base_url)
        hostname = match.group(1) if match else None
        print("hostname", hostname)
        args = {
            "hostname": hostname,
            "port": 22,
            "username": "cloud",
            "key_path": "id_rsa_cloud",
            "command": '''sudo uname -r'''
        }

        sshresult = ssh_execute_command(**args)
        print("Host is_X86 ssh:", sshresult)
        print("is_X86 sshresult:", "x86" in sshresult)
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
        print("Hosts getClusterId self.clusterId:", self.clusterId)
        print("Hosts getClusterId self.archType", self.archType)
        print({"clusterId" : self.clusterId, "archType" : self.archType})
        return {"clusterId" : self.clusterId, "archType" : self.archType}

    def updateLicense(self, license_text, license_id):
        """
                :return:
                返回集群ID
                """
        if license_id =="" or license_id ==None:
            license_id = "t2t2t124-t3t1-4ttt-9475-t97t3159t41t"
        url = f"{self.base_url}/api/resource/updateLicense"

        print("app license_id:", license_id)
        print("app license_text:", license_text)
        payload = {"licenseCode":license_text,"id":license_id}
        listhost_rs = self.session.post(url, json=payload, verify=False)
        print("host updateLicense response", listhost_rs.json())
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
        print("hasLicense getLicenseId",license_id)
        return license_id
