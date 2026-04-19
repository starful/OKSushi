import os
import time
import random
import re
import shutil
import frontmatter
from google import genai
from google.genai import types
from dotenv import load_dotenv

# ==========================================
# ⚙️ 설정 (GCP 프로젝트 정보)
# ==========================================
load_dotenv()

GCP_PROJECT  = os.environ.get("GCP_PROJECT", "starful-258005")
GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.dirname(SCRIPT_DIR)
CONTENT_DIR = os.path.join(BASE_DIR, 'app', 'content')
IMAGES_DIR  = os.path.join(BASE_DIR, 'app', 'static', 'images')
# 최종 실패 시 대체할 기본 이미지 파일 (반드시 이 경로에 존재해야 함)
DEFAULT_IMG = os.path.join(IMAGES_DIR, 'default.jpg')

# 보호할 파일 목록
PROTECTED = {'logo.png', 'favicon.ico', 'default.jpg', 'og_image.png'}

def generate_image(image_prompt, save_path, retry=False):
    """
    Imagen 4.0을 사용하여 이미지를 생성합니다. 
    실패 시 안전한 프롬프트로 1회 재시도하며, 최종 실패 시 default.jpg로 대체합니다.
    """
    client = genai.Client(
        vertexai=True,
        project=GCP_PROJECT,
        location=GCP_LOCATION,
    )

    # 1. 프롬프트 정제 (필터링 방지)
    if retry:
        # 재시도 시: 극도로 안전한 범용 프롬프트 사용
        clean_prompt = "A high-end Japanese sushi platter with assorted nigiri, tuna, and salmon, professional food photography, 8k, neutral background"
    else:
        # 일반 시도: 특정 상호명 및 인물 이름 제거
        clean_prompt = re.sub(r'Sukiyabashi Jiro|Jiro|Sushiro|Kura|Inomata|Midori|Shinjuku|Ginza', 'Luxury sushi', str(image_prompt), flags=re.IGNORECASE)

    enhanced_prompt = (
        f"{clean_prompt}. "
        "Top-down 45-degree angle, photorealistic, ultra-detailed, "
        "professional food photography, 8K resolution, no people, no text, no watermark."
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

        # 2. 결과 검증 및 저장
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
                # 💡 최종 실패: default.jpg 복사
                if os.path.exists(DEFAULT_IMG):
                    shutil.copy(DEFAULT_IMG, save_path)
                    print(f"  🚩 최종 실패 -> {os.path.basename(save_path)}를 default.jpg로 대체함")
                else:
                    print(f"  ❌ 에러: default.jpg 파일이 {IMAGES_DIR}에 없습니다!")
                return False

    except Exception as e:
        print(f"  ❌ 생성 오류: {e}")
        if not retry:
            return generate_image(image_prompt, save_path, retry=True)
        
        # 에러 발생 시에도 최종적으로 default.jpg 복사
        if os.path.exists(DEFAULT_IMG):
            shutil.copy(DEFAULT_IMG, save_path)
            print(f"  🚩 에러 발생 -> default.jpg로 대체 완료")
        return False

def run():
    """
    MD 파일들을 읽어 이미지 생성이 필요한 항목들을 처리합니다.
    """
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR, exist_ok=True)

    # 1. 대상 safe_name 추출 (English 마크다운 기준)
    targets = []
    if os.path.exists(CONTENT_DIR):
        for fname in os.listdir(CONTENT_DIR):
            if fname.endswith('_en.md'):
                targets.append(fname.replace('_en.md', ''))

    targets = sorted(targets)
    total = len(targets)
    print(f"\n🍣 OKSushi 이미지 엔진 가동 (Vertex AI)")
    print(f"   대상: 총 {total}개 아이템\n")

    for i, name in enumerate(targets, 1):
        save_path = os.path.join(IMAGES_DIR, f"{name}.jpg")

        # 2. 기존 파일 체크 (정상 파일이면 건너뜀, 1KB 미만이면 깨진 것으로 간주하고 다시 생성)
        if os.path.exists(save_path):
            if os.path.getsize(save_path) > 1024: # 1KB 이상만 정상으로 인정
                print(f"[{i:03d}/{total}] {name} -> ⏭️  이미 존재함")
                continue
            else:
                os.remove(save_path)

        print(f"[{i:03d}/{total}] {name} 생성 중...")
        
        # 3. MD 파일에서 프롬프트 읽기
        try:
            md_path = os.path.join(CONTENT_DIR, f"{name}_en.md")
            with open(md_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                prompt = post.get('image_prompt', 'Luxury premium sushi nigiri')
            
            generate_image(prompt, save_path)
            time.sleep(1.2) # API 할당량 보호를 위한 지연
        except Exception as e:
            print(f"  ❌ MD 읽기 실패 ({name}): {e}")

    print("\n🎉 모든 이미지 프로세싱이 완료되었습니다.")

if __name__ == "__main__":
    run()