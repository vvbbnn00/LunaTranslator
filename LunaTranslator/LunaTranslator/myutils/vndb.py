from urllib.parse import quote
import base64
import queue, time, requests, re, os, hashlib
from traceback import print_exc
from myutils.proxy import getproxy
from myutils.config import globalconfig
from threading import Thread


def b64string(a):
    return hashlib.md5(a.encode('utf8')).hexdigest()


def vndbdownloadimg(url, wait=True):
    savepath = './cache/vndb/' + b64string(url) + '.jpg'
    if os.path.exists(savepath):
        return savepath

    def _(url, savepath):
        headers = {
            'sec-ch-ua': '"Microsoft Edge";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            'Referer': 'https://vndb.org/',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.42',
            'sec-ch-ua-platform': '"Windows"',
        }
        try:
            time.sleep(1)
            _content = requests.get(url, headers=headers, proxies=getproxy()).content
            with open(savepath, 'wb') as ff:
                ff.write(_content)
            return savepath
        except:
            return None

    if wait:
        return _(url, savepath)
    else:
        Thread(target=_, args=(url, savepath)).start()
        return None


def vndbdowloadinfo(vid):
    cookies = {
        'vndb_samesite': '1',
    }

    headers = {
        'authority': 'vndb.org',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'sec-ch-ua': '"Microsoft Edge";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.42',
    }
    url = 'https://vndb.org/' + vid
    savepath = './cache/vndb/' + b64string(url) + '.html'
    # print(url,savepath)
    if not os.path.exists(savepath):
        try:
            time.sleep(1)
            response = requests.get(url, cookies=cookies, headers=headers, proxies=getproxy())
            with open(savepath, 'w', encoding='utf8') as ff:
                ff.write(response.text)
        except:
            return None
    return savepath


def searchforidimage(title):
    if isinstance(title, str):
        if os.path.exists('./cache/vndb') == False:
            os.mkdir('./cache/vndb')
        js = requests.post('https://api.vndb.org/kana/vn', json={
            "filters": ["search", "=", title],
            "fields": "image.url", "sort": "searchrank"
        }, proxies=getproxy())
        try:
            results = js.json()['results']
        except:
            print(js.text)
            return {}
        if len(results) == 0:
            js = requests.post('https://api.vndb.org/kana/release', json={
                "filters": ["search", "=", title],
                "fields": "vns.id", "sort": "searchrank"
            }, proxies=getproxy())
            results = js.json()['results']
            if len(results) == 0:
                return {}
            vns = results[0]['vns']
            if len(vns) == 0: return {}
            vid = vns[0]['id']
            js = requests.post('https://api.vndb.org/kana/vn', json={
                "filters": ["id", "=", vid],
                "fields": "image.url"
            }, proxies=getproxy())
            try:
                results = js.json()['results']
            except:
                print(js.text)
                return {}
            img = results[0]['image']['url']
        else:
            img = results[0]['image']['url']
            vid = results[0]['id']
    elif isinstance(title, int):
        vid = 'v{}'.format(title)
        js = requests.post('https://api.vndb.org/kana/vn', json={
            "filters": ["id", "=", vid],
            "fields": "image.url"
        }, proxies=getproxy())
        try:
            results = js.json()['results']
        except:
            print(js.text)
            return {}
        img = results[0]['image']['url']
    return {'vid': vid, 'infopath': vndbdowloadinfo(vid), 'imagepath': vndbdownloadimg(img)}


import re


def parsehtmlmethod(infopath):
    with open(infopath, 'r', encoding='utf8') as ff:
        text = ff.read()
    ##隐藏横向滚动
    text = text.replace('<body>', '<body style="overflow-x: hidden;">')
    ##删除header
    text = re.sub('<header>([\\s\\S]*?)</header>', '', text)
    text = re.sub('<footer>([\\s\\S]*?)</footer>', '', text)
    text = re.sub('<article class="vnreleases"([\\s\\S]*?)</article>', '', text)
    text = re.sub('<article class="vnstaff"([\\s\\S]*?)</article>', '', text)
    text = re.sub('<article id="stats"([\\s\\S]*?)</article>', '', text)

    text = re.sub('<nav>([\\s\\S]*?)</nav>', '', text)
    text = re.sub('<p class="itemmsg">([\\s\\S]*?)</p>', '', text)
    text = re.sub('<div id="vntags">([\\s\\S]*?)</div>', '', text)
    text = re.sub('<div id="tagops">([\\s\\S]*?)</div>', '', text)
    resavepath = infopath + 'parsed.html'

    if globalconfig['languageuse'] == 0:
        text = re.sub('<a href="(.*?)" lang="ja-Latn" title="(.*?)">(.*?)</a>',
                      '<a href="\\1" lang="ja-Latn" title="\\3">\\2</a>', text)

    hrefs = re.findall('src="(.*?)" width="(.*?)" height="(.*?)"', text)
    # print(hrefs)
    for href in hrefs:
        if href[0].startswith('https://t.vndb.org/st/'):
            href1 = href[0].replace('https://t.vndb.org/st/', 'https://t.vndb.org/sf/')
            localimg = vndbdownloadimg(href1, False)
            if localimg:
                text = text.replace('src="{}" width="{}" height="{}"'.format(href[0], href[1], href[2]),
                                    'src="file://{}" width="512"'.format(os.path.abspath(localimg).replace('\\', '/')))
                text = text.replace('href="{}"'.format(href1),
                                    'href="file://{}"'.format(os.path.abspath(localimg).replace('\\', '/')))
        elif href[0].startswith('https://t.vndb.org/cv/'):
            localimg = vndbdownloadimg(href[0], False)
            if localimg:
                text = text.replace('src="{}"'.format(href[0]),
                                    'src="file://{}"'.format(os.path.abspath(localimg).replace('\\', '/')))

    with open(resavepath, 'w', encoding='utf8') as ff:
        ff.write(text)

    return resavepath
