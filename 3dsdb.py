from bs4 import BeautifulSoup
import json, re
import os, resource, math
import requests, aiohttp, asyncio, ssl
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def getFieldFromData(uid_data, field_name):
    soup = BeautifulSoup(uid_data, features='xml')
    field = soup.find(field_name)
    return field.text
    
def getContentCount(content):
    soup = BeautifulSoup(content, features='xml')
    content_tag = soup.find("contents")
    return content_tag['total']

def ReadContentCountFromFile(region):
    try:
        contents = open('./xmls/titlelist_{0}.xml'.format(region)).read()
    except:
        contents = 0xFFFFF
    return getContentCount(contents)


def getXmlsFromCDN(region):
    print ("[*] Requesting content")
    r = requests.get('https://samurai.ctr.shop.nintendo.net/samurai/ws/{}/titles?shop_id=1&limit=5000&offset=0'.format(region), verify=False)
    match = getContentCount(r.text) == ReadContentCountFromFile(region)
    print ("[*] Did content count change? {}".format(bool(match ^ 1)))
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
        print ('[-] FAIL with error', e)

async def fetch_all_async(session, urls, loop, context):
    results = await asyncio.gather(*[loop.create_task(fetch(session, url, context))
                                   for url in urls])
    return results

def getSizeFromData(uid_data):
    try:
        size_bytes = int(getFieldFromData(uid_data, 'content_size'))
    except:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return '{0} {1} [{2} blocks]'.format(s, size_name[i], int(round(size_bytes / (128 * 1024))))

def isNameTag(tag):
    #print ("Tag {}".format(tag.name) + "Tag Parent {}".format(tag.parent.name))
    return tag.name == 'name' and tag.parent.name == 'title'

async def doXML(region):
    contents = open("xmls/titlelist_{}.xml".format(region)).read()
    soup = BeautifulSoup(contents, features='xml')
    
    uids = soup.find_all('title')
    prods = soup.find_all('product_code')
    names = soup.find_all(isNameTag)
    name = [i.text.replace('\n', ' ') for i in names]
    prod = [i.text for i in prods]
    tuids = [uid['id'] for uid in uids]
    
    uid_url_list = ['https://ninja.ctr.shop.nintendo.net/ninja/ws/{0}/title/{1}/ec_info'.format(region, uid) for uid in tuids]
    loop = asyncio.get_event_loop_policy().get_event_loop() 
    
    context = ssl.create_default_context()
    context.load_cert_chain('keys/key.pem')
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession(loop = loop) as session:
            data = await fetch_all_async(session, uid_url_list, loop, context)
            await session.close()
    print(data[0:10])

    size = []
    for _uiddata in data:
        size.append(getSizeFromData(_uiddata))
    tids = [getFieldFromData(_uiddata, 'title_id') for _uiddata in data]
    data = [{'Name': n, 'UID': u, 'TitleID': t, 'Size': s, 'Product Code' : p} for n, u, t, s, p in zip(name, tuids, tids, size, prod)]
    contents = open("jsons/list_{0}.json".format(region), "w+")
    contents.write(json.dumps(data, indent = 4))
    contents.close()

regions = ["GB", "US", "JP", "TW", "KR"]

commit = False

for i in regions:
    if getXmlsFromCDN(i) == 0: # This functions checks for the sha too. If matches then returns 1
        print ("[*] Updating JSON for {}".format(i))
        asyncio.run(doXML(i))
        print ("[+] Update complete")
        commit = True

exit(commit ^ 1) # Exit with 1 or 0