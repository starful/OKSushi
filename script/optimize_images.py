"""
OK 시리즈 공통 이미지 최적화기
─ app/static/images/*.jpg 를 리사이즈 + 품질 압축합니다.
"""
import os
from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR   = os.path.dirname(SCRIPT_DIR)
IMAGES_DIR = os.path.join(BASE_DIR, 'app', 'static', 'images')

MAX_WIDTH  = 1200
MAX_HEIGHT = 800
QUALITY    = 82  # 0-95, 82가 품질/용량 균형점


def optimize(filepath: str):
    try:
        with Image.open(filepath) as img:
            original_size = os.path.getsize(filepath)

            # RGBA → RGB 변환 (JPEG는 투명채널 미지원)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # 리사이즈 (비율 유지)
            img.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)

            img.save(filepath, 'JPEG', quality=QUALITY, optimize=True)
            new_size = os.path.getsize(filepath)
            saved_kb = (original_size - new_size) // 1024
            print(f"✅ {os.path.basename(filepath)}: {original_size//1024}KB → {new_size//1024}KB (절약 {saved_kb}KB)")
    except Exception as e:
        print(f"❌ {os.path.basename(filepath)}: {e}")


def run():
    if not os.path.exists(IMAGES_DIR):
        print("❌ images 디렉터리 없음")
        return

    targets = [
        os.path.join(IMAGES_DIR, f)
        for f in os.listdir(IMAGES_DIR)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        and not f.startswith('logo')
        and not f.startswith('favicon')
    ]

    if not targets:
        print("최적화할 이미지 없음")
        return

    print(f"🖼️  {len(targets)}개 이미지 최적화 시작...")
    for path in targets:
        optimize(path)
    print("🎉 이미지 최적화 완료")


if __name__ == "__main__":
    run()
