"""
OK 시리즈 공통 이미지 생성기 (Google Imagen 3) - 수정 버전
"""
import os
import re
import base64
import frontmatter
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.dirname(SCRIPT_DIR)
CONTENT_DIR = os.path.join(BASE_DIR, 'app', 'content')
IMAGES_DIR  = os.path.join(BASE_DIR, 'app', 'static', 'images')

def clean_md(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```[a-z]*\n', '', text)
    text = re.sub(r'\n```$', '', text)
    if '---' in text and not text.startswith('---'):
        text = '---' + text.split('---', 1)[1]
    return text

def generate_image(safe_name: str, prompt: str):
    out_path = os.path.join(IMAGES_DIR, f"{safe_name}.jpg")
    if os.path.exists(out_path):
        print(f"⏭️  Skip (already exists): {safe_name}.jpg")
        return

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=API_KEY)
        
        print(f"🎨 이미지 생성 시도 중: {safe_name}...")
        
        response = client.models.generate_images(
            model='imagen-4.0-fast-generate-001',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio='16:9',
                output_mime_type='image/jpeg',
            )
        )

        # ✅ 응답 검증 로직 강화
        if not response or not hasattr(response, 'generated_images') or not response.generated_images:
            print(f"❌ 이미지 생성 실패 ({safe_name}): API가 이미지를 반환하지 않았습니다. (세이프티 필터 가능성)")
            return

        # 이미지 데이터 추출
        generated_img = response.generated_images[0]
        if not hasattr(generated_img, 'image') or not generated_img.image:
             print(f"❌ 이미지 데이터 없음 ({safe_name})")
             return
             
        img_bytes = base64.b64decode(generated_img.image.image_bytes)
        
        os.makedirs(IMAGES_DIR, exist_ok=True)
        with open(out_path, 'wb') as f:
            f.write(img_bytes)
        print(f"✅ 이미지 생성 완료: {safe_name}.jpg")

    except Exception as e:
        print(f"❌ API 호출 에러 ({safe_name}): {e}")

def run():
    if not API_KEY:
        print("❌ GEMINI_API_KEY 없음")
        return

    processed = set()
    # 파일 목록을 정렬하여 순차적으로 처리
    file_list = sorted([f for f in os.listdir(CONTENT_DIR) if f.endswith('_en.md')])
    
    for filename in file_list:
        safe_name = filename.replace('_en.md', '')
        if safe_name in processed:
            continue

        fpath = os.path.join(CONTENT_DIR, filename)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip(): continue
                post = frontmatter.loads(clean_md(content))
            
            prompt = str(post.get('image_prompt', ''))
            if not prompt or len(prompt) < 10:
                print(f"⚠️  image_prompt 부족/없음: {filename}")
                continue
                
            generate_image(safe_name, prompt)
            processed.add(safe_name)
        except Exception as e:
            print(f"❌ 파일 처리 실패 ({filename}): {e}")

if __name__ == "__main__":
    run()