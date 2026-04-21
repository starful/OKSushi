import os
import json
import re
import frontmatter
from datetime import datetime

# ==========================================
# ⚙️ 설정 (config.py의 data_key와 일치해야 함)
# ==========================================
DATA_KEY = "sushis"

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(BASE_DIR, 'app', 'content')
OUTPUT_PATH = os.path.join(BASE_DIR, 'app', 'static', 'json', 'items_data.json')

def clean_md(text: str) -> str:
    """AI 마크다운 생성 시 포함될 수 있는 코드 블록 문자를 제거합니다."""
    text = text.strip()
    text = re.sub(r'^```[a-z]*\n', '', text)
    text = re.sub(r'\n```$', '', text)
    return text

def main():
    print(f"🔨 Building {DATA_KEY}_data.json (Unified Data Engine)...")
    items = []

    if not os.path.exists(CONTENT_DIR):
        print("❌ content 디렉터리 없음")
        return

    # 1. 모든 마크다운 파일 탐색
    all_files = [f for f in os.listdir(CONTENT_DIR) if f.endswith('.md')]
    
    for filename in all_files:
        # 가이드 파일은 별도로 처리하므로 아이템 빌드에서는 제외
        if filename.startswith('guide'):
            continue
        
        fpath = os.path.join(CONTENT_DIR, filename)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                raw_content = f.read()

            # 마크다운 파싱
            post = frontmatter.loads(clean_md(raw_content))
            
            # 💡 [핵심] 카테고리 추출 및 정규화 로직
            # 문자열("A, B")로 들어있든 리스트(["A", "B"])로 들어있든 리스트로 통일
            cats_raw = post.get('categories', [])
            if isinstance(cats_raw, str):
                # 문자열인 경우 콤마로 분리
                cats = [c.strip() for c in cats_raw.split(',') if c.strip()]
            elif isinstance(cats_raw, list):
                # 리스트인 경우 각 항목 청소
                cats = [str(c).strip() for c in cats_raw if c]
            else:
                cats = []

            # 💡 실시간 디버깅 출력: 이 로그가 [] 가 아니어야 웹사이트 숫자가 나옵니다!
            if cats:
                print(f"  ✅ {filename}: {cats}")
            else:
                print(f"  ⚠️  {filename}: 카테고리 정보 없음 (Empty [])")

            # 위도/경도 숫자 변환
            try:
                lat = float(post.get('lat', 0))
                lng = float(post.get('lng', 0))
            except (ValueError, TypeError):
                lat, lng = 0.0, 0.0

            # 필수 데이터가 있는 경우만 JSON에 추가
            if lat != 0:
                item_id = filename.replace('.md', '')
                items.append({
                    "id":          item_id,
                    "lang":        'ko' if '_ko' in filename else 'en',
                    "title":       str(post.get('title', 'Untitled')),
                    "lat":         lat,
                    "lng":         lng,
                    "categories":  cats, # 정상적으로 정제된 카테고리 리스트
                    "thumbnail":   str(post.get('thumbnail', '/static/images/default.jpg')),
                    "address":     str(post.get('address', 'Japan')),
                    "published":   str(post.get('date', datetime.now().strftime('%Y-%m-%d'))),
                    "summary":     str(post.get('summary', ''))[:180],
                    "link":        f"/item/{item_id}",
                })
        except Exception as e:
            print(f"❌ Skip {filename} due to error: {e}")

    # 2. 날짜순 정렬
    items.sort(key=lambda x: x['published'], reverse=True)

    # 3. 최종 JSON 생성
    output = {
        "last_updated": datetime.now().strftime("%Y.%m.%d"),
        "total_count":  len(items),
        DATA_KEY:       items,
    }

    # 4. 파일 저장
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 빌드 완료: 총 {len(items)}개 아이템 데이터가 저장되었습니다.")
    print(f"📍 경로: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()