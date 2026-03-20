from core.selector import get_selection_and_time

def test_selector():
    print("화면이 반투명해지면 마우스를 드래그하여 영역을 선택해보세요.")
    # 임의로 최대 버퍼를 60초로 가정하고 실행
    rect, seconds = get_selection_and_time(max_seconds=60.0)
    
    if rect and seconds:
        print(f"선택 완료! 영역: {rect}, 추출 시간: {seconds}초")
    else:
        print("선택이 취소되었습니다.")

if __name__ == "__main__":
    test_selector()