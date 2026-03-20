import time
from core.recorder import BackgroundRecorder
from core.processor import process_and_save_gif
import config
import os

def debug_test():
    print("디버그 1: 백그라운드 레코더 시작 (3초 대기)")
    recorder = BackgroundRecorder(fps=10, buffer_seconds=10)
    recorder.start()
    time.sleep(3)
    
    snapshot = recorder.get_snapshot()
    recorder.stop()
    
    print(f"디버그 2: 스냅샷 프레임 수: {len(snapshot)}")
    
    if not snapshot:
        print("에러: 스냅샷이 비어 있습니다.")
        return
        
    # 가상의 영역과 시간 (1초, 좌상단 100x100 크기)
    test_rect = (0, 0, 100, 100)
    test_seconds = 1.0
    
    print(f"디버그 3: GIF 처리 및 저장 시도 (영역: {test_rect}, 시간: {test_seconds}초)")
    
    try:
        process_and_save_gif(snapshot, test_rect, test_seconds, 10, config.OUTPUT_DIR)
        print("디버그 완료: 에러 없이 끝까지 도달했습니다.")
    except Exception as e:
        print(f"디버그 에러 발생: {e}")
        
    if os.path.exists(config.OUTPUT_DIR) and os.listdir(config.OUTPUT_DIR):
        print(f"출력 폴더 내용물: {os.listdir(config.OUTPUT_DIR)}")
    else:
        print("출력 폴더가 비어 있습니다.")

if __name__ == "__main__":
    debug_test()