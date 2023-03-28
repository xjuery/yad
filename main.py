import docker
import uuid
import click
import os
import tarfile
import json
import datetime


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
