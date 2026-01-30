from os.path import exists

import requests
import time
import base64
import urllib3


def encodePass(password):
    """
    Encode password for login and createuser API
    :param password: str - plain password
    :return: str - encoded password
    """
    timestamp = int(time.time() * 1000)  # 获取毫秒级时间戳
    newstring = f"cloudcmp{password}_{timestamp}"  # 字符串拼接
    bytes_data = newstring.encode('utf-8')          # UTF-8编码
    encoded_pass = base64.b64encode(bytes_data).decode('utf-8')  # Base64编码并解码为字符串
    return encoded_pass

class VMTestFramework:
    def __init__(self):
        """初始化配置参数"""
        self.base_url = "https://172.118.13.201"  # API基础地址
        self.session = requests.Session()
        self.auth_token = None
        self.timeout = 20 * 60  # 20分钟超时时间
        self.session.verify = False  # 禁用SSL验证
        urllib3.disable_warnings()

    def login(self, username: str, password: str) -> bool:
        """
        POST登录接口，返回认证token并设置会话头和Cookie
        包含：
        - Authorization: Bearer Token
        - Cookie: sessionId=xxx; userId=xxx
        """
        login_url = f"{self.base_url}/api/resource/login"
        payload = {
            "loginName": username,
            "password": encodePass(password),  # 使用密码加密方法
            "loginType": "front"
        }

        # 发送登录请求
        #response = self.session.post(login_url, json=payload)
        response = self.session.post(login_url, json=payload, verify=False)
        print(response.json())
        if response.status_code == 200:
            # 提取响应中的token和sessionID
            response_data = response.json()
            self.auth_token = response_data.get("token")
            session_id = response_data.get("data").get("sessionId")  # 假设响应中包含sessionId字段
            print("sessionId: ", session_id)
            # 固定用户ID（根据实际业务需求调整）
            user_id = response_data.get("data").get("userId")
            print("user_id: ", user_id)
            # 设置认证头
            auth_header = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
            self.session.headers.update(auth_header)

            # 设置Cookie
            #cookie_value = f"sessionId={session_id}; userId={user_id}"
            self.session.cookies.set("sessionId", session_id)  # 推荐使用cookies.set方法
            self.session.cookies.set("userId", user_id)
            # 也可以直接设置Cookie头（两种方式二选一）
            # self.session.headers.update({"Cookie": cookie_value})

            return True
        return False

    def isready_from_vm_name(self, vm_name: str) -> dict:
        """
        返回虚拟机ID
        """
        vm_url = f"{self.base_url}/api/resource/listVirtualMachine"
        payload = {"pageNumber":1,"pageSize":20,"isInRecycleBin":False,"nameLike":vm_name}
        response = self.session.post(vm_url, json=payload, verify=False)
        print("isready_from_vm_name_response", response.json())
        if response.status_code == 200:
            data_list = response.json().get("data", [])
            sourcevmid = data_list[0]["id"]
            print("sourcevmid:", sourcevmid)
            status = data_list[0]["status"]
            print("status", status)
            taskStatus = data_list[0]["taskStatus"]
            print("taskStatus", taskStatus)
            if status == "START" and taskStatus == "NONE":
                return sourcevmid  # 返回虚拟机信息字典
            return ""

    def exists_vm(self, vm_name: str) -> dict:
        """
        返回虚拟机ID
        """
        vm_url = f"{self.base_url}/api/resource/listVirtualMachine"
        payload = {"pageNumber":1,"pageSize":20,"isInRecycleBin":False,"nameLike":vm_name}
        response = self.session.post(vm_url, json=payload, verify=False)
        print("exists_vm_response", response.json())
        if response.status_code == 200:
            data_list = response.json().get("data", [])
            if data_list:
                return True  # 返回虚拟机信息字典
            return False
        return 500

    def clone_vm(self, clonename: str  ,source_vm_id: str) -> str:
        """
        POST克隆虚拟机接口
        返回克隆虚拟机ID
        """
        clone_url = f"{self.base_url}/api/resource/copyVirtualMachineLink"
        payload = {"virtualMachineId":source_vm_id,"interface":[{"netType":"Normal","multyQueueNum":1,"macMethod":"mapping","securityGroupId":"df6b9b2a-5917-4e8c-9ca1-5b6046ed5c97","networkId":"47f728d7-4507-4695-9fc1-a8987bfac00d","nicModel":"vlan","subnets":[{"subnetId":"0ee4d0bc-cf17-4a70-9f2d-bad62d97e916","isDefaultRoute":True}]}],"cpu":1,"sockets":1,"sockets1":1,"cpuMode":"custom","balloonSwitch":False,"isMemMonopoly":False,"memory":2,"numaEnable":False,"compatibilityMode":False,"name":clonename,"count":1,"cloneType":"LINK","isStart":True,"haEnable":True,"priority":1,"cpuLimitEnabled":False,"cpuLimit":None,"cpuShareLevel":"MID","cpuShare":2048}
        response = self.session.post(clone_url, json=payload, verify=False)
        print("clone_response", response.json())
        if response.status_code == 200:
            return response.json().get("data").get("ids")[0]
        return ""

    def poll_clone_status(self, clone_id: str) -> bool:
        """
        轮询克隆虚拟机状态
        直到成功或超时
        """
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            status_url = f"{self.base_url}/vms/{clone_id}"
            response = self.session.get(status_url)

            if response.status_code == 200:
                status = response.json().get("status")
                if status == "ACTIVE":
                    return True
            time.sleep(5)  # 每5秒轮询一次
        return False

    def delete_clone_vm(self, clone_id: str) -> bool:
        """
        DELETE删除克隆虚拟机
        需先确认状态正常
        """
        # 先查询状态
        status_url = f"{self.base_url}/api/resource/deleteVirtualMachine"
        payload = {"ids":[clone_id]}
        response = self.session.post(status_url, json=payload, verify=False)
        if response.status_code == 200:
            return True
        return False


