import urllib.request
import requests
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

def dlBeatMap(beatmapset, osuSessIds):
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

    # response = requests.get(
    #     "https://old.ppy.sh/d/{}".format(bmsId),
    #     headers={'osu_session': osuSessIds},
    #     stream=True
    # )
    osuSessIds = "eyJpdiI6ImdEZGFoMmtZOEV1TzhSRVwvUW9wME1nPT0iLCJ2YWx1ZSI6IkZ6dEErVnRncXRYYjNveG9NWDZJTVgyeU9QQmZaaDhnSHhvNFhUMWpLYjBCaWkyU2lcL2o1UklFQnBNOHFpcFRyMVBNcVBVSmFjNUZKQXNZdEpFTThjUT09IiwibWFjIjoiN2EwYWU3YTgzMWM4OTIwZWRiMDAzOWMwYmEyMjRkNzkyNWIzNzVkNjc4NTk0MTdjZGM5YThjMmE0NjNjY2FlYiJ9"
    quota_chk = requests.get(
        "https://osu.ppy.sh/home/download-quota-check".format(bmsId),
        headers={'cookie': 'osu_session={}'.format(osuSessIds)},
        stream=True
    )
    print("STATUS CODE {}: {}".format(bmsId, quota_chk.status_code))
    response = requests.get(
        "https://osu.ppy.sh/beatmapsets/{}/download".format(bmsId),
        headers={'cookie': 'osu_session={}'.format(osuSessIds)},
        stream=True
    )
    print("STATUS CODE {}: {}".format(bmsId, response.status_code))
    with open(bmsPath + "{}.zip".format(bmsId), 'wb') as beatmap:
        for chunk in response.iter_content(chunk_size=512 * 1024):
            if chunk:
                beatmap.write(chunk)


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

    authentication_url = 'https://osu.ppy.sh/session'
    payload = {
        'action': 'login',
        'username': osuUser,
        'password': osuPass,
        'redirect': 'index.php',
        'sid': '',
        'login': 'Login'
    }

    response = requests.post(authentication_url, data=payload)
    print(response.headers['Set-Cookie'])#.split("; "))
    osuSessIds = list(filter(lambda x: "osu_session=" in x ,response.headers['Set-Cookie'].split("; ")))[1]
    osuSessIds = osuSessIds.split("osu_session=")[1]
    print("STATUS_CODE")
    assert response.status_code == 200, "Please check your credentials, (in cred.txt)"

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

                dlBeatMap(beatmapset, osuSessIds)
                numFound += 1
                if (numFound >= numData):
                    break
            
            if (maxSongs == sys.maxsize):
                maxSongs = data['total']
                print("Max Songs: {}".format(maxSongs))
        
        numSongs += len(data['beatmapsets'])
        curCursor = "&cursor%5Bplay_count%5D={}&cursor%5B_id%5D={}".format(data['cursor']['play_count'], data['cursor']['_id']) 
        
        print(data['cursor'])