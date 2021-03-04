import json
import requests
import base64
import configparser

#将compass用户名和密码base64加密放到http请求头里面
def BasicAuthHeaders(user, password):
    user_pass = "%s:%s" % (user, password)
    tmp = base64.b64encode(user_pass.encode('utf-8'))
    user_pass_base64 = str(tmp,'utf-8')
    headers = {
        'Content-Type': 'application/json'
    }
    headers["Authorization"] = "Basic %s" % (user_pass_base64)
    return headers
#获取compass平台所有集群名字和id
def GetClusterList(compass_host,headers):
    url = "http://%s:6002/apis/admin.cluster.caicloud.io/v1alpha1/clusters" % (compass_host)
    r = requests.get(url, headers=headers)
    cluster_dict = {}
    for cluster in r.json()['clusters']:
        if cluster["status"] == "running":
            cluster_dict[cluster["config"]["cluster_name"]] = cluster["_id"]
    return cluster_dict
#jumpserver登录获取token信息,并返回新的headers
def GetJumpserverToken(jumpserver_host, headers, user, password):
    payload = "{\"username\": \"%s\", \"password\": \"%s\"}" % (user, password)
    url="http://%s/api/v1/authentication/auth/" % (jumpserver_host)
    r = requests.post(url, headers=headers, data=payload)
    token = r.json()["token"]
    headers["Authorization"] = "Bearer %s" % (token)
    return headers
#创建资产节点树
def CreateJumpserverNode(jumpserver_host, headers, node):
    url="http://%s/api/v1/assets/nodes/" % (jumpserver_host)
    payload={'value': node}
    payload = json.dumps(payload)
#     r = requests.post(url, headers, data=payload)
    r = requests.request("POST", url, headers=headers, data=payload)
    if r.status_code == 201:
        return r.json()["id"]
    return r.status_code

#获取节点树的uuid
def GetAssetsNodeUUID(jumpserver_host, headers, node_name):
    print(node_name)
    url="http://%s/api/v1/assets/nodes/" % (jumpserver_host)
    r = requests.get(url, headers=headers)
    print(r.json())
    for item in r.json():
        if item["value"] == node_name:
            AssetsNodeUUID = item["id"]
            print(AssetsNodeUUID)
    return AssetsNodeUUID


#获取指定集群内节点信息
def GetClusterNode(compass_host, cluster_id, headers):
    url = "http://%s:6002/apis/admin.cluster.caicloud.io/v2alpha1/clusters/%s/nodes" % (compass_host, cluster_id)
    r = requests.get(url, headers=headers)
    node_dict = {}
    for item in r.json()['items']:
        node_dict[item["metadata"]["name"]] = item["status"]["addresses"][0]["address"]
    return node_dict
#创建管理用户和系统用户，这里统一为一个，为具有sudo权限的用户
#管理用户是用来统计资产信息，推送系统用户的，如果不需要，可以随便设置一个用户，必须要有，因为创建资产时候要填
#系统用户是用来登录服务器的，这个必须填对，必须创建，否则登录不了机器
#20210125更新，管理用户不给了，权限太高
def CreateAdminUser(jumpserver_host, headers, user, password):
    url="http://%s/api/v1/assets/admin-users/" % (jumpserver_host)
    payload = {"name": user,"password": "password","username": user}
    payload = json.dumps(payload)
    #print(payload)
    r = requests.post(url, headers=headers, data=payload)
    status_code = r.status_code
    #print(r.json())
    return status_code
#jumpserver创建系统用户
def CreateSystemUser(jumpserver_host, headers, user, password):
    url="http://%s/api/v1/assets/system-users/" % (jumpserver_host)
    payload = {"name": user,"password": password,"username": user, "auto_push": "false"}
    payload = json.dumps(payload)
    #print(payload)
    r = requests.post(url, headers=headers, data=payload)
    status_code = r.status_code
    #print(r.json())
    return status_code
