import time
from core.recorder import BackgroundRecorder

def test_recording():
    # 10 FPS, 최대 60초 저장 가능 설정
    print("녹화를 시작합니다. (5초간 대기...)")
    recorder = BackgroundRecorder(fps=10, buffer_seconds=60)
    recorder.start()
    
    # 5초 동안 백그라운드 캡처가 돌아가도록 메인 스레드 대기
    time.sleep(5)
    
    # 스냅샷 가져오기
    snapshot = recorder.get_snapshot()
    print(f"총 캡처된 프레임 수: {len(snapshot)} 개 (예상: 약 50개)")
    
    # 첫 프레임과 마지막 프레임 시간차 계산
    if len(snapshot) > 1:
        first_time = snapshot[0]['timestamp']
        last_time = snapshot[-1]['timestamp']
        print(f"첫 프레임과 마지막 프레임의 시간 차: {last_time - first_time:.2f} 초")
    
    recorder.stop()
    print("테스트 종료.")

if __name__ == "__main__":
    test_recording()