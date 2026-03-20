import sys
import os
import argparse
import pickle

# Qt DPI 관련 경고 메시지 숨김 처리
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"

from PyQt6.QtWidgets import (
    QApplication, QWidget, QDialog, QVBoxLayout, QHBoxLayout, 
    QLabel, QSlider, QPushButton
)
from PyQt6.QtCore import Qt, QRect, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QImage, QRegion, QPixmap

# 프로젝트 루트 경로를 sys.path에 추가하여 config.py를 임포트 가능하게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class CaptureDialog(QDialog):
    def __init__(self, max_seconds, snapshot, bg_image, rect, parent=None):
        super().__init__(parent)
        self.max_seconds = max_seconds
        self.snapshot = snapshot
        
        # 기본값: 과거 10초 전 ~ 0초 전 (현재)
        self.start_sec = min(10.0, max_seconds)
        self.end_sec = 0.0
        
        self.rect = rect
        self.bg_image = bg_image
        
        # 미리보기 관련 변수
        self.preview_frames = []
        self.current_frame_idx = 0
        self.is_playing = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_preview_frame)
        
        self.init_ui()
        self.show_static_preview()
        
    def init_ui(self):
        self.setWindowTitle("GIF 캡처 구간 설정")
        self.setFixedSize(500, 680)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        
        # 1. 미리보기 레이블
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #222; border: 2px solid #555; border-radius: 8px;")
        self.preview_label.setFixedSize(460, 350)
        layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 2. 구간 표시 텍스트
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 10px; margin-bottom: 5px;")
        self.update_time_label()
        layout.addWidget(self.time_label)
        
        # 3. 슬라이더 영역
        slider_layout = QVBoxLayout()
        self.max_val = int(self.max_seconds * 10)
        
        # --- 시작 시점 슬라이더 ---
        start_layout = QHBoxLayout()
        start_lbl = QLabel("시작:")
        start_lbl.setFixedWidth(40)
        start_layout.addWidget(start_lbl)
        self.start_slider = QSlider(Qt.Orientation.Horizontal)
        self.start_slider.setMinimum(0)
        self.start_slider.setMaximum(self.max_val)
        self.start_slider.setValue(int((self.max_seconds - self.start_sec) * 10))
        self.start_slider.valueChanged.connect(self.on_start_changed)
        start_layout.addWidget(self.start_slider)
        slider_layout.addLayout(start_layout)
        
        # --- 종료 시점 슬라이더 ---
        end_layout = QHBoxLayout()
        end_lbl = QLabel("종료:")
        end_lbl.setFixedWidth(40)
        end_layout.addWidget(end_lbl)
        self.end_slider = QSlider(Qt.Orientation.Horizontal)
        self.end_slider.setMinimum(0)
        self.end_slider.setMaximum(self.max_val)
        self.end_slider.setValue(self.max_val)
        self.end_slider.valueChanged.connect(self.on_end_changed)
        end_layout.addWidget(self.end_slider)
        slider_layout.addLayout(end_layout)
        
        layout.addLayout(slider_layout)
        layout.addSpacing(10)
        
        # 4. 하단 버튼 레이아웃
        btn_layout = QHBoxLayout()
        
        self.btn_preview = QPushButton("▶ 미리보기")
        self.btn_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_preview.setStyleSheet("""
            QPushButton {
                padding: 12px; font-size: 14px; font-weight: bold; 
                background-color: #2196F3; color: white; border-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #0b7dda; }
        """)
        self.btn_preview.clicked.connect(self.toggle_preview)
        
        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                padding: 12px; font-size: 14px; font-weight: bold; 
                background-color: #f44336; color: white; border-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #da190b; }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("해당 구간 렌더링 시작")
        self.btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ok.setStyleSheet("""
            QPushButton {
                padding: 12px; font-size: 14px; font-weight: bold; 
                background-color: #4CAF50; color: white; border-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.btn_ok.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_preview)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def show_static_preview(self):
        """정지된 배경 이미지(마지막 프레임)에서 선택 영역을 크롭하여 보여줌"""
        ratio = self.devicePixelRatioF()
        rx = int(self.rect[0] * ratio)
        ry = int(self.rect[1] * ratio)
        rw = int(self.rect[2] * ratio)
        rh = int(self.rect[3] * ratio)
        
        crop_rect = QRect(rx, ry, rw, rh)
        cropped_image = self.bg_image.copy(crop_rect)
        pixmap = QPixmap.fromImage(cropped_image)
        scaled_pixmap = pixmap.scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(scaled_pixmap)

    def toggle_preview(self):
        """미리보기 재생/정지 토글"""
        if self.is_playing:
            self.stop_preview()
        else:
            self.start_preview()

    def start_preview(self):
        if not self.snapshot:
            return
            
        self.btn_preview.setText("■ 미리보기 정지")
        self.is_playing = True
        
        # 선택된 구간 프레임 필터링 및 디코딩 준비
        latest_time = self.snapshot[-1]['timestamp']
        target_start_time = latest_time - self.start_sec
        target_end_time = latest_time - self.end_sec
        
        self.preview_frames.clear()
        
        # 해상도 배율 보정된 크롭 영역 계산
        ratio = self.devicePixelRatioF()
        rx = int(self.rect[0] * ratio)
        ry = int(self.rect[1] * ratio)
        rw = int(self.rect[2] * ratio)
        rh = int(self.rect[3] * ratio)
        crop_rect = QRect(rx, ry, rw, rh)
        
        # 해당 구간의 바이트 데이터를 QPixmap으로 변환하고 잘라냄
        for frame in self.snapshot:
            if target_start_time <= frame['timestamp'] <= target_end_time:
                pixmap = QPixmap()
                pixmap.loadFromData(frame['image_bytes'])
                cropped = pixmap.copy(crop_rect)
                scaled = cropped.scaled(self.preview_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.preview_frames.append(scaled)
        
        if not self.preview_frames:
            self.stop_preview()
            return
            
        self.current_frame_idx = 0
        # FPS에 맞게 타이머 시작 (예: 10FPS -> 100ms마다 업데이트)
        interval = int(1000 / config.FPS)
        self.timer.start(interval)

    def stop_preview(self):
        self.timer.stop()
        self.is_playing = False
        self.btn_preview.setText("▶ 미리보기")
        self.show_static_preview()

    def update_preview_frame(self):
        """타이머에 의해 주기적으로 호출되어 다음 프레임을 표시"""
        if not self.preview_frames:
            return
            
        self.preview_label.setPixmap(self.preview_frames[self.current_frame_idx])
        self.current_frame_idx += 1
        
        # 끝까지 재생하면 처음부터 반복(루프)
        if self.current_frame_idx >= len(self.preview_frames):
            self.current_frame_idx = 0

    def update_time_label(self):
        duration = max(0.1, self.start_sec - self.end_sec)
        self.time_label.setText(f"구간: 과거 {self.start_sec:.1f}초 전 ~ {self.end_sec:.1f}초 전 (총 {duration:.1f}초)")

    def on_start_changed(self, value):
        if self.is_playing:
            self.stop_preview()
            
        if value > self.end_slider.value():
            self.end_slider.blockSignals(True)
            self.end_slider.setValue(value)
            self.end_slider.blockSignals(False)
            
        self.start_sec = self.max_seconds - (self.start_slider.value() / 10.0)
        self.end_sec = self.max_seconds - (self.end_slider.value() / 10.0)
        self.update_time_label()

    def on_end_changed(self, value):
        if self.is_playing:
            self.stop_preview()
            
        if value < self.start_slider.value():
            self.start_slider.blockSignals(True)
            self.start_slider.setValue(value)
            self.start_slider.blockSignals(False)
            
        self.start_sec = self.max_seconds - (self.start_slider.value() / 10.0)
        self.end_sec = self.max_seconds - (self.end_slider.value() / 10.0)
        self.update_time_label()

class SelectorOverlay(QWidget):
    def __init__(self, max_seconds, snapshot_path=None):
        super().__init__()
        self.max_seconds = max_seconds
        self.snapshot = None
        self.bg_image = None
        
        # 피클 파일(snapshot) 로드 및 배경 이미지 추출
        if snapshot_path and os.path.exists(snapshot_path):
            with open(snapshot_path, "rb") as f:
                self.snapshot = pickle.load(f)
            
            if self.snapshot:
                # 가장 마지막 프레임을 배경으로 사용
                last_frame_bytes = self.snapshot[-1]['image_bytes']
                self.bg_image = QImage.fromData(last_frame_bytes)
            
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.Tool)
        
        if not self.bg_image:
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            
        self.showFullScreen()
        
        self.start_point = None
        self.end_point = None
        
    def paintEvent(self, event):
        painter = QPainter(self)
        
        if self.bg_image and not self.bg_image.isNull():
            painter.drawImage(self.rect(), self.bg_image)
        
        if self.start_point and self.end_point:
            x = min(self.start_point.x(), self.end_point.x())
            y = min(self.start_point.y(), self.end_point.y())
            w = abs(self.start_point.x() - self.end_point.x())
            h = abs(self.start_point.y() - self.end_point.y())
            
            rect = QRect(x, y, w, h)
            
            region = QRegion(self.rect())
            region -= QRegion(rect)
            
            painter.setClipRegion(region)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
            painter.setClipping(False)
            
            pen = QPen(QColor(255, 0, 0), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)
        else:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
            
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.position().toPoint()
            self.end_point = self.start_point
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            QApplication.instance().quit()
            
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            QApplication.instance().quit()
            
    def mouseMoveEvent(self, event):
        if self.start_point:
            self.end_point = event.position().toPoint()
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.start_point:
            self.end_point = event.position().toPoint()
            
            x = min(self.start_point.x(), self.end_point.x())
            y = min(self.start_point.y(), self.end_point.y())
            w = abs(self.start_point.x() - self.end_point.x())
            h = abs(self.start_point.y() - self.end_point.y())
            
            if w > 10 and h > 10:
                self.ask_time(x, y, w, h)
            else:
                self.start_point = None
                self.end_point = None
                self.update()

    def ask_time(self, x, y, w, h):
        self.hide()
        
        dialog = CaptureDialog(self.max_seconds, self.snapshot, self.bg_image, (x, y, w, h))
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            start_sec = dialog.start_sec
            end_sec = dialog.end_sec
            
            ratio = self.devicePixelRatioF()
            rx = int(x * ratio)
            ry = int(y * ratio)
            rw = int(w * ratio)
            rh = int(h * ratio)
            
            print(f"RESULT:{rx},{ry},{rw},{rh},{start_sec},{end_sec}")
            
        QApplication.instance().quit()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max_seconds", type=float, default=60.0)
    parser.add_argument("--bg_image", type=str, default="")
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # bg_image 인자로 이제 스냅샷 피클 파일 경로가 들어옴
    overlay = SelectorOverlay(args.max_seconds, args.bg_image)
    app.exec()

if __name__ == "__main__":
    main()
