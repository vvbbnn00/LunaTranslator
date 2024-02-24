from PyQt5.QtWidgets import QDesktopWidget, QMainWindow, QApplication, QPushButton, QTabBar, QStylePainter, \
    QStyleOptionTab, QStyle, QMessageBox, QDialog, QLabel, QHBoxLayout, QInputDialog
from PyQt5.QtGui import QCursor, QCloseEvent, QColor, QTextCursor
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QRect, QPoint, QObject
from myutils.config import _TR, globalconfig
from PyQt5.QtWidgets import QColorDialog, QSpinBox, QDoubleSpinBox, QPushButton, QComboBox, QLabel, QDialogButtonBox, \
    QLineEdit, QGridLayout, QApplication, QTabBar, QVBoxLayout
from traceback import print_exc
import qtawesome, functools, gobject, threading
from myutils.wrapper import Singleton
from myutils.hwnd import showintab


@Singleton
class dialog_showinfo(QDialog):

    def __init__(self, parent, title, info) -> None:
        super().__init__(parent, Qt.WindowCloseButtonHint)
        self.setWindowTitle(title)
        l = QLabel(info)
        layout = QHBoxLayout()
        layout.addWidget(l)
        self.setLayout(layout)
        self.show()


def getQMessageBox(parent=None, title="", text="", useok=True, usecancel=False, okcallback=None, cancelcallback=None,
                   tr=True):
    msgBox = QMessageBox(parent)
    if tr:
        title, text = _TR(title), _TR(text)
    msgBox.setWindowTitle((title))
    msgBox.setText((text))
    btn = 0
    if useok: btn |= QMessageBox.Ok
    if usecancel: btn |= QMessageBox.Cancel

    msgBox.setStandardButtons(btn)
    msgBox.setDefaultButton(QMessageBox.Ok)
    ret = msgBox.exec()

    if ret == QMessageBox.Ok and okcallback:
        okcallback()
    elif ret == QMessageBox.Cancel and cancelcallback:
        cancelcallback()


def isinrect(pos, rect):
    x, y = pos.x(), pos.y()
    x1, x2, y1, y2 = rect
    return x >= x1 and x <= x2 and y <= y2 and y >= y1


class saveposwindow(QMainWindow):
    def __init__(self, parent, dic=None, key=None, flags=None) -> None:
        if flags:
            super().__init__(parent, flags=flags)
        else:
            super().__init__(parent)
        d = QApplication.primaryScreen()
        self.dic, self.key = dic, key
        if self.dic:
            dic[key][0] = min(max(dic[key][0], 0), d.size().width() - dic[key][2])
            dic[key][1] = min(max(dic[key][1], 0), d.size().height() - dic[key][3])
            self.setGeometry(*dic[key])

    def resizeEvent(self, a0) -> None:
        if self.dic:
            if self.isMaximized() == False:
                self.dic[self.key] = list(self.geometry().getRect())

    def moveEvent(self, a0) -> None:
        if self.dic:
            if self.isMaximized() == False:
                self.dic[self.key] = list(self.geometry().getRect())

    def closeEvent(self, event: QCloseEvent):
        if self.dic:
            if self.isMaximized() == False:
                self.dic[self.key] = list(self.geometry().getRect())


class closeashidewindow(saveposwindow):
    showsignal = pyqtSignal()
    realshowhide = pyqtSignal(bool)

    def __init__(self, parent, dic=None, key=None) -> None:
        super().__init__(parent, dic, key)
        self.showsignal.connect(self.showfunction)
        self.realshowhide.connect(self.realshowhidefunction)
        if globalconfig['showintab_sub']:
            showintab(int(self.winId()), True)

    def realshowhidefunction(self, show):
        if show:
            self.showNormal()
        else:
            self.hide()

    def showfunction(self):
        if self.isMinimized():
            self.showNormal()
        elif self.isHidden():
            self.show()
        else:
            self.hide()

    def closeEvent(self, event: QCloseEvent):
        self.hide()
        event.ignore()
        super().closeEvent(event)


