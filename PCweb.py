import os, json
from PCfunctions import *
from flask import Flask, request, render_template, redirect, url_for, flash, send_file, Response, send_from_directory
from flask_cors import CORS


app = Flask(__name__)
CORS(app)
app.secret_key = 'PowerControlWeb'

# 首页跳转
@app.route('/', methods=['GET', 'POST'])
def home():
    return send_file('PowerControl教程.pdf', mimetype='application/pdf')

# 配置页
@app.route('/config', methods=['GET', 'POST'])
def index():
    yaml_config = Web_data.df.read_config_yaml()
    if not bool(yaml_config):
        return '配置文件读取失败，检查权限' ,500
    # 获取请求中的密钥
    web_key = request.args.get('key')
    if web_key != Web_data.web_key:
        return '请在url中填入正确的key', 401
    if request.method == 'POST':
        # 获取表单数据
        yaml_config['bemfa']['enabled'] = bool(request.form.get('bemfa.enabled'))
        yaml_config['bemfa']['uid'] = trans_str(request.form.get('bemfa.uid'))
        yaml_config['bemfa']['topic'] = trans_str(request.form.get('bemfa.topic'))
        yaml_config['devices']['name'] = trans_str(request.form.get('devices.name'))
        yaml_config['devices']['ip'] = trans_str(request.form.get('devices.ip'))
        yaml_config['devices']['wol']['enabled'] = bool(request.form.get('devices.wol.enabled'))
        yaml_config['devices']['wol']['mac'] = trans_str(request.form.get('devices.wol.mac'))
        yaml_config['devices']['shutdown']['enabled'] = bool(request.form.get('devices.shutdown.enabled'))
        yaml_config['devices']['shutdown']['method']['netrpc'] = bool(request.form.get('devices.shutdown.method.netrpc'))
        yaml_config['devices']['shutdown']['method']['udp'] = bool(request.form.get('devices.shutdown.method.udp'))
        yaml_config['devices']['shutdown']['account'] = trans_str(request.form.get('devices.shutdown.account'))
        yaml_config['devices']['shutdown']['password'] = trans_str(request.form.get('devices.shutdown.password'))
        yaml_config['devices']['shutdown']['time'] = trans_str(request.form.get('devices.shutdown.time'))
        yaml_config['devices']['ping']['enabled'] = bool(request.form.get('devices.ping.enabled'))
        yaml_config['devices']['ping']['time'] = trans_str(request.form.get('devices.ping.time'))
        yaml_config['functions']['log']['enabled'] = bool(request.form.get('functions.log.enabled'))
        yaml_config['functions']['log']['level'] = trans_str(request.form.get('functions.log.level'))
        yaml_config['functions']['push_notifications']['enabled'] = bool(request.form.get('functions.push_notifications.enabled'))
        yaml_config['functions']['push_notifications']['ServerChan_turbo']['enabled'] = bool(request.form.get('functions.push_notifications.ServerChan_turbo.enabled'))
        yaml_config['functions']['push_notifications']['ServerChan_turbo']['SendKey'] = trans_str(request.form.get('functions.push_notifications.ServerChan_turbo.SendKey'))
        yaml_config['functions']['push_notifications']['ServerChan_turbo']['channel'] = trans_str(request.form.get('functions.push_notifications.ServerChan_turbo.channel'))
        yaml_config['functions']['push_notifications']['ServerChan3']['enabled'] = bool(request.form.get('functions.push_notifications.ServerChan3.enabled'))
        yaml_config['functions']['push_notifications']['ServerChan3']['SendKey'] = trans_str(request.form.get('functions.push_notifications.ServerChan3.SendKey'))
        yaml_config['functions']['push_notifications']['Qmsg']['enabled'] = bool(request.form.get('functions.push_notifications.Qmsg.enabled'))
        yaml_config['functions']['push_notifications']['Qmsg']['key'] = trans_str(request.form.get('functions.push_notifications.Qmsg.key'))
        yaml_config['functions']['push_notifications']['Qmsg']['qq'] = trans_str(request.form.get('functions.push_notifications.Qmsg.qq'))
        
        # 保存配置
        save_yaml = Web_data.df.write_config_yaml(yaml_config)
        if save_yaml == True:
            flash(get_time() + '\n' +'配置保存成功，请重启服务或容器生效')
        else:
            flash(get_time() + '\n' +'配置保存失败：' + str(save_yaml))
        return redirect(url_for('index')+ f'?key={web_key}')
    if not Web_data.ping_enabled:
        flash(get_time() + '\n' +'未启用ping，设备状态未知')
    else:
        flash(get_time() + '\n' + Web_data.device_name + ' ' + Web_data.df.pc_state[0])
    return render_template('index.html', config=yaml_config, run_time= Web_data.df.run_time())

