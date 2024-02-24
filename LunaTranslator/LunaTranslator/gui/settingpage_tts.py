import functools

from PyQt5.QtWidgets import QComboBox
from gui.inputdialog import getsomepath1, autoinitdialog
from myutils.config import globalconfig, _TRL
import os, functools
import gobject
from gui.usefulwidget import getsimplecombobox, getspinbox, getcolorbutton, yuitsu_switch, getsimpleswitch, gettextedit


def setTab5_direct(self):
    self.voicecombo = QComboBox()
    self.voicelistsignal.connect(functools.partial(showvoicelist, self))
    self.voicecombo.currentTextChanged.connect(lambda x: changevoice(self, x))


def setTab5(self):
    self.tabadd_lazy(self.tab_widget, ('语音合成'), lambda: setTab5lz(self))


def voicevox_config_dialog(parent, d, callback=None):
    """
    Path With URL TextLine
    :param parent: parent
    :param d: The dict to be modified
    :param callback: callback
    """
    autoinitdialog(parent, 'VOICEVOX', 800, [
        # d refers to the dict to be modified
        # k refers to the key in the dict
        {'t': 'file', 'l': 'VoiceVox文件夹', 'd': d, 'k': 'path', 'dir': True, 'filter': ""},
        {'t': 'lineedit', 'l': 'VoiceVox URL', 'd': d, 'k': 'base_url', 'placeholder': 'http://127.0.0.1:50021'},
        {'l': '若使用本地VoiceVox，只需填写文件夹路径即可；若使用远程VoiceVox，需填写URL地址。'},
        {'l': '若VoiceVox URL为空，则默认为 http://127.0.0.1:50021'},
        {'t': 'okcancel', 'callback': callback},
    ])


def getttsgrid(self):
    grids = []
    i = 0
    self.ocrswitchs = {}
    line = []
    for name in globalconfig['reader']:

        _f = './LunaTranslator/tts/{}.py'.format(name)
        if os.path.exists(_f) == False:
            continue

        line += [
            ((globalconfig['reader'][name]['name']), 6),
            getsimpleswitch(globalconfig['reader'][name], 'use', name=name, parent=self,
                            callback=functools.partial(yuitsu_switch, self, globalconfig['reader'], 'readerswitchs',
                                                       name, gobject.baseobject.startreader), pair='readerswitchs'),

        ]
        if name in ['voiceroid2', 'voiceroidplus']:
            line += [getcolorbutton(globalconfig, '',
                                    callback=functools.partial(getsomepath1, self, globalconfig['reader'][name]['name'],
                                                               globalconfig['reader'][name], 'path',
                                                               globalconfig['reader'][name]['name'],
                                                               gobject.baseobject.startreader, True), icon='fa.gear',
                                    constcolor="#FF69B4")]
        elif name in ['voicevox']:
            line += [getcolorbutton(globalconfig, '',
                                    callback=functools.partial(voicevox_config_dialog, self,
                                                               globalconfig['reader'][name],
                                                               gobject.baseobject.startreader),
                                    icon='fa.gear',
                                    constcolor="#FF69B4")]
        else:
            line += ['']
        if i % 3 == 2:
            grids.append(line)
            line = []
        else:
            line += ['']
        i += 1
    if len(line):
        grids.append(line)
    return grids


def setTab5lz(self):
    grids = getttsgrid(self)
    grids += [
        [],
        [("选择声音", 6), (self.voicecombo, 15)],
        [('语速:(-10~10)', 6), (getspinbox(-10, 10, globalconfig['ttscommon'], 'rate'), 3)],
        [('音量:(0~100)', 6), (getspinbox(0, 100, globalconfig['ttscommon'], 'volume'), 3)],
        [('自动朗读', 6), (getsimpleswitch(globalconfig, 'autoread'), 1)],
        [('朗读原文', 6), (getsimpleswitch(globalconfig, 'read_raw'), 1), '', '', ('朗读翻译', 6),
         (getsimpleswitch(globalconfig, 'read_trans'), 1)],
        [('朗读的翻译', 6), (
            getsimplecombobox(_TRL([globalconfig['fanyi'][x]['name'] for x in globalconfig['fanyi']]), globalconfig,
                              'read_translator'), 15)],
        [('跳过自动朗读正则', 6), (gettextedit(globalconfig, 'not_read_regex'), 15)],
    ]
    gridlayoutwidget = self.makegrid(grids)
    gridlayoutwidget = self.makescroll(gridlayoutwidget)
    return gridlayoutwidget


def changevoice(self, text):
    globalconfig['reader'][gobject.baseobject.reader_usevoice]['voice'] = gobject.baseobject.reader.voicelist[
        self.voicecombo.currentIndex()]


def showvoicelist(self, vl, idx):
    self.voicecombo.blockSignals(True)
    self.voicecombo.clear()
    self.voicecombo.addItems(vl)
    if idx >= 0:
        self.voicecombo.setCurrentIndex(idx)
    self.voicecombo.blockSignals(False)
