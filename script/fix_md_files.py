import os
import csv
import re
import frontmatter

# 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, 'script', 'csv', 'items.csv')
CONTENT_DIR = os.path.join(BASE_DIR, 'app', 'content')

# 매핑 사전 (CSV의 Features -> 우리가 정한 슬림 카테고리)
CAT_MAP = {
    "Omakase": "오마카세", "Michelin": "미슐랭", "Kaiten": "회전초밥",
    "Market": "시장스시", "Tsukiji": "시장스시", "Toyosu": "시장스시",
    "Budget": "가성비", "Affordable": "가성비", "Value": "가성비",
    "Solo": "혼밥", "Fast": "혼밥", "Standing": "혼밥", "Pairing": "사케/술"
}

def get_safe_name(name):
    return re.sub(r"[^a-z0-9_]", "", name.lower().replace(" ", "_").replace("'", ""))

def run():
    print("🚑 [OKSushi] 마크다운 카테고리 강제 복구 시작...")
    
    # 1. CSV 데이터 읽기
    csv_data = {}
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            safe_name = get_safe_name(row['Name'])
            csv_data[safe_name] = row['Features']

    # 2. 마크다운 파일 하나씩 수정
    count = 0
    for filename in os.listdir(CONTENT_DIR):
        if not filename.endswith('.md') or filename.startswith('guide'): continue
        
        # 파일명에서 접미사 제거 (sukiyabashi_jiro_en -> sukiyabashi_jiro)
        safe_id = filename.rsplit('_', 1)[0]
        
        if safe_id in csv_data:
            filepath = os.path.join(CONTENT_DIR, filename)
            try:
                # 텍스트로 읽어서 YAML 오류 방지
                with open(filepath, 'r', encoding='utf-8') as f:
                    raw = f.read()
                
                # frontmatter 로드 시도 (실패 시 수동 쪼개기)
                try:
                    post = frontmatter.loads(raw)
                except:
                    parts = raw.split('---', 2)
                    if len(parts) < 3: continue
                    post = frontmatter.Post(parts[2], title=filename)

                # CSV Features를 기반으로 카테고리 생성
                features = csv_data[safe_id]
                new_cats = []
                for key, val in CAT_MAP.items():
                    if key.lower() in features.lower():
                        new_cats.append(val)
                
                # 매칭 실패 시 기본값
                if not new_cats: new_cats = ["오마카세"]
                
                post['categories'] = list(set(new_cats))
                
                # 저장
                with open(filepath, 'wb') as f:
                    frontmatter.dump(post, f)
                
                count += 1
                if count % 20 == 0: print(f"  ✅ {count}개 수복 완료...")
            except Exception as e:
                print(f"  ❌ 에러 ({filename}): {e}")

    print(f"\n✨ 총 {count}개의 마크다운 파일이 정상화되었습니다!")

if __name__ == "__main__":
    run()