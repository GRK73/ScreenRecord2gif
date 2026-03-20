import os

# 사용자 설정
HOTKEY = "ctrl+shift+x"  # 글로벌 단축키
BUFFER_SECONDS = 60      # 유지할 과거 시간(초)
FPS = 10                 # 초당 캡처 프레임 수
OUTPUT_DIR = "output"    # 저장될 폴더

# 폴더가 없으면 생성
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
