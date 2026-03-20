import os
from datetime import datetime
from io import BytesIO
from PIL import Image

def process_and_save_gif(snapshot, rect, start_sec, end_sec, fps, output_dir):
    """
    버퍼 스냅샷에서 원하는 구간의 프레임을 추출하고,
    지정된 영역을 잘라내어 GIF로 저장합니다.
    """
    if not snapshot:
        print("버퍼가 비어있습니다.")
        return
        
    # 최신 프레임의 타임스탬프 (가장 현재에 가까움)
    latest_time = snapshot[-1]['timestamp']
    
    # 시간 범위를 타임스탬프로 역산
    # start_sec가 20, end_sec가 5라면:
    # target_start_time = latest_time - 20 (가장 오래된 시점)
    # target_end_time = latest_time - 5    (가장 최신에 가까운 시점)
    target_start_time = latest_time - start_sec
    target_end_time = latest_time - end_sec
    
    # 지정한 과거 시간(초) 내의 프레임만 필터링 후 압축 해제(디코딩)
    valid_frames = []
    for frame in snapshot:
        if target_start_time <= frame['timestamp'] <= target_end_time:
            # 바이트 데이터를 다시 PIL Image로 복원
            img = Image.open(BytesIO(frame['image_bytes']))
            img.load() # 메모리에 안전하게 적재
            valid_frames.append(img)
    
    if not valid_frames:
        print("선택한 시간 범위에 해당하는 프레임이 버퍼에 없습니다.")
        return
        
    print(f"총 {len(valid_frames)}개의 프레임이 추출되었습니다. 렌더링을 시작합니다...")
    
    x, y, w, h = rect
    crop_box = (x, y, x + w, y + h)
    
    # 추출된 모든 프레임을 선택된 영역으로 크롭
    cropped_frames = []
    for img in valid_frames:
        cropped = img.crop(crop_box)
        cropped_frames.append(cropped)
        
    # 파일명 생성 (예: 20240320_153022.gif)
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".gif"
    filepath = os.path.join(output_dir, filename)
    
    duration = int(1000 / fps)
    
    # 첫 프레임에 나머지 프레임을 append하여 GIF로 저장
    cropped_frames[0].save(
        filepath,
        save_all=True,
        append_images=cropped_frames[1:],
        duration=duration,
        loop=0,
        optimize=True
    )
    
    print(f"GIF 저장 완료: {filepath}")
    return filepath