#获取服务器管理用户的uuid,这里默认获取的系统用户就是我们刚开始创建的用户
def GetAdminUserUUID(jumpserver_host, headers, user):
    url="http://%s/api/v1/assets/admin-users/" % (jumpserver_host)
    r = requests.get(url, headers=headers)
    for item in r.json():
        if item["name"] == user:
            AdminUserUUID = item["id"]
    return AdminUserUUID

#获取jumpserver平台管理员用户的uuid
def GetJumpserverAdminUserUUID(jumpserver_host, headers, user):
    url="http://%s/api/v1/users/users" % (jumpserver_host)
    r = requests.get(url, headers=headers)
    for item in r.json():
        if item["name"] == user:
            JumpserverAdminUserUUID = item["id"]
    return JumpserverAdminUserUUID

#获取jumpserver系统用户的uuid
def GetJumpserverSystemUserUUID(jumpserver_host, headers, user):
    url="http://%s/api/v1/assets/system-users/" % (jumpserver_host)
    r = requests.get(url, headers=headers)
    for item in r.json():
        if item["name"] == user:
            JumpserverAdminUserUUID = item["id"]
    return JumpserverAdminUserUUID



def AssetCreate(hostname, ip, admin_user, nodes, jumpserver_host, headers):
    url="http://%s/api/v1/assets/assets/" % (jumpserver_host)
    print(hostname, ip, admin_user, nodes, jumpserver_host, headers)
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
    r = requests.request("POST",url, headers = headers, data = payload)
#资产授权
def perms_asset_permissions_create(user, system_user, cluster_node_uuid, jumpserver_host, jumpserver_headers):
    url="http://%s/api/v1/perms/asset-permissions/" % (jumpserver_host)
    payload="{\"assets\":[],\"nodes\":[\"4b2764b9-2243-4417-8a30-fe37fee0d1d9\"],\"actions\":[\"all\"],\"is_active\":true,\"date_start\":\"2021-01-24T08:39:14.836Z\",\"date_expired\":\"2120-12-31T08:39:14.836Z\",\"name\":\"admin\",\"users\":[\"f7777903-835c-4d88-a515-7e6cdc9e719e\"],\"system_users\":[\"54c26b11-e867-406c-bdf5-ef8892ecb192\"]}"
    payload = payload.replace("f7777903-835c-4d88-a515-7e6cdc9e719e", user)
    payload = payload.replace("54c26b11-e867-406c-bdf5-ef8892ecb192", system_user)
    payload = payload.replace("4b2764b9-2243-4417-8a30-fe37fee0d1d9", cluster_node_uuid)
    r = requests.request("POST", url, headers = jumpserver_headers, data = payload)
    print(user, system_user, r.json())

# 删除default分支下面所有资产
def asset_delete_all(nodes, jumpserver_host, jumpserver_headers):
    url = "http://%s/api/v1/assets/assets/?node_id=%s&show_current_asset=0&spm=4a64225a-eeeb-465c-bbaf-975e6a105c30" % (jumpserver_host, nodes)
    payload = {}
    r = requests.request("DELETE", url, headers = jumpserver_headers, data = payload)
    print("删除节点结果：", r.status_code)


