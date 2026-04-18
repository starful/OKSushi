import os
import time
import random
import re
import frontmatter
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT  = os.environ.get("GCP_PROJECT", "starful-258005")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.dirname(SCRIPT_DIR)
CONTENT_DIR = os.path.join(BASE_DIR, 'app', 'content')
IMAGES_DIR  = os.path.join(BASE_DIR, 'app', 'static', 'images')

# 촬영 스타일 (다양성 유지)
CAMERA_ANGLES = ["overhead flat-lay shot", "dramatic 45-degree angle shot", "side profile close-up"]
MOODS = ["bright minimalist Japanese sushi bar", "warm rustic wooden interior", "high-end modern restaurant"]

def get_random_style():
    return random.choice(CAMERA_ANGLES), random.choice(MOODS)

def generate_image(image_prompt, save_path, retry=False):
    client = genai.Client(vertexai=True, project=GCP_PROJECT, location=GCP_LOCATION)
    angle, mood = get_random_style()

    # 1. 강력한 필터링 (브랜드 및 인물 이름 제거)
    if retry:
        # 재시도 시에는 아주 단순한 프롬프트로 변경
        clean_prompt = "A high-end platter of diverse fresh nigiri sushi, tuna, salmon, and sea urchin, authentic Japanese food photography"
    else:
        # 일반 시도 시 상호명 제거
        clean_prompt = re.sub(r'Sukiyabashi Jiro|Jiro|Sushiro|Kura Sushi|Kura|Asakusa|Shinjuku', 'Luxury sushi', str(image_prompt), flags=re.IGNORECASE)

    enhanced_prompt = (
        f"{clean_prompt}. Composition: {angle}. Atmosphere: {mood}. "
        "Photorealistic, ultra-detailed, professional food photography, 8K, no people, no text."
    )

    try:
        response = client.models.generate_images(
            model='imagen-4.0-fast-generate-001',
            prompt=enhanced_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
                output_mime_type='image/jpeg',
                person_generation="dont_allow",
            )
        )

        # ✅ 수정된 체크 로직: 이미지 데이터가 실제로 있는지 확인
        if response.generated_images and response.generated_images[0].image and response.generated_images[0].image.image_bytes:
            image_bytes = response.generated_images[0].image.image_bytes
            with open(save_path, 'wb') as f:
                f.write(image_bytes)
            print(f"  ✅ 생성 완료: {os.path.basename(save_path)} ({len(image_bytes)//1024}KB)")
            return True
        else:
            if not retry:
                print(f"  ⚠️  필터 차단 의심 -> 안전 프롬프트로 재시도 중...")
                return generate_image(image_prompt, save_path, retry=True)
            else:
                print(f"  ❌ 생성 실패: 응답에 이미지 데이터가 없음")
                return False

    except Exception as e:
        print(f"  ❌ 생성 오류: {e}")
        return False

def run():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    targets = []
    if os.path.exists(CONTENT_DIR):
        for fname in os.listdir(CONTENT_DIR):
            if fname.endswith('_en.md'):
                targets.append(fname.replace('_en.md', ''))

    print(f"🍣 OKSushi 이미지 생성 시작 (Vertex AI 모드)")

    for i, name in enumerate(sorted(targets), 1):
        save_path = os.path.join(IMAGES_DIR, f"{name}.jpg")
        
        # 이미 성공한 파일(예: midori)은 건너뜀
        if os.path.exists(save_path) and os.path.getsize(save_path) > 1000:
            print(f"[{i:02d}] {name} -> ⏭️  이미 존재")
            continue

        print(f"[{i:02d}] {name} 생성 중...")
        with open(os.path.join(CONTENT_DIR, f"{name}_en.md"), 'r') as f:
            post = frontmatter.load(f)
            prompt = post.get('image_prompt', 'Premium nigiri sushi')
        
        generate_image(prompt, save_path)
        time.sleep(1.2) # 안전을 위한 지연

if __name__ == "__main__":
    run()