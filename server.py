from PyQt5 import QtCore, QtWidgets, QtGui, uic
import sys
import socket
from threading import Thread


class MainWin(QtWidgets.QMainWindow):
    valueChanged = QtCore.pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.theme = {"sent": "#665b49",
                      "recv": "#282e3a",
                      "bckg": "#1e2126"}

        self.conn_info = None
        self.net_sock = None
        self.in_buffer = []
        self.valueChanged.connect(self.update_recv)
        self.initUi()

    def initUi(self):
        uic.loadUi('files/server.ui', self)  # Load the .ui file
        # self.setFixedSize(self.frameGeometry().size())
        self.actionExit.setShortcut("Ctrl+Q")
        self.actionExit.setStatusTip('Exit The App')
        self.actionExit.triggered.connect(self.close_application)

        # Temp api access inits
        if 1 == 0:
            self.enc_btn = QtWidgets.QPushButton()
            self.in_txt = QtWidgets.QTextEdit()
            self.vert_list = QtWidgets.QVBoxLayout()
            self.scroll = QtWidgets.QScrollArea()
            self.scroll_content = QtWidgets.QWidget()

        self.enc_btn.setEnabled(False)
        self.in_txt.setEnabled(False)
        self.enc_btn.clicked.connect(self.send)
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_content)
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_layout.setAlignment(QtCore.Qt.AlignTop)
        self.installEventFilter(self)
        # self.status.addStretch()
        # lbl = QtWidgets.QLabel(f"Listening at {self.net_sock.getsockname()[0]} on Port {self.net_sock.getsockname()[1]}...")
        # lbl.setFont(QtGui.QFont("Noto Sans", 11, QtGui.QFont.Bold))
        # self.status.addWidget(lbl)
        # self.status.addStretch()

        self.setStyleSheet(f"background-color: {self.theme['recv']}; color: #ffffff")
        self.menubar.setStyleSheet(f"background-color: {self.theme['recv']}; color: #ffffff")
        self.in_txt.setStyleSheet(f"border-radius: 10px; background-color: #4b566b; color: #ffffff")
        self.enc_btn.setStyleSheet(f"background-color: {self.theme['recv']}; color: #ffffff")
        self.scroll_content.setStyleSheet(f"background-color: {self.theme['bckg']}; color: #ffffff")
        self.show()  # Show the GUI

    def getConnInfo(self):
        return self.conn_info

    def setSock(self, sock):
        self.net_sock = sock
        self.enc_btn.setEnabled(True)
        self.in_txt.setEnabled(True)

    def update_in_buffer(self, msg):
        if msg:
            self.in_buffer.append(msg)

        self.valueChanged.emit(None)

    def eventFilter(self, obj, event):
        focused_widget = QtWidgets.QApplication.focusWidget()
        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if event.type() == QtCore.QEvent.KeyRelease and focused_widget in [self.in_txt, self.enc_btn] \
                and event.key() == QtCore.Qt.Key_Return and modifiers != QtCore.Qt.ShiftModifier:
            self.enc_btn.click()
            return True

        return super().eventFilter(obj, event)

    def send(self):
        msg = self.in_txt.toPlainText().strip('\n')
        self.net_sock.send(msg.encode("utf-8"))
        lbl = QtWidgets.QLabel(msg)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        lbl.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
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
        while len(self.in_buffer):
            msg = self.in_buffer.pop(0)
            lbl = QtWidgets.QLabel(msg.strip('\n'))
            lbl.setWordWrap(True)
            lbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            lbl.setFont(QtGui.QFont("Arial", 11, QtGui.QFont.Bold))
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

    def close_application(self):
        choice = QtWidgets.QMessageBox.question(self, 'Exit',
                                                "Close the application?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            sys.exit()
        else:
            pass


class ServerThread(Thread):
    def __init__(self, win: MainWin):
        Thread.__init__(self)
        self.win = win

    def run(self):
        # while self.win.getConnInfo():
        #     pass

        shost = "127.0.0.1"
        sport = 9092
        BUFFER_SIZE = 2048
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((shost, sport))
        sock.listen(1)

        conn, _ = sock.accept()
        self.win.setSock(conn)

        try:
            while True:
                buff = conn.recv(BUFFER_SIZE)
                msg = buff.decode("utf-8")
                self.win.update_in_buffer(msg)
        except Exception as e:
            sock.close()
            print(e)


app = QtWidgets.QApplication(sys.argv)
app.setStyle("Fusion")
window = MainWin() 
serverThread = ServerThread(window)
serverThread.daemon = True
serverThread.start()
sys.exit(app.exec_())
