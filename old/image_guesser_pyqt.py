import logging
import math
import sys
import uuid
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget,QLabel,QFrame,QLineEdit,QMessageBox,QPushButton,QVBoxLayout,QFileDialog
from PyQt5 import QtCore, QtGui

from ITService import ITService
logging.basicConfig(level=logging.INFO)

class MouseTrackingApp(QMainWindow):

    WINDOW_DISPLAY_SIZE = 950
    IMG_DISPLAY_SIZE = 800

    def __init__(self):
        super().__init__()
        self.service = ITService()

        self.setWindowTitle("GUESS  THE IMAGE")
        self.setGeometry(0, 0, self.WINDOW_DISPLAY_SIZE, self.WINDOW_DISPLAY_SIZE)
        self.frameFiles = QFrame(self)
        self.boxLayout = QVBoxLayout()
        self.numImgLabel = QLabel()
        self.refreshNumImgs()
        self.numImgLabel.setStyleSheet("padding-left :230px; font-size:40px; ")
        self.uploadButton = QPushButton("UPLOAD FILES")
        self.uploadButton.setStyleSheet("padding :15px; margin:200px;background-color:rgb(0,0,100);color:rgb(240,240,240)")
        self.boxLayout.addWidget(self.uploadButton)
        self.uploadButton.clicked.connect(self.uploadFiles)
        self.boxLayout.addWidget(self.numImgLabel)
        self.playBtn = QPushButton("PLAY")
        self.playBtn.setStyleSheet("padding :15px; margin:200px;background-color:rgb(0,0,100);color:rgb(240,240,240)")
        self.boxLayout.addWidget(self.playBtn)
        self.playBtn.clicked.connect(self.playBtnPress)
        self.mainwidget = QWidget()
        self.mainwidget.setLayout(self.boxLayout)
        self.setCentralWidget(self.mainwidget)

        if (self.numImgs > 0):
            self.createImgFrame()

    def refreshNumImgs(self):
        self.numImgs = self.service.getNumOfImages()
        self.numImgLabel.setText("Num of saved Imgs: " + str(self.numImgs))
            
        
    def createImgFrame(self):
        self.frameImg = QFrame(self)
        self.frameImg.setGeometry(0, 0, self.WINDOW_DISPLAY_SIZE, self.WINDOW_DISPLAY_SIZE)
        self.frameImg.hide()
        
        self.photo = QLabel(self.frameImg)
        self.photo.setGeometry(QtCore.QRect(0, 0, self.IMG_DISPLAY_SIZE, self.IMG_DISPLAY_SIZE))
        self.photo.setScaledContents(False)
        self.guessEntry = QLineEdit(self.frameImg)
        self.guessEntry.setPlaceholderText("Enter your guess") 
        self.guessEntry.move(0, self.IMG_DISPLAY_SIZE + 10)
        self.guessEntry.resize(400,50)
        self.guessEntry.returnPressed.connect(self.enterGuess)
        self.quitBtn = QPushButton(self.frameImg)
        self.quitBtn.setText("QUIT")
        self.quitBtn.resize(400,50)
        self.quitBtn.setStyleSheet("font-size:20px; ")
        self.quitBtn.move(500, self.IMG_DISPLAY_SIZE + 10)
        self.quitBtn.clicked.connect(self.quitBtnPress)
        self.loadImgRes = self.service.loadImg(self.service.randomDoc())
        self.renderImg()
        
    def playBtnPress(self):
       self.mainwidget.hide()
       self.frameImg.show()  
       self.setCentralWidget(self.frameImg) 

    def quitBtnPress(self):
       print(self.loadImgRes['label'])
       msg = QMessageBox()
       msg.setIcon(QMessageBox.Information)
       msg.setText(self.loadImgRes['label'])
       retval = msg.exec_()  

    def enterGuess(self):
        if (self.guessEntry.text().lower() == self.loadImgRes['label']):
            lenRects, lenBlackRects = self.service.countShownRects(self.loadImgRes['rects'])
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("GUESSED IT with squares shown: " + str(lenRects - lenBlackRects) + " of " + str(lenRects))
            retval = msg.exec_()
        self.guessEntry.setText('')    

    def uploadFiles (self):
        filePathTuple = QFileDialog.getOpenFileName(self, 'Open File', '.')
        if (filePathTuple[0] != ''):
            self.service.uploadImgFiles(filePathTuple[0])
            self.refreshNumImgs()
            self.createImgFrame()
         
        
    def renderImg(self):
        myuuid = uuid.uuid4()
        self.loadImgRes["img"].save("temp.jpg")
        self.photo.setPixmap(QtGui.QPixmap("temp.jpg"))
        self.photo.setScaledContents(True)
        self.photo.update()

    def mousePressEvent(self, event):

        if (event.pos().x() > self.IMG_DISPLAY_SIZE) or (event.pos().y() > self.IMG_DISPLAY_SIZE):
            return
        if not(self.frameImg.isVisible()):
            return
        
        sX = math.floor((event.pos().x()*self.loadImgRes['img_size'])/self.IMG_DISPLAY_SIZE)
        sY = math.floor((event.pos().y()*self.loadImgRes['img_size'])/self.IMG_DISPLAY_SIZE)
        self.service.checkClickOnImg(self.loadImgRes,[sX,sY])
        self.renderImg()
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MouseTrackingApp()
    window.show()
    sys.exit(app.exec_())

