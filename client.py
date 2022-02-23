from PyQt5 import QtCore, QtWidgets, QtGui, uic
import re
import os
import json
import sys
import time
import socket
from threading import Thread
from queue import Queue


def check_ip_input(ip, port):
    IP_pattern = "(([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\\.){3}([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])"
    err = 0

    z = re.match(IP_pattern, ip)
    if not z or not z.span() == (0, len(ip)):
        err += 1

    try:
        if not 0 <= int(port) <= 65535:
            err += 2
    except ValueError:
        err += 2

    return err


class MainWin(QtWidgets.QMainWindow):
    eventSig = QtCore.pyqtSignal(str)

    def __init__(self, queue):
        super().__init__()

        self.theme = {"sent": "#665b49",
                      "recv": "#282e3a",
                      "light": "#4b566b",
                      "bckg": "#1e2126"}

        self.centerOnScreen()
        self.conn_info = None
        self.net_sock = None
        self.data_queue = queue
        self.eventSig.connect(self.handleSig)
        self.initUi()

        if self.read_config() == -1:
            self.getConfig()

    def initUi(self):
        uic.loadUi('files/client.ui', self)  # Load the .ui file
        # self.setFixedSize(self.frameGeometry().size())

        # Temp api access inits
        if 1 == 0:
            self.enc_btn = QtWidgets.QPushButton()
            self.in_txt = QtWidgets.QTextEdit()
            self.scroll = QtWidgets.QScrollArea()
            self.scroll_content = QtWidgets.QWidget()
            self.status = QtWidgets.QHBoxLayout()
            self.setAddr = QtWidgets.QAction()

        self.enc_btn.setEnabled(False)
        self.in_txt.setEnabled(False)
        self.setAddr.triggered.connect(self.getAddr)
        self.status.addStretch()
        icon = QtWidgets.QLabel()
        mv = QtGui.QMovie("files/loading.gif")
        icon.setMovie(mv)
        mv.setScaledSize(QtCore.QSize(20, 20))
        mv.start()
        self.status.addWidget(icon)
        lbl = QtWidgets.QLabel(" Establishing connection...")
        lbl.setFont(QtGui.QFont("Noto Sans", 11, QtGui.QFont.Bold))
        self.status.addWidget(lbl)
        self.status.addStretch()

        self.enc_btn.clicked.connect(self.send)
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_content)
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_layout.setAlignment(QtCore.Qt.AlignTop)
        self.installEventFilter(self)

        self.setStyleSheet(f"background-color: {self.theme['recv']}; color: #ffffff")
        self.menubar.setStyleSheet(f"background-color: {self.theme['recv']}; color: #ffffff")
        self.in_txt.setStyleSheet(f"border-radius: 10px; background-color: {self.theme['light']}; color: #ffffff")
        self.enc_btn.setStyleSheet(
            f"disabled{{background-color:black;}};background-color: {self.theme['recv']}; color: #ffffff")
        self.scroll_content.setStyleSheet(f"background-color: {self.theme['bckg']}; color: #ffffff")

        self.show()  # Show the GUI

    def read_config(self):
        if not os.path.exists("files/config.json"): return -1

        config = json.load(open("files/config.json", 'r'))
        self.conn_info = (config["server"], config["port"])

        return 0

    def centerOnScreen(self):
        self.move(QtWidgets.QDesktopWidget().screenGeometry().center() - self.geometry().center())

    def eventFilter(self, obj, event):
        focused_widget = QtWidgets.QApplication.focusWidget()
        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if event.type() == QtCore.QEvent.KeyRelease and focused_widget in [self.in_txt, self.enc_btn] \
                and event.key() == QtCore.Qt.Key_Return and modifiers != QtCore.Qt.ShiftModifier:
            self.enc_btn.click()
            return True

        return super().eventFilter(obj, event)

    def handleSig(self, sig):
        if sig == "connected":
            for i in reversed(range(self.status.count())):
                if self.status.itemAt(i).widget():
                    self.status.itemAt(i).widget().deleteLater()
                else:
                    self.status.removeItem(self.status.itemAt(i))

            self.status.addStretch()
            lbl = QtWidgets.QLabel(f"Connected to {self.net_sock.getsockname()[0]} at {self.net_sock.getsockname()[1]}")
            lbl.setFont(QtGui.QFont("Noto Sans", 12, QtGui.QFont.Bold))
            self.status.addWidget(lbl)
            self.status.addStretch()

            self.enc_btn.setEnabled(True)
            self.in_txt.setEnabled(True)

        if sig == "in_msg":
            self.update_recv()

    def getConnInfo(self):
        return self.conn_info

    def setSock(self, sock):
        self.net_sock = sock

    def getAddr(self):
        addrDialog = AddrDialog(self.theme)
        addrDialog.move(self.normalGeometry().center() - addrDialog.geometry().center())
        if addrDialog.exec_():
            self.conn_info = addrDialog.returnInfo()

    def getConfig(self):
        dialog = ConfigDialog(self.theme)
        dialog.move(self.normalGeometry().center() - dialog.geometry().center())
        if dialog.exec_():
            self.conn_info = dialog.returnInfo()

    def send(self):
        msg = self.in_txt.toPlainText().strip('\n')
        if not msg: return
        self.net_sock.send(msg.encode("utf-8"))
        lbl = QtWidgets.QLabel(msg)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        lbl.setFont(QtGui.QFont("Noto Sans", 11, QtGui.QFont.Bold))
        self.in_txt.setPlainText("")
        hbox = QtWidgets.QHBoxLayout()
        lbl.setStyleSheet(
            f"margin-top: 7px; margin-right: 5px; border-radius: 5px; padding-left: 10px; padding-right: 10px; background: {self.theme['sent']};")
        lbl.adjustSize()
        lbl.setFixedHeight(lbl.size().height() + 20)
        hbox.addStretch()
        hbox.addWidget(lbl)
        self.scroll_layout.addLayout(hbox)
        scroll_bar = self.scroll.verticalScrollBar()
        scroll_bar.rangeChanged.connect(lambda: scroll_bar.setValue(scroll_bar.maximum()))
        self.in_txt.setFocus()

    def update_recv(self):
        while not self.data_queue.empty():
            msg = self.data_queue.get()
            lbl = QtWidgets.QLabel(msg.strip('\n'))
            lbl.setWordWrap(True)
            lbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            lbl.setFont(QtGui.QFont("Noto Sans", 11, QtGui.QFont.Bold))
            hbox = QtWidgets.QHBoxLayout()
            lbl.setStyleSheet(
                f"margin-top: 7px; margin-left: 5px; border-radius: 5px; padding-left: 10px; padding-right: 10px; background: {self.theme['recv']};")
            lbl.adjustSize()
            lbl.setFixedHeight(lbl.size().height() + 20)
            hbox.addWidget(lbl)
            hbox.addStretch()
            self.scroll_layout.addLayout(hbox)
            scroll_bar = self.scroll.verticalScrollBar()
            scroll_bar.rangeChanged.connect(lambda: scroll_bar.setValue(scroll_bar.maximum()))
            self.in_txt.setFocus()


