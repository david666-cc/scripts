import requests
import json
import configparser

class Compass():

    def __init__(self, conifg_filename):
        cps_config = configparser.ConfigParser()
        cps_config.read(conifg_filename)
        self.env = cps_config.get('compass', 'env')
        self.domain = cps_config.get('compass', 'domain')
        self.user = cps_config.get('compass', 'user')
        self.password = cps_config.get('compass', 'password', raw=True)
        self.vhost_user = cps_config.get('vhost', 'user')
        self.vhost_password = cps_config.get('vhost', 'password', raw=True)
        self.cargo_name = cps_config.get('cargo', 'name')
        self.cargo_hosts = (cps_config.get('cargo', 'hosts')).split(',')
        self.__session = ""

    # compass登录信息
    def gen_compass_session(self):
        session = requests.Session()
        session.auth = (self.user,self.password)
        session.headers.update({"Content-Type":"application/json"})
        self.__session = session
        return self.__session

    #获取集群名字和id
    def get_cluster_list(self):
        url = "https://%s/hodor/apis/admin.cluster.caicloud.io/v1alpha1/clusters" % (self.domain)
        result = self.__session.get(url)
        cluster_dict = {}
        for cluster in result.json()['clusters']:
            if cluster["status"] == "running":
                cluster_dict[cluster["config"]["cluster_name"]] = cluster["_id"]
        return cluster_dict

    #获取指定集群下的节点信息
    def get_cluster_nodes(self, cluster_id:str):
        url = "https://%s/hodor/apis/admin.cluster.caicloud.io/v2alpha1/clusters/%s/nodes" % (self.domain, cluster_id)
        result = self.__session.get(url)
        print(result.status_code)
        nodes_dict = {}
        for item in result.json()['items']:
            nodes_dict[item["metadata"]["name"]] = item["status"]["addresses"][0]["address"]
        return nodes_dict


