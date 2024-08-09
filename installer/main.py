import subprocess
from pathenv import add_to_path, remove_from_path # type: ignore
from pathvalidate import sanitize_filepath
from pathlib import Path
from tkinter.filedialog import askdirectory
import elevate # type: ignore
import os
import sys
import tempfile
import shutil
import platform
import zipfile
import requests
from PyQt5 import QtCore, QtGui, QtWidgets, QtSvg
from PyQt5.QtWidgets import QApplication, QMainWindow

is_installed = bool(shutil.which("mathscript"))

def res(str):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, str)

class Ui_MainWindow(object):
    if platform.system() == 'Windows':
        program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
    elif platform.system() == 'Darwin': # macOS
        program_files = '/Applications'
    else:
        program_files = '/usr/local/bin'

    INSTALL_DIR = str(Path(shutil.which("mathscript")).parent) if is_installed else os.path.join(program_files, "MathScript") # type: ignore

    try:
        INSTALLED_VERSION = subprocess.check_output(['mathscript', '--version']).decode('utf-8').strip().removeprefix('MathScript ') if is_installed else None
    except subprocess.CalledProcessError:
        INSTALLED_VERSION = None

    def setupUi(self, MainWindow):
        MainWindow.setFixedSize(561, 362)
        MainWindow.setWindowTitle("MathScript Installer")
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowIcon(QtGui.QIcon(res('logo.svg')))

        self.MainWindow = MainWindow

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.widget_image = QtWidgets.QWidget(self.centralwidget)
        self.widget_image.setGeometry(QtCore.QRect(0, 0, 151, MainWindow.height()))
        self.widget_image.setStyleSheet("background-color: #ee3333;")
        self.widget_image.setObjectName("widget_image")

        self.svgWidjet = QtSvg.QSvgWidget(self.centralwidget)
        self.svgWidjet.setGeometry(QtCore.QRect(0, self.widget_image.height() - self.widget_image.width(), *(self.widget_image.width(),) * 2))
        self.svgWidjet.load(res("logo.svg"))
        self.svgWidjet.setObjectName("svgWidjet")

        self.label_title = QtWidgets.QLabel(self.centralwidget)
        self.label_title.setText("MathScript Installer")
        self.label_title.setGeometry(QtCore.QRect(180, 20, 351, 31))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.label_title.setFont(font)
        self.label_title.setObjectName("label_title")

        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setEnabled(True)
        self.progressBar.setGeometry(QtCore.QRect(180, 100, 361, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.progressBar.setOrientation(QtCore.Qt.Horizontal)
        self.progressBar.setInvertedAppearance(False)
        self.progressBar.setTextDirection(QtWidgets.QProgressBar.TopToBottom)
        self.progressBar.setObjectName("progressBar")

        self.label_instructions = QtWidgets.QLabel(self.centralwidget)
        self.label_instructions.setEnabled(True)
        self.label_instructions.setGeometry(QtCore.QRect(180, 70, 321, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.label_instructions.setFont(font)
        self.label_instructions.setObjectName("label_instructions")

        self.commandLinkButton_install = QtWidgets.QCommandLinkButton(self.centralwidget)
        self.commandLinkButton_install.setText("Install")
        self.commandLinkButton_install.setGeometry(QtCore.QRect(180, 100, 351, 41))
        self.commandLinkButton_install.clicked.connect(self.to_license_page)
        self.commandLinkButton_install.setObjectName("commandLinkButton_install")

        self.commandLinkButton_repair = QtWidgets.QCommandLinkButton(self.centralwidget)
        self.commandLinkButton_repair.setText("Repair")
        self.commandLinkButton_repair.clicked.connect(self.to_repair_page)
        self.commandLinkButton_repair.setGeometry(QtCore.QRect(180, 100, 351, 41))
        self.commandLinkButton_repair.setObjectName("commandLinkButton_repair")

        self.commandLinkButton_uninstall = QtWidgets.QCommandLinkButton(self.centralwidget)
        self.commandLinkButton_uninstall.setText("Uninstall")
        self.commandLinkButton_uninstall.setGeometry(QtCore.QRect(180, 150, 351, 41))
        self.commandLinkButton_uninstall.clicked.connect(self.to_uninstall_page)
        self.commandLinkButton_uninstall.setObjectName("commandLinkButton_uninstall")

        self.commandLinkButton_update = QtWidgets.QCommandLinkButton(self.centralwidget)
        self.commandLinkButton_update.setText("Update")
        self.commandLinkButton_update.setGeometry(QtCore.QRect(180, 200, 351, 41))
        self.commandLinkButton_update.clicked.connect(self.to_install_process_page)
        self.commandLinkButton_update.setObjectName("commandLinkButton_update")

        self.textBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser.setGeometry(QtCore.QRect(170, 100, 371, 221))
        self.textBrowser.setStyleSheet("background-color: transparent;")
        self.textBrowser.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.textBrowser.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.textBrowser.setObjectName("textBrowser")

        self.pushButton_next = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_next.setGeometry(QtCore.QRect(470, 330, 75, 23))
        self.pushButton_next.setObjectName("pushButton_next")

        self.pushButton_back = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_back.setText("Go Back")
        self.pushButton_back.setGeometry(QtCore.QRect(390, 330, 75, 23))
        self.pushButton_back.setObjectName("pushButton_back")

        self.lineEdit_folder_path = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit_folder_path.setGeometry(QtCore.QRect(180, 100, 291, 21))
        self.lineEdit_folder_path.setObjectName("lineEdit_folder_path")

        self.pushButton_select_path = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_select_path.setText("Select")
        self.pushButton_select_path.setGeometry(QtCore.QRect(470, 100, 75, 21))
        self.pushButton_select_path.setObjectName("pushButton_select_path")

        self.pushButton_cancel_all = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_cancel_all.setText("Cancel all")
        self.pushButton_cancel_all.setGeometry(QtCore.QRect(170, 330, 75, 23))
        self.pushButton_cancel_all.clicked.connect(MainWindow.close)
        self.pushButton_cancel_all.setObjectName("pushButton_cancel_all")

        MainWindow.setCentralWidget(self.centralwidget)

        self.to_startup_page()

        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def hide_all(self):
        self.commandLinkButton_install.hide()
        self.commandLinkButton_repair.hide()
        self.commandLinkButton_uninstall.hide()
        self.commandLinkButton_update.hide()
        self.textBrowser.hide()
        self.progressBar.hide()
        self.pushButton_next.hide()
        self.pushButton_select_path.hide()
        self.lineEdit_folder_path.hide()
        self.textBrowser.hide()

        self.progressBar.setValue(0)

        self.pushButton_next.setText("Next")
        self.pushButton_next.setEnabled(True)
        self.pushButton_back.setEnabled(True)
        
        try:
            self.pushButton_next.clicked.disconnect()
            self.pushButton_back.clicked.disconnect()
        except Exception:
            pass

    def to_startup_page(self):
        self.hide_all()
        self.pushButton_back.hide()
        
        self.label_instructions.setText("Choose an option:")
        
        if is_installed:
            self.commandLinkButton_repair.show()
            self.commandLinkButton_uninstall.show()

            resp = requests.get('https://api.github.com/repos/foxypiratecove37350/MathScript/releases/latest')
            latest_version = resp.json()["tag_name"] if resp.status_code == 200 else None
            
            if self.INSTALLED_VERSION and latest_version and \
               self.INSTALLED_VERSION < latest_version:
                self.commandLinkButton_update.show()
        else:
            self.commandLinkButton_install.show()

    def to_license_page(self):
        self.hide_all()
        self.textBrowser.show()
        self.pushButton_next.show()
        self.pushButton_back.show()

        self.pushButton_next.setText("Accept")
        self.pushButton_next.clicked.connect(self.to_install_config_page)
        self.pushButton_back.clicked.connect(self.to_startup_page)

        with open(res("LICENSE"), 'r') as f:
            license_ = f.read()

        self.textBrowser.setText(license_)

        self.label_instructions.setText("License Agreement:")

    def to_install_config_page(self):
        self.hide_all()

        self.lineEdit_folder_path.show()
        self.pushButton_select_path.show()
        self.pushButton_next.show()

        self.pushButton_next.setText("Next")

        self.pushButton_select_path.clicked.connect(lambda: self.lineEdit_folder_path.setText(askdirectory(title='Choose MathScript installation directory')))
        self.pushButton_next.clicked.connect(lambda: self.to_install_process_page(self.lineEdit_folder_path.text()))
        self.pushButton_back.clicked.connect(self.to_license_page)

        self.lineEdit_folder_path.setText(self.INSTALL_DIR)
        self.label_instructions.setText("Installation directory (must be empty):")

        def check():
            path = self.lineEdit_folder_path.text().strip().replace('\\', '/')
            if not os.path.exists(path) and sanitize_filepath(path) == path:
                self.pushButton_next.setEnabled(True)
            elif os.path.exists(path):
                path_obj = Path(path)
                if path_obj.is_dir():
                    if not any(path_obj.iterdir()):
                        self.pushButton_next.setEnabled(True)
            else:
                self.pushButton_next.setEnabled(False)

        check()

        self.lineEdit_folder_path.textEdited.connect(check)

    def to_install_process_page(self, path = None, version='latest'):
        self.hide_all()
        self.progressBar.show()
        self.pushButton_back.hide()

        self.label_instructions.setText("Downloading files...")
        self.pushButton_next.setText("Next")

        file_to_download = f"mathscript_{platform.system().lower().replace('darwin', 'macos')}.zip"
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, file_to_download)

        url = f"https://github.com/foxypiratecove37350/MathScript/releases/{version}/download/{file_to_download}"

        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024
        progress = 0

        with open(temp_file_path, 'wb') as file:
            for data in response.iter_content(block_size):
                file.write(data)
                progress += len(data)
                self.progressBar.setValue(int(progress / total_size * 100))

        self.label_instructions.setText("Unzipping files...")

        install_dir = path or self.INSTALL_DIR
        os.makedirs(install_dir, exist_ok=True)

        with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
            total_files = len(zip_ref.infolist())
            for i, file in enumerate(zip_ref.infolist()):
                zip_ref.extract(file, install_dir)
                self.progressBar.setValue(int((i + 1) / total_files * 100))
        
        os.remove(temp_file_path)

        try:
            self.label_instructions.setText("Adding to PATH")
            self.progressBar.hide()
            elevate.elevate()
            add_to_path(install_dir)
            self.to_installation_finished_page()
        except OSError:
            self.label_instructions.setText("Installation failed. Please run the installer as administrator/allow administrator privileges.")
            self.progressBar.hide()
            self.pushButton_back.hide()
            self.pushButton_next.hide()

            os.remove(install_dir)

    def to_installation_finished_page(self):
        self.hide_all()
        self.textBrowser.show()
        self.pushButton_next.show()

        self.textBrowser.setText("You can now enjoy MathScript using the `mathscript` command in a command prompt.")
        self.label_instructions.setText("Installation finished.")

        self.pushButton_cancel_all.hide()
        self.pushButton_back.hide()

        self.pushButton_next.setText("Quit")
        self.pushButton_next.clicked.connect(self.MainWindow.close)
    
    def to_uninstall_page(self):
        self.hide_all()
        self.pushButton_back.show()
        self.pushButton_next.show()

        self.label_instructions.setText("Are you sure you want to uninstall MathScript?")

        def uninstall():
            self.label_instructions.setText("Uninstallation in progress...")
            self.progressBar.show()

            install_dir = self.INSTALL_DIR
            if os.path.exists(install_dir):
                total_files = len(list(Path(install_dir).rglob('*')))
                progress = 0

                def delete_directory(path):
                    for item in Path(path).iterdir():
                        if item.is_dir():
                            delete_directory(item)
                        else:
                            item.unlink()
                        nonlocal progress
                        progress += 1
                        self.progressBar.setValue(int(progress / total_files * 100))
                    Path(path).rmdir()

                try:
                    delete_directory(install_dir)
                    self.progressBar.setValue(100)
                    self.progressBar.hide()
                    self.label_instructions.setText("Removing from the PATH...")
                    remove_from_path(install_dir)
                    self.label_instructions.setText("Uninstallation completed.")
                    self.pushButton_back.hide()
                    self.pushButton_next.setText("Quit")
                    self.pushButton_next.clicked.connect(self.MainWindow.close)
                except Exception as e:
                    self.label_instructions.setText(f"Uninstallation failed:")
                    self.textBrowser.show()
                    self.textBrowser.setText(str(e))
                    self.progressBar.hide()
                    self.pushButton_next.setText("Retry")
                    self.pushButton_next.clicked.connect(self.to_uninstall_page)
            else:
                self.label_instructions.setText("Installation directory not found.")
                self.progressBar.hide()
                self.pushButton_back.hide()
                self.pushButton_next.setText("Quit")
                self.pushButton_next.clicked.connect(self.MainWindow.close)
            
        self.pushButton_next.setText("Uninstall")
        self.pushButton_next.clicked.connect(uninstall)
        self.pushButton_back.clicked.connect(self.to_startup_page)

    def to_repair_page(self):
        self.hide_all()
        self.pushButton_back.show()
        self.pushButton_next.show()

        self.label_instructions.setText("Are you sure you want to repair MathScript?")
            
        self.pushButton_next.setText("Repair")
        self.pushButton_next.clicked.connect(lambda: [remove_from_path(self.INSTALL_DIR), self.to_install_process_page(version=self.INSTALLED_VERSION)])
        self.pushButton_back.clicked.connect(self.to_startup_page)

app = QApplication([])
window = QMainWindow()
ui = Ui_MainWindow()
ui.setupUi(window)
window.show()
app.exec_()