import time
import threading
from pynput import keyboard as pynput_keyboard
import config
import subprocess
import sys
import os

from core.recorder import BackgroundRecorder
from core.processor import process_and_save_gif

is_capturing = False

def run_ui_process(max_seconds, bg_image_path):
    """
    서브프로세스로 PyQt UI를 독립적으로 실행하여 메인 스레드와의 충돌을 원천 차단합니다.
    """
    # python -m core.selector 형태로 실행
    cmd = [
        sys.executable, "-m", "core.selector", 
        "--max_seconds", str(max_seconds), 
        "--bg_image", bg_image_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        # UI 프로세스가 출력한 결과값 파싱
        for line in result.stdout.splitlines():
            if line.startswith("RESULT:"):
                parts = line.replace("RESULT:", "").split(",")
                x, y = int(parts[0]), int(parts[1])
                w, h = int(parts[2]), int(parts[3])
                start_s = float(parts[4])
                end_s = float(parts[5])
                return (x, y, w, h), start_s, end_s
    except Exception as e:
        print(f"[오류] UI 프로세스 실행 중 문제 발생: {e}")
        
    return None, None, None

def run_processing(snapshot, rect, start_sec, end_sec):
    try:
        filepath = process_and_save_gif(
            snapshot=snapshot,
            rect=rect,
            start_sec=start_sec,
            end_sec=end_sec,
            fps=config.FPS,
            output_dir=config.OUTPUT_DIR
        )
        if filepath:
            print(f"[성공] 파일이 정상적으로 저장되었습니다: {filepath}")
        else:
            print("[오류] process_and_save_gif 함수가 파일 경로를 반환하지 않았습니다.")
    except Exception as e:
        print(f"[치명적 오류] GIF 저장 중 예외가 발생했습니다: {e}")

import traceback

import pickle

def handle_capture(recorder):
    global is_capturing
    
    if is_capturing:
        return
        
    is_capturing = True
    try:
        snapshot = recorder.get_snapshot()
        if not snapshot:
            print("\n[오류] 버퍼가 비어있습니다. 잠시 후 다시 시도해주세요.")
            return
            
        print("\n[이벤트] 스냅샷 확보 완료! 화면을 일시 정지합니다...")
        
        # 스냅샷 전체 데이터를 임시 파일(pickle)로 저장하여 UI 프로세스에 전달
        temp_snap_path = os.path.join(config.OUTPUT_DIR, "temp_snapshot.pkl")
        try:
            with open(temp_snap_path, "wb") as f:
                pickle.dump(snapshot, f)
        except Exception as e:
            print(f"[오류] 스냅샷 임시 저장 실패: {e}")
            return
            
        # 별도 프로세스로 UI 띄우기 (배경 이미지가 아니라 스냅샷 파일을 넘김)
        print("[로그] UI 프로세스를 호출합니다...")
        rect, start_sec, end_sec = run_ui_process(config.BUFFER_SECONDS, temp_snap_path)
        
        # 임시 파일 삭제
        if os.path.exists(temp_snap_path):
            try:
                os.remove(temp_snap_path)
            except:
                pass
        
        if rect and start_sec is not None:
            print(f"[로그] UI 반환 완료 -> 선택된 영역: {rect}, 구간: {start_sec}초 전 ~ {end_sec}초 전")
            print("[로그] GIF 렌더링 및 저장 프로세스를 시작합니다... (백그라운드 진행)")
            
            threading.Thread(target=run_processing, args=(snapshot, rect, start_sec, end_sec), daemon=True).start()
        else:
            print("[취소됨] 사용자가 캡처를 취소했거나 영역/시간 값이 유효하지 않습니다.")
            
        print(f"\n대기 중... [{config.HOTKEY}]를 누르세요.")
    except Exception as e:
        print(f"\n[치명적 오류] 캡처 처리 중 예외 발생: {e}")
        traceback.print_exc()
    finally:
        is_capturing = False

def on_hotkey(recorder):
    # 단축키 후킹 스레드를 멈추지 않게 하기 위해 캡처 작업을 즉시 새 스레드로 넘깁니다.
    threading.Thread(target=handle_capture, args=(recorder,), daemon=True).start()

def main():
    print("====================================")
    print("  Instant Replay GIF Maker 시작...")
    print("====================================")
    
    # 1. 백그라운드 캡처 시작
    recorder = BackgroundRecorder(fps=config.FPS, buffer_seconds=config.BUFFER_SECONDS)
    recorder.start()
    
    print(f"\n[설정] 단축키 활성화: [{config.HOTKEY}]")
    print(f"[설정] 설정 버퍼: {config.BUFFER_SECONDS}초 / {config.FPS}FPS")
    print("프로그램을 종료하시려면 콘솔에서 Ctrl+C를 누르세요.\n")
    
    # 2. 글로벌 단축키 등록 및 실행 (pynput 방식)
    # pynput은 'ctrl'을 '<ctrl>'로 표기하는 방식의 차이가 있으므로 간단히 매핑
    hotkey_str = config.HOTKEY.replace("ctrl", "<ctrl>").replace("shift", "<shift>").replace("alt", "<alt>")
    
    with pynput_keyboard.GlobalHotKeys({
        hotkey_str: lambda: on_hotkey(recorder)
    }) as h:
        try:
            h.join()
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
        finally:
            recorder.stop()

if __name__ == "__main__":
    main()
