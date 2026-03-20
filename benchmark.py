import mss
import time
from PIL import Image
import io

def benchmark():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        
        start = time.time()
        for i in range(10):
            # 1. 화면 캡처
            sct_img = sct.grab(monitor)
            
            # 2. PIL Image로 변환 및 JPEG 메모리 압축
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            
            data = buffer.getvalue()
        end = time.time()
        
        avg_time = (end - start) / 10
        print(f"평균 캡처+압축 소요 시간: {avg_time:.4f} 초")
        print(f"압축된 프레임 크기: {len(data) / 1024:.2f} KB")

if __name__ == "__main__":
    benchmark()
