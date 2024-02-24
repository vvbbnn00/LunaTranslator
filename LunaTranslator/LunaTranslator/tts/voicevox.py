import time
import os
import requests
from traceback import print_exc
from tts.basettsclass import TTSbase

from myutils.subproc import subproc_w, autoproc

DEFAULT_BASE_URL = "http://127.0.0.1:50021"


class TTS(TTSbase):
    base_url: str
    init = False

    def init(self):
        dir_path = self.config.get('path')
        exe_path = os.path.join(dir_path, 'run.exe')
        base_url = self.config.get('base_url')

        can_start = False

        # Check if the VoiceVox executable and directory exist
        if os.path.exists(exe_path) and os.path.exists(dir_path):
            can_start = True
            if not base_url:
                base_url = DEFAULT_BASE_URL
            self.engine = autoproc(
                subproc_w(os.path.join(self.config['path'], 'run.exe'), cwd=self.config['path'], name='voicevox'))

        # Check if the VoiceVox URL is valid
        if base_url:
            try:
                response = requests.get(base_url + '/speakers', timeout=5)
                response.raise_for_status()
                can_start = True
            except requests.exceptions.RequestException:
                print(f"[TTS] VoiceVox URL {base_url} is not valid.")
                return

        if not can_start:
            print(f"[TTS] VoiceVox is not installed or the URL is not valid.")
            return

        self.init = True
        self.base_url = base_url

    def getvoicelist(self):
        if not self.init:
            print(f"[TTS] VoiceVox is not initialized.")
            return []
        while True:
            try:
                response = requests.get(f'{self.base_url}/speakers').json()
                # print(response)
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
        if not self.init:
            print(f"[TTS] VoiceVox is not initialized.")
            return
        # def _():
        if True:
            response = requests.post(f'{self.base_url}/audio_query', params={
                'speaker': voiceidx,
                'text': content
            })
            print(response.json())
            fname = str(time.time())
            response = requests.post(f'{self.base_url}/synthesis', params={
                'speaker': voiceidx,
            }, json=response.json(), headers={
                'Content-Type': 'application/json',
            })
            with open('./cache/tts/' + fname + '.wav', 'wb') as ff:
                ff.write(response.content)
            return './cache/tts/' + fname + '.wav'
