from flask import Flask, request, render_template_string, jsonify, render_template, session
import requests
import re
from datetime import datetime
from utils.audit import  ArcherAudit
from TestCaseApp.licensemake1 import LicenseService

from lib.ArcherTestToolServer import ArcherServer
from lib.Hosts import Hosts
from lib.Images import Images
from utils.audit import ArcherAudit
app = Flask(__name__, template_folder="../templates")
app.secret_key = 'a7b1d8e0f9c2d3a4e5b6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8'

@app.route('/', methods=['GET', 'POST'])
def index():
    result = ""
    return render_template('tools.html', result=result)

@app.route('/disk/disk_info', methods=['GET'])
def disk_info():
    server_ip = request.args.get('serverip')
    session['server_ip'] = server_ip
    return render_template('disk_info.html', serverip = server_ip)

@app.route('/disk/check_disk_info', methods=['POST'])
def check_disk_info():
    print("session serverip:", session['server_ip'])
    vmname = request.form['instance_name']
    print("from form vmname:", vmname)
    session['vmname'] = vmname
    server = ArcherServer("admin", "Admin@123", session['server_ip'])
    vm_id = server.id_of_vm(vmname)
    if vm_id=="":
        return render_template('disk_info.html', serverip=session['server_ip'], result="", vmname=vmname)
    print("app vmid:", vm_id)
    result = server.disk_info_of_vm(vm_id)
    print(result)
    return render_template('disk_info.html', serverip = session['server_ip'] ,result = result,vmname = vmname )

@app.route('/image/upload', methods=['GET','POST'])
def upload_image():
    if request.method == 'GET':
        server_ip = request.args.get('serverip')
        session['server_ip'] = server_ip
        print("session serverip:", server_ip)
        host = Hosts("admin", "Admin@123", server_ip)
        storInfo  = host.getHostStorInfo()
        return render_template('image.html', serverip = session['server_ip'] ,result = storInfo )
    if request.method == 'POST':
        data = request.get_json()
        print("post data", data)
        imagestool = Images("admin", "Admin@123", session['server_ip'])
        host = Hosts("admin", "Admin@123", session['server_ip'])
        print("ip:{}.架构is_X86{},zoneID{},storageType{},storageManageId({}".format(session['server_ip'], host.is_X86(),data["zoneId"],data["storageType"],data["storageManageId"]))
        if host.is_X86():
            imagestool.upload_isos_x86(data["zoneId"], data["storageType"], data["storageManageId"])
        elif data["storageType"] == "ARSTOR":
            imagestool.upload_images_arm_raw(data["zoneId"], data["storageType"], data["storageManageId"])
        else:
            imagestool.upload_images_arm_qcow2(data["zoneId"], data["storageType"], data["storageManageId"])
        return jsonify({
            "status": "success",
            "message": "Upload request received",
            "request_id": "REQ_123456"
        })

@app.route('/license/import', methods=['GET','POST'])
def import_license():
    if request.method == 'GET':
        server_ip = request.args.get('serverip')
        session['server_ip'] = server_ip
        print("session serverip:", server_ip)
        host = Hosts("admin", "Admin@123", server_ip)
        clusterinfo  = host.getClusterInfo()
        return render_template('license.html', serverip = session['server_ip'] ,result = clusterinfo )
    if request.method == 'POST':
        password = request.form.get('password')
        cluster_id = request.form.get('clusterId')
        arch_type = request.form.get('archType')
        archerAudit = ArcherAudit("admin", password, session['server_ip'])
        if not archerAudit.setSession():
            return jsonify({
            "success": False,
            "message": "admin密码不对",
            "request_id": "REQ_123456"
        })
        licensetxt = LicenseService.get_permit_info(cluster_id, arch_type, 100,30,100,100,100,"2026-12-31")
        licensetxt = licensetxt.get("pgp_message")
        print("app  licensetxt:",licensetxt)
        host = Hosts("admin", password, session['server_ip'])
        lid = host.getLicenseId()
        host.updateLicense(licensetxt,lid)
        return jsonify({
            "success": True,
            "message": "导入操作完成",
            "request_id": "REQ_123456"
        })


@app.route('/<path:path>')
def handle_undefined_paths(path):
    return render_template('tools.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)