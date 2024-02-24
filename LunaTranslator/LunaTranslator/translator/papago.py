from traceback import print_exc
import requests
import hmac, base64, re
import uuid, time
from myutils.config import globalconfig
from translator.basetranslator import basetrans


class TS(basetrans):
    def langmap(self):
        return {"zh": "zh-CN", "cht": "zh-TW"}

    def inittranslator(self):
        headers = {
            'authority': 'papago.naver.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'zh-CN,zh;q=0.9',
            'sec-ch-ua': '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',

        }
        host_html = self.session.get('https://papago.naver.com/', headers=headers
                                     ).text
        url_path = re.compile('/home.(.*?).chunk.js').search(host_html).group()
        self.language_url = ''.join(['https://papago.naver.com', url_path])
        lang_html = self.session.get(self.language_url, headers=headers).text
        self.auth_key = self.get_auth_key(lang_html)
        self.uuid = uuid.uuid4().__str__()

    def get_auth_key(self, lang_html: str) -> str:
        return re.compile('AUTH_KEY:"(.*?)"').findall(lang_html)[0]

    def get_auth(self, url, auth_key, device_id, time_stamp):
        auth = hmac.new(key=auth_key.encode(), msg='{}\n{}\n{}'.format(device_id, url, time_stamp).encode(),
                        digestmod='md5').digest()
        return 'PPG {}:{}'.format(device_id, base64.b64encode(auth).decode())

    def translate(self, content):
        tm = str(int(time.time() * 1000))
        headers = {
            'authority': 'papago.naver.com',
            'accept': 'application/json',
            'accept-language': 'zh-CN',
            'authorization': self.get_auth('https://papago.naver.com/apis/n2mt/translate', self.auth_key, self.uuid,
                                           tm),
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'device-type': 'pc',
            'origin': 'https://papago.naver.com',
            'referer': 'https://papago.naver.com/',
            'sec-ch-ua': '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'timestamp': tm,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
            'x-apigw-partnerid': 'papago',
        }

        data = {
            'deviceId': self.uuid,
            'locale': self.tgtlang,
            'dict': 'true',
            'dictDisplay': '30',
            'honorific': 'false',
            'instant': 'false',
            'paging': 'false',
            'source': self.srclang,
            'target': self.tgtlang,
            'text': content,
        }

        r = self.session.post('https://papago.naver.com/apis/n2mt/translate', headers=headers, data=data)

        data = r.json()

        return data['translatedText']
