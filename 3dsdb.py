from bs4 import BeautifulSoup
import json, hashlib, re
import os, resource
import requests, aiohttp, asyncio, ssl
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def sha256(data):
    return hashlib.sha256(repr(data).encode('utf-8')).hexdigest()

def getSha(region):
    contents = open('./xmls/titlelist_{0}.xml'.format(region)).read()
    return sha256(contents)

def getXmlsFromCDN(region):
    print ("[*] Requesting content")
    r = requests.get('https://samurai.ctr.shop.nintendo.net/samurai/ws/{}/titles?shop_id=1&limit=5000&offset=0'.format(region), verify=False)
    match = sha256(r.text) == getSha(region)
    print ("[*] Do sha match ? {}".format(bool(match)))
    if match == False:
        open("xmls/titlelist_{}.xml".format(region), "w+").write(r.text)
        return 0
    
    return 1

async def fetch(session, url, context):
    try:
        async with session.get(url, ssl = context, timeout = 1000) as response:
            if response.status != 200:
                response.raise_for_status()
            return await response.text()
    except Exception as e:
        print ('[-] FAIL with error %s', e)

async def fetch_all_async(session, urls, loop, context):
    results = await asyncio.gather(*[loop.create_task(fetch(session, url, context))
                                   for url in urls])
    return results

def getTIDFromData(uid_data):
    soup = BeautifulSoup(uid_data, features='xml')
    title_id = soup.find('title_id')
    return title_id.text

def isNameTag(tag):
    #print ("Tag {}".format(tag.name) + "Tag Parent {}".format(tag.parent.name))
    return tag.name == 'name' and tag.parent.name == 'title'

async def doXML(path):
    contents = open("xmls/titlelist_{}.xml".format(path)).read()
    soup = BeautifulSoup(contents, features='xml')
    uids = soup.find_all('title')
    names = soup.find_all(isNameTag)
    name = [i.text.replace('\n', ' ') for i in names]
    tuids = [uid['id'] for uid in uids]
    uid_url_list = ['https://ninja.ctr.shop.nintendo.net/ninja/ws/GB/title/{}/ec_info'.format(uid) for uid in tuids]
    loop = asyncio.get_event_loop_policy().get_event_loop() 
    
    context = ssl.create_default_context()
    context.load_cert_chain('keys/key.pem')
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession(loop = loop) as session:
            data = await fetch_all_async(session, uid_url_list, loop, context)
            await session.close()
    print(data[0:10])
    tids = [getTIDFromData(_uiddata) for _uiddata in data]
    data = [{'Name': n, 'UID': u, 'TitleID': t } for n, u, t in zip(name, tuids, tids)]
    contents = open("jsons/list_{0}.json".format(path), "w+")
    contents.write(json.dumps(data))
    contents.close()

regions = ["GB", "US", "JP"]

commit = False

for i in regions:
    if getXmlsFromCDN(i) == 0: # This functions checks for the sha too. If matches then returns 1
        print ("[*] Updating JSON for {}".format(i))
        asyncio.run(doXML(i))
        print ("[+] Update complete")
        commit = True

exit(commit ^ 1) # Exit with 1 or 0