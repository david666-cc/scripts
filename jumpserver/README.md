##  **RESTful API练手** :writing_hand:

---

通过api将compass集群和节点信息输出到jumpserver管理。(仅供参考。python初级用户，仅仅为了实现某些功能。)

### 文件结构

```bash
├── README.md
├── cps-idc-prod.ini		#compass 环境配置信息
├── cps-idc-stg.ini			#compass 环境配置信息
├── jms-config.ini			#jumpserver 环境登陆信息
├── jumpserver_v2.py		#compass和jumpserver相关方法
├── main.py					#主函数文件
└── sendmail.py				#邮件发送jumpserver资产信息
```

### 使用方法

- 1、每个compass环境信息写一个配置文件
- 2、jumpserver环境信息写一个配置文件
- 3、修改main.py
- 4、python3 main.py
- (可选)5、sendmail.py：创建cronjob，定时发送资产信息到邮箱

### 注意事项

- 1、python模块需要提前安装，没有版本限制
  - requests：模拟HTTP请求
  - configparser：操作配置文件
  - email,smtplib：发送邮件
  - pandas：数据分析
- 2、全部使用https接口。务必配置https证书，哪怕是自签的。
- 3、所有集群的名字都要是唯一的，需要提前修改好。