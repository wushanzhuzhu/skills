from flask import Flask, request, render_template_string, jsonify, render_template
import requests
import re
from datetime import datetime
app = Flask(__name__, template_folder="templates")


class LicenseService:
    """
    许可证服务类
    包含完整的JMeter流程实现
    """

    @staticmethod
    def get_permit_info(clusterId, architecture, numNodes, length, numCPUs, numArstorCPUs, numArstorNodes, serviceDate):
        """
        执行完整的许可证处理流程：
        1. 登录获取会话
        2. 创建permit
        3. 导入license
        4. 提取PGP消息
        """
        # 创建会话保持cookie
        session = requests.Session()

        # 1. 登录获取会话ID
        login_url = "http://178.104.163.119:8082/login"
        login_data = {
            "ajax": "false",
            "password": "Admin@123",
            "username": "wushan"
        }

        login_resp = session.post(login_url, data=login_data)
        if login_resp.status_code != 200:
            raise Exception("登录失败")

        # 2. 创建permit
        permit_url = "http://178.104.163.119:8082/api/v3/permit/post"
        if length > 30:
            length = 30
        permit_data = {
            "partyUuid": "a7d2-6187-bf9a-4998-bb19",
            "description": "",
            "permitType": "Premium",
            "numNodes": numNodes,
            "capacity": 0,
            "length": length,
            "timeUnit": "Days",
            "count": 1,
            "partial": 0,
            "version": "3.2.1",
            "productTag": "ArcherOS 5.0",
            "architecture": architecture,
            "numCPUs": numCPUs,
            "numVMs": 0,
            "numArstorCPUs": numArstorCPUs,
            "numArstorNodes": numArstorNodes,
            "serviceDate": serviceDate
        }

        permit_resp = session.get(permit_url, params=permit_data)
        if permit_resp.status_code != 200:
            raise Exception("创建permit失败")

        # 解析permit ID
        permit_id = re.search(r'\"uuid\":\s*\"([^\"]+)\"', permit_resp.text).group(1)

        # 3. 导入license
        import_url = "http://178.104.163.119:8082/api/v3/lic/public/post"
        import_data = {
            "clusterId": clusterId,
            "permits": permit_id,
            "siteInfo": "ONLYforTEST",
            "companyName": "内部测试用",
            "partyUuid": "a7d2-6187-bf9a-4998-bb19"
        }

        print("LicenseService import_data:", import_data)

        import_resp = session.get(import_url, params=import_data)
        print("LicenseService import_resp:", import_resp)

        if import_resp.status_code != 200:
            raise Exception("导入license失败")

        # 4. 提取PGP消息
        pgp_match = re.search(
            r'-----BEGIN PGP MESSAGE-----([\s\S]+?)-----END PGP MESSAGE-----',
            import_resp.text
        )

        if not pgp_match:
            raise Exception("未找到PGP消息")

        return {
            "clusterId": clusterId,
            "architecture": architecture,
            "permit_id": permit_id,
            "pgp_message": pgp_match.group(0).strip(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


@app.route('/permit', methods=['POST'])
def permit_endpoint():
    """
    Flask端点：/permit
    返回许可证处理结果
    """
    arch = request.form['arch']
    cluster_id = request.form['cluster_id']
    numNodes = request.form['numNodes']
    length = request.form['length']
    numCPUs = request.form['numCPUs']
    numArstorCPUs = request.form['numArstorCPUs']
    numArstorNodes = request.form['numArstorNodes']
    serviceDate = request.form['cert_start_date']
    print("serviceDate:%s",serviceDate)
    try:
        result = LicenseService.get_permit_info(cluster_id, arch, numNodes, length, numCPUs, numArstorCPUs, numArstorNodes, serviceDate)
        return render_template('index.html', result=result)
    except Exception as e:
        return f"处理失败: {str(e)}", 500

@app.route('/', methods=['GET', 'POST'])
def index():
    result = ""
    if request.method == 'POST':
        # 获取用户输入
        arch = request.form['arch']
        cluster_id = request.form['cluster_id']

        try:
            # 创建会话保持登录状态
            with requests.Session() as session:
                # 模拟登录
                response = session.post(LOGIN_ENDPOINT, data=CREDENTIALS, timeout=5)
                response.raise_for_status()

                # 调用令牌生成API
                token_response = session.post(
                    TOKEN_ENDPOINT,
                    json={"arch": arch, "cluster_id": cluster_id},
                    timeout=5
                )
                token_response.raise_for_status()

                # 提取授权字符串
                result = token_response.json().get('auth_token', '未获取到有效token')

        except requests.exceptions.RequestException as e:
            result = f"请求失败: {str(e)}"
        except Exception as e:
            result = f"处理失败: {str(e)}"
    return render_template('index.html', result=result)


if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=5000, debug=True)
    data = f'2026-12-31'
    s = LicenseService.get_permit_info("2c9c820e-f011d9d5-ad967996-583dbee2", "X86", 100,30,100,100,100,data)
    print (s)