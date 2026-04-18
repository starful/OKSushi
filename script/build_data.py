import os
import json
import re
import frontmatter
from datetime import datetime

# 설정: 다른 OK 시리즈와 겹치지 않도록 sushis로 설정
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
    print(f"🔨 Building {DATA_KEY}_data.json ...")
    items = []

    if not os.path.exists(CONTENT_DIR):
        print("❌ content 디렉터리 없음")
        return

    for filename in os.listdir(CONTENT_DIR):
        if not filename.endswith('.md') or '_ko' in filename: # 기본적으로 en 기준으로 빌드 (데이터 중복 방지)
            continue

        fpath = os.path.join(CONTENT_DIR, filename)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                raw = f.read()

            post = frontmatter.loads(clean_md(raw))

            # 카테고리 리스트화
            cats = post.get('categories', [])
            if isinstance(cats, str):
                cats = [c.strip() for c in cats.split(',')]

            # lat / lng 숫자 변환
            try:
                lat = float(post.get('lat') or 0)
                lng = float(post.get('lng') or 0)
            except:
                lat, lng = 0.0, 0.0

            if lat == 0.0: continue

            item_id = filename.replace('.md', '')
            items.append({
                "id":          item_id,
                "lang":        str(post.get('lang', 'en')),
                "title":       str(post.get('title', 'Untitled')),
                "lat":         lat,
                "lng":         lng,
                "categories":  cats,
                "thumbnail":   str(post.get('thumbnail', '/static/images/default.jpg')),
                "address":     str(post.get('address', 'Japan')),
                "published":   str(post.get('date', datetime.now().strftime('%Y-%m-%d'))),
                "summary":     str(post.get('summary', ''))[:200],
                "agoda":       str(post.get('agoda', '')),
                "link":        f"/item/{item_id}",
            })
        except Exception as e:
            print(f"❌ Skip {filename}: {e}")

    # 최종 결과물 생성
    output = {
        "last_updated": datetime.now().strftime("%Y.%m.%d"),
        "total_count":  len(items),
        DATA_KEY:       items, # 여기서 sushis 키를 사용함
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"🎉 완료: {len(items)}개 아이템이 {DATA_KEY} 키로 저장되었습니다.")

if __name__ == "__main__":
    main()