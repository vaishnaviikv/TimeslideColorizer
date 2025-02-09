#     __                                    ___            __
#    /\ \__  __                            /\_ \    __    /\ \
#    \ \ ,_\/\_\    ___ ___      __    ____\//\ \  /\_\   \_\ \     __
#     \ \ \/\/\ \ /' __` __`\  /'__`\ /',__\ \ \ \ \/\ \  /'_` \  /'__`\
#      \ \ \_\ \ \/\ \/\ \/\ \/\  __//\__, `\ \_\ \_\ \ \/\ \L\ \/\  __/
#       \ \__\\ \_\ \_\ \_\ \_\ \____\/\____/ /\____\\ \_\ \___,_\ \____\
#        \/__/ \/_/\/_/\/_/\/_/\/____/\/___/  \/____/ \/_/\/__,_ /\/____/
#
#           a super-simple gui to slide old photographs into TODAY
#


# PySide6 requirements
#from tkinter import image_types
from PySide6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PySide6.QtWidgets import QGroupBox, QPushButton, QHBoxLayout, QLineEdit
from PySide6.QtWidgets import QCheckBox, QComboBox, QSlider, QFileDialog
from PySide6.QtWidgets import QSizePolicy, QMenuBar, QMainWindow, QMenu, QTextBrowser
from PySide6.QtGui     import QPixmap, QIcon, QAction, QTextCursor
from PySide6.QtCore    import Qt, QCoreApplication#, pyqtSignal
from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


# required for pyinstaller: pytorch
import os
os.environ["PYTORCH_JIT"] = "0"

# set up delodify
from deoldify import device
from deoldify.device_id import DeviceId
device.set(device = DeviceId.GPU0)
from deoldify.visualize import * # this line causes failure with pyinstaller
torch.backends.cudnn.benchmark = True
import torchvision
# from fastai.learner import Learner
# from fastai.vision.data import ImageDataLoaders

# set up image enhance
#import cv2
#from cv2 import dnn_superres

# other
import sys
#import threading
#import tensorflow as tf
#from cgitb import text
#import shutil
from PIL import Image
import urllib.request
import validators
import requests
#import urllib.request
from io import BytesIO
import tempfile
#import numpy as np
#import time

# set working directory
# (used for development vs bundled paths)
try:
   wd = sys._MEIPASS
except AttributeError:
   wd = os.path.dirname(os.path.realpath(__file__))
os.chdir(wd)
model_dir = f"{wd}/models"

# load pretrained torch models
os.environ["TORCH_HOME"] = model_dir

# canvas
init_canv_width  = 640
init_canv_height = 440
init_win_width   = 600
init_win_height  = 738

class timeslideApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.resize(init_win_width, init_win_height)

        # image canvas
        self.img_lbl = QLabel()
        self.img_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.img_lbl.setMinimumSize(init_canv_width, init_canv_height)
        img_pth = f'{wd}/imgs/dustbowl.jpg'
        self.showImage(img_pth)

        # frame - status
        frame_status = QGroupBox(self)
        frame_status.setTitle("Status")
        layout_status = QVBoxLayout()
        self.lbl_status = QLabel("")
        frame_status.setLayout(layout_status)
        layout_status.addWidget(self.lbl_status)
        self.setStatus("Load a photo to start.")

        # load photo
        frame_loadstep = QGroupBox(self)
        frame_loadstep.setTitle("Load Photo")
        layout_loadstep = QHBoxLayout()
        lbl_loadstep_or = QLabel("   or      ")
        frame_loadstep.setLayout(layout_loadstep)
        btn_loadlocal = QPushButton("Load Local Photo")
        btn_loadlocal.clicked.connect(self.loadLocal)
        self.text_loadstep_url = QLineEdit()
        btn_load_url = QPushButton("Load URL")
        btn_load_url.clicked.connect(self.loadURL)
        layout_loadstep.addWidget(btn_loadlocal)
        layout_loadstep.addWidget(lbl_loadstep_or)
        layout_loadstep.addWidget(self.text_loadstep_url, 1)
        self.text_loadstep_url.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        layout_loadstep.addWidget(btn_load_url)

        # colorize
        frame_stepcolor = QGroupBox(self)
        frame_stepcolor.setTitle("Colorize")
        layout_stepcolor = QHBoxLayout()
        self.cbox_stepcolor = QCheckBox("Colorize")
        self.cbox_stepcolor.setChecked(1)
        self.cbox_stepcolor.setToolTip("Colorize the photo using the deolidify project, "
            "using their pretrained model weights.")
        self.ddown_stepcolor = QComboBox()
        self.ddown_stepcolor.addItems(["Stable", "Artistic"])
        self.ddown_stepcolor.setToolTip("Artistic: More colorful.\n"
            "Stable: Not as colorful, but fewer glitches.\n"
            "According to deoldify, Stable should be used for landscapes "
            "and portraits; Artistic otherwise.")
        self.sldr_stepcolor = QSlider(Qt.Orientation.Horizontal)
        min_rndr_fctr = 7
        max_rndr_fctr = 45
        self.sldr_stepcolor.setMinimum(min_rndr_fctr)
        self.sldr_stepcolor.setMaximum(max_rndr_fctr)
        self.sldr_stepcolor.setToolTip("According to De-oldify, older images tend to "
            "benefit from a lower render factor (which is faster). Newer images tend to "
            "benefit from a higher render factor.")
        frame_stepcolor.setLayout(layout_stepcolor)
        layout_stepcolor.addWidget(self.cbox_stepcolor)
        layout_stepcolor.addWidget(QLabel("     Model:"))
        layout_stepcolor.addWidget(self.ddown_stepcolor)
        layout_stepcolor.addWidget(QLabel("    Render Factor:"))
        layout_stepcolor.addWidget(self.sldr_stepcolor, 1)
        self.renderLabel = QLabel("7")
        layout_stepcolor.addWidget(self.renderLabel)
        self.sldr_stepcolor.valueChanged.connect(self.updateRenderLabel)

        # enhance
        #frame_stepenhance = QGroupBox(self)
        #frame_stepenhance.setTitle("Enhance (Upscale)")
        #layout_stepenhance = QHBoxLayout()
        #cbox_stepenhance = QCheckBox("Enhance")
        #ddown_stepenhance = QComboBox()
        #ddown_stepenhance.addItems(["EDSR", "ESPCN", "FSRCNN", "LapSRN"])
        #frame_stepenhance.setLayout(layout_stepenhance)
        #layout_stepenhance.addWidget(cbox_stepenhance)
        #layout_stepenhance.addWidget(QLabel("    Model:"))
        #layout_stepenhance.addWidget(ddown_stepenhance)
        #layout_stepenhance.addWidget(QLabel("          Multiplier:"))
        #sldr_stepenhance = QSlider(Qt.Orientation.Horizontal)
        #value_list_lo = [2, 3, 4]
        #value_list_hi = [2, 4, 8]
        #layout_stepenhance.addWidget(sldr_stepenhance, 1)
        #self.multLabel = QLabel(str(value_list_lo[0]))
        #layout_stepenhance.addWidget(self.multLabel)
        #sldr_stepenhance.valueChanged.connect(self.updateMultLabel)

        # finalize
        frame_stepslide = QGroupBox(self)
        frame_stepslide.setTitle("Finalize")
        layout_stepslide = QHBoxLayout()
        btn_slidetime = QPushButton("Slide Time!")
        btn_slidetime.clicked.connect(self.slideTime)
        btn_savenewphoto = QPushButton("Save New Photo")
        btn_savenewphoto.clicked.connect(self.saveImage)
        frame_stepslide.setLayout(layout_stepslide)
        layout_stepslide.addWidget(btn_slidetime, 1)
        layout_stepslide.addWidget(btn_savenewphoto)

        # overall layout
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.central.vbox = QVBoxLayout()
        self.central.vbox.addWidget(self.img_lbl)#alignment=Qt.AlignmentFlag.AlignCenter)
        self.central.vbox.addWidget(frame_status,    stretch=0)
        self.central.vbox.addWidget(frame_loadstep,  stretch=0)
        self.central.vbox.addWidget(frame_stepcolor, stretch=0)
        #self.central.vbox.addWidget(frame_stepenhance, stretch=0)
        self.central.vbox.addWidget(frame_stepslide, stretch=0)
        self.central.setLayout(self.central.vbox)

        # actions
        exitAct  = QAction("Exit TimeSlide", self)
        exitAct.triggered.connect(QCoreApplication.quit)
        loadAct  = QAction("Load Local Photo...", self)
        loadAct.triggered.connect(self.loadLocal)
        saveAct  = QAction("Save New Photo As...", self)
        saveAct.triggered.connect(self.saveImage)
        licAct   = QAction("License", self)
        licAct.triggered.connect(self.showLicense)
        abtAct   = QAction("About", self)
        abtAct.triggered.connect(self.showAbout)

        # menu bar
        menuBar = self.menuBar()
        menuBar.setNativeMenuBar(False)
        fileMenu = menuBar.addMenu("File")
        fileMenu.addAction(loadAct)
        fileMenu.addAction(saveAct)
        fileMenu.addAction(exitAct)
        helpMenu = menuBar.addMenu("Help")
        helpMenu.addAction(licAct)
        helpMenu.addAction(abtAct)

        self.setWindowTitle('TimeSlide v0.5.1')
        self.show();
        self.centerWindow()

    def updateRenderLabel(self, value):
        self.renderLabel.setText(str(value))
    def updateMultLabel(self, value):
        self.multLabel.setText(str(value))

    def resizeEvent(self, event):
        new_width = self.img_lbl.size().width()
        new_height = self.img_lbl.size().height()
        self.img = self.pix_map.scaled(
            new_width,
            new_height,
            Qt.AspectRatioMode.KeepAspectRatio,  # Ensure aspect ratio is maintained
            Qt.TransformationMode.FastTransformation  # Use fast transformation mode
        )
        self.img_lbl.setPixmap(self.img)
        return super().resizeEvent(event)

    def centerWindow(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def loadLocal(self):
        """
        Load local file
        """
        filepath = QFileDialog.getOpenFileName(self, 'Load photo', wd)
        if filepath[0]:
            self.setStatus(f"Opened {filepath[0]}")
            self.showImage(filepath[0])

    def loadURL(self):
        """
        Load URL
        """
        url = self.text_loadstep_url.text()
        if not validators.url(url):
            self.setStatus("Invalid URL")
        else:
            self.showImage(url)

    def setStatus(self, text):
        """
        Set Status Text
        """
        self.lbl_status.setText(text)
        self.lbl_status.repaint()
        QApplication.processEvents()

    def showImage(self, img_pth):
        """
        Show the given image
        """

        # set globally
        self.img_pth = img_pth

        # load the pixel map
        if not validators.url(img_pth): # local path
            self.pix_map = QPixmap(img_pth)
            self.is_url = False
        else:                           # url
            img_data = urllib.request.urlopen(img_pth).read()
            self.pix_map = QPixmap()
            self.pix_map.loadFromData(img_data)
            self.is_url = True
        
    def setCanvasProperties(self):
        new_width = self.img_lbl.size().width()
        new_height = self.img_lbl.size().height()
        self.img = self.pix_map.scaled(
            new_width,
            new_height,
            Qt.AspectRatioMode.KeepAspectRatio,  # Ensure aspect ratio is maintained
            Qt.TransformationMode.SmoothTransformation  # Use smooth transformation mode for better quality
        )
        self.img_lbl.setPixmap(self.img)
        self.img_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)  # Center align the image label
        
        # open the image
        if self.is_url:
            self.setStatus("Downloading...")
            response = requests.get(img_pth)
            self.img_base = Image.open(BytesIO(response.content))
            tmp = tempfile.NamedTemporaryFile()
            self.img_base.save(tmp.name+".png")
            self.img_pth = (tmp.name+".png")
            self.setStatus(f"Downloaded image.")
        else:
            self.img_base = Image.open(img_pth)
        self.update()

    def slideTime(self):

        # colorize
        if self.cbox_stepcolor.isChecked():

            # get settings
            model_i   = self.ddown_stepcolor.currentIndex()
            model     = self.ddown_stepcolor.currentText()
            artistic  = False if model_i == 0 else True
            rndr_fctr = self.sldr_stepcolor.value()
            
            # set status
            self.setStatus(f"Colorizing ({model} {rndr_fctr}). Please wait...")

            # perform colorization
            colorizer = get_image_colorizer(artistic=artistic)
            self.result_path = colorizer.plot_transformed_image(path=self.img_pth,
                render_factor=rndr_fctr, compare=False, watermarked=False)
            self.showImage(str(self.result_path.absolute()))

        self.setStatus("Time slide complete.")

    def saveImage(self):
        """
        Save the timeslid image
        """
        save_pth = QFileDialog.getSaveFileName(self, 'Save File')
        if save_pth[0]:
            self.img_base.save(save_pth[0])
            self.setStatus('File saved.')
    
    def showLicense(self):
        """
        Show the License
        """
        self.licWin = licenseWindow()

    def showAbout(self):
        """
        Show the About
        """
        self.abtWin = aboutWindow()

class licenseWindow(QTextBrowser):
    """
    License Window
    """
    def __init__(self):
        super().__init__()

        # read license text and add
        f = open("LICENSE")
        licText = f.read()
        f.close()
        self.insertPlainText(licText)
        self.setWindowTitle("GNU General Public License v3")
        self.resize(580,500)
        self.show()

        # scroll to top
        self.verticalScrollBar().setValue(0)

class aboutWindow(QTextBrowser):
    """
    About Window
    """
    def __init__(self):
        super().__init__()

        # read license text and add
        self.append("\n")
        self.append("                    created for fun by bpops")
        self.append("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href=\"https://github.com/bpops/timeslide\">https://github.com/bpops/timeslide</a>")
        self.setWindowTitle("About")
        self.resize(300,100)
        self.setOpenExternalLinks(True)
        self.show()

        # scroll to top
        self.verticalScrollBar().setValue(0)

def main():
    app = QApplication(sys.argv)
    ex = timeslideApp()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()