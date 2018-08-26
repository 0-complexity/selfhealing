import time
from JumpScale import j

descr = """
Checks the last modified timestamp of all images and compare it with the available image in the server and update the image if needed.
"""

organization = "greenitglobe"
category = "monitor.maintenance"
author = "ali.chaddad@gig.tech"
license = "bsd"
version = "1.0"
period = "0 0 * * *"  # Once a day
startatboot = True
enable = True
queue = "process"
roles = ["controller"]
timeout = 60 * 60 * 3


def action():
    ccl = j.clients.osis.getNamespace("cloudbroker")
    pcl = j.clients.portal.getByInstance2("main")
    images = ccl.image.search(
        {"status": {"$nin": ["DESTROYED", "DELETED"]}, "url": {"$ne": ""}}, size=0
    )[1:]
    for image in images:
        url = image["url"]
        modified_time = j.system.net.getServerFileLastModified(url)
        if modified_time != image["lastModified"]:
            task_guid = pcl.cloudbroker.image.syncCreateImage(
                name=image["name"],
                url=url,
                gid=image["gid"],
                imagetype=image["type"],
                boottype=image["bootType"],
                username=image["username"],
                password=image["password"],
                accountId=image["accountId"],
                hotresize=image["hotResize"],
                _async=True,
            )
            curr_time = int(time.time())
            while int(time.time()) < curr_time + timeout / 6:
                report = pcl.system.task.get(taskguid=task_guid)
                if report and report[0] is True:
                    pcl.cloudbroker.image.delete(
                        imageId=image["id"], reason="Image update script"
                    )
                    break


if __name__ == "__main__":
    action()
