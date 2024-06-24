import sys
import cv2
import numpy as np
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFileDialog, QMessageBox, QInputDialog, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt, QDateTime
from PyQt5.QtGui import QPixmap, QImage
import datetime

# Load the UI file
Ui_MainWindow, _ = uic.loadUiType("AI_inference_video_player______.ui")

class VideoWidget(QGraphicsView):
    def __init__(self, parent=None):
        super(VideoWidget, self).__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.frame = None
        self.paused = False
        self.video_path = ""
        self.main_window = parent  # Reference to MainWindow parent
        self.fps = 0
        self.width = 0
        self.height = 0
        self.target_width = 0
        self.target_height = 0
        self.last_frame_time = QDateTime.currentMSecsSinceEpoch()
        self.recording = False
        self.out = None

        # Disable scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def set_video_path(self, path):
        self.video_path = path
        self.init_video_capture()

    def set_rtsp_path(self, path):
        self.video_path = path
        self.init_video_capture()

    def init_video_capture(self):
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(self.video_path, cv2.CAP_FFMPEG)
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size to reduce latency
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.setFixedSize(self.target_width, self.target_height)
            self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)  # Fit the view to the item
            self.main_window.update_status(f"FPS: {self.fps:.2f} | Resolution: {self.width}x{self.height} -> {self.target_width}x{self.target_height} | Stream opened successfully.")
        else:
            self.main_window.update_status("Failed to open stream.")
            QMessageBox.warning(self, "Stream Error", "Failed to open the stream. Please check the RTSP server or network connection.")

    def play(self):
        if self.cap and self.cap.isOpened():
            self.paused = False
            self.timer.start(30)  # Start or resume playing
            self.main_window.update_status(f"FPS: {self.fps:.2f} | Resolution: {self.width}x{self.height} -> {self.target_width}x{self.target_height} | Playing video...")
            self.main_window.update_play_button("Stop")

    def pause(self):
        self.paused = True
        self.timer.stop()  # Pause the video
        self.main_window.update_status(f"FPS: {self.fps:.2f} | Resolution: {self.width}x{self.height} -> {self.target_width}x{self.target_height} | Video paused.")

    def stop(self):
        self.paused = False
        self.timer.stop()  # Stop the video
        if self.cap:
            self.cap.release()
        if self.recording:
            self.stop_recording()
        self.cap = cv2.VideoCapture(self.video_path)  # Reset to the start
        self.main_window.update_status(f"FPS: {self.fps:.2f} | Resolution: {self.width}x{self.height} -> {self.target_width}x{self.target_height} | Video stopped.")
        self.main_window.update_play_button("Start")

    def update_frame(self):
        if not self.paused and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                self.handle_stream_failure()
                return
            frame = cv2.resize(frame, (self.target_width, self.target_height))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)
            self.pixmap_item.setPixmap(QPixmap.fromImage(image))
            self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)  # Fit the view to the item

            if self.recording:
                self.out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

            current_time = QDateTime.currentMSecsSinceEpoch()
            elapsed_time = current_time - self.last_frame_time
            if elapsed_time > 0:
                self.fps = 1000 / elapsed_time
            self.last_frame_time = current_time
            self.main_window.update_status(f"FPS: {self.fps:.2f} | Resolution: {self.width}x{self.height} -> {self.target_width}x{self.target_height} | {self.main_window.current_status}")

    def handle_stream_failure(self):
        self.timer.stop()
        self.main_window.update_status("The stream has stopped. Please check the RTSP server or network connection.")
        QMessageBox.warning(self, "Stream Error", "The stream has stopped. Please check the RTSP server or network connection.")
        self.stop()

    def take_snapshot(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if self.target_width and self.target_height:
                    frame = cv2.resize(frame, (self.target_width, self.target_height))
                options = QFileDialog.Options()
                options |= QFileDialog.DontUseNativeDialog
                file_name, _ = QFileDialog.getSaveFileName(self, "Save Snapshot", "", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)", options=options)
                if file_name:
                    file_extension = file_name.split('.')[-1]
                    if file_extension.lower() not in ['png', 'jpg', 'jpeg']:
                        QMessageBox.critical(self, "Error", "Invalid file extension. Please choose a valid file extension (png, jpg, jpeg).")
                        return
                    try:
                        cv2.imwrite(file_name, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                        QMessageBox.information(self, "Snapshot", f"Snapshot saved as {file_name}")
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to save snapshot: {e}")

    def start_recording(self):
        if self.cap and self.cap.isOpened():
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_name, _ = QFileDialog.getSaveFileName(self, "Save Recording", "", "AVI Files (*.avi);;MP4 Files (*.mp4);;All Files (*)", options=options)
            if file_name:
                fourcc = cv2.VideoWriter_fourcc(*'XVID') if file_name.endswith('.avi') else cv2.VideoWriter_fourcc(*'mp4v')
                self.out = cv2.VideoWriter(file_name, fourcc, self.fps, (self.target_width, self.target_height))
                self.recording = True
                self.main_window.update_status(f"Recording started: {file_name}")

    def stop_recording(self):
        if self.recording:
            self.recording = False
            if self.out:
                self.out.release()
                self.out = None
            self.main_window.update_status("Recording stopped")

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.setFixedSize(2300, 1350)  # Set the main window size to 2300x1350
        self.current_status = "Ready"

        # Replace the placeholder QWidget with our VideoWidget
        self.video_widget = VideoWidget(self)  # Pass self as parent
        layout = QVBoxLayout(self.centralwidget)
        self.centralwidget.setLayout(layout)
        layout.addWidget(self.video_widget)

        self.init_ui()

    def init_ui(self):
        self.comboResolution.currentIndexChanged.connect(self.set_resolution)
        self.BtnConnect.clicked.connect(self.enter_rtsp_url)
        self.BtnStart.clicked.connect(self.play_video)
        self.BtnPause.clicked.connect(self.pause_video)
        self.BtnSnapshot.clicked.connect(self.take_snapshot)
        self.BtnRecording.clicked.connect(self.toggle_recording)
        self.set_resolution()  # Initialize with default resolution

    def set_resolution(self):
        resolution = self.comboResolution.currentText()
        width, height = map(int, resolution.split('x'))
        self.video_widget.target_width = width
        self.video_widget.target_height = height
        self.video_widget.setFixedSize(width, height)  # Update VideoWidget size
        self.video_widget.fitInView(self.video_widget.pixmap_item, Qt.KeepAspectRatio)  # Fit the view to the item

    def select_video_path(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi)", options=options)
        if file_name:
            self.video_widget.set_video_path(file_name)
            self.current_status = f"Loaded video file: {file_name}"
            self.update_status(self.current_status)

    def enter_rtsp_url(self):
        text, ok = QInputDialog.getText(self, 'RTSP URL', 'Enter RTSP URL:')
        if ok:
            self.video_widget.set_rtsp_path(text)
            self.current_status = f"Loaded RTSP stream: {text}"
            self.update_status(self.current_status)

    def play_video(self):
        if self.BtnStart.text() == "Start":
            self.current_status = "Playing video..."
            self.video_widget.play()
            self.BtnStart.setText("Stop")
        else:
            self.current_status = "Video stopped."
            self.video_widget.stop()
            self.BtnStart.setText("Start")

    def pause_video(self):
        if self.video_widget.paused:
            self.current_status = "Playing video..."
            self.video_widget.play()
            self.BtnPause.setText("Pause")
        else:
            self.current_status = "Video paused."
            self.video_widget.pause()
            self.BtnPause.setText("Resume")

    def take_snapshot(self):
        self.video_widget.take_snapshot()

    def toggle_recording(self):
        if self.video_widget.recording:
            self.video_widget.stop_recording()
            self.BtnRecording.setText("Recording")
        else:
            self.video_widget.start_recording()
            self.BtnRecording.setText("Stop Recording")

    def update_status(self, message):
        self.statusbar.showMessage(message)  # Update statusbar with the message

    def update_play_button(self, text):
        self.BtnStart.setText(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
