import sys
import cv2
import numpy as np
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QOpenGLWidget, QFileDialog
from PyQt5.QtCore import QTimer
from OpenGL.GL import *

# Load the UI file
Ui_MainWindow, _ = uic.loadUiType("AI_inference_video_player.ui")

class VideoWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super(VideoWidget, self).__init__(parent)
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.frame = None
        self.paused = False
        self.video_path = ""
        self.resolution = (640, 480)  # Default resolution

    def set_video_path(self, path):
        self.video_path = path
        self.cap = cv2.VideoCapture(self.video_path)

    def set_resolution(self, resolution):
        self.resolution = resolution

    def play(self):
        if self.cap and self.cap.isOpened():
            self.paused = False
            self.timer.start(30)  # Start or resume playing

    def pause(self):
        self.paused = True
        self.timer.stop()  # Pause the video

    def stop(self):
        self.paused = False
        self.timer.stop()  # Stop the video
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(self.video_path)  # Reset to the start

    def initializeGL(self):
        glEnable(GL_TEXTURE_2D)

    def paintGL(self):
        if self.frame is not None:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glDrawPixels(self.frame.shape[1], self.frame.shape[0], GL_RGB, GL_UNSIGNED_BYTE, self.frame)

    def update_frame(self):
        if not self.paused and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.resize(frame, self.resolution)  # Resize frame
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.frame = np.flip(frame, 0)
                self.update()

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.video_widget = VideoWidget(self.openGLWidget)
        self.init_ui()

    def init_ui(self):
        self.comboBox.addItems(["640x480", "1920x1080"])
        self.pushButton.clicked.connect(self.play_video)
        self.pushButton_2.clicked.connect(self.pause_video)
        self.pushButton_3.clicked.connect(self.stop_video)
        self.pushButton_4.clicked.connect(self.select_video_path)

    def select_video_path(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi)", options=options)
        if file_name:
            self.video_widget.set_video_path(file_name)

    def play_video(self):
        resolution = self.comboBox.currentText()
        if resolution == "640x480":
            self.video_widget.set_resolution((640, 480))
        elif resolution == "1920x1080":
            self.video_widget.set_resolution((1920, 1080))
        self.video_widget.play()

    def pause_video(self):
        self.video_widget.pause()

    def stop_video(self):
        self.video_widget.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
