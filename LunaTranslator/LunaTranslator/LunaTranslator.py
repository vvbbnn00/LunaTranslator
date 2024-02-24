import time
import re
import os, threading, ctypes
from traceback import print_exc
from myutils.config import globalconfig, savehook_new_list, savehook_new_data, noundictconfig, transerrorfixdictconfig, \
    setlanguage, _TR, static_data
import threading
from myutils.utils import minmaxmoveobservefunc, kanjitrans, checkifnewgame, stringfyerror
from myutils.wrapper import threader
from gui.showword import searchwordW
from myutils.hwnd import pid_running, getpidexe, testprivilege, ListProcess
from textsource.copyboard import copyboard
from textsource.texthook import texthook
from textsource.fridahook import fridahook
from textsource.ocrtext import ocrtext
import gui.selecthook
import gui.translatorUI
from gui.languageset import languageset
import zhconv, functools
import gui.transhist
import gui.edittext
import importlib
from functools import partial
from gui.settin import Settin
from gui.showocrimage import showocrimage
from gui.attachprocessdialog import AttachProcessDialog
import hmac, pytz, uuid
import windows
import re, gobject
import winsharedutils
from myutils.post import POSTSOLVE
from myutils.vnrshareddict import vnrshareddict
from gui.usefulwidget import Prompt, getQMessageBox


class _autolock:
    def __init__(self, lock) -> None:
        self.lock = lock
        lock.acquire()

    def __del__(self):
        self.lock.release()


class MAINUI():
    def __init__(self) -> None:
        super().__init__()
        self.lasttranslatorindex = 0
        self.usefultranslators = 0
        self.translators = {}
        self.cishus = {}
        self.reader = None
        self.textsource_p = None
        self.currentmd5 = '0'
        self.currenttext = ''
        self.currentread = ''
        self.refresh_on_get_trans_signature = 0
        self.currentsignature = None
        self.isrunning = True
        self.solvegottextlock = threading.Lock()
        self.castkata2hira = str.maketrans(static_data['allkata'], static_data['allhira'])
        self.casthira2kata = str.maketrans(static_data['allhira'], static_data['allkata'])

    @property
    def textsource(self):
        return self.textsource_p

    @textsource.setter
    def textsource(self, _):
        if _ is None and self.textsource_p:
            try:
                self.textsource_p.end()
            except:
                print_exc()
        self.textsource_p = _

        self.currentmd5 = '0' if _ is None else _.md5

    @threader
    def loadvnrshareddict(self, _=None):
        vnrshareddict(self)

    def solvebeforetrans(self, content):

        zhanweifu = 0
        mp1 = {}
        mp2 = {}
        mp3 = {}
        if noundictconfig['use']:
            for key in noundictconfig['dict']:
                usedict = False
                if type(noundictconfig['dict'][key]) == str:
                    usedict = True
                else:
                    for i in range(len(noundictconfig['dict'][key]) // 2):
                        if noundictconfig['dict'][key][i * 2] in ['0', self.currentmd5]:
                            usedict = True
                            break

                if usedict and key in content:
                    xx = 'ZX{}Z'.format(chr(ord("B") + zhanweifu))
                    content = content.replace(key, xx)
                    mp1[xx] = key
                    zhanweifu += 1
        if globalconfig['gongxiangcishu']['use']:
            for key, value in self.sorted_vnrshareddict_pre:

                if key in content:
                    content = content.replace(key, value['text'])
            for key, value in self.sorted_vnrshareddict:

                if key in content:
                    # print(key)
                    # if self.vnrshareddict[key]['src']==self.vnrshareddict[key]['tgt']:
                    #     content=content.replace(key,self.vnrshareddict[key]['text'])
                    # else:
                    xx = 'ZX{}Z'.format(chr(ord("B") + zhanweifu))
                    content = content.replace(key, xx)
                    mp2[xx] = key
                    zhanweifu += 1

        return content, (mp1, mp2, mp3)

    def solveaftertrans(self, res, mp):
        mp1, mp2, mp3 = mp
        # print(res,mp)#hello
        if noundictconfig['use']:
            for key in mp1:
                reg = re.compile(re.escape(key), re.IGNORECASE)
                if type(noundictconfig['dict'][mp1[key]]) == str:
                    v = noundictconfig['dict'][mp1[key]]
                elif type(noundictconfig['dict'][mp1[key]]) == list:
                    v = ""
                    for i in range(len(noundictconfig['dict'][mp1[key]]) // 2):
                        if noundictconfig['dict'][mp1[key]][i * 2] in ['0', self.currentmd5]:
                            v = noundictconfig['dict'][mp1[key]][i * 2 + 1]
                            break
                res = reg.sub(v, res)
        if globalconfig['gongxiangcishu']['use']:
            for key in mp2:
                reg = re.compile(re.escape(key), re.IGNORECASE)
                res = reg.sub(self.vnrshareddict[mp2[key]]['text'], res)
            for key, value in self.sorted_vnrshareddict_post:
                if key in res:
                    res = res.replace(key, value['text'])
        if transerrorfixdictconfig['use']:
            for key in transerrorfixdictconfig['dict']:
                res = res.replace(key, transerrorfixdictconfig['dict'][key])
        return res

    def _POSTSOLVE(self, s):
        ss = POSTSOLVE(s)
        self.settin_ui.showandsolvesig.emit(s)
        return ss

    def textgetmethod(self, text, is_auto_run=True, embedcallback=None, onlytrans=False):
        _autolock(self.solvegottextlock)
        needclear = True
        if onlytrans == False:
            self.currentsignature = time.time()
        if type(text) == str:
            if text.startswith('<notrans>'):
                self.translation_ui.displayres.emit('', globalconfig['rawtextcolor'], text[len('<notrans>'):],
                                                    onlytrans)
                self.currenttext = text
                self.currentread = text
                return
            elif text.startswith('<msg_warning_with_text>'):
                length = len('<msg_warning_with_text>')
                idx = text.find('</msg_warning_with_text>')
                warningtext = text[length:idx]
                text = text[idx + length + 1:]
                self.translation_ui.displaystatus.emit(warningtext, 'red', True, False)
                needclear = False
            else:
                msgs = [
                    ('<msg_info_not_refresh>', globalconfig['rawtextcolor'], False),
                    ('<msg_info_refresh>', globalconfig['rawtextcolor'], True),
                    ('<msg_error_not_refresh>', 'red', False),
                    ('<msg_error_refresh>', 'red', True),
                ]
                for msg, color, refresh in msgs:
                    if text.startswith(msg):
                        self.translation_ui.displaystatus.emit(text[len(msg):], color, refresh, False)
                        return
            if text == '' or len(text) > 100000:
                if embedcallback:
                    embedcallback('')
                return

        try:
            if type(text) == list:
                origin = '\n'.join(text)
                text = '\n'.join([self._POSTSOLVE(_) for _ in text])
            else:
                origin = text
                text = self._POSTSOLVE(text)
        except Exception as e:
            msg = str(type(e))[8:-2] + ' ' + str(e).replace('\n', '').replace('\r', '')
            self.translation_ui.displaystatus.emit(msg, 'red', True, True)
            return

        while len(text) and text[-1] in '\r\n \t':  # 在后处理之后在去除换行，这样换行符可以当作行结束符给后处理用
            text = text[:-1]

        if text == '' or (is_auto_run and (text == self.currenttext or len(text) > (
                max(globalconfig['maxoriginlength'], globalconfig['maxlength'])))):
            if embedcallback:
                embedcallback('')
            return

        try:
            self.textsource.sqlqueueput((text, origin,))
        except:
            pass
        if onlytrans == False:
            self.currenttext = text
            if globalconfig['outputtopasteboard'] and globalconfig['sourcestatus2']['copy']['use'] == False:
                winsharedutils.clipboard_set(text)

            if globalconfig['read_raw']:
                self.currentread = text
                self.autoreadcheckname()

        try:
            if self.hira_:
                hira = self.hira_.fy(text)
                for _1 in range(len(hira)):
                    _ = len(hira) - 1 - _1
                    if globalconfig['hira_vis_type'] == 0:
                        hira[_]['hira'] = hira[_]['hira'].translate(self.castkata2hira)
                    elif globalconfig['hira_vis_type'] == 1:
                        hira[_]['hira'] = hira[_]['hira'].translate(self.casthira2kata)
                    elif globalconfig['hira_vis_type'] == 2:
                        __kanas = [static_data['hira'] + ['っ'], static_data['kata'] + ['ッ']]
                        target = static_data['roma'] + ['-']
                        for _ka in __kanas:
                            for __idx in range(len(_ka)):
                                _reverse_idx = len(_ka) - 1 - __idx
                                hira[_]['hira'] = hira[_]['hira'].replace(_ka[_reverse_idx], target[_reverse_idx])
            else:
                hira = []
        except:
            print_exc()
            hira = []
        if globalconfig['refresh_on_get_trans'] == False:
            self.translation_ui.displayraw1.emit(hira, text, globalconfig['rawtextcolor'], onlytrans, needclear)
            _showrawfunction = None
            _showrawfunction_sig = 0
        else:
            _showrawfunction = functools.partial(self.translation_ui.displayraw1.emit, hira, text,
                                                 globalconfig['rawtextcolor'], onlytrans, needclear)
            _showrawfunction_sig = time.time()

        text_solved, optimization_params = self.solvebeforetrans(text)

        skip = is_auto_run and (
                len(text_solved) < globalconfig['minlength'] or len(text_solved) > globalconfig['maxlength'])

        self.premtalready = ['premt']
        self.usefultranslators = len(self.translators)
        if 'premt' in self.translators:
            try:
                res = self.translators['premt'].translate(text_solved)
                for k in res:
                    self.premtalready.append(k)
                    if k in globalconfig['fanyi']:
                        _colork = k
                    else:
                        _colork = 'premt'
                    self.GetTranslationCallback(onlytrans, _colork, self.currentsignature, optimization_params,
                                                _showrawfunction, _showrawfunction_sig, text, res[k], embedcallback)

            except:
                print_exc()
        if globalconfig['loadbalance']:
            usenum = min(globalconfig['loadbalance_oncenum'], len(self.translators))
        else:
            usenum = len(self.translators)
        if usenum:
            thistimeusednum = 0
            self.lasttranslatorindex = self.lasttranslatorindex % len(self.translators)
            _len = len(self.translators)
            keys = list(self.translators.keys()) + list(self.translators.keys())
            keys = keys[self.lasttranslatorindex:self.lasttranslatorindex + _len]
            # print(keys,usenum,self.lasttranslatorindex)
            for engine in keys:
                if engine not in self.premtalready:
                    self.translators[engine].gettask((partial(self.GetTranslationCallback, onlytrans, engine,
                                                              self.currentsignature, optimization_params,
                                                              _showrawfunction, _showrawfunction_sig, text), text,
                                                      text_solved, skip, embedcallback, is_auto_run, hira))
                thistimeusednum += 1
                self.lasttranslatorindex += 1
                if (thistimeusednum >= usenum):
                    break

    def GetTranslationCallback(self, onlytrans, classname, currentsignature, optimization_params, _showrawfunction,
                               _showrawfunction_sig, contentraw, res, embedcallback):
        self.usefultranslators -= 1
        if embedcallback is None and currentsignature != self.currentsignature: return

        embedtrans = self.GetTranslationCallback_(onlytrans, classname, currentsignature, optimization_params,
                                                  _showrawfunction, _showrawfunction_sig, contentraw, res)

        if embedtrans is None and self.usefultranslators == 0:
            embedtrans = ''
        if embedcallback and embedtrans is not None:
            embedcallback(embedtrans)

    def GetTranslationCallback_(self, onlytrans, classname, currentsignature, optimization_params, _showrawfunction,
                                _showrawfunction_sig, contentraw, res):

        if type(res) == str:
            if res.startswith('<msg_translator>'):
                if currentsignature == self.currentsignature:
                    self.translation_ui.displaystatus.emit(
                        globalconfig['fanyi'][classname]['name'] + ' ' + res[len('<msg_translator>'):], 'red',
                        onlytrans, False)
                return

        res = self.solveaftertrans(res, optimization_params)

        if onlytrans == False:
            if globalconfig['read_trans'] and (
                    list(globalconfig['fanyi'].keys())[globalconfig['read_translator']] == classname):
                self.currentread = res
                self.readcurrent()

        needshowraw = _showrawfunction and self.refresh_on_get_trans_signature != _showrawfunction_sig
        if needshowraw:
            self.refresh_on_get_trans_signature = _showrawfunction_sig
            _showrawfunction()

        if currentsignature == self.currentsignature and globalconfig['showfanyi']:
            self.translation_ui.displayres.emit(globalconfig['fanyi'][classname]['name'],
                                                globalconfig['fanyi'][classname]['color'], res, onlytrans)

        try:
            self.textsource.sqlqueueput((contentraw, classname, res))
        except:
            pass

        if globalconfig['embedded']['as_fast_as_posible'] or classname == list(globalconfig['fanyi'])[
            globalconfig['embedded']['translator']]:
            return (kanjitrans(zhconv.convert(res, 'zh-tw')) if globalconfig['embedded']['trans_kanji'] else res)

    @threader
    def autoreadcheckname(self):
        try:
            time.sleep(globalconfig['textthreaddelay'] / 1000)
            name = (self.textsource.currentname)
            names = savehook_new_data[self.textsource.pname]['allow_tts_auto_names'].split('|')
            needpass = False
            if name in names:
                needpass = True

            # name文本是类似“美香「おはよう」”的形式
            text = name
            for _name in names:
                if text.startswith(_name) or text.endswith(_name):
                    if len(text) >= len(_name) + 3:  # 2个引号+至少1个文本内容。
                        needpass = True
                        break

            if needpass == False:  # name not in names:
                self.readcurrent()
            gobject.baseobject.textsource.currentname = None
        except:
            # print_exc()
            self.readcurrent()

    def readcurrent(self, force=False):
        if not hasattr(self, 'reader') or self.reader is None:
            print('[TTS] No reader has been initialized.')
            return
        try:
            if force or globalconfig['autoread']:
                self.reader.read(self.currentread)
        except:
            print_exc()

    @threader
    def startreader(self, use=None, checked=True):
        try:
            self.reader.end()
        except:
            pass
        self.reader = None
        self.settin_ui.voicelistsignal.emit([], -1)
        if checked:
            if use is None:

                for key in globalconfig['reader']:
                    if globalconfig['reader'][key]['use'] and os.path.exists(('./LunaTranslator/tts/' + key + '.py')):
                        use = key
                        break
            if use:
                aclass = importlib.import_module('tts.' + use).TTS

                self.reader_usevoice = use
                self.reader = aclass(use, self.settin_ui.voicelistsignal, self.settin_ui.mp3playsignal)

    def selectprocess(self, selectedp):
        self.textsource = None
        pids, pexe, hwnd = (selectedp)
        checkifnewgame(pexe, windows.GetWindowText(hwnd))
        if globalconfig['sourcestatus2']['texthook']['use']:
            self.textsource = texthook(pids, hwnd, pexe)
        elif globalconfig['sourcestatus2']['fridahook']['use']:
            if len(pids) != 1:
                getQMessageBox(self.settin_ui, "错误", "Only support pid num of 1")
                return
            try:
                self.textsource = fridahook(0, self.settin_ui.fridascripts[self.settin_ui.Scriptscombo.currentIndex()],
                                            pexe, pids[0])
            except:
                print_exc()

    # @threader
    def starttextsource(self, use=None, checked=True):
        self.translation_ui.showhidestate = False
        self.translation_ui.refreshtooliconsignal.emit()
        self.settin_ui.selectbutton.setEnabled(
            globalconfig['sourcestatus2']['texthook']['use'] or globalconfig['sourcestatus2']['fridahook']['use'])
        self.settin_ui.selecthookbutton.setEnabled(globalconfig['sourcestatus2']['texthook']['use'])
        self.textsource = None
        if checked:
            classes = {'ocr': ocrtext, 'copy': copyboard, 'texthook': None, 'fridahook': None}
            if use is None:
                use = list(filter(lambda _: globalconfig['sourcestatus2'][_]['use'], classes.keys()))
                use = None if len(use) == 0 else use[0]
            if use is None:
                return
            elif classes[use] is None:
                pass
            else:
                self.textsource = classes[use]()

    @threader
    def starthira(self, use=None, checked=True):
        if checked:
            hirasettingbase = globalconfig['hirasetting']
            _hira = None
            for name in hirasettingbase:
                if hirasettingbase[name]['use']:
                    if os.path.exists('./LunaTranslator/hiraparse/' + name + '.py') == False:
                        continue
                    _hira = importlib.import_module('hiraparse.' + name).hira
                    break

            try:
                if _hira:
                    self.hira_ = _hira()
                else:
                    self.hira_ = None
            except:
                print_exc()
                self.hira_ = None
        else:
            self.hira_ = None

    def fanyiinitmethod(self, classname):
        try:
            if classname == 'selfbuild':
                if os.path.exists('./userconfig/selfbuild.py') == False:
                    return None
                aclass = importlib.import_module('selfbuild').TS
            else:
                if os.path.exists('./LunaTranslator/translator/' + classname + '.py') == False:
                    return None
                aclass = importlib.import_module('translator.' + classname).TS
        except Exception as e:
            print_exc()
            self.textgetmethod(
                '<msg_error_not_refresh>' + globalconfig['fanyi'][classname]['name'] + ' import failed : ' + str(
                    stringfyerror(e)))
            return None
        return aclass(classname)

    def prepare(self, now=None, _=None):
        self.commonloader('fanyi', self.translators, self.fanyiinitmethod, now)

    def commonloader(self, fanyiorcishu, dictobject, initmethod, _type=None):
        if _type:
            self.commonloader_warp(fanyiorcishu, dictobject, initmethod, _type)
        else:
            for key in globalconfig[fanyiorcishu]:
                self.commonloader_warp(fanyiorcishu, dictobject, initmethod, key)

    @threader
    def commonloader_warp(self, fanyiorcishu, dictobject, initmethod, _type):
        try:
            if _type in dictobject:
                try:
                    dictobject[_type].notifyqueuforend()
                except:
                    pass
                dictobject.pop(_type)
            if globalconfig[fanyiorcishu][_type]['use'] == False:
                return
            item = initmethod(_type)
            if item:
                dictobject[_type] = item
        except:
            print_exc()

    def startxiaoxueguan(self, type_=None, _=None):
        self.commonloader('cishu', self.cishus, self.cishuinitmethod, type_)

    def cishuinitmethod(self, type_):
        try:
            aclass = importlib.import_module('cishu.' + type_)
            aclass = getattr(aclass, type_)
        except:
            return

        class cishuwrapper:
            def __init__(self, _type) -> None:
                self._ = _type()

            @threader
            def search(self, sentence):
                try:
                    res = self._.search(sentence)
                    if res is None or res == '':
                        return
                    self.callback(res)
                except:
                    pass

        _ = cishuwrapper(aclass)
        return _

    def onwindowloadautohook(self):
        textsourceusing = globalconfig['sourcestatus2']['texthook']['use'] or \
                          globalconfig['sourcestatus2']['fridahook']['use']
        if not (globalconfig['autostarthook'] and textsourceusing):
            return
        elif self.AttachProcessDialog.isVisible():
            return
        else:
            try:
                if self.textsource is None:
                    hwnd = windows.GetForegroundWindow()
                    pid = windows.GetWindowThreadProcessId(hwnd)
                    name_ = getpidexe(pid)
                    if name_ and name_ in savehook_new_list:
                        lps = ListProcess(False)
                        for pids, _exe in lps:
                            if _exe == name_:

                                # if any(map(testprivilege,pids)):
                                self.textsource = None
                                if globalconfig['sourcestatus2']['texthook']['use']:

                                    idx = savehook_new_list.index(name_)
                                    savehook_new_list.insert(0, savehook_new_list.pop(idx))
                                    needinserthookcode = savehook_new_data[name_]['needinserthookcode']
                                    self.textsource = texthook(pids, hwnd, name_,
                                                               autostarthookcode=savehook_new_data[name_]['hook'],
                                                               needinserthookcode=needinserthookcode)
                                elif len(pids) == 1 and globalconfig['sourcestatus2']['fridahook']['use'] and \
                                        savehook_new_data[name_]['fridahook']['loadmethod'] == 0:
                                    self.textsource = fridahook(0, savehook_new_data[name_]['fridahook']['js'], name_,
                                                                pids[0], hwnd)
                                break

                else:
                    pids = self.textsource.pids
                    if sum([int(pid_running(pid)) for pid in pids]) == 0:
                        self.textsource = None
            except:

                print_exc()

    def autohookmonitorthread(self):
        for game in savehook_new_data:
            checkifnewgame(game)
        while self.isrunning:
            self.onwindowloadautohook()
            time.sleep(0.5)  # 太短了的话，中间存在一瞬间，后台进程比前台窗口内存占用要大。。。

    def autocheckhwndexists(self):
        def setandrefresh(bool):
            if self.translation_ui.isbindedwindow != bool:
                self.translation_ui.isbindedwindow = bool
                self.translation_ui.refreshtooliconsignal.emit()

        while self.isrunning:
            if self.textsource:

                hwnd = self.textsource.hwnd

                if hwnd == 0:
                    if globalconfig['sourcestatus2']['texthook']['use']:
                        fhwnd = windows.GetForegroundWindow()
                        pids = self.textsource.pids
                        if hwnd == 0 and windows.GetWindowThreadProcessId(fhwnd) in pids:
                            if 'once' not in dir(self.textsource):
                                self.textsource.once = True
                                self.textsource.hwnd = fhwnd
                                setandrefresh(True)
                    else:
                        setandrefresh(False)
                else:
                    if windows.GetWindowThreadProcessId(hwnd) == 0:
                        self.textsource.hwnd = 0
                        setandrefresh(False)
                    elif 'once' not in dir(self.textsource):
                        self.textsource.once = True
                        setandrefresh(True)
                if len(self.textsource.pids):
                    _mute = winsharedutils.GetProcessMute(self.textsource.pids[0])
                    if self.translation_ui.processismuteed != _mute:
                        self.translation_ui.processismuteed = _mute
                        self.translation_ui.refreshtooliconsignal.emit()
            else:
                setandrefresh(False)

            time.sleep(0.5)

    def aa(self):
        self.translation_ui = gui.translatorUI.QUnFrameWindow()

        self.translation_ui.show()
        self.mainuiloadafter()

    def checkgameplayingthread(self):
        while True:
            statistictime = time.time()
            time.sleep(1)

            try:
                _hwnd = windows.GetForegroundWindow()
                _pid = windows.GetWindowThreadProcessId(_hwnd)
                if self.textsource and 'pids' in dir(self.textsource) and len(self.textsource.pids):
                    try:
                        if _pid in self.textsource.pids:
                            savehook_new_data[self.textsource.pname]['statistic_playtime'] += (
                                    time.time() - statistictime)
                    except:
                        pass
                else:
                    name_ = getpidexe(_pid)
                    if name_ and name_ in savehook_new_list:
                        savehook_new_data[name_]['statistic_playtime'] += (time.time() - statistictime)
            except:
                print_exc()

    def mainuiloadafter(self):
        self.transhis = gui.transhist.transhist(self.translation_ui)
        gobject.overridestdio()

        self.loadvnrshareddict()
        self.prepare()
        self.startxiaoxueguan()
        self.starthira()

        self.settin_ui = Settin(self.translation_ui)
        gobject.baseobject.Prompt = Prompt()
        self.startreader()

        self.edittextui = gui.edittext.edittext(self.translation_ui)
        self.searchwordW = searchwordW(self.translation_ui)
        self.hookselectdialog = gui.selecthook.hookselect(self.settin_ui)
        self.showocrimage = showocrimage(self.settin_ui)
        self.AttachProcessDialog = AttachProcessDialog(self.settin_ui, self.selectprocess, self.hookselectdialog)
        self.starttextsource()
        threading.Thread(target=self.autocheckhwndexists).start()
        threading.Thread(target=self.autohookmonitorthread).start()
        threading.Thread(target=minmaxmoveobservefunc, args=(self.translation_ui,)).start()
        threading.Thread(target=self.checkgameplayingthread).start()

    def checklang(self):
        if globalconfig['language_setted_2.4.5'] == False:
            x = languageset(static_data['language_list_show'])
            x.exec()
            globalconfig['language_setted_2.4.5'] = True
            globalconfig['languageuse'] = x.current
            globalconfig['tgtlang3'] = x.current
            setlanguage()
