from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListView, QDialogButtonBox, \
    QApplication, QPushButton, QMainWindow
from PyQt5.QtGui import QStandardItemModel, QPixmap, QColor, QIcon, QStandardItem, QFont
import functools
from traceback import print_exc
from myutils.config import globalconfig, _TR, _TRL
import sys
import windows
import time, os
from myutils.hwnd import getpidexe, ListProcess, mouseselectwindow, getExeIcon, testprivilege, getpidhwndfirst
import qtawesome

from gui.usefulwidget import closeashidewindow, getQMessageBox


class AttachProcessDialog(closeashidewindow):
    setcurrentpidpnamesignal = pyqtSignal(int, int)

    def selectwindowcallback(self, pid, hwnd):
        if pid == os.getpid():
            return
        name = getpidexe(pid)
        lps = ListProcess(False)
        _pids = None
        for pids, _exe in lps:
            if _exe == name:
                _pids = pids
                break
        if _pids is None:
            _pids = [pid]
        self.processEdit.setText(name)
        self.processIdEdit.setText(','.join([str(pid) for pid in _pids]))
        [_.show() for _ in self.windowtextlayoutwidgets]
        self.windowtext.setText(windows.GetWindowText(hwnd))
        self.selectedp = (_pids, name, hwnd)

    def __init__(self, parent, callback, hookselectdialog=None):
        super(AttachProcessDialog, self).__init__(parent, globalconfig, 'attachprocessgeo')
        self.setcurrentpidpnamesignal.connect(self.selectwindowcallback)

        self.iconcache = {}

        self.callback = callback
        self.hookselectdialog = hookselectdialog
        self.selectedp = None
        self.setWindowTitle(
            _TR('选择进程') + " " + _TR("当前权限") + " " + _TR("管理员" if windows.IsUserAnAdmin() else "非管理员"))
        self.setWindowIcon(qtawesome.icon("fa.gear"))
        w = QWidget()
        self.layout1 = QVBoxLayout()
        self.label = QLabel(
            _TR('如果没看见想要附加的进程，可以尝试点击下方按钮后点击游戏窗口,或者尝试使用管理员权限运行本软件'))
        self.button = QPushButton(_TR('点击此按钮后点击游戏窗口'))
        self.button.clicked.connect(functools.partial(mouseselectwindow, self.setcurrentpidpnamesignal.emit))
        self.layout1.addWidget(self.label)
        self.layout1.addWidget(self.button)
        self.layout2 = QHBoxLayout()
        self.processIdEdit = QLineEdit()
        self.layout2.addWidget(QLabel(_TR('进程号')))
        self.layout2.addWidget(self.processIdEdit)
        self.processEdit = QLineEdit()
        self.layout3 = QHBoxLayout()
        self.layout3.addWidget(QLabel(_TR('程序名')))
        self.layout3.addWidget(self.processEdit)

        self.windowtext = QLineEdit()
        self.windowtextlayoutwidgets = [QLabel(_TR('窗口名')), self.windowtext]
        [_.hide() for _ in self.windowtextlayoutwidgets]
        self.layout2.addWidget(self.windowtextlayoutwidgets[0])
        self.layout2.addWidget(self.windowtextlayoutwidgets[1])
        self.processList = QListView()
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.layout1.addLayout(self.layout2)
        self.layout1.addLayout(self.layout3)
        self.layout1.addWidget(self.processList)
        bottomlayout = QHBoxLayout()
        refreshbutton = QPushButton(_TR("刷新"))
        refreshbutton.clicked.connect(self.refreshfunction)
        bottomlayout.addWidget(refreshbutton)
        bottomlayout.addWidget(self.buttonBox)

        self.layout1.addLayout(bottomlayout)
        w.setLayout(self.layout1)
        # self.setLayout(self.layout1)
        self.setCentralWidget(w)
        # print(time.time()-t1)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.close)
        self.processList.clicked.connect(self.selectedfunc)
        self.processIdEdit.textEdited.connect(self.editpid)

        self.processEdit.setReadOnly(True)
        self.windowtext.setReadOnly(True)

    def refreshfunction(self):

        self.windowtext.clear()
        self.processEdit.clear()
        self.processIdEdit.clear()
        [_.hide() for _ in self.windowtextlayoutwidgets]
        self.selectedp = None

        ########################### 
        self.model = QStandardItemModel(self.processList)
        # print(time.time()-t1)
        self.processlist = ListProcess()
        # print(time.time()-t1)
        self.processList.setModel(self.model)
        for pid, pexe in self.processlist:
            if pexe in self.iconcache:
                icon = self.iconcache[pexe]
            else:
                icon = getExeIcon(pexe)
                self.iconcache[pexe] = icon
            item = QStandardItem(icon, pexe)
            item.setEditable(False)
            self.model.appendRow(item)

    def showEvent(self, e):
        if self.hookselectdialog:
            self.hookselectdialog.realshowhide.emit(False)
        self.refreshfunction()
        # print(time.time()-t1)

    def safesplit(self, process):
        try:
            return [int(_) for _ in process.split(',')]
        except:
            return []

    def editpid(self, process):
        pids = self.safesplit(process)
        self.selectedp = (pids, getpidexe(pids[0]), self.guesshwnd(pids))
        self.processEdit.setText(self.selectedp[1])
        [_.hide() for _ in self.windowtextlayoutwidgets]

    def selectedfunc(self, index):
        pids, pexe = self.processlist[index.row()]
        self.processEdit.setText(pexe)
        self.processIdEdit.setText(','.join([str(pid) for pid in pids]))
        [_.hide() for _ in self.windowtextlayoutwidgets]
        self.selectedp = pids, pexe, self.guesshwnd(pids)

    def guesshwnd(self, pids):
        for pid in pids:
            hwnd = getpidhwndfirst(pid)
            if (hwnd) != 0:
                return hwnd
        return 0

    def accept(self):
        if self.selectedp is None:
            self.close()
        else:
            if self.selectedp[1] is None:
                getQMessageBox(self, "错误", "无法识别的路径！")
                return
            # for pid in self.selectedp[0]:

            #     if(not testprivilege(pid)): 
            #         getQMessageBox(self,"错误","权限不足，请使用管理员权限运行本程序！")
            #         return
            self.close()
            self.callback(self.selectedp)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    a = AttachProcessDialog()
    a.show()

    app.exit(app.exec_())
