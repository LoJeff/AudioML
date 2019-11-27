import urllib.request
import requests
from requests import session
import re
import json
import os
import sys
import zipfile
import shutil
import time

def getBeatMapSet(curCursor, urlFilter):
    response = requests.get("https://osu.ppy.sh/beatmapsets/search" + urlFilter + curCursor)
    return response.json()

def dlBeatMap(beatmapset):
    bmsId = beatmapset['id']
    bmsPath = "data/{}/".format(bmsId)
    # Clean folder first
    for fileName in os.listdir(bmsPath):
        filePath = bmsPath + fileName
        try:
            if os.path.isfile(filePath) or os.path.islink(filePath):
                os.unlink(filePath)
            elif os.path.isdir(filePath):
                shutil.rmtree(filePath)
        except Exception as e:
            print("Error when deleting {}. Reason: {}".format(filePath, e))

    # Download the beatmap from osu
    response = urllib.request.urlopen("https://old.ppy.sh/d/{}".format(bmsId))
    #yresponse = session().get("https://old.ppy.sh/d/{}".format(bmsId), stream=True)
    # response = requests.get("https://old.ppy.sh/d/{}".format(bmsId), allow_redirects=True, auth=(osuUser, osuPass))
    open(bmsPath + "{}.zip".format(bmsId), 'wb').write(response.read())
    # with open(bmsPath + "{}.zip".format(bmsId), 'wb') as beatmap:
    #     for chunk in response.iter_content(chunk_size=512 * 1024):
    #         if chunk:
    #             beatmap.write(chunk)


if __name__ == "__main__":
    numData = 10

    if (len(sys.argv) > 1):
        numData = int(sys.argv[1])

    print("Finding {} Mania Songs".format(numData))

    # Authentication
    
    cred = open("cred.txt", "r")
    credLines = cred.readlines()
    osuUser = credLines[0]#input('Enter your osu username: ')
    osuPass = credLines[1]#input('Enter your osu password: ')

    authentication_url = 'https://osu.ppy.sh/forum/ucp.php?mode=login'
    manager = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    manager.add_password(None, authentication_url, osuUser, osuPass)
    auth = urllib.request.HTTPBasicAuthHandler(manager)

    opener = urllib.request.build_opener(auth)
    urllib.request.install_opener(opener)
    # payload = {
    #     'action': 'login',
    #     'username': osuUser,
    #     'password': osuPass,
    #     'redirect': 'index.php',
    #     'sid': '',
    #     'login': 'Login'
    # }

    # response = session().post(authentication_url, data=payload)
    # print(response.headers)
    # print(response.headers['Set-Cookie'].split("; "))

    urlFilter = "?m=3&sort=plays_desc&s=any"
    curCursor = ""

    maxSongs = sys.maxsize
    numFound = 0
    numSongs = 0
    while (numFound < numData and maxSongs > (numSongs)):
        data = getBeatMapSet(curCursor, urlFilter)

        # Search through all beatmapsets
        for beatmapset in data['beatmapsets']:
            if (beatmapset['availability']['download_disabled']):
                continue
            hasMania = False
            for beatmap in beatmapset['beatmaps']:
                if (beatmap['mode_int'] == 3):
                    hasMania = True
                    break
            if (hasMania):
                print("{}: {} : {}".format(beatmapset['title'], beatmapset['id'], beatmapset['play_count']))
                beatmapSetPath = 'data/{}'.format(beatmapset['id'])
                if not os.path.exists(beatmapSetPath):
                    os.mkdir(beatmapSetPath)

                dlBeatMap(beatmapset)
                numFound += 1
                if (numFound >= numData):
                    break
            
            if (maxSongs == sys.maxsize):
                maxSongs = data['total']
                print("Max Songs: {}".format(maxSongs))
        
        numSongs += len(data['beatmapsets'])
        curCursor = "&cursor%5Bplay_count%5D={}&cursor%5B_id%5D={}".format(data['cursor']['play_count'], data['cursor']['_id']) 
        
        print(data['cursor'])