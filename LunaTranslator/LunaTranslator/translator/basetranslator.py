from traceback import print_exc
from queue import Queue

from myutils.config import globalconfig, translatorsetting, static_data
from threading import Thread, Lock
import os, time, codecs
import zhconv, gobject
import sqlite3
from myutils.commonbase import commonbase

from myutils.utils import stringfyerror, autosql
from myutils.commonbase import ArgsEmptyExc
from myutils.wrapper import stripwrapper


class TimeOut(Exception):
    pass


class Threadwithresult(Thread):
    def __init__(self, func, defalut, ignoreexceptions):
        super(Threadwithresult, self).__init__()
        self.func = func
        self.result = defalut
        self.istimeout = True
        self.ignoreexceptions = ignoreexceptions
        self.exception = None

    def run(self):
        try:
            self.result = self.func()
        except Exception as e:
            self.exception = e
        self.istimeout = False

    def get_result(self, timeout=1, checktutukufunction=None):
        # Thread.join(self,timeout)
        # 不再超时等待，只检查是否是最后一个请求，若是则无限等待，否则立即放弃。
        while checktutukufunction and checktutukufunction() and self.istimeout:
            Thread.join(self, 0.1)

        if self.ignoreexceptions:
            return self.result
        else:
            if self.istimeout:
                raise TimeOut()
            elif self.exception:
                raise self.exception
            else:
                return self.result


def timeoutfunction(func, timeout=100, default=None, ignoreexceptions=False, checktutukufunction=None):
    t = Threadwithresult(func, default, ignoreexceptions)
    t.start()
    return t.get_result(timeout, checktutukufunction)


