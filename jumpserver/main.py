import os
from jumpserver_v2 import Jumpserver
from jumpserver_v2 import Compass

def CompassToJumpserver(cps:object, jms:object):
    """ 将compass集群节点信息写入jumpserver里面 """

    #登录jumpserver和compass
    # jms.gen_jumpserver_session(jms.domain, jms.user, jms.password)
    cps.gen_compass_session()

    #获取cps集群名和集群id
    cps_cluster_dict = cps.get_cluster_list()

    #jumpserver创建管理用户和系统用户。管理用户：推送系统用户，获取资产信息；系统用户：用户连接资产的用户
    #alias_name是页面上显示的名字
    alias_name = cps.env + '-' + cps.vhost_user
    status_code = jms.create_admin_user(cps.vhost_user, cps.vhost_password, alias_name)
    print("创建管理用户结果：", status_code)
    admin_user_uuid = jms.get_admin_user_uuid(alias_name)
    print("管理员用户uuid：", admin_user_uuid)

    status_code = jms.create_system_user(cps.vhost_user, cps.vhost_password, alias_name)
    print("创建系统用户结果：", status_code)
    system_user_uuid = jms.get_system_user_uuid(alias_name)
    print("系统用户uuid：", system_user_uuid)

    #获取jumpserver登录用户uuid
    jumpserver_user_uuid = jms.get_jumpserver_user_uuid(jms.user)
    print("jumpserver用户%s的uuid是%s" % (jms.user, jumpserver_user_uuid))

    #遍历集群，开始获取节点信息，写入jumpserver
    for cluster in cps_cluster_dict:
        print(cluster, cps_cluster_dict[cluster])
        jumpserver_node_uuid = jms.create_node(cluster)
        jumpserver_node_uuid = jms.get_node_uuid(cluster)
        #获取当前集群下的节点信息
        cluster_node_dict = cps.get_cluster_nodes(cps_cluster_dict[cluster])

        #添加节点到jumpserver
        for cluster_node in cluster_node_dict:
            cluster_node_ip = cluster_node_dict[cluster_node]
            cluster_node_name = cluster + "-" + cluster_node
            jms.create_asset(cluster_node_name, cluster_node_ip, admin_user_uuid, jumpserver_node_uuid)

        #资产授权
        permission_name = cps.env + '-' + cluster
        jms.perms_asset_permissions_create(jumpserver_user_uuid, system_user_uuid, jumpserver_node_uuid, permission_name)

    #添加cargo资产信息
    jumpserver_node_uuid = jms.create_node(cps.cargo_name)
    jumpserver_node_uuid = jms.get_node_uuid(cps.cargo_name)
    for host in cps.cargo_hosts:
        cargo_node_ip = host
        cargo_node_name = cps.cargo_name + "-" + cargo_node_ip
        jms.create_asset(cargo_node_name, cargo_node_ip, admin_user_uuid, jumpserver_node_uuid) 
    #cargo资产授权
    permission_name = cps.env + '-' + cps.cargo_name
    jms.perms_asset_permissions_create(jumpserver_user_uuid, system_user_uuid, jumpserver_node_uuid, permission_name)
    

if __name__ == '__main__':

    #绝对路径
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    jms_config = os.path.join(BASE_DIR, "jms-config.ini")
    idc_stg_config = os.path.join(BASE_DIR, "cps-idc-stg.ini")
    idc_prod_config = os.path.join(BASE_DIR, "cps-idc-prod.ini")

    #登录jumpserver
    my_jms = Jumpserver(jms_config)
    my_jms.gen_jumpserver_session()

    #删除所有节点
    #获取jumpserver DEFAULT节点的uuid
    DEFAULT_node_uuid = my_jms.get_node_uuid("Default")
    # 删除所有资产信息
    my_jms.asset_delete_all(DEFAULT_node_uuid)

    #compass配置
    cps_idc_stg = Compass(idc_stg_config)
    cps_idc_prod = Compass(idc_prod_config)

    #添加节点
    CompassToJumpserver(cps_idc_stg, my_jms)
    CompassToJumpserver(cps_idc_prod, my_jms)

