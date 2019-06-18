from bs4 import BeautifulSoup
import json, re
import os, resource, math, io, struct
import requests, aiohttp, asyncio, ssl
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def GetFieldFromData(uid_data, field_name):
    soup = BeautifulSoup(uid_data, features='xml')
    field = soup.find(field_name)
    return field.text
    
def GetContentCount(content):
    soup = BeautifulSoup(content, features='xml')
    content_tag = soup.find("contents")
    return content_tag['total']

def ReadContentCountFromFile(region):
    try:
        contents = open('xmls/titlelist_{0}.xml'.format(region)).read()
    except:
        return -1
    return GetContentCount(contents)

def ReadVersionList():
    try:
        content = open('xmls/versionlist.xml').read()
    except:
        content = 0xFFFFF
    return content

def GenXmlFromVerList(buf):
    xml_doc = ""
    tid_template = """  <titleid>\n    <tid>%(tid)s</tid>\n    <ver>%(ver)s</ver>\n  </titleid>\n"""

    verlist = io.BytesIO(buf)
    magic = verlist.read(0x10)

    for chunk in iter(lambda: verlist.read(0x10), ''):
        try:
            tid, ver, unk = struct.unpack("<QII", chunk)
        except:
            break
        data = {'tid':"{:016X}".format(tid) , 'ver':ver }
        xml_doc += tid_template % data
    xml_doc = """<titleids>\n""" + xml_doc + """</titleids>"""
    return xml_doc

    
def GetXmlsFromCDN(region):
    print ("[*] Requesting content")
    r = requests.get('https://samurai.ctr.shop.nintendo.net/samurai/ws/{}/titles?shop_id=1&limit=5000&offset=0'.format(region), verify=False)
    match = GetContentCount(r.text) == ReadContentCountFromFile(region)
    print ("[*] Did content count change? {}".format(bool(match ^ 1)))
    if match == False:
        open("xmls/titlelist_{}.xml".format(region), "w+").write(r.text)
        return 0
    return 1

def GetVersionListFromCDN():
    print("[*] Requesting VersionList")
    r = requests.get('https://tagaya-ctr.cdn.nintendo.net/tagaya/versionlist', verify=False, stream=True)
    xml = GenXmlFromVerList(r.content)
    match = xml == ReadVersionList()
    print ("[*] Did versionlist change? {}".format(bool(match ^ 1)))
    if match == False:
        open("xmls/versionlist.xml", "w+").write(xml)
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
        size_bytes = int(GetFieldFromData(uid_data, 'content_size'))
    except:
        return "0B [N/A]"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return '{0} {1} [{2} blocks]'.format(s, size_name[i], int(round(size_bytes / (128 * 1024))))

def isNameTag(tag):
    #print ("Tag {}".format(tag.name) + "Tag Parent {}".format(tag.parent.name))
    return tag.name == 'name' and tag.parent.name == 'title'

def GetVersionForTitleID(versionlist, tid):
    soup = BeautifulSoup(versionlist, 'xml')
    for buf in soup.find_all('titleid'):
        if buf.tid.text == tid:
            return buf.ver.text
    return "N/A"

async def DoXML(region):
    contents = open("xmls/titlelist_{}.xml".format(region)).read()
    versionlist = open("xmls/versionlist.xml").read()

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
    
    tids = [GetFieldFromData(_uiddata, 'title_id') for _uiddata in data]
    vers = [GetVersionForTitleID(versionlist, tid) for tid in tids]

    data = [{'Name': n, 'UID': u, 'TitleID': t, 'Version': v, 'Size': s, 'Product Code' : p} for n, u, t, v, s, p in zip(name, tuids, tids, vers, size, prod)]
    
    contents = open("jsons/list_{0}.json".format(region), "w+")
    contents.write(json.dumps(data, indent = 4))
    contents.close()

regions = ["GB", "US", "JP", "TW", "KR"]

commit = False

match = GetVersionListFromCDN()

for i in regions:
    if GetXmlsFromCDN(i) == 0 or match == 0: # This functions checks for the sha too. If matches then returns 1
        print ("[*] Updating JSON for {}".format(i))
        asyncio.run(DoXML(i))
        print ("[+] Update complete")
        commit = True

exit(commit ^ 1) # Exit with 1 or 0