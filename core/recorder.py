import mss
import time
import threading
from collections import deque
from PIL import Image
import io

class BackgroundRecorder:
    def __init__(self, fps, buffer_seconds):
        self.fps = fps
        self.interval = 1.0 / fps
        self.max_frames = fps * buffer_seconds
        
        # 순환 큐 (deque) -> 지정된 길이를 넘어가면 가장 오래된 데이터를 자동 삭제함
        self.buffer = deque(maxlen=self.max_frames)
        self.is_recording = False
        self.thread = None
        
        # 멀티스레드 환경에서 버퍼 복사 시 발생할 수 있는 동시성 이슈 방지용 락
        self.lock = threading.Lock()

    def _record_loop(self):
        with mss.mss() as sct:
            # 주 모니터 사용 (인덱스 1)
            monitor = sct.monitors[1]
            
            while self.is_recording:
                start_time = time.time()
                
                # 1. 화면 캡처
                sct_img = sct.grab(monitor)
                
                # 2. PIL Image로 변환 및 메모리상에서 JPEG로 압축
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                
                buffer = io.BytesIO()
                # quality 80: 화질 저하는 거의 없으면서 용량은 원본 대비 약 1/40 수준으로 감소
                img.save(buffer, format="JPEG", quality=80)
                compressed_bytes = buffer.getvalue()
                
                # 시간 정보와 압축된 바이트 데이터를 함께 저장
                frame_data = {
                    "timestamp": time.time(),
                    "image_bytes": compressed_bytes
                }
                
                with self.lock:
                    self.buffer.append(frame_data)
                
                # 3. FPS 제어
                elapsed = time.time() - start_time
                sleep_time = self.interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

    def start(self):
        if self.is_recording:
            return
        self.is_recording = True
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_recording = False
        if self.thread:
            self.thread.join()

    def get_snapshot(self):
        """현재 버퍼에 있는 화면 기록의 복사본(Snapshot)을 반환합니다."""
        with self.lock:
            return list(self.buffer)
