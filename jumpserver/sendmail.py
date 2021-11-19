import requests
import smtplib
import os
import pandas as pd
from jumpserver_v2 import Jumpserver
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
from email.mime.multipart import MIMEMultipart


SENDER_PASSWORD = ''
SENDER_EMAIL = 'xxx@xxx.cn'
SMTP_SERVER = 'smtp.xxx.net'
# SMTP_PORT = 465

TO_MAIL = ['xxx@xxx.com']

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))

def send_mail(file):
    sender = SENDER_EMAIL
    receivers = TO_MAIL  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
    # 三个参数：第一个为文本内容，第二个 plain 设置文本格式，第三个 utf-8 设置编码
    #HTML = '<html> <body><h1> GDS Jumpserver 资产信息</h1> </html>'
    content = MIMEText(html, 'html', 'utf-8')
    message = MIMEMultipart()
    message.attach(content)
    subject = 'jumpserver 资产信息'
    message['From'] = _format_addr('devops团队 <%s>' % SENDER_EMAIL)
    message['Subject'] = Header(subject, 'utf-8')
    message['To'] = ";".join(TO_MAIL)
 
    att = MIMEText(open(file, 'rb').read(), 'base64', 'utf-8')
    filename = os.path.basename(file)
    att["Content-Disposition"] = 'attachment; filename={}'.format(filename)
    message.attach(att)

    try:
        # smtpObj = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        # smtpObj.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtpObj = smtplib.SMTP(SMTP_SERVER)
        smtpObj.sendmail(sender, receivers, message.as_string())
        print ("邮件发送成功")
    except smtplib.SMTPException:
        print ("Error: 无法发送邮件")

if __name__ == '__main__':
    #配置文件使用绝对路径
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    jms_file = os.path.join(BASE_DIR, "jms.csv")
    jms_config = os.path.join(BASE_DIR, " jms-config.ini")
    my_jms = Jumpserver(jms_config)
    my_jms_session = my_jms.gen_jumpserver_session()


    #html表格添加漂亮的边框
    style2="""
        <style type="text/css">
        table {
        border-right: 1px solid #99CCFF;
        border-bottom: 1px solid #99CCFF;
        }
        table td {
        border-left: 1px solid #99CCFF;
        border-top: 1px solid #99CCFF;
        }

        table th {
        border-left: 1px solid #99CCFF;
        border-top: 1px solid #99CCFF;
        }

        </style>
    """

    r = my_jms_session.get("https://%s/api/v1/assets/assets/?format=csv" % my_jms.domain)

    with open(jms_file, 'w') as f:
        f.write(r.text)
    #清洗数据，删除空列
    df = pd.read_csv(jms_file)
    df = df.dropna(axis=1, how='any', thresh=None, subset=None, inplace=False)
    df.to_csv(jms_file)
    #筛选数据，保留cargo和master节点机器
    df = df[['*主机名', '*IP', '管理用户名称', '*系统平台', '节点名称']][df['*主机名'].str.contains('master|cargo')]
    #生成html并修改样式
    df_html = df.to_html(index=True)
    html=str(df_html).replace('<table border="1" class="dataframe">','<table border="0" class="dataframe" style="width:100%" cellspacing="2" cellpadding="2">')
    html=str(html).replace('<tr style="text-align: right;">',' <div style="text-align:center;width:100%;padding: 8px; line-height: 1.42857; vertical-align: top; border-top-width: 1px; border-top-color: rgb(221, 221, 221); background-color: #3399CC;color:#fff"><strong><font size="4">GDS Jumpserver资产信息(完整资产信息见附件)</font></strong></div><tr style="background-color:#FFCC99;text-align:center;">')
    html=str(html).replace('<tr>','<tr style="text-align:center">')
    html=str(html).replace('<th></th>','<th>num</th>')
    html += style2

    send_mail(jms_file)
