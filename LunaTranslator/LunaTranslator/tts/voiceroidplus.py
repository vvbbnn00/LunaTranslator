from myutils.config import globalconfig, _TR
import time
import os
import windows
from traceback import print_exc
from tts.basettsclass import TTSbase

from myutils.subproc import subproc_w, autoproc


class TTS(TTSbase):

    def init(self):
        self.path = ''
        self.voice = ''
        self.rate = ''

        self.voicelist = self.getvoicelist()
        if globalconfig['reader'][self.typename]['voice'] not in self.voicelist:
            globalconfig['reader'][self.typename]['voice'] = self.voicelist[0]

    def voiceshowmap(self, voice):
        name = voice.split('_')[0]
        jpname = {
            'yukari': '結月ゆかり',
            'akari': '紲星あかり',
            'kiritan': '東北きりたん',
            'itako': '東北イタコ',
            'zunko': '東北ずん子',
            'yuzuru': '伊織弓鶴',
            'tsuina': 'ついなちゃん',
            'akane': '琴葉茜',
            'aoi': '琴葉葵',
            'kou': '水奈瀬コウ',
            'sora': '桜乃そら',
            'tamiyasu': '民安ともえ',
            'ai': '月読アイ',
            'shouta': '月読ショウタ',
            'seika': '京町セイカ',
            'una': '音街ウナ',
            'yoshidakun': '鷹の爪吉田',
            'galaco': 'ギャラ子'
        }
        vv = jpname[name]
        if 'west' in voice:
            vv += '（関西弁）'
        return vv

    def getvoicelist(self):
        voicelist = []
        if os.path.exists(self.config['path']) == False:
            return []
        l = os.listdir(os.path.join(self.config['path'], 'Voice'))

        for _ in l:
            if '_' in _:
                _l = _.split('_')
                if len(_l) >= 2:
                    if _l[-1] == '22':
                        voicelist.append(_)
        return voicelist

    def checkpath(self):
        if self.config["path"] == "":
            return False
        if os.path.exists(self.config["path"]) == False:
            return False
        if self.config["path"] != self.path or self.config["voice"] != self.voice or globalconfig["ttscommon"][
            "rate"] != self.rate:
            self.path = self.config["path"]
            self.rate = globalconfig["ttscommon"]["rate"]
            self.voice = self.config["voice"]
            fname = str(time.time())
            savepath = os.path.join(os.getcwd(), 'cache/tts', fname + '.wav')
            dllpath = os.path.join(self.path, 'aitalked.dll')

            exepath = os.path.join(os.getcwd(), 'files/plugins/shareddllproxy32.exe')
            self.savepath = savepath

            t = time.time()
            t = str(t)
            pipename = '\\\\.\\Pipe\\voiceroid2_' + t
            waitsignal = 'voiceroid2waitload_' + t
            # 速率不可调
            self.engine = autoproc(subproc_w(
                '"{}" voiceroid2 "{}" "{}" {} 22050 0 "{}"  {} {}'.format(exepath, self.config["path"], dllpath,
                                                                          self.config["voice"], savepath, pipename,
                                                                          waitsignal), name='voicevoid2'))

            windows.WaitForSingleObject(windows.AutoHandle(windows.CreateEvent(False, False, waitsignal)),
                                        windows.INFINITE);
            windows.WaitNamedPipe(pipename, windows.NMPWAIT_WAIT_FOREVER)
            self.hPipe = windows.AutoHandle(
                windows.CreateFile(pipename, windows.GENERIC_READ | windows.GENERIC_WRITE, 0,
                                   None, windows.OPEN_EXISTING, windows.FILE_ATTRIBUTE_NORMAL, None))

    def speak(self, content, rate, voice, voice_idx):
        self.checkpath()
        # def _():
        if True:

            try:
                content.encode('shift-jis')
            except:
                return
            code1 = content.encode('shift-jis')
            # print(code1)
            windows.WriteFile(self.hPipe, code1)

            fname = windows.ReadFile(self.hPipe, 1024, None).decode('utf8')
            if os.path.exists(fname):
                return (fname)