if __name__=='__main__':
    config = configparser.ConfigParser()
    config.read('./config.ini')
    # jumpserver的地址,登录用户，密码
    jumpserver_host = config.get('jumpserver', 'host')
    jumpserver_user = config.get('jumpserver', 'user')
    jumpserver_password = config.get('jumpserver', 'password', raw=True)
    # compass的地址，登录用户，密码
    compass_host = config.get('compass', 'host')
    compass_user = config.get('compass', 'user')
    compass_password = config.get('compass', 'password', raw=True)
    # 服务器的登录用户名和密码
    vhost_user = config.get('vhost', 'user')
    vhost_password = config.get('vhost', 'password', raw=True)
    cargo_name = config.get('cargo', 'name')
    cargo_hosts = (config.get('cargo', 'hosts')).split(',')
    print(cargo_hosts)


    #将认证信息转换成http请求头
    compass_headers = BasicAuthHeaders(compass_user, compass_password)

    #获取compass平台里面的集群名字和uuid
    cluster_dict = GetClusterList(compass_host, compass_headers)
    #获取jumpserver登录token
    jumpserver_headers = {
        'Content-Type': 'application/json'
    }
    jumpserver_headers = GetJumpserverToken(jumpserver_host, jumpserver_headers, jumpserver_user, jumpserver_password)
    #jumpserver创建管理员用户和系统用户
    status_code = CreateAdminUser(jumpserver_host, jumpserver_headers, vhost_user, vhost_password)
    print("创建管理员用户：", status_code)
    status_code = CreateSystemUser(jumpserver_host, jumpserver_headers, vhost_user, vhost_password)
    print("创建系统用户：", status_code)
    #获取管理员用户uuid，这个管理员用户是服务器管理员
    AdminUserUUID = GetAdminUserUUID(jumpserver_host, jumpserver_headers, vhost_user)
    print(AdminUserUUID)
    #获取Administrator用户的uuid，这个用户是jumpserver管理员
    AdministratorUUID = GetJumpserverAdminUserUUID(jumpserver_host, jumpserver_headers, "Administrator")
    #获取系统用户的uuid
    SystemUserUUID = GetJumpserverSystemUserUUID(jumpserver_host, jumpserver_headers, vhost_user)
    #获取DEFAULT树节点的uuid
    DEFAULT_AssetsNodeUUID = GetAssetsNodeUUID(jumpserver_host, jumpserver_headers, "Default")


    #删除DEFAULT树节点下面的所有资产
    asset_delete_all(DEFAULT_AssetsNodeUUID, jumpserver_host, jumpserver_headers)

    
    #遍历所有集群，开始创建树节点，并给树节点下面添加资产
    for cluster in cluster_dict:
        #创建树节点的时候会返回树节点的uuid
        cluster_node_uuid = CreateJumpserverNode(jumpserver_host, jumpserver_headers, cluster)
        cluster_node_uuid = GetAssetsNodeUUID(jumpserver_host, jumpserver_headers, cluster)
        print("创建节点结果：", status_code)
        cluster_uuid = cluster_dict[cluster]
        #获取该集群下面的机器列表
        node_dict = GetClusterNode(compass_host, cluster_uuid, compass_headers)
        #资产授权，将树节点授权给admin用户，系统用户为上面设置的那个系统用户
        # perms_asset_permissions_create(AdministratorUUID, SystemUserUUID, cluster_node_uuid, jumpserver_host, jumpserver_headers)

        print(node_dict)
        for node in node_dict:
            node_name = node
            node_ip = node_dict[node_name]
            # if "master" in node_name:
            #     node_name = cluster + "-" + node_name
            #节点前面加上集群的名字
            node_name = cluster + "-" + node_name
            
            AssetCreate(node_name, node_ip, AdminUserUUID, cluster_node_uuid, jumpserver_host, jumpserver_headers)   
    #添加cargo机器，创建节点树并获取节点UUID
    cargo_node_uuid = CreateJumpserverNode(jumpserver_host, jumpserver_headers, cargo_name)
    cargo_node_uuid = GetAssetsNodeUUID(jumpserver_host, jumpserver_headers, cargo_name)
    for host in cargo_hosts:
        node_name = cargo_name + "-" + host
        node_ip = host
        AssetCreate(node_name, node_ip, AdminUserUUID, cargo_node_uuid, jumpserver_host, jumpserver_headers)   
    
    
    #资产授权,直接把DEFAULT根节点授权
    perms_asset_permissions_create(AdministratorUUID, SystemUserUUID, DEFAULT_AssetsNodeUUID, jumpserver_host, jumpserver_headers)

