from JumpScale import j

descr = """
Restarts a stopped disk on the right storage router.
"""

organization = "greenitglobe"
category = "selfhealing"
author = "geert@greenitglobe.com"
version = "1.0"

enable = True
async = False
queue = "process"
timeout = 60 * 10


def action(vpool, storagedriver, volume_id):
    import sys

    sys.path.append("/opt/OpenvStorage")
    import volumedriver.storagerouter.storagerouterclient as src

    client = src.LocalStorageRouterClient(
        "arakoon://config/ovs/vpools/{vpool}/hosts/{storagedriver}/config?ini=%2Fopt%2FOpenvStorage%2Fconfig%2Farakoon_cacc.ini".format(
            vpool=vpool, storagedriver=storagedriver
        )
    )
    client.restart_object(volume_id, False)