def main():
    """主测试流程"""
    tester = VMTestFramework()

    # 1. 登录
    if not tester.login("admin", "password"):
        print("登录失败，终止测试")
        return

    # 2. 获取原始虚拟机信息
    original_vm = tester.get_vm_info("original_vm")
    if not original_vm:
        print("未找到原始虚拟机")
        return

    # 3. 检查状态并克隆
    if original_vm.get("status") == "ACTIVE":
        clone_id = tester.clone_vm(original_vm.get("id"))
        if not clone_id:
            print("克隆操作失败")
            return

        # 4. 轮询克隆状态
        if tester.poll_clone_status(clone_id):
            print("克隆成功，虚拟机ID:", clone_id)

            # 5. 删除克隆虚拟机
            if tester.delete_clone_vm(clone_id):
                print("克隆虚拟机删除成功")
            else:
                print("删除失败：状态异常或接口错误")
        else:
            print("克隆超时或失败")
    else:
        print("原始虚拟机状态非ACTIVE，跳过克隆")


if __name__ == "__main__":
    f = 1
    while f < 100:
        test = VMTestFramework()
        test.login("admin", "Admin@123")
        svmid = ""
        i = 0
        while svmid=="":
            print("获取源虚拟机ID中:第%i次" % i)
            if i > 10:
                print ("源虚拟机状态未达预期，终止测试")
                exit(0)
            svmid = test.isready_from_vm_name("wushan123_10")
            i = i+1
            time.sleep(20)
        print("源虚拟机ID:", svmid)
        cname = "auto_DS_0002"
        clonevmid = test.clone_vm(cname, svmid)
        print("clonevmid:", clonevmid)
        if clonevmid == "":
            print("未正常获取克隆虚拟机ID")
        print(f"{cname}克隆中：{clonevmid}")

        isreadyc = ""
        j = 0
        while isreadyc=="":
            j = j + 1
            print(f"检测克隆虚拟机是否进入运行中状态：{j}次")
            isreadyc = test.isready_from_vm_name(cname)
            if j > 10:
                print("克隆虚拟机未进入运行中状态，退出测试")
                exit(0)
            time.sleep(60)
        print("删除克隆虚拟机")
        test.delete_clone_vm(isreadyc)

        k = 0
        isreadyc = True
        while isreadyc:
            isreadyc = test.exists_vm(isreadyc)
            time.sleep(10)
            k = k + 1
            if k > 10:
                print("克隆虚拟机未检测到被清理，退出测试")
                exit(0)
        print(f"完成第{f}次克隆虚拟机-删除虚拟机，success")
        f = f + 1