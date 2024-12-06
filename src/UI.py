import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os

ICON_PATH = None

# 상수
SORT_BY_NAME_ASC    = 0
SORT_BY_NAME_DESC   = 1
SORT_BY_TIME_ASC    = 2
SORT_BY_TIME_DESC   = 3
SORT_BY_SIZE_ASC    = 4
SORT_BY_SIZE_DESC   = 5
SORT_BY_EXT_ASC     = 6
SORT_BY_EXT_DESC    = 7
SORT_BY_VIRUS_ASC   = 8
SORT_BY_VIRUS_DESC  = 9
SORT_BY_EXTCHK_ASC  = 10
SORT_BY_EXTCHK_DESC = 11

class Shortcut(QWidget):
    class ShortcutButton(QtWidgets.QPushButton):
            def __init__(self, text, path, explorer):
                super().__init__(text)
                self.explorer = explorer
                self.path = path
                self.setSizePolicy(self.sizePolicy().Minimum, self.sizePolicy().Fixed)

                self.clicked.connect(self.action)

            def action(self):
                self.explorer.changeDirectory(self.path)
        
    def __init__(self, explorer):
        super().__init__()
        self.explorer = explorer
        self.layout = QHBoxLayout()
        self.layout.setAlignment(Qt.AlignLeft)

        # 파일탐색조
        titleLabel = QLabel("파일탐색조     ")
        titleLabel.setFont(QFont("Malgun Gothic", 10, QFont.Bold))
        self.layout.addWidget(titleLabel)

        # 바로가기 모음
        homePath = os.path.expanduser("~")
        desktopPath = os.path.join(homePath, "Desktop")
        downloadsPath = os.path.join(homePath, "Downloads")
        documentsPath = os.path.join(homePath, "Documents")
        picturesPath = os.path.join(homePath, "Pictures")
        videosPath = os.path.join(homePath, "Videos")
        
        homeBtn = self.ShortcutButton('홈', homePath, self.explorer)
        self.layout.addWidget(homeBtn)
        desktopBtn = self.ShortcutButton('바탕화면', desktopPath, self.explorer)
        self.layout.addWidget(desktopBtn)
        downloadsBtn = self.ShortcutButton('다운로드', downloadsPath, self.explorer)
        self.layout.addWidget(downloadsBtn)
        documentsBtn = self.ShortcutButton('문서', documentsPath, self.explorer)
        self.layout.addWidget(documentsBtn)
        picturesBtn = self.ShortcutButton('사진', picturesPath, self.explorer)
        self.layout.addWidget(picturesBtn)
        videosBtn = self.ShortcutButton('동영상', videosPath, self.explorer)
        self.layout.addWidget(videosBtn)
        
        self.setLayout(self.layout)
    
class ToolBar(QToolBar):
    def __init__(self, explorer):
        super().__init__()
        self.explorer = explorer
        
        changeToPrevDirectory = QAction('⭠', self)
        changeToPrevDirectory.triggered.connect(self.changeToPrevDirectory)
        self.addAction(changeToPrevDirectory)

        changeToNextDirectory = QAction('⭢', self)
        changeToNextDirectory.triggered.connect(self.changeToNextDirectory)
        self.addAction(changeToNextDirectory)

        changeToParentDirectory = QAction('⭡', self)
        changeToParentDirectory.triggered.connect(self.changeToParentDirectory)
        self.addAction(changeToParentDirectory)

        refresh = QAction('↺', self)
        refresh.triggered.connect(self.refresh)
        self.addAction(refresh)
    
    def changeToPrevDirectory(self):
        self.explorer.changeToPrevDirectory()
    
    def changeToNextDirectory(self):
        self.explorer.changeToNextDirectory()
    
    def changeToParentDirectory(self):
        self.explorer.changeToParentDirectory()

    def refresh(self):
        self.explorer.listDirectory()


class ExplorerWidget(QWidget):
    def __init__(self, explorer):
        super().__init__()
        self.explorer = explorer