class MySwitch(QPushButton):
    def __init__(self, parent=None, sign=True, enable=True):
        self.status1 = 0
        self.status2 = 0
        self.colors = [
            '#7f7f7f',
            '#afafaf',
            '#FFa9d4',
            '#FF69B4',
        ]
        self.icons = [
            "fa.times",
            "fa.check"
        ]
        super().__init__(parent)

        self.setStyleSheet('''background-color: rgba(255, 255, 255, 0);
          color: black;
          border: 0px;
          font: 100 10pt;''')

        self.clicked.connect(self.setChecked)
        self.setIconSize(QSize(25, 25))
        self.setEnabled(enable)
        self.setCheckable(True)
        self.setChecked(sign)

    def setChecked(self, a0):
        super().setChecked(a0)
        self.status1 = a0
        self.setIcon(qtawesome.icon(self.icons[self.status1], color=self.colors[self.status1 * 2 + self.status2]))

    def setEnabled(self, a0):
        super().setEnabled(a0)
        self.status2 = a0
        self.setIcon(qtawesome.icon(self.icons[self.status1], color=self.colors[self.status1 * 2 + self.status2]))


class resizableframeless(saveposwindow):
    def __init__(self, parent, flags, dic, key) -> None:
        super().__init__(parent, dic, key, flags)
        self.setMouseTracking(True)

        self._padding = 5
        # 设置鼠标跟踪判断扳机默认值
        self._move_drag = False
        self._corner_drag = False
        self._bottom_drag = False
        self._lcorner_drag = False
        self._right_drag = False
        self._left_drag = False

    def isinrect(self, pos, rect):
        return isinrect(pos, rect)

    def resizeEvent(self, e):

        if self._move_drag == False:
            self._right_rect = [self.width() - self._padding, self.width() + 1, 0, self.height() - self._padding]
            self._left_rect = [-1, self._padding, 0, self.height() - self._padding]
            self._bottom_rect = [self._padding, self.width() - self._padding, self.height() - self._padding,
                                 self.height() + 1]
            self._corner_rect = [self.width() - self._padding, self.width() + 1, self.height() - self._padding,
                                 self.height() + 1]
            self._lcorner_rect = [-1, self._padding, self.height() - self._padding, self.height() + 1]

    def mousePressEvent(self, event):
        # 重写鼠标点击的事件 

        if (event.button() == Qt.LeftButton) and (self.isinrect(event.pos(), self._corner_rect)):
            # 鼠标左键点击右下角边界区域
            self._corner_drag = True
        elif (event.button() == Qt.LeftButton) and (self.isinrect(event.pos(), self._right_rect)):
            # 鼠标左键点击右侧边界区域
            self._right_drag = True
        elif (event.button() == Qt.LeftButton) and (self.isinrect(event.pos(), self._left_rect)):
            # 鼠标左键点击右侧边界区域
            self._left_drag = True
            self.startxp = (event.globalPos() - self.pos())
            self.startx = event.globalPos().x()
            self.startw = self.width()
        elif (event.button() == Qt.LeftButton) and (self.isinrect(event.pos(), self._bottom_rect)):
            # 鼠标左键点击下侧边界区域
            self._bottom_drag = True
        elif (event.button() == Qt.LeftButton) and (self.isinrect(event.pos(), self._lcorner_rect)):
            # 鼠标左键点击下侧边界区域
            self._lcorner_drag = True
            self.startxp = (event.globalPos() - self.pos())
            self.startx = event.globalPos().x()
            self.startw = self.width()
        # and (event.y() < self._TitleLabel.height()):
        elif (event.button() == Qt.LeftButton):
            # 鼠标左键点击标题栏区域
            self._move_drag = True
            self.move_DragPosition = event.globalPos() - self.pos()

    def mouseMoveEvent(self, QMouseEvent):
        # 判断鼠标位置切换鼠标手势 

        pos = QMouseEvent.pos()

        if self._move_drag == False:
            if self.isinrect(pos, self._corner_rect):
                self.setCursor(Qt.SizeFDiagCursor)
            elif self.isinrect(pos, self._lcorner_rect):
                self.setCursor(Qt.SizeBDiagCursor)
            elif self.isinrect(pos, self._bottom_rect):
                self.setCursor(Qt.SizeVerCursor)
            elif self.isinrect(pos, self._right_rect):
                self.setCursor(Qt.SizeHorCursor)
            elif self.isinrect(pos, self._left_rect):
                self.setCursor(Qt.SizeHorCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
        if Qt.LeftButton and self._right_drag:

            # 右侧调整窗口宽度
            self.resize(pos.x(), self.height())
        elif Qt.LeftButton and self._left_drag:
            # 右侧调整窗口宽度  
            self.setGeometry((QMouseEvent.globalPos() - self.startxp).x(), self.y(),
                             self.startw - (QMouseEvent.globalPos().x() - self.startx), self.height())
            # self.resize(pos.x(), self.height())
        elif Qt.LeftButton and self._bottom_drag:
            # 下侧调整窗口高度
            self.resize(self.width(), QMouseEvent.pos().y())
        elif Qt.LeftButton and self._lcorner_drag:
            # 下侧调整窗口高度
            self.setGeometry((QMouseEvent.globalPos() - self.startxp).x(), self.y(),
                             self.startw - (QMouseEvent.globalPos().x() - self.startx), QMouseEvent.pos().y())
        elif Qt.LeftButton and self._corner_drag:
            # 右下角同时调整高度和宽度
            self.resize(pos.x(), pos.y())
        elif Qt.LeftButton and self._move_drag:
            # 标题栏拖放窗口位置
            self.move(QMouseEvent.globalPos() - self.move_DragPosition)

    def mouseReleaseEvent(self, QMouseEvent):
        # 鼠标释放后，各扳机复位
        self._move_drag = False
        self._corner_drag = False
        self._bottom_drag = False
        self._lcorner_drag = False
        self._right_drag = False
        self._left_drag = False


class rotatetab(QTabBar):
    def tabSizeHint(self, index):
        s = QTabBar.tabSizeHint(self, index)
        s.transpose()
        return s

    def paintEvent(self, e):
        painter = QStylePainter(self)
        opt = QStyleOptionTab()
        for i in range(self.count()):
            self.initStyleOption(opt, i)
            painter.drawControl(QStyle.CE_TabBarTabShape, opt)
            painter.save()
            s = opt.rect.size()
            s.transpose()
            r = QRect(QPoint(), s)
            r.moveCenter(opt.rect.center())
            opt.rect = r
            c = self.tabRect(i).center()
            painter.translate(c)
            painter.rotate(90)
            painter.translate(-c)
            painter.drawControl(QStyle.CE_TabBarTabLabel, opt)
            painter.restore()


class Prompt_dialog(QDialog):
    def __init__(self, parent, title, info, default='') -> None:
        super().__init__(parent)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint & ~Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setWindowTitle(title)
        self.setWindowIcon(qtawesome.icon('fa-question'))

        _layout = QVBoxLayout()

        _layout.addWidget(QLabel(info))

        self.text = []
        for _ in default:
            if isinstance(_, str):
                self.text.append(QLineEdit(_))
            else:
                le = QLineEdit()
                le.setPlaceholderText(_[0])
                self.text.append((le))
            _layout.addWidget(self.text[-1])
        button = QDialogButtonBox(QDialogButtonBox.Ok)
        button.accepted.connect(self.accept)
        _layout.addWidget(button)
        self.setLayout(_layout)
        self.resize(400, 1)
        cursor = QCursor()
        pos = cursor.pos()
        num_screens = QDesktopWidget().screenCount()
        for i in range(num_screens):
            _rect = QDesktopWidget().screenGeometry(i)
            if isinrect(pos, [_rect.getRect()[_] for _ in [0, 2, 1, 3]]):
                self.move(_rect.width() // 2 - self.width() // 2, _rect.height() // 3)
                break


class Prompt(QObject):
    call = pyqtSignal(str, str, list, list)

    def __init__(self) -> None:
        super().__init__()
        self.call.connect(self.getinputfunc)

    def getinputfunc(self, title, info, default, callback):
        _dia = Prompt_dialog(gobject.baseobject.settin_ui, title, info, default)

        _dia.exec()

        text = []
        for _t in _dia.text:
            text.append(_t.text())
        callback[0](text)


def callbackwrap(d, k, call, _):
    d[k] = _
    if call:
        try:
            call(_)
        except:
            print_exc()


def getsimplecombobox(lst, d, k, callback=None):
    s = QComboBox()
    s.addItems(lst)
    if (k not in d) or (d[k] >= len(lst)): d[k] = 0
    s.setCurrentIndex(d[k])
    s.currentIndexChanged.connect(functools.partial(callbackwrap, d, k, callback))
    return s


def getspinbox(mini, maxi, d, key, double=False, step=1, callback=None, dec=1):
    if double:
        s = QDoubleSpinBox()
        s.setDecimals(dec)
    else:
        s = QSpinBox()
        d[key] = int(d[key])
    s.setMinimum(mini)
    s.setMaximum(maxi)
    s.setSingleStep(step)
    s.setValue(d[key])
    s.valueChanged.connect(functools.partial(callbackwrap, d, key, callback))
    return s


def getcolorbutton(d, key, callback, name=None, parent=None, icon="fa.paint-brush", constcolor=None, enable=True,
                   transparent=True, qicon=None):
    if qicon is None:
        qicon = qtawesome.icon(icon, color=constcolor if constcolor else d[key])
    b = QPushButton(qicon, "")
    b.setEnabled(enable)
    b.setIconSize(QSize(20, 20))
    if transparent:
        b.setStyleSheet('''background-color: rgba(255, 255, 255, 0);
            color: black;
            border: 0px;
            font: 100 10pt;''')
    b.clicked.connect(callback)
    if name:
        setattr(parent, name, b)
    return b


def yuitsu_switch(parent, configdict, dictobjectn, key, callback, checked):
    dictobject = getattr(parent, dictobjectn)
    if checked:
        for k in dictobject:
            configdict[k]['use'] = k == key
            dictobject[k].setChecked(k == key)

    if callback:
        callback(key, checked)


def getsimpleswitch(d, key, enable=True, callback=None, name=None, pair=None, parent=None, default=None):
    if default:
        if key not in d:
            d[key] = default

    b = MySwitch(sign=d[key], enable=enable)
    b.clicked.connect(functools.partial(callbackwrap, d, key, callback))

    if pair:
        if pair not in dir(parent):
            setattr(parent, pair, {})
        getattr(parent, pair)[name] = b
    elif name:
        setattr(parent, name, b)
    return b


def selectcolor(parent, configdict, configkey, button, item=None, name=None, callback=None):
    color = QColorDialog.getColor(QColor(configdict[configkey]), parent)
    if not color.isValid():
        return
    if button is None:
        button = getattr(item, name)
    button.setIcon(qtawesome.icon("fa.paint-brush", color=color.name()))
    configdict[configkey] = color.name()

    if callback:
        try:
            callback()
        except:
            print_exc()


def getboxlayout(widgets, lc=QHBoxLayout):
    cp_layout = lc()
    for w in widgets:
        cp_layout.addWidget(w)
    return cp_layout


def textbrowappendandmovetoend(textOutput, sentence, addspace=True):
    scrollbar = textOutput.verticalScrollBar()
    atBottom = scrollbar.value() + 3 > scrollbar.maximum() or scrollbar.value() / scrollbar.maximum() > 0.975
    cursor = QTextCursor(textOutput.document())
    cursor.movePosition(QTextCursor.End)
    cursor.insertText((('' if textOutput.document().isEmpty() else '\n') if addspace else '') + sentence)
    if (atBottom):
        scrollbar.setValue(scrollbar.maximum())