class Jumpserver():
    def __init__(self, conifg_filename:str):
        jms_config = configparser.ConfigParser()
        jms_config.read(conifg_filename)
        self.domain = jms_config.get('jumpserver', 'domain')
        self.user = jms_config.get('jumpserver', 'user')
        self.password = jms_config.get('jumpserver', 'password', raw=True)
        self.__session = ""

    #jumpserver登录session
    def gen_jumpserver_session(self):
        session = requests.Session()
        session.headers.update({"Content-Type":"application/json"})
        payload = "{\"username\": \"%s\", \"password\": \"%s\"}" % (self.user, self.password)
        url="https://%s/api/v1/authentication/auth/" % (self.domain)
        result = session.post(url, data=payload)
        print(result)
        if result.status_code == 400:
            print("jumpserver登录认证失败")
        jumpserver_token = result.json()["token"]
        session.headers["Authorization"] = "Bearer %s" % (jumpserver_token)
        self.__session = session
        return self.__session
    
    #创建节点树
    def create_node(self, node_name):
        url="https://%s/api/v1/assets/nodes/" % (self.domain)
        payload={'value': node_name}
        payload = json.dumps(payload)
        result = self.__session.post(url, data=payload)
        if result.status_code == 201:
            return result.json()["id"]
        return result.status_code

    #获取节点树的uuid
    def get_node_uuid(self, node_name):
        url="https://%s/api/v1/assets/nodes/" % (self.domain)
        result = self.__session.get(url)
        print(result.json())
        for item in result.json():
            if item["value"].lower() == node_name.lower():
                node_uuid = item["id"]
                print(node_name, "节点的uuid是：", node_uuid)
        return node_uuid

    #创建管理用户，root权限，推送系统用户，获取资产信息使用，如果不想给，可以随便设置一个密码
    def create_admin_user(self, admin_user_name, admin_user_password, name):
        url="https://%s/api/v1/assets/admin-users/" % (self.domain)
        #这里password加了引号，也就是错误的密码
        payload = {"name": name,"password": "password","username": admin_user_name}
        payload = json.dumps(payload)
        result = self.__session.post(url, data=payload)
        status_code = result.status_code
        return status_code

    #获取服务器管理用户的uuid,这里默认获取的系统用户就是我们刚开始创建的用户
    def get_admin_user_uuid(self, admin_user_name):
        url="https://%s/api/v1/assets/admin-users/" % (self.domain)
        result = self.__session.get(url)
        for item in result.json():
            if item["name"] == admin_user_name:
                admin_user_uuid = item["id"]
        return admin_user_uuid

    #创建系统用户，连接资产时候使用的用户
    def create_system_user(self, system_user_name, system_user_password, name):
        url="https://%s/api/v1/assets/system-users/" % (self.domain)
        payload = {"name": name,"password": system_user_password,"username": system_user_name, "auto_push": "false"}
        payload = json.dumps(payload)
        result = self.__session.post(url, data=payload)
        status_code = result.status_code
        return status_code

    #获取jumpserver系统用户的uuid
    def get_system_user_uuid(self, system_user):
        url="https://%s/api/v1/assets/system-users/" % (self.domain)
        result = self.__session.get(url)
        for item in result.json():
            if item["name"] == system_user:
                system_user_uuid = item["id"]
        return system_user_uuid

    #获取jumpserver登录用户uuid
    def get_jumpserver_user_uuid(self, jumpserver_user):
        url="https://%s/api/v1/users/users" % (self.domain)
        result = self.__session.get(url)
        for item in result.json():
            if item["username"] == jumpserver_user:
                jumpserver_user_uuid = item["id"]
        return jumpserver_user_uuid



    #创建资产，资产就是服务器
    def create_asset(self, hostname, ip, admin_user, nodes):
        url="https://%s/api/v1/assets/assets/" % (self.domain)
        print(hostname, ip, admin_user, nodes, self.domain)
    #     asset_info = """{
    #       "hostname": "hostname",
    #       "ip": "ip",
    #       "is_active": true,
    #       "admin_user": admin_user,
    #       "platform": "Linux",
    #       "nodes": [
    #           "nodes"
    #       ]
    #     }"""
        payload="{\n  \"hostname\": \"xcb-web1\",\n  \"ip\": \"10.9.9.9\",\n  \"is_active\": true,\n  \"admin_user\": \"e90a89d7-0a51-4e1b-bf3c-f1f6e72ba3be\",\n  \"platform\": \"Linux\",\n  \"nodes\": [\n    \"07ac235b-42f8-402f-93bd-3a234c797116\"\n  ]\n}"
        payload = payload.replace("xcb-web1", hostname)
        payload = payload.replace("10.9.9.9", ip)
        payload = payload.replace("e90a89d7-0a51-4e1b-bf3c-f1f6e72ba3be", admin_user)
        payload = payload.replace("07ac235b-42f8-402f-93bd-3a234c797116", nodes)
        result = self.__session.post(url, data = payload)
    

    #节点授权
    def perms_asset_permissions_create(self, jumpserver_user_uuid, system_user_uuid, jumpserver_node_uuid, permission_name):
        url="https://%s/api/v1/perms/asset-permissions/" % (self.domain)
        payload="{\"assets\":[],\"nodes\":[\"4b2764b9-2243-4417-8a30-fe37fee0d1d9\"],\"actions\":[\"all\"],\"is_active\":true,\"date_start\":\"2021-01-24T08:39:14.836Z\",\"date_expired\":\"2120-12-31T08:39:14.836Z\",\"name\":\"admin\",\"users\":[\"f7777903-835c-4d88-a515-7e6cdc9e719e\"],\"system_users\":[\"54c26b11-e867-406c-bdf5-ef8892ecb192\"]}"
        payload = payload.replace("f7777903-835c-4d88-a515-7e6cdc9e719e", jumpserver_user_uuid)
        payload = payload.replace("54c26b11-e867-406c-bdf5-ef8892ecb192", system_user_uuid)
        payload = payload.replace("4b2764b9-2243-4417-8a30-fe37fee0d1d9", jumpserver_node_uuid)
        payload = payload.replace("admin", permission_name)
        result = self.__session.post(url, data = payload)
        print(jumpserver_user_uuid, system_user_uuid, self.domain)



    #删除节点下所有资产，spm值我也不知道是啥
    def asset_delete_all(self, nodes):
        url = "https://%s/api/v1/assets/assets/?node_id=%s&show_current_asset=0&spm=4a64225a-eeeb-465c-bbaf-975e6a105c30" % (self.domain, nodes)
        result = self.__session.delete(url)
        print("删除节点结果：", result.status_code)
