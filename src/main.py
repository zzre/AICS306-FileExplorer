from UI import *
from FileExplorer import FileExplorer

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow(FileExplorer)
    mw.show()
    sys.exit(app.exec_())
