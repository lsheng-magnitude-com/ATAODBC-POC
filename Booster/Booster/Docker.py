from __future__ import print_function


# Todo: add more features to this module in the future
class Docker(object):
    """
    ET Wrapper

    """

    def __init__(self, image, tag):
        self.image = image
        self.tag = tag

    def getPullCmd(self):
        return "docker pull " + self.image + ":" + self.tag

    def getRunCmd(self, container):
        return "docker run --name " + container + " -d " + self.image + ":" + self.tag

    def getStopCmd(self, container):
        return "docker stop " + container

    def getRmCmd(self, container):
        return "docker rm " + container

    def getStopAllCmd(self):
        return "docker stop $(docker ps -a -q) || true"

    def getRmAllCmd(self):
        return "docker rm $(docker ps -a -q) || true"

    def getRmVolumesCmd(self):
        return "docker volume rm $(docker volume ls -q) || true"


if __name__ == '__main__':
    # TODO
    pass