class ConfigDialog(QtWidgets.QDialog):
    def __init__(self, theme=None):
        super().__init__()
        uic.loadUi('files/Config_Dialog.ui', self)
        self.setStyleSheet(f"background-color: {theme['bckg']}; color: #ffffff")
        self.IP_box.setStyleSheet(f"background-color: {theme['recv']}; color: #ffffff")
        self.port_box.setStyleSheet(f"background-color: {theme['recv']}; color: #ffffff")
        self.selection.setStyleSheet(f"background-color: {theme['light']}; color: #ffffff")

    def accept(self):
        err = check_ip_input(self.IP_box.text(), self.port_box.text())
        print(err)

    def returnInfo(self):
        json.dump({
            "server": self.IP_box.text(),
            "port": int(self.port_box.text()),
            "theme": "default"
        }, open("files/config.json", 'w'))

        return self.IP_box.text(), int(self.port_box.text())


class AddrDialog(QtWidgets.QDialog):
    def __init__(self, theme):
        super().__init__()
        uic.loadUi('files/Address_Dialog.ui', self)
        self.theme = theme
        self.setStyleSheet(f"background-color: {self.theme['bckg']}; color: #ffffff")
        self.IP_box.setStyleSheet(f"background-color: {self.theme['recv']}; color: #ffffff; border-radius: 5px")
        self.port_box.setStyleSheet(f"background-color: {self.theme['recv']}; color: #ffffff; border-radius: 5px")
        self.selection.setStyleSheet(f"background-color: {self.theme['light']}; color: #ffffff")

    def accept(self):
        err = check_ip_input(self.IP_box.text(), self.port_box.text())
        if err == 0:
            super().accept()
        if err == 1:
            self.IP_box.setStyleSheet(f"background-color: {self.theme['recv']}; color: #ffffff; border-radius: 5px; border: 1px solid red")
            self.port_box.setStyleSheet(f"background-color: {self.theme['recv']}; color: #ffffff; border-radius: 5px")
        if err == 2:
            self.IP_box.setStyleSheet(f"background-color: {self.theme['recv']}; color: #ffffff; border-radius: 5px")
            self.port_box.setStyleSheet(f"background-color: {self.theme['recv']}; color: #ffffff; border-radius: 5px; border: 1px solid red")
        if err == 3:
            self.IP_box.setStyleSheet(f"background-color: {self.theme['recv']}; color: #ffffff; border-radius: 5px; border: 1px solid red")
            self.port_box.setStyleSheet(f"background-color: {self.theme['recv']}; color: #ffffff; border-radius: 5px; border: 1px solid red")

    def returnInfo(self):
        return self.IP_box.text(), int(self.port_box.text())


class ConnThread(Thread):
    def __init__(self, win, queue):
        Thread.__init__(self)
        self.win = win
        self.data_queue = queue
        self.conn_info = None
        self.interrupt = False

    def run(self):
        while not self.conn_info:
            self.conn_info = self.win.getConnInfo()

        BUFFER_SIZE = 2048
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            self.win.setSock(sock)
            while True:
                try:
                    sock.connect(self.conn_info)
                    self.win.eventSig.emit("connected")
                    break
                except ConnectionRefusedError:
                    time.sleep(1)
                    pass

            while True:
                buff = sock.recv(BUFFER_SIZE)
                msg = buff.decode("utf-8")

                if msg:
                    self.data_queue.put(msg)
                    self.win.eventSig.emit("in_msg")


app = QtWidgets.QApplication(sys.argv)
app.setStyle("Fusion")
data_queue = Queue()
window = MainWin(data_queue)
connThread = ConnThread(window, data_queue)
connThread.daemon = True
connThread.start()
sys.exit(app.exec_())
