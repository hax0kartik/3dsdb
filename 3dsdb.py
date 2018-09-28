from bs4 import BeautifulSoup
import json
import hashlib
import re
import os
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def sha256(data):
    return hashlib.sha256(repr(data).encode('utf-8')).hexdigest()

def getSha(region):
    contents = open('./xmls/titlelist_{0}.xml'.format(region)).read()
    return sha256(contents)

def getXmlsFromCDN(region):
    print ("[*] Requesting content")
    r = requests.get('https://samurai.ctr.shop.nintendo.net/samurai/ws/{}/titles?shop_id=1&limit=3000&offset=0'.format(region), verify=False)
    match = sha256(r.text) == getSha(region)
    print ("[*] Do sha match ? {}".format(bool(match)))
    if match == False:
        open("xmls/titlelist_{}.xml".format(region), "w+").write(r.text)
        return 0
    
    return 1

def getTIDForUID(uid):
    #print (uid)
    link = 'https://ninja.ctr.shop.nintendo.net/ninja/ws/GB/title/{}/ec_info'.format(uid)
    try:
        r = requests.get(link, cert=('keys/key.pem'), verify=False)
    except:
        return
    soup = BeautifulSoup(r.text, features='xml')
    title_id = soup.find('title_id')
    return title_id.text

def isNameTag(tag):
    #print ("Tag {}".format(tag.name) + "Tag Parent {}".format(tag.parent.name))
    return tag.name == 'name' and tag.parent.name == 'title'

def doXML(path):
    contents = open("xmls/titlelist_{}.xml".format(path)).read()
    soup = BeautifulSoup(contents, features='xml')
    uids = soup.find_all('title')
    names = soup.find_all(isNameTag)
    name = [i.text.replace('\n', ' ') for i in names]
    tuids = [uid['id'] for uid in uids]
    tids = [getTIDForUID(uid) for uid in tuids]
    data = [{'Name': n, 'UID': u, 'TitleID': t } for n, u, t in zip(name, tuids, tids)]
    contents = open("jsons/list_{0}.json".format(path), "w+")
    contents.write(json.dumps(data))
    contents.close()

regions = ["GB", "US", "JP"]

commit = False
for i in regions:
    if getXmlsFromCDN(i) == 0: # This functions checks for the sha too. If matches then returns 1
        print ("[*] Updating JSON for {}".format(i))
        doXML(i)
        print ("[+] Update complete")
        commit = True

exit(commit) # Exit with 1 or 0