class TabWidget(QtWidgets.QTabWidget):
    moveAreaClicked = QtCore.pyqtSignal()
    tabClicked = QtCore.pyqtSignal()
    close = QtCore.pyqtSignal()
    doubleClicked = QtCore.pyqtSignal()
    iconClicked = QtCore.pyqtSignal()
    minimize = QtCore.pyqtSignal()
    maximize = QtCore.pyqtSignal()

    class Button(QtWidgets.QToolButton):
        def __init__(self, text: str, hoverColor: str, backgroundColor: str, icon: QIcon) -> None:
            super().__init__()
            style = 'QToolButton:hover {{ background-color: {}; }} '.format(hoverColor)
            style += 'QToolButton:pressed {{ background-color: {}; }} '.format(backgroundColor)
            self.setStyleSheet(style)

            self.setDefaultAction(QtWidgets.QAction(icon, text, self))

            self.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.MinimumExpanding)

    def __init__(self, parent, FileExplorer):
        super().__init__()
        self.parent = parent
        self.FileExplorer = FileExplorer
        self.startResizeMargin = 5
        self.currentIdx = 0
        self.explorers = []
        self.copiedFiles = None     # 복사할 파일 목록
        self.cut = False            # 잘라내기 여부



        self.icon = self.Button('', '', '', QIcon(os.path.join(ICON_PATH, "explorer.ico")))
        self.icon.triggered.connect(self.info)

        self.shadeButtonMenu = QtWidgets.QMenu()
        self.shadeButton = self.Button('Minimize', '#dddddd', '#dddddd', QIcon(QApplication.style().standardPixmap(QtWidgets.QStyle.SP_TitleBarUnshadeButton)))
        self.shadeButton.setPopupMode(self.Button.InstantPopup)
        self.shadeButton.setMenu(self.shadeButtonMenu)
        self.shadeButton.setStyleSheet( self.shadeButton.styleSheet() + 'QToolButton::menu-indicator { image: none; }' )
        
        self.minimizeButton = self.Button('Minimize', '#dddddd', '#dddddd', QIcon(QApplication.style().standardPixmap(QtWidgets.QStyle.SP_TitleBarMinButton)))
        self.minimizeButton.triggered.connect(self.minimize)
        
        self.maximizeButton = self.Button('Maximize', '#dddddd', '#dddddd', QIcon(QApplication.style().standardPixmap(QtWidgets.QStyle.SP_TitleBarMaxButton)))
        self.maximizeButton.triggered.connect(self.maximize)
        
        self.closeButton = self.Button('Close', '#dd0000', '#dd0000', QIcon(QApplication.style().standardPixmap(QtWidgets.QStyle.SP_TitleBarCloseButton)))
        self.closeButton.triggered.connect(self.close)

        spacer = QtWidgets.QLabel()
        spacer.setMinimumWidth(20)
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)

        rightButtons = QtWidgets.QWidget()
        rightButtons.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.MinimumExpanding)
        rightButtons.setLayout(QtWidgets.QHBoxLayout())
        rightButtons.layout().setSpacing(0)
        rightButtons.layout().setContentsMargins(0, 0, 0, 0)
        rightButtons.layout().addWidget(spacer)
        # rightButtons.layout().addWidget(self.shadeButton)
        rightButtons.layout().addWidget(self.minimizeButton)
        rightButtons.layout().addWidget(self.maximizeButton)
        rightButtons.layout().addWidget(self.closeButton)

        self.setCornerWidget(self.icon, QtCore.Qt.TopLeftCorner)
        self.setCornerWidget(rightButtons, QtCore.Qt.TopRightCorner)
        self.setStyleSheet('''
            QTabWidget::pane { border: none; background-color: #fff; } 
            QTabBar::tab { border: 1px solid; 
                           border-color: #ccc ; 
                           margin: 5px 0px 0px 0px; 
                           padding: 0px 10px 0px 10px; 
                           height: 25px; 
                           background-color: #aaa; 
                           color: #000; 
                           } 
            QTabBar::tab:selected { 
                           border: none; 
                           margin: 0px 0px 0px 0px; 
                           padding: 0px 10px 0px 10px; 
                           height: 32px; 
                           background-color: #fff; 
                           color: #000; 
                           } 
            QToolButton { height: 32px; width: 32px; border: none; }
        ''')
        self.setMovable(True)
        
        super().addTab(QtWidgets.QLabel(), '+')
        self.addButton = self.widget(0)

        self.currentChanged.connect(self.tabChanged)
        self.tabBar().tabBarClicked.connect(self.onTabBarClicked)
        self.tabBar().tabMoved.connect(self.onTabMoved)

        # addButton에 close 버튼 없애기
        QTimer.singleShot(0, lambda : self.tabBar().setTabButton(self.count() - 1, QTabBar.RightSide, None))

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab) 

        self.isMaximized = False
        self.setMouseTrackingForAllChild(self)

    def setMouseTrackingForAllChild(self, widget):
        widget.setMouseTracking(True)
        for child in widget.findChildren(QWidget):
            self.setMouseTrackingForAllChild(child)

    def info(self):
        pass

    def minimize(self):
        self.parent.showMinimized()

    def maximize(self):
        if self.isMaximized:
            self.parent.setWindowState(Qt.WindowNoState)
        if not self.isMaximized:
            self.parent.setWindowState(Qt.WindowMaximized)
        self.isMaximized = not self.isMaximized

    def close(self):
        sys.exit()

    def addShadeMenu(self, action: QtWidgets.QAction) -> None:
        self.shadeButtonMenu.addAction(action)

    def addTab(self):
        explorer = self.FileExplorer(os.path.abspath(os.getcwd()), updateCallback=self.parent.updateWindow)
        widget = ExplorerWidget(explorer)
        mainLayout = QVBoxLayout()
        widget.setLayout(mainLayout)
        listViewLayout = QHBoxLayout()

        tableWidget = QTableWidget()
        self.tableWidget = tableWidget
        tableWidget.setColumnCount(6)

        tableWidget.setHorizontalHeaderLabels(['이름', '수정한 날짜', '크기', '확장자', '바이러스', '확장자 검사'])
        tableWidget.horizontalHeader().sectionClicked.connect(self.setSortType)
        tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        tableWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        tableWidget.setShowGrid(False)

        # 기본 정렬
        tableWidget.sortType = SORT_BY_NAME_DESC

        # 더블 클릭으로 실행
        tableWidget.cellDoubleClicked.connect(self.startFile)

        # 선택된 행의 색상 변경
        tableWidget.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #a0a0ff;
                color: white;
            }
        """)

        tableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        tableWidget.customContextMenuRequested.connect(self.parent.showContextMenu)

        # 오른쪽 화면 속성 업데이트
        tableWidget.itemSelectionChanged.connect(self.parent.updateAttributes)

        # 바로가기 버튼 모음
        shortcutLayout = QHBoxLayout()
        shortcut = Shortcut(explorer)
        shortcutLayout.addWidget(shortcut)
        mainLayout.addLayout(shortcutLayout)

        # 현재 경로
        upperLayout = QHBoxLayout()
        cwdWidget = QLineEdit(os.getcwd())
        cwdWidget.setObjectName('cwdWidget')
        upperLayout.addWidget(cwdWidget, 70)

        # 검색 위젯
        searchWidget = QLineEdit()
        searchWidget.setPlaceholderText("검색")
        searchWidget.setObjectName('searchWidget')
        searchWidget.returnPressed.connect(self.searchFile)
        upperLayout.addWidget(searchWidget, 30)
        mainLayout.addLayout(upperLayout)

        # 버튼 모음
        buttonLayout = QHBoxLayout()
        toolbar = ToolBar(explorer)
        buttonLayout.addWidget(toolbar)
        mainLayout.addLayout(buttonLayout)

        # 속성
        listViewLayout.addWidget(tableWidget, 60)
        subLayout = QVBoxLayout()
        
        attributes = QGridLayout()
        
        attributes.setAlignment(Qt.AlignTop)
        attributes.setContentsMargins(20, 20, 20, 20)
        attributes.setSpacing(20)
        attributes.setObjectName("attributesWidget")

        subLayout.addLayout(attributes)
        listViewLayout.addLayout(subLayout, 40)
        mainLayout.addLayout(listViewLayout)

        index = self.count() - 1

        tabText = explorer.getCurrentPath()
        if os.path.basename(tabText):
            tabText = os.path.basename(tabText)

        super().insertTab(index, widget, tabText)
        index = index if index > 0 else 0
        self.setCurrentIndex(index)
        self.currentIdx = index

        explorer.listDirectory()

    def closeTab(self, index):
        self.removeTab(index)

        if index == 0:
            index = 1
        
        if index - 1 == self.count() - 1:
            self.parent.close()

        else:
            self.setCurrentIndex(index - 1)
            self.currentIdx = index - 1

    def setSortType(self, index):
        currentTab = self.currentWidget()
        table = currentTab.findChild(QTableWidget)

        if table.sortType == index*2:
            table.sortType ^= 1
        else:
            table.sortType = index*2

        self.parent.updateWindow(currentTab.explorer.getCurrentFileList())
        
    def startFile(self, row, column):
        currentTab = self.currentWidget()
        explorer = currentTab.explorer
        
        filename = self.tableWidget.item(row, 0).text()
        filepath = os.path.join(os.getcwd(), filename)
        
        if os.path.isdir(filepath):
            explorer.changeDirectory(filepath)
        else:
            explorer.startFile(filepath)

    def searchFile(self):
        currentTab = self.currentWidget()
        searchText = currentTab.findChild(QLineEdit, 'searchWidget').text()
        currentTab.explorer.updateCurrentFileList(currentTab.explorer.searchFile(searchText))
        self.parent.updateWindow(currentTab.explorer.getCurrentFileList())

    def setCurrentIndex(self, index):
        self.currentIdx = index
        return super().setCurrentIndex(index)    
    
    def tabChanged(self, currentIdx):
        if currentIdx > self.count() - 2:
            self.setCurrentIndex(self.currentIdx)
        else:
            currentTab = self.currentWidget()
            os.chdir(currentTab.explorer.getCurrentPath())
            currentTab = self.currentWidget()
            currentTab.explorer.listDirectory()

    def onTabBarClicked(self, index):
        if index > self.count() - 2:
            self.addTab()

    def onTabMoved(self, fromIndex, toIndex):
        index = self.indexOf(self.addButton)
        self.tabBar().moveTab(index, self.count() - 1)

class TitleBar(QWidget):
    height = 70
    def __init__(self, parent, FileExplorer):
        super().__init__()
        self.parent = parent
        
        # layout 생성
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)

        # TabWidget 생성
        self.tabWidget = TabWidget(parent, FileExplorer)
        self.tabWidget.setCurrentIndex(0)
        self.tabWidget.setTabsClosable(True)
        self.tab1 = QWidget()
        self.layout.addWidget(self.tabWidget)

        # 버튼 생성
        self.closeButton = QPushButton(' ')                            
        self.closeButton.clicked.connect(self.close)
        self.closeButton.setStyleSheet("""
            background-color: #DC143C;
            border-radius: 10px;
            height: {};
            width: {};
            margin-right: 3px;
            font-weight: bold;
            color: #000;
            font-family: "Webdings";
            qproperty-text: "r";
        """.format(self.height/1.7,self.height/1.7))

        self.maxButton = QPushButton(' ')
        self.maxButton.clicked.connect(self.maximize)
        self.maxButton.setStyleSheet("""
            background-color: #32CD32;
            border-radius: 10px;
            height: {};
            width: {};
            margin-right: 3px;
            font-weight: bold;
            color: #000;
            font-family: "Webdings";
            qproperty-text: "1";
        """.format(self.height/1.7,self.height/1.7))

        self.hideButton = QPushButton(' ')
        self.hideButton.clicked.connect(self.hide)
        self.hideButton.setStyleSheet("""
            background-color: #FFFF00;
            border-radius: 10px;
            height: {};
            width: {};
            margin-right: 3px;
            font-weight: bold;
            color: #000;
            font-family: "Webdings";
            qproperty-text: "0";
        """.format(self.height/1.7,self.height/1.7))

        # 버튼 목록을 tabWidget에 추가
        self.buttons = QWidget()
        self.buttonsLayout = QHBoxLayout()
        self.buttons.setStyleSheet("""
            border-radius: 20px;
            background-color: red;
        """)
        self.buttonsLayout.addWidget(self.hideButton)
        self.buttonsLayout.addWidget(self.maxButton)
        self.buttonsLayout.addWidget(self.closeButton)
        self.buttons.setLayout(self.buttonsLayout)

        self.setLayout(self.layout)

        self.start = QPoint(0, 0)
        self.isMousePressed = False
        self.isMaximized = False

        self.setMouseTrackingForAllChild(self)

    def setMouseTrackingForAllChild(self, widget):
        widget.setMouseTracking(True)
        for child in widget.findChildren(QWidget):
            self.setMouseTrackingForAllChild(child)

    def resizeEvent(self, QResizeEvent):
        super().resizeEvent(QResizeEvent)

    def mousePressEvent(self, event):
        self.start = self.mapToGlobal(event.pos())
        self.isMousePressed = True
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.pos().y() < 58 and not self.parent.isResizing and self.isMousePressed:
            self.end = self.mapToGlobal(event.pos())
            self.movement = self.end-self.start
            self.parent.move(self.mapToGlobal(self.movement))
            self.start = self.end
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.isMousePressed = False
        super().mouseReleaseEvent(event)

    def close(self):
        sys.exit()

    def maximize(self):
        if self.isMaximized:
            self.parent.setWindowState(Qt.WindowNoState)
        if not self.isMaximized:
            self.parent.setWindowState(Qt.WindowMaximized)
        self.isMaximized = not self.isMaximized

    def hide(self):
        self.parent.showMinimized()

class StatusBar(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.initUI()
        self.showMessage("status")

    def initUI(self):
        self.label = QLabel("Status Bar")
        self.label.setFixedHeight(24)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label.setStyleSheet("""
            background-color: #23272a;
            font-size: 12px;
            padding-left: 5px;
            color: white;
        """)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        self.setMouseTrackingForAllChild(self)

    def showMessage(self, text):
        self.label.setText(text)

    def setMouseTrackingForAllChild(self, widget):
        widget.setMouseTracking(True)
        for child in widget.findChildren(QWidget):
            self.setMouseTrackingForAllChild(child)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

class CustomInputDialog(QDialog):
    def __init__(self, parent=None, title="", label="", default="", placeholder=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 150)
        self.setWindowFlags(Qt.Dialog| Qt.WindowCloseButtonHint)
        self.setWindowIcon(QIcon(os.path.join(ICON_PATH, "explorer.ico")))

        # 폰트 설정
        font = QFont("Arial", 10)

        # 메인 레이아웃
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # 상단 설명 라벨
        self.label = QLabel(label)
        self.label.setFont(font)
        self.label.setAlignment(Qt.AlignLeft)
        self.layout.addWidget(self.label)

        # 입력 필드
        self.lineEdit = QLineEdit(self)
        self.lineEdit.setFont(font)
        self.lineEdit.setText(default)
        self.lineEdit.setPlaceholderText(placeholder)
        self.lineEdit.setStyleSheet("""
            QLineEdit {
                border: 2px solid #5B9BD5;
                border-radius: 8px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #2E75B6;
            }
        """)
        self.layout.addWidget(self.lineEdit)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #C0C0C0;")
        self.layout.addWidget(separator)

        # 버튼 레이아웃
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(15)

        # 확인 버튼
        self.okButton = QPushButton("확인")
        self.okButton.setFont(font)
        self.okButton.setStyleSheet("""
            QPushButton {
                background-color: #5B9BD5;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2E75B6;
            }
            QPushButton:pressed {
                background-color: #1C4E80;
            }
        """)
        self.okButton.clicked.connect(self.accept)

        # 취소 버튼
        self.cancelButton = QPushButton("취소")
        self.cancelButton.setFont(font)
        self.cancelButton.setStyleSheet("""
            QPushButton {
                background-color: #E7E6E6;
                color: #000;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #D4D4D4;
            }
            QPushButton:pressed {
                background-color: #B0B0B0;
            }
        """)
        self.cancelButton.clicked.connect(self.reject)
        self.buttonLayout.addWidget(self.okButton)
        self.buttonLayout.addWidget(self.cancelButton)
        self.layout.addLayout(self.buttonLayout)

    def getText(self):
        if self.exec_() == QDialog.Accepted:
            return self.lineEdit.text(), True
        else:
            return "", False

class CustomMessageBox(QDialog):
    def __init__(self, parent=None, title="", message=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 120)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setWindowIcon(QIcon(os.path.join(ICON_PATH, "explorer.ico")))

        font = QFont("Arial", 10)

        # 메인 레이아웃
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)

        self.messageLabel = QLabel(message)
        self.messageLabel.setFont(font)
        self.messageLabel.setAlignment(Qt.AlignLeft)
        self.messageLabel.setWordWrap(True)
        self.layout.addWidget(self.messageLabel)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #C0C0C0;")
        self.layout.addWidget(separator)

        # 버튼
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(15)

        self.yesButton = QPushButton("예")
        self.yesButton.setFont(font)
        self.yesButton.setStyleSheet("""
            QPushButton {
                background-color: #5B9BD5;
                color: white;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #2E75B6;
            }
            QPushButton:pressed {
                background-color: #1C4E80;
            }
        """)
        self.yesButton.clicked.connect(self.accept)

        self.noButton = QPushButton("아니오")
        self.noButton.setFont(font)
        self.noButton.setStyleSheet("""
            QPushButton {
                background-color: #E7E6E6;
                color: #000;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #D4D4D4;
            }
            QPushButton:pressed {
                background-color: #B0B0B0;
            }
        """)
        self.noButton.clicked.connect(self.reject)

        self.buttonLayout.addWidget(self.yesButton)
        self.buttonLayout.addWidget(self.noButton)
        self.layout.addLayout(self.buttonLayout)

    def showMessage(self):
        return self.exec_() == QDialog.Accepted

class ReadOnlyTableWidgetItem(QTableWidgetItem):
    def __init__(self, text, backgroundColor=None, textColor=None, icon=None):
        super().__init__(text)
        self.setFlags(self.flags() & ~Qt.ItemIsEditable) # edit 불가능하게

        if backgroundColor:
            self.setBackground(backgroundColor)
        if textColor:
            self.setForeground(textColor)
        if icon:
            self.setIcon(icon)

class MainWindow(QWidget):
    def __init__(self, FileExplorer):
        global ICON_PATH
        super().__init__()

        if hasattr(sys, '_MEIPASS'):
            ICON_PATH = os.path.join(sys._MEIPASS, "assets", "icons")
        else:
            ICON_PATH = f'{os.path.dirname(__file__)}\\..\\assets\\icons'

        self.safeIcon = QIcon(os.path.join(ICON_PATH, "safe.ico"))
        self.unsafeIcon = QIcon(os.path.join(ICON_PATH, "unsafe.ico"))

        self.resize(1500, 900)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)        
        self.setWindowTitle('Explorer')
        self.setMouseTracking(True)

        self.titleBar = TitleBar(self, FileExplorer)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.addWidget(self.titleBar)
        self.setLayout(self.layout)

        self.gripSize = 5
        self.isResizing = False
        self.resizeDirection = None

        # 초기 탭 생성
        self.titleBar.tabWidget.addTab()
    
    def updateWindow(self, files):
        tabWidget = self.titleBar.tabWidget
        widget = tabWidget.currentWidget()

        # 탭 이름 변경
        currentPath = widget.explorer.getCurrentPath()
        tabText = currentPath
        if os.path.basename(tabText):
            tabText = os.path.basename(tabText)
        
        tabWidget.setTabText(tabWidget.currentIndex(), tabText)

        # 경로 업데이트
        cwdWidget = widget.findChild(QLineEdit, 'cwdWidget')
        cwdWidget.setText(currentPath)

        # 목록 업데이트
        tableWidget = widget.findChild(QTableWidget)
        tableWidget.setRowCount(len(files))

        # 정렬
        if tableWidget.sortType == SORT_BY_NAME_ASC:
            files.sort(key = lambda x: (x[0] is None, x[0]))
        elif tableWidget.sortType == SORT_BY_NAME_DESC:
            files.sort(key = lambda x: (x[0] is None, x[0]), reverse=True)
        elif tableWidget.sortType == SORT_BY_TIME_ASC:
            files.sort(key = lambda x: (x[1] is None, x[1]))
        elif tableWidget.sortType == SORT_BY_TIME_DESC:
            files.sort(key = lambda x: (x[1] is None, x[1]), reverse=True)
        elif tableWidget.sortType == SORT_BY_SIZE_ASC:
            files.sort(key = lambda x: (x[2] is None, x[2]))
        elif tableWidget.sortType == SORT_BY_SIZE_DESC:
            files.sort(key = lambda x: (x[2] is None, x[2]), reverse=True)
        elif tableWidget.sortType == SORT_BY_EXT_ASC:
            files.sort(key = lambda x: (x[3] is None, x[3]))
        elif tableWidget.sortType == SORT_BY_EXT_DESC:
            files.sort(key = lambda x: (x[3] is None, x[3]), reverse=True)
        elif tableWidget.sortType == SORT_BY_VIRUS_ASC:
            files.sort(key = lambda x: (x[4] is None, x[4]))
        elif tableWidget.sortType == SORT_BY_VIRUS_DESC:
            files.sort(key = lambda x: (x[4] is None, x[4]), reverse=True)
        elif tableWidget.sortType == SORT_BY_EXTCHK_ASC:
            files.sort(key = lambda x: (x[5] is None, x[5]))
        elif tableWidget.sortType == SORT_BY_EXTCHK_DESC:
            files.sort(key = lambda x: (x[5] is None, x[5]), reverse=True)
    
        for row, (filename, mdate, filesize, filetype, isMalicious, badType) in enumerate(files):
            bg = None
            txt = None

            if isMalicious:
                malicious = '바이러스'
                maliciousIcon = self.unsafeIcon
            elif isMalicious == None:
                malicious = ''
                maliciousIcon = None
            elif isMalicious == -1:
                malicious = 'err'
            else:
                malicious = '안전'
                maliciousIcon = self.safeIcon

            if badType == True:
                badFormat = '불일치'
                badFormatIcon = self.unsafeIcon
            elif badType == None:
                badFormat = ''
                badFormatIcon = None
            else:
                badFormat = '안전'
                badFormatIcon = self.safeIcon

            tableWidget.setItem(row, 0, ReadOnlyTableWidgetItem(filename, backgroundColor=bg, textColor=txt))
            tableWidget.setItem(row, 1, ReadOnlyTableWidgetItem(mdate, backgroundColor=bg, textColor=txt))
            tableWidget.setItem(row, 2, ReadOnlyTableWidgetItem(filesize, backgroundColor=bg, textColor=txt))
            tableWidget.setItem(row, 3, ReadOnlyTableWidgetItem(filetype, backgroundColor=bg, textColor=txt))
            tableWidget.setItem(row, 4, ReadOnlyTableWidgetItem(malicious, backgroundColor=bg, textColor=txt, icon=maliciousIcon))
            tableWidget.setItem(row, 5, ReadOnlyTableWidgetItem(badFormat, backgroundColor=bg, textColor=txt, icon=badFormatIcon))
            
    def showContextMenu(self, position):
        tabWidget = self.titleBar.tabWidget
        currentTab = tabWidget.currentWidget()
        explorer = currentTab.explorer
        table = currentTab.findChild(QTableWidget)
        
        # 현재 선택된 아이템 확인
        indexes = table.selectedIndexes()
        if not indexes:
            return
            
        # 선택된 행의 파일명 가져오기
        row = indexes[0].row()
        filename = table.item(row, 0).text()
        filepath = os.path.join(os.getcwd(), filename)
        
        # 메뉴 생성
        menu = QMenu()
        openAction = menu.addAction("열기")
        copyAction = menu.addAction("복사")
        pasteAction = menu.addAction("붙여넣기")
        cutAction = menu.addAction("잘라내기")
        deleteAction = menu.addAction("삭제")
        renameAction = menu.addAction("이름 변경")
        if not os.path.isdir(filepath):
            virusCheckAction = menu.addAction("바이러스 토탈 검사")
        
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ccc;
            }
            QMenu::item {
                padding: 5px 30px 5px 30px;
            }
            QMenu::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background-color: #ccc;
                margin: 4px 0px 4px 0px;
            }
        """)
        
        # 메뉴 표시 / 선택된 항목을 action에 저장
        action = menu.exec_(table.viewport().mapToGlobal(position))
        
        if action is None:
            return
            
        if action == openAction:
            explorer.startFile(filepath)
        
        elif action == copyAction:
            tabWidget.copiedFiles = [filepath]
            tabWidget.cut = False
        
        elif action == pasteAction:
            if tabWidget.copiedFiles:
                # 복사
                explorer.copyFiles(tabWidget.copiedFiles, os.getcwd())

                # 잘라내기
                if tabWidget.cut:
                    explorer.removeFiles(tabWidget.copiedFiles)    
                    tabWidget.copiedFiles.clear()
        
        elif action == cutAction:
            tabWidget.copiedFiles = [filepath]
            tabWidget.cut = True
        
        elif action == deleteAction:
            dialog = CustomMessageBox(self, "확인", f'"{filename}"을(를) 삭제하시겠습니까?')
            reply = dialog.showMessage()
            if reply == True:
                explorer.remove(filename)
                self.updateAttributes()
        
        elif action == renameAction:
            dialog = CustomInputDialog(self, "이름 변경", "새 이름을 입력하세요:", filename, "이름을 입력하세요...")
            newName, ok = dialog.getText()
            if ok and newName:
                explorer.renameFile(filename, newName)
                self.updateAttributes()

        elif action == virusCheckAction:
            explorer.virusCheck(filename)
            explorer.listDirectory()
            self.updateAttributes()


    def updateAttributes(self):
        tabWidget = self.titleBar.tabWidget
        currentTab = tabWidget.currentWidget()
        explorer = currentTab.explorer
        table = currentTab.findChild(QTableWidget)
        layout = currentTab.findChild(QGridLayout, "attributesWidget")

        # 현재 선택된 아이템 확인
        indexes = table.selectedIndexes()
        if not indexes:
            return

        # 선택된 행의 파일명 가져오기
        row = indexes[0].row()
        filename = table.item(row, 0).text()
        fileFormat, filepath, filesize, ctime, mtime, filetype, score, chkDate, url = explorer.getAttribute(filename)
        
        # getAttribute
        attr = []

        # 1. 파일명
        key = QLabel(f"<b>파일명</b>")
        val = QLabel(filename)
        attr.append([key, val])

        # 2. 파일 형식

        # 3. 위치
        filepathLayout = QHBoxLayout()
        filepathLayout.setAlignment(Qt.AlignLeft)
        filepathLayout.setContentsMargins(0, 0, 0, 0)
        
        key = QLabel(f"<b>위치</b>")
        val = QLineEdit()
        val.setPlaceholderText(filepath)
        val.setReadOnly(True)
        attr.append([key, val])

        # 4. 크기
        key = QLabel(f"<b>크기</b>")
        val = QLabel(filesize)
        attr.append([key, val])
        
        # 5. 만든 날짜
        key = QLabel(f"<b>만든 날짜</b>")
        val = QLabel(ctime)
        attr.append([key, val])

        # 6. 수정 날짜
        key = QLabel(f"<b>수정한 날짜</b>")
        val = QLabel(mtime)
        attr.append([key, val])
        
        # 7. 확장자
        key = QLabel(f"<b>확장자</b>")
        val = QLabel(filetype)
        attr.append([key, val])
        
        # 8. 바이러스 토탈
        key = QLabel(f"<b>바이러스 토탈</b>")
        val = QLabel(score)
        attr.append([key, val])

        # 9. 바이러스 토탈 검사일
        key = QLabel(f"<b>바이러스 토탈 검사 날짜</b>")
        val = QLabel(chkDate)
        attr.append([key, val])

        for row, widgets in enumerate(attr):
            for col in range(len(widgets)):
                old = layout.itemAtPosition(row, col)
                if old and old.widget():
                    layout.removeWidget(old.widget())

                if len(widgets) == 1:
                    layout.addWidget(widgets[col], row, col, 10, 2)
                else:
                    layout.addWidget(widgets[col], row, col)

    def mousePressEvent(self, event):
        self.startPosition = event.pos()
        if self.isOnEdge(event.pos()):
            self.isResizing = True
            self.resizeDirection = self.getResizeDirection(event.pos())
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.isResizing:
            self.resizeWindow(event.pos())
        else:
            self.updateCursorShape(event.pos())
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.isResizing = False
        self.resizeDirection = None
        self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

    def isOnEdge(self, pos):
        rect = self.rect()
        return (pos.x() < self.gripSize or
                pos.x() > rect.width() - self.gripSize or
                pos.y() < self.gripSize or
                pos.y() > rect.height() - self.gripSize)

    def getResizeDirection(self, pos: QPoint) -> str:
        rect = self.rect()
        if pos.x() < self.gripSize and pos.y() < self.gripSize:
            return 'top-left'
        elif pos.x() > rect.width() - self.gripSize and pos.y() < self.gripSize:
            return 'top-right'
        elif pos.x() < self.gripSize and pos.y() > rect.height() - self.gripSize:
            return 'bottom-left'
        elif pos.x() > rect.width() - self.gripSize and pos.y() > rect.height() - self.gripSize:
            return 'bottom-right'
        elif pos.x() < self.gripSize:
            return 'left'
        elif pos.x() > rect.width() - self.gripSize:
            return 'right'
        elif pos.y() < self.gripSize:
            return 'top'
        elif pos.y() > rect.height() - self.gripSize:
            return 'bottom'
        else:
            return None

    def resizeWindow(self, pos: QPoint):
        rect = self.geometry()
        dx = pos.x() - self.startPosition.x()
        dy = pos.y() - self.startPosition.y()

        if 'left' in self.resizeDirection:
            width = rect.width() - dx
            if width > self.minimumWidth():
                rect.setLeft(rect.left() + dx)
        if 'right' in self.resizeDirection:
            width = pos.x()
            if width > self.minimumWidth():
                rect.setRight(rect.left() + width)
        if 'top' in self.resizeDirection:
            height = rect.height() - dy
            if height > self.minimumHeight():
                rect.setTop(rect.top() + dy)
        if 'bottom' in self.resizeDirection:
            height = pos.y()
            if height > self.minimumHeight():
                rect.setBottom(rect.top() + height)

        self.setGeometry(rect)

    def updateCursorShape(self, pos):
        rect = self.rect()
        if pos.x() < self.gripSize and pos.y() < self.gripSize:
            self.setCursor(Qt.SizeFDiagCursor)
        elif pos.x() > rect.width() - self.gripSize and pos.y() < self.gripSize:
            self.setCursor(Qt.SizeBDiagCursor)
        elif pos.x() < self.gripSize and pos.y() > rect.height() - self.gripSize:
            self.setCursor(Qt.SizeBDiagCursor)
        elif pos.x() > rect.width() - self.gripSize and pos.y() > rect.height() - self.gripSize:
            self.setCursor(Qt.SizeFDiagCursor)
        elif pos.x() < self.gripSize or pos.x() > rect.width() - self.gripSize:
            self.setCursor(Qt.SizeHorCursor)
        elif pos.y() < self.gripSize or pos.y() > rect.height() - self.gripSize:
            self.setCursor(Qt.SizeVerCursor)
            pass
        else:
            self.setCursor(Qt.ArrowCursor)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())