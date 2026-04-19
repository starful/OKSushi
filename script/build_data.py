# script/build_data.py 전체 소스

import os
import json
import re
import frontmatter
from datetime import datetime

DATA_KEY = "sushis"
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(BASE_DIR, 'app', 'content')
OUTPUT_PATH = os.path.join(BASE_DIR, 'app', 'static', 'json', 'items_data.json')

def clean_md(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```[a-z]*\n', '', text)
    text = re.sub(r'\n```$', '', text)
    if '---' in text and not text.startswith('---'):
        text = '---' + text.split('---', 1)[1]
    return text

def main():
    print(f"🔨 Building {DATA_KEY}_data.json (Multi-language)...")
    items = []

    if not os.path.exists(CONTENT_DIR):
        print("❌ content 디렉터리 없음")
        return

    for filename in os.listdir(CONTENT_DIR):
        if not filename.endswith('.md'): continue
        
        # 💡 핵심 수정: 모든 파일을 읽도록 함 (언어 상관없이)
        fpath = os.path.join(CONTENT_DIR, filename)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                raw = f.read()

            post = frontmatter.loads(clean_md(raw))
            
            # 파일명에서 base_id 추출 (예: sukiyabashi_jiro_en -> sukiyabashi_jiro)
            # lang 설정 (en 또는 ko)
            item_lang = 'ko' if '_ko' in filename else 'en'
            
            cats = post.get('categories', [])
            if isinstance(cats, str):
                cats = [c.strip() for c in cats.split(',')]

            try:
                lat = float(post.get('lat') or 0)
                lng = float(post.get('lng') or 0)
            except:
                lat, lng = 0.0, 0.0

            if lat == 0.0: continue

            # items_data.json에 저장될 객체
            items.append({
                "id":          filename.replace('.md', ''),
                "lang":        item_lang, # 💡 언어 구분값 저장
                "title":       str(post.get('title', 'Untitled')),
                "lat":         lat,
                "lng":         lng,
                "categories":  cats,
                "thumbnail":   str(post.get('thumbnail', '/static/images/default.jpg')),
                "address":     str(post.get('address', 'Japan')),
                "published":   str(post.get('date', datetime.now().strftime('%Y-%m-%d'))),
                "summary":     str(post.get('summary', ''))[:200],
                "link":        f"/item/{filename.replace('.md', '')}",
            })
        except Exception as e:
            print(f"❌ Skip {filename}: {e}")

    output = {
        "last_updated": datetime.now().strftime("%Y.%m.%d"),
        "total_count":  len(items),
        DATA_KEY:       items,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"🎉 완료: {len(items)}개 데이터 빌드됨 (KO/EN 포함)")

if __name__ == "__main__":
    main()