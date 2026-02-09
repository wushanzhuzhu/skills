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

class ArcherServer:
    def __init__(self, username, password, url):
        audit = ArcherAudit(username, password, url)
        if audit.setSession():
            self.session = audit.session
        else:
            self.session = None
        self.base_url = url

    def id_of_vm(self, vm_name):
        vm_url = f"{self.base_url}/api/resource/listVirtualMachine"
        payload = {"pageNumber": 1, "pageSize": 20, "isInRecycleBin": False, "nameLike": vm_name}
        response = self.session.post(vm_url, json=payload, verify=False)
        logger.info("id_of_vm response", response.json())
        if response.status_code == 200:
            data_list = response.json().get("data", [])
            if data_list:
                sourcevmid = data_list[0]["id"]
                logger.info("sourcevmid:", sourcevmid)
                #status = data_list[0]["status"]
                #logger.info("status", status)
                #taskStatus = data_list[0]["taskStatus"]
                #logger.info("taskStatus", taskStatus)
                #if status == "START" and taskStatus == "NONE":
                return sourcevmid  # 返回虚拟机信息字典
        return ""

    def disk_info_of_vm(self, vm_id) -> list:
        """
        通过虚拟机名称获取虚拟所挂载的虚拟磁盘的列表
        通过安超API
        返回disk信息已包含云管的副本数和重建优先级。
        """
        url = f"{self.base_url}/api/resource/listDisk"
        logger.info("disk_info_of_vm vm_id:", vm_id)
        payload = {"vdiApplication":False,"vmId":vm_id,"pageNumber":1,"pageSize":20}
        logger.info("disk_info_of_vm payload", payload)
        response = self.session.post(url, json=payload, verify=False)
        logger.info("disk_list_of_vm方法请求返回", response.json())
        disk_ids = []
        if response.status_code == 200:
            disk_result =  response.json().get("data")
            for  l in disk_result:
                if l.get("id") is not None:
                    disk_ids.append([{"diskStoreName": l.get("diskStoreName"),"resource_disk_id": l.get("id"),"mirroringNumber": l.get("mirroringNumber"),"rebuildPriority": l.get("rebuildPriority")}, {"stack_disk_id": l.get("ref")}])

        for item in disk_ids:
            stackdiskid = item[1].get("stack_disk_id")
            pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            match = re.search(pattern, self.base_url)
            hostname = match.group(1) if match else None
            logger.info("stackdiskid:", stackdiskid)
            logger.info("hostname", hostname)
            args = {
                "hostname": hostname,
                "port": 22,
                "username": "cloud",
                "key_path": "id_rsa_cloud",
                "command": '''sudo docker exec  mxsp zklist -i $(arblock show '''+ stackdiskid+ ''' | grep provider_location | awk '{print $4}' | xargs -I {} ls -i /vstor{}/volume-'''+ stackdiskid+ ''' | awk 'NR==1{print $1}' ) -p | grep -E "numberOfMirrors|rebuildPriority"'''
            }
            sshresult = ssh_execute_command(**args)
            sshresult = convert_policy_string_to_dict(sshresult)
            mirrosargs = {
                "hostname": hostname,
                "port": 22,
                "username": "cloud",
                "key_path": "id_rsa_cloud",
                "command": '''sudo docker exec  mxsp zklist -i $(arblock show ''' + stackdiskid + ''' | grep provider_location | awk '{print $4}' | xargs -I {} ls -i /vstor{}/volume-''' + stackdiskid + ''' | awk 'NR==1{print $1}' ) -l |grep  mirror | awk '{print $1}' | sort -u'''
            }
            mirrors =ssh_execute_command(**mirrosargs)
            logger.info("mirrors", mirrors)
            item[1].update(sshresult)
            item[1].update({"mirrorsInfo": mirrors})
            logger.info("item[1]", item[1])
        logger.info("disk_ids:", disk_ids)
        return disk_ids


    def resource_info_of_disk(self, disk_id):
        pass
    def stack_info_of_disk(self, disk_id):

        pass


if __name__ == "__main__":
    server = ArcherServer("admin", "Admin@123", "https://172.118.13.201")
    vm_id = server.id_of_vm("wushan123_10")
    server.disk_info_of_vm(vm_id)