class basetrans(commonbase):
    def langmap(self):
        return {}

    def inittranslator(self):
        pass

    def translate(self, content):
        return ''

    @property
    def multiapikeycurrent(self):

        class alternatedict(dict):
            def __getitem__(self2, __key):
                t = super().__getitem__(__key)
                if type(t) != str:
                    raise Exception("Incorrect use of multiapikeycurrent")
                if '|' in t:
                    ts = t.split('|')
                    t = ts[self.multiapikeycurrentidx % len(ts)]
                return t.strip()

        return alternatedict(translatorsetting[self.typename]['args'])

    ############################################################
    _globalconfig_key = 'fanyi'
    _setting_dict = translatorsetting

    def level2init(self):
        self.multiapikeycurrentidx = -1
        self.queue = Queue()
        self.sqlqueue = None
        self._safe_private_init()

        self.lastrequesttime = 0
        self._cache = {}

        self.newline = None

        if self.transtype != 'pre':
            try:
                self.sqlwrite2 = autosql(sqlite3.connect('./translation_record/cache/{}.sqlite'.format(self.typename),
                                                         check_same_thread=False, isolation_level=None))
                try:
                    self.sqlwrite2.execute('CREATE TABLE cache(srclang,tgtlang,source,trans);')
                except:
                    pass
            except:
                print_exc
            self.sqlqueue = Queue()
            Thread(target=self._sqlitethread).start()
        Thread(target=self._fythread).start()

    def _safe_private_init(self):
        try:
            self._private_init()
        except Exception as e:
            gobject.baseobject.textgetmethod('<msg_error_not_refresh>' + globalconfig['fanyi'][self.typename][
                'name'] + ' inittranslator failed : ' + str(stringfyerror(e)))
            print_exc()

    def notifyqueuforend(self):
        if self.sqlqueue:
            self.sqlqueue.put(None)
        self.queue.put(None)

    def _private_init(self):
        self.inittranslator()

    def _sqlitethread(self):
        while self.using:
            task = self.sqlqueue.get()
            if task is None: break
            try:

                src, trans = task
                self.sqlwrite2.execute('INSERT into cache VALUES(?,?,?,?)', (self.srclang, self.tgtlang, src, trans))

            except:
                print_exc()

    @property
    def is_gpt_like(self):
        try:
            return translatorsetting[self.typename]['is_gpt_like']
        except:
            return False

    @property
    def needzhconv(self):
        l = static_data["language_list_translator_inner"][globalconfig['tgtlang3']]
        return l == 'cht' and 'cht' not in self.langmap()

    @property
    def using(self):
        return globalconfig['fanyi'][self.typename]['use']

    @property
    def transtype(self):
        return globalconfig['fanyi'][self.typename].get('type', 'free')

    def gettask(self, content):
        self.queue.put((content))

    def longtermcacheget(self, src):
        try:
            ret = self.sqlwrite2.execute('SELECT * FROM cache WHERE source = ?', (src,)).fetchall()
            # 有的时候，莫名其妙的卡住，不停的查询失败时的那个句子。。。
        except:
            return None
        for srclang, tgtlang, source, trans in ret:
            if (srclang, tgtlang) == (self.srclang, self.tgtlang):
                return trans

    def longtermcacheset(self, src, tgt):
        self.sqlqueue.put((src, tgt))

    def shorttermcacheget(self, src):
        langkey = (self.srclang, self.tgtlang)
        if langkey not in self._cache:
            self._cache[langkey] = {}
        try:
            return self._cache[langkey][src]
        except KeyError:
            return None

    def shorttermcacheset(self, src, tgt):
        langkey = (self.srclang, self.tgtlang)

        if langkey not in self._cache:
            self._cache[langkey] = {}
        self._cache[langkey][src] = tgt

    def cached_translate(self, contentsolved, hira, is_auto_run):
        is_using_gpt_and_retrans = is_auto_run == False and self.is_gpt_like
        if is_using_gpt_and_retrans == False:
            res = self.shorttermcacheget(contentsolved)
            if res:
                return res
        if globalconfig['uselongtermcache']:
            res = self.longtermcacheget(contentsolved)
            if res:
                return res

        if self.transtype == 'offline':
            res = self.dispatch_translate(contentsolved, hira)
        else:
            res = self.intervaledtranslate(contentsolved, hira)

        if globalconfig['uselongtermcache']:
            self.longtermcacheset(contentsolved, res)
        self.shorttermcacheset(contentsolved, res)

        return res

    def maybecachetranslate(self, contentraw, contentsolved, hira, is_auto_run):
        if self.transtype == 'pre':
            res = self.translate(contentraw)
        else:
            res = self.cached_translate(contentsolved, hira, is_auto_run)
        return res

    def intervaledtranslate(self, content, hira):
        interval = globalconfig['requestinterval']
        current = time.time()
        self.current = current
        sleeptime = interval - (current - self.lastrequesttime)

        if sleeptime > 0:
            time.sleep(sleeptime)
        self.lastrequesttime = time.time()
        if (current != self.current) or (self.using == False):
            raise Exception

        self.multiapikeycurrentidx += 1

        res = self.dispatch_translate(content, hira)

        return res

    def dispatch_translate(self, content, hira):
        if 'translate_with_extra' in dir(self):
            res = self.translate_with_extra(content, {'hira': hira})
        else:
            res = self.translate(content)
        return res

    @property
    def onlymanual(self):
        if 'manual' not in globalconfig['fanyi'][self.typename]:
            return False
        return globalconfig['fanyi'][self.typename]['manual']

    def _fythread(self):
        self.needreinit = False
        while self.using:

            savelast = []
            while True:
                _ = self.queue.get()
                if _ is None: break
                callback, contentraw, contentsolved, skip, embedcallback, is_auto_run, hira = _
                if embedcallback is not None:
                    savelast.clear()

                savelast.append(_)
                if self.queue.empty():
                    break
            if self.using == False: break
            if savelast[0][4] is not None:
                callback, contentraw, contentsolved, skip, embedcallback, is_auto_run, hira = savelast.pop(0)
                for _ in savelast:
                    self.gettask(_)
            if embedcallback is None:
                if skip:
                    continue
                if is_auto_run and self.onlymanual:
                    continue

            try:
                checktutukufunction = lambda: ((embedcallback is not None) or self.queue.empty()) and self.using
                if checktutukufunction():
                    def reinitandtrans():
                        if self.needreinit:
                            self.needreinit = False
                            self.renewsesion()
                            self._private_init()
                        return self.maybecachetranslate(contentraw, contentsolved, hira, is_auto_run)

                    res = timeoutfunction(reinitandtrans, checktutukufunction=checktutukufunction)
                    if self.needzhconv:
                        res = zhconv.convert(res, 'zh-tw')

                    callback(res, embedcallback)

            except Exception as e:
                if self.using and globalconfig['showtranexception']:
                    if isinstance(e, ArgsEmptyExc):
                        msg = str(e)
                    elif isinstance(e, TimeOut):
                        # 更改了timeout机制。timeout只会发生在队列非空时，故直接放弃
                        continue
                    else:
                        print_exc()
                        msg = stringfyerror(e)
                        self.needreinit = True
                    msg = '<msg_translator>' + msg

                    callback(msg, embedcallback)
