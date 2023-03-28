import docker
import uuid
import click
import os
import tarfile
import json
import datetime
import hashlib

def getImageLocally(imageName):
    tmpDirectory = os.path.dirname(__file__)
    client = docker.from_env()
    image = client.images.get(imageName)

    fullPath = tmpDirectory + '/' + str(uuid.uuid4()) + '.tar'
    f = open(fullPath, 'wb')
    for chunk in image.save():
        f.write(chunk)
    f.close()

    return fullPath


def parseDockerImage(imageName):
    imagePath = getImageLocally(imageName)

    layers = []
    imageArchive = tarfile.open(imagePath)
    for member in imageArchive:
        if member.isdir():
            layerDesc = imageArchive.extractfile(member.name + "/json")
            layerJsonDesc = json.loads(layerDesc.read())
            try:
                parentName = layerJsonDesc["parent"]
            except:
                parentName = None

            layer = {
                "id": layerJsonDesc["id"],
                "parent": parentName
            }

            content = []
            layerContentTar = imageArchive.extractfile(member.name + "/layer.tar")
            layerContent = tarfile.open(fileobj=layerContentTar, mode="r:")
            for contentMember in layerContent:
                c = {
                    "name": contentMember.name,
                    "size": contentMember.size,
                    "mtime": str(datetime.datetime.utcfromtimestamp(contentMember.mtime).isoformat()),
                    "mode": oct(contentMember.mode)[-3:],
                    "uid": contentMember.uid,
                    "gid": contentMember.gid,
                    "uname": contentMember.uname,
                    "gname": contentMember.gname
                }

                if contentMember.isfile():
                    contentMemberContent = layerContent.extractfile(contentMember.name)
                    c["md5sum"] = hashlib.md5(contentMemberContent.read()).hexdigest()
                    c["type"] = "file"
                elif contentMember.isdir():
                    c["type"] = "directory"
                elif contentMember.issym():
                    c["type"] = "symboliclink"
                elif contentMember.islnk():
                    c["type"] = "hardlink"
                elif contentMember.ischr():
                    c["type"] = "characterdevice"
                elif contentMember.isblk():
                    c["type"] = "blockdevice"
                elif contentMember.isfifo():
                    c["type"] = "fifo"
                content.append(c)

            layer["content"] = content
            layers.append(layer)

    return layers


@click.command()
@click.argument('imagename')
def main(imagename):
    layers = parseDockerImage(imagename)
    print(json.dumps(layers))


if __name__ == '__main__':
    main()
