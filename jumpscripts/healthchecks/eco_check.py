import time
from JumpScale import j

descr = """
Checks the number of error condidtions filed: if more than 5 are filed per hour will go into warning state,
and into error state if it exceeds 10 per hour
"""

organization = "cloudscalers"
author = "chaddada@greenitglobe.com"
category = "System Load"
license = "bsd"
version = "1.0"
period = 60 * 60  # always in sec
timeout = 20
enable = True
async = True
log = True
queue = 'process'
roles = ['master']


def action():
    message = '%s number of ecos were filed in last hour'
    state = 'OK'
    current_time = int(time.time())
    limit_time = current_time - period
    scl = j.clients.osis.getNamespace('system')
    eco_count = scl.eco.count({'pushtime': {'$gte': limit_time, '$lte': current_time}})
    if eco_count > 10:
        state = 'ERROR'
    elif eco_count > 5:
       state = 'WARNING'
    result = [{'state': state, 'category': category, 'message': message % eco_count, 'uid': 'ecorate'}]
    return result

if __name__ == '__main__':
    import yaml
    print(yaml.dump(action(), default_flow_style=False))
