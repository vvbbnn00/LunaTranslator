from myutils.config import globalconfig
import time
import os
import requests, json, threading
from traceback import print_exc
from tts.basettsclass import TTSbase

from myutils.subproc import subproc_w, autoproc


class TTS(TTSbase):

    def init(self):

        if os.path.exists(self.config['path']) == False or \
                os.path.exists(os.path.join(self.config['path'], 'run.exe')) == False:
            return
        self.engine = autoproc(
            subproc_w(os.path.join(self.config['path'], 'run.exe'), cwd=self.config['path'], name='voicevox'))

    def getvoicelist(self):
        while True:
            try:

                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Pragma': 'no-cache',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.52',
                    'sec-ch-ua': '"Chromium";v="106", "Microsoft Edge";v="106", "Not;A=Brand";v="99"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                }

                response = requests.get('http://127.0.0.1:50021/speakers', headers=headers,
                                        proxies={'http': None, 'https': None}).json()
                print(response)
                # self.voicelist=[_['name'] for _ in response]
                # return self.voicelist
                voicedict = {}
                for speaker in response:
                    styles = speaker['styles']
                    for style in styles:
                        voicedict[style['id']] = "%s(%s)" % (speaker['name'], style['name'])
                self.voicelist = ["%02d %s" % (i, voicedict[i]) for i in range(len(voicedict))]
                return self.voicelist
            except:
                print_exc()
                time.sleep(1)
            break

    def speak(self, content, rate, voice, voiceidx):

        # def _():
        if True:
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }

            params = {
                'speaker': voiceidx,
                'text': content
            }

            response = requests.post('http://localhost:50021/audio_query', params=params, headers=headers,
                                     proxies={'http': None, 'https': None})
            print(response.json())
            fname = str(time.time())
            headers = {
                'Content-Type': 'application/json',
            }
            params = {
                'speaker': voiceidx,
            }
            response = requests.post('http://localhost:50021/synthesis', params=params, headers=headers,
                                     data=json.dumps(response.json()))
            with open('./cache/tts/' + fname + '.wav', 'wb') as ff:
                ff.write(response.content)
            return ('./cache/tts/' + fname + '.wav')
