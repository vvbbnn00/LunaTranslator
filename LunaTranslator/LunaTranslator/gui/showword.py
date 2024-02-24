from re import search
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QMainWindow, QApplication, QVBoxLayout, QFontDialog, QTextBrowser, \
    QLineEdit, QPushButton, QTabWidget, QMenu, QAction
from PyQt5.QtGui import QFont, QTextCursor, QFontMetrics
from PyQt5.QtCore import Qt, pyqtSignal, QSize
import qtawesome, functools, json
import threading, gobject
from queue import Queue
from myutils.config import globalconfig
from traceback import print_exc
from myutils.config import globalconfig, _TR, _TRL

from gui.usefulwidget import closeashidewindow


class searchwordW(closeashidewindow):
    getnewsentencesignal = pyqtSignal(str)
    searchthreadsignal = pyqtSignal(str, dict, str)
    showtabsignal = pyqtSignal(str, str)

    def __init__(self, parent):
        super(searchwordW, self).__init__(parent, globalconfig, 'sw_geo')
        self.setupUi()
        # self.setWindowFlags(self.windowFlags()&~Qt.WindowMinimizeButtonHint)
        self.getnewsentencesignal.connect(self.getnewsentence)
        self.setWindowTitle(_TR('查词'))

    def showresfun(self, k, res):
        first = res.split('<hr>')[0]

        self.textbs[k].insertHtml(first)
        self.textbs[k].firsttext = self.textbs[k].toPlainText()
        self.textbs[k].insertHtml(res[len(first):])

        scrollbar = self.textbs[k].verticalScrollBar()
        scrollbar.setValue(0)
        self.tab.setTabVisible(self._k.index(k), True)

    def setupUi(self):
        self.setWindowIcon(qtawesome.icon("fa.search"))

        self.showtabsignal.connect(self.showresfun)

        self.centralWidget = QWidget(self)
        self.setWindowIcon(qtawesome.icon("fa.gear"))
        self.hboxlayout = QHBoxLayout(self.centralWidget)
        self.vboxlayout = QVBoxLayout()

        self.searchlayout = QHBoxLayout()
        self.vboxlayout.addLayout(self.searchlayout)
        self.searchtext = QLineEdit()
        # self.searchtext.setFont(font)
        self.searchlayout.addWidget(self.searchtext)
        self.searchbutton = QPushButton(qtawesome.icon("fa.search"), '')  # _TR("搜索"))

        # self.searchbutton.setFont(font)
        self.searchbutton.clicked.connect(lambda: self.search((self.searchtext.text())))
        self.searchlayout.addWidget(self.searchbutton)

        self.soundbutton = QPushButton(qtawesome.icon("fa.music"), "")
        # self.searchbutton.setFont(font)
        self.soundbutton.clicked.connect(self.langdu)
        self.searchlayout.addWidget(self.soundbutton)

        self.tab = QTabWidget(self)

        self.vboxlayout.addWidget(self.tab)
        self.hboxlayout.addLayout(self.vboxlayout)
        self.setCentralWidget(self.centralWidget)

        self.textbs = {}

        _k = []
        _name = []
        for cishu in globalconfig['cishu']:
            _name.append(globalconfig['cishu'][cishu]['name'])
            _k.append(cishu)
        self._k = _k
        _name = _TRL(_name)

        for i in range(len(_name)):
            textOutput = QTextBrowser(self)
            # textOutput.setFont(font)
            textOutput.setContextMenuPolicy(Qt.CustomContextMenu)
            textOutput.setUndoRedoEnabled(False)
            textOutput.setReadOnly(True)
            textOutput.setOpenLinks(False)
            self.tab.addTab(textOutput, _name[i])
            self.textbs[self._k[i]] = (textOutput)

            textOutput.setContextMenuPolicy(Qt.CustomContextMenu)

            textOutput.customContextMenuRequested.connect(functools.partial(self.showmenu, i, textOutput))
        self.hiding = True
        self.searchthreadsignal.connect(self.searchthread)
        self.setfonts()

    def setfonts(self):
        font = QFont()
        font.fromString(globalconfig['sw_fontstring'])
        fm = QFontMetrics(font)
        self.searchbutton.setIconSize(QSize(fm.height(), fm.height()))
        self.soundbutton.setIconSize(QSize(fm.height(), fm.height()))
        self.setFont(font)
        self.tab.setFont(font)
        self.searchtext.setFont(font)

        for _ in self.textbs:
            self.textbs[_].setFont(font)

    def langdu(self):
        if gobject.baseobject.reader:
            gobject.baseobject.reader.read(self.searchtext.text())

    def showmenu(self, ii, to: QTextBrowser, p):
        menu = QMenu(self)
        ziti = QAction(_TR("字体"))
        menu.addAction(ziti)
        action = menu.exec(to.mapToGlobal(p))
        if action == ziti:

            font, ok = QFontDialog.getFont(self.font(), parent=self)

            if ok:
                globalconfig['sw_fontstring'] = font.toString()
                self.setfonts()

    def getnewsentence(self, sentence):
        self.showNormal()
        self.searchtext.setText(sentence)

        self.search(sentence)

    def searchthread(self, k, _mp, sentence):

        _mp[k].callback = functools.partial(self.showtabsignal.emit, k)
        _mp[k].search(sentence)

    def search(self, sentence):
        if sentence == '':
            return

        _mp = {}
        _mp.update(gobject.baseobject.cishus)

        for k in self._k:
            self.tab.setTabVisible(self._k.index(k), False)
            self.textbs[k].clear()
            if k in _mp:
                threading.Thread(target=self.searchthreadsignal.emit, args=(k, _mp, sentence)).start()