# 关机
@app.route('/shutdown', methods=['GET', 'POST'])
def shutdown():
    # 获取请求中的密钥
    web_key = request.args.get('key')
    if web_key != Web_data.web_key:
        return '请在url中填入正确的key', 401
    rs = pcshutdown()
    if rs:
        if 'succeeded' in rs:
            print_and_log("[Web]已发送关机指令",2)
            send_message('已发送关机指令')
            return Web_data.device_name + '已发送关机指令', 200  # 返回200 OK状态码
        else:
            print_and_log("[Web]关机指令发送失败："+ rs ,3)
            send_message('关机指令发送失败')
            return Web_data.device_name + '发送关机指令失败，检查配置或是否已经离线', 200
    else:
        print_and_log('[Web]未启用远程关机！' ,3)
        send_message('未启用远程关机！')
        return '未启用远程关机！', 403

# 网络唤醒
@app.route('/wol', methods=['GET', 'POST'])
def wol():
    web_key = request.args.get('key')
    if web_key != Web_data.web_key:
        return '请在url中填入正确的key', 401
    rs = pcwol()
    if rs:
        if rs == True:
            print_and_log("[Web]已发送唤醒指令" , 2)
            send_message('已发送唤醒指令')
            return Web_data.device_name + '已发送唤醒指令', 200  # 返回200 OK状态码
        else:
            print_and_log("[Web]发送唤醒指令失败:" + rs , 3)
            send_message('发送唤醒指令失败')
            return Web_data.device_name + '发送唤醒指令失败', 200
    else:
        print_and_log('[Web]未启用网络唤醒！' ,3)
        send_message('未启用网络唤醒！')
        return '未启用网络唤醒！', 403

# ping
@app.route('/ping', methods=['GET', 'POST'])
def ping():
    web_key = request.args.get('key')
    if web_key != Web_data.web_key:
        return '请在url中填入正确的key', 401
    if not Web_data.ping_enabled:
        return '未启用ping!', 403
    try:
        ping_result = pcping()
        if 'Reply' in ping_result:
            rs = {"device_name": Web_data.device_name, "device_status_cn": "在线" ,"device_status": "on" , "ping_result" : ping_result}
        elif 'timed out' in ping_result:
            rs = {"device_name": Web_data.device_name, "device_status_cn": "离线" ,"device_status": "off" , "ping_result" : ping_result}
        return Response(
                json.dumps(rs, ensure_ascii=False),
                mimetype='application/json; charset=utf-8'
            ), 200
    except Exception as e:
        return 'error:' + str(e) ,200

# restart
@app.route('/restart', methods=['POST'])
def restart():
    # 获取请求中的密钥
    web_key = request.args.get('key')
    if web_key == Web_data.web_key:
        os._exit(0)

# 测试消息推送
@app.route('/testpush', methods=['GET'])
def testpush():
    web_key = request.args.get('key')
    if web_key != Web_data.web_key:
        return '请在url中填入正确的key', 401
    rs = send_message('PowerControl消息推送测试')
    rs = {key: value for key, value in rs.items() if value is not None}
    if rs:
        return Response(
                json.dumps(rs, ensure_ascii=False),
                mimetype='application/json; charset=utf-8'
            ), 200
    else:
        return '至少启用一个推送通道'

# 更新日志
@app.route('/changelog', methods=['GET'])
def change_log():
    try:
        # 读取 change.log 文件内容
        with open('change.log', 'r', encoding='GBK') as file:
            log_content = file.read()
        
        # 返回文件内容，并设置合适的 Content-Type
        return Response(log_content, mimetype='text/plain')
    except FileNotFoundError:
        return "error", 404

# 下载
@app.route('/download', methods=['GET'])
def download():
    return send_from_directory('static', 'PCshutdown.exe', as_attachment=True)

# 代码
@app.route('/code', methods=['GET'])
def copy_code():
    return render_template('code.html')
'''---------------------------------------------------------------------------------'''
class Web_data():
    web_key=''
    df = None
    device_name=''
    ping_enabled = False
class PCweb():
    def __init__(self, web_port, web_key, data_funcs):
        self.web_port = web_port
        self.web_key = web_key
        self.df = data_funcs
        print_and_log("web初始化成功",2)
    def set_web_data(self):
        Web_data.web_key = self.web_key
        Web_data.df =self.df
        Web_data.ping_enabled = self.df.ping_enabled
        Web_data.device_name = self.df.device_name
    def run(self):
        self.set_web_data()
        print_and_log("web服务启动", 2)
        app.run(host=self.df.local_ip, port=self.web_port)
        

if __name__ == '__main__':
    pass