import requests
import base64
import base64
import uuid
import time
import hashlib
from ocrengines.baseocrclass import baseocr


class OCR(baseocr):
    def langmap(self):
        return {"zh": "zh-CHS", "cht": "zh-CHT"}

    def freetest(self, imgfile):

        headers = {
            'authority': 'aidemo.youdao.com',
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://ai.youdao.com',
            'referer': 'https://ai.youdao.com/',
            'sec-ch-ua': '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        }
        with open(imgfile, 'rb') as ff:
            f = ff.read()
        b64 = base64.b64encode(f)
        data = {
            'imgBase': 'data:image/jpeg;base64,' + str(b64, encoding='utf8'),
            'lang': '',
            'company': '',
        }

        response = self.session.post('https://aidemo.youdao.com/ocrtransapi1', headers=headers, data=data)

        try:
            return '<notrans>' + self.space.join([l['tranContent'] for l in response.json()['lines']])
        except:
            raise Exception(response.text)

    def ocrapi(self, imgfile):

        self.checkempty(['APP_KEY', 'APP_SECRET'])
        APP_KEY, APP_SECRET = self.config['APP_KEY'], self.config['APP_SECRET']

        # 待翻译图片路径, 例windows路径：PATH = "C:\\youdao\\media.jpg"
        PATH = imgfile

        '''
        添加鉴权相关参数 -
            appKey : 应用ID
            salt : 随机值
            curtime : 当前时间戳(秒)
            signType : 签名版本
            sign : 请求签名
            
            @param appKey    您的应用ID
            @param appSecret 您的应用密钥
            @param paramsMap 请求参数表
        '''

        def addAuthParams(appKey, appSecret, params):
            q = params.get('q')
            if q is None:
                q = params.get('img')
            salt = str(uuid.uuid1())
            curtime = str(int(time.time()))
            sign = calculateSign(appKey, appSecret, q, salt, curtime)
            params['appKey'] = appKey
            params['salt'] = salt
            params['curtime'] = curtime
            params['signType'] = 'v3'
            params['sign'] = sign

        '''
            计算鉴权签名 -
            计算方式 : sign = sha256(appKey + input(q) + salt + curtime + appSecret)
            @param appKey    您的应用ID
            @param appSecret 您的应用密钥
            @param q         请求内容
            @param salt      随机值
            @param curtime   当前时间戳(秒)
            @return 鉴权签名sign
        '''

        def calculateSign(appKey, appSecret, q, salt, curtime):
            strSrc = appKey + getInput(q) + salt + curtime + appSecret
            return encrypt(strSrc)

        def encrypt(strSrc):
            hash_algorithm = hashlib.sha256()
            hash_algorithm.update(strSrc.encode('utf-8'))
            return hash_algorithm.hexdigest()

        def getInput(input):
            if input is None:
                return input
            inputLen = len(input)
            return input if inputLen <= 20 else input[0:10] + str(inputLen) + input[inputLen - 10:inputLen]

        def createRequest():
            '''
            note: 将下列变量替换为需要请求的参数
            取值参考文档: https://ai.youdao.com/DOCSIRMA/html/%E8%87%AA%E7%84%B6%E8%AF%AD%E8%A8%80%E7%BF%BB%E8%AF%91/API%E6%96%87%E6%A1%A3/%E5%9B%BE%E7%89%87%E7%BF%BB%E8%AF%91%E6%9C%8D%E5%8A%A1/%E5%9B%BE%E7%89%87%E7%BF%BB%E8%AF%91%E6%9C%8D%E5%8A%A1-API%E6%96%87%E6%A1%A3.html
            '''
            lang_from = self.srclang
            lang_to = self.tgtlang
            render = '0'  # '是否需要服务端返回渲染的图片'
            type = '1'

            # 数据的base64编码
            q = readFileAsBase64(PATH)
            data = {'q': q, 'from': lang_from, 'to': lang_to, 'render': render, 'type': type}

            addAuthParams(APP_KEY, APP_SECRET, data)

            header = {'Content-Type': 'application/x-www-form-urlencoded'}
            res = doCall('https://openapi.youdao.com/ocrtransapi', header, data, 'post')
            return res

        def doCall(url, header, params, method):
            if 'get' == method:
                return self.session.get(url, params)
            elif 'post' == method:
                return self.session.post(url, params, header)

        def readFileAsBase64(path):
            f = open(path, 'rb')
            data = f.read()
            return str(base64.b64encode(data), 'utf-8')

        self.countnum()

        response = createRequest()
        try:

            text = [_['tranContent'] for _ in response.json()['resRegions']]
            box = [[int(_) for _ in l['boundingBox'].split(',')] for l in response.json()['resRegions']]
            return '<notrans>' + self.common_solve_text_orientation(box, text)
        except:
            raise Exception(response.text)

    def ocr(self, imgfile):
        interfacetype = self.config['接口']
        if interfacetype == 0:
            return self.freetest(imgfile)
        elif interfacetype == 1:
            return self.ocrapi(imgfile)
        raise Exception("unknown")
