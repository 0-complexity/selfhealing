from JumpScale import j
descr = """
Check if there are partition issues in RabbitMQ. If issues were found it will restart RabbitMQ. 
"""

organization = 'cloudscalers'
author = "chaddada@greenitglobe.com"
version = "1.0"
category = "monitor.healthcheck"
roles = ['storagedriver']
period = 1800
timeout = 180
enable = True
async = True
queue = 'process'
log = True

def action():
    import sys
    sys.path.append('/opt/OpenvStorage')
    from ovs.extensions.healthcheck.generic_hc import OpenvStorageHealthCheck
    from ovs.extensions.healthcheck.helpers.rabbitmq import RabbitMQ
    if OpenvStorageHealthCheck.LOCAL_SR.node_type == 'MASTER':
        rabbit = RabbitMQ(ip=OpenvStorageHealthCheck.LOCAL_SR.ip)
        cls_status = rabbit.cluster_status()
        if cls_status[0] != 200: # in case of cluster_status as error
            j.errorconditionhandler.raiseOperationalWarning(category=category, tags= "RabbitMQ", message="Couldn't retrieve RabbitMQ cluster status")
            return
        else:
            _, hostname = j.system.process.execute('hostname -s')
            hostname = 'rabbit@{}'.format(hostname.strip())
            if len(cls_status[1][hostname]['partitions']) > 1:
                node_in_cluster = cls_status[1][hostname]['partitions'][0]
                j.errorconditionhandler.raiseOperationalWarning(category=category, tags="RabbitMQ", message="RabbitMQ on {} has partitions issues will restart to solve.".format(hostname))
                j.system.process.execute("""rabbitmqctl stop_app; rabbitmqctl reset; rabbitmqctl join_cluster {}; 
                                            rabbitmqctl start_app; systemctl restart ovs-workers""".format(node_in_cluster))

if __name__ == '__main__':
    action()
