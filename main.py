import sys
import cv2
import numpy as np
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QOpenGLWidget
from PyQt5.QtCore import QTimer
from OpenGL.GL import *

# Load the UI file
Ui_MainWindow, _ = uic.loadUiType("/Users/iseung-won/AI_inference_video_player/AI_inference_video_player.ui")

class VideoWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super(VideoWidget, self).__init__(parent)
        video_path = "/Users/iseung-won/AI_inference_video_player/test_data/KakaoTalk_Video_2024-06-22-19-57-49.mp4"
        self.cap = cv2.VideoCapture(video_path)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 30 ms
        self.frame = None

    def initializeGL(self):
        glEnable(GL_TEXTURE_2D)

    def paintGL(self):
        if self.frame is not None:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glDrawPixels(self.frame.shape[1], self.frame.shape[0], GL_RGB, GL_UNSIGNED_BYTE, self.frame)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame = np.flip(frame, 0)
            self.update()

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.video_widget = VideoWidget(self.openGLWidget)
        self.setCentralWidget(self.video_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
