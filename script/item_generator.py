"""
OK 시리즈 공통 아이템 컨텐츠 생성기
─ config.py의 설정을 읽어 아이템별 마크다운 파일을 생성합니다.
─ 새 프로젝트 시작 시 PROMPT_CONFIG만 수정하면 됩니다.
"""
import os
import csv
import re
import concurrent.futures
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
BASE_DIR    = os.path.dirname(SCRIPT_DIR)
CONTENT_DIR = os.path.join(BASE_DIR, 'app', 'content')

# ============================================================
# ✅ 새 프로젝트 만들 때 여기를 수정하세요
# ============================================================
PROMPT_CONFIG = {
    "item_type":       "Sushi Restaurant",
    "item_type_ko":    "스시 레스토랑",
    "categories": {
        "en": ["Omakase", "Kaiten", "Michelin", "Budget", "Market", "Solo", "Premium", "Local Gem"],
        "ko": ["오마카세", "회전초밥", "미슐랭", "가성비", "수산시장", "혼밥가능", "프리미엄", "현지인맛집"],
    },
    "min_length": 6500, # 스시는 재료 설명이 중요하므로 조금 더 길게 설정
    "schema_type": "Restaurant",
}
# ============================================================


def clean_ai_response(text: str) -> str:
    text = text.strip()
    text = re.sub(r'^```[a-z]*\n', '', text)
    text = re.sub(r'\n```$', '', text)
    text = re.sub(r'^(##\s*)?yaml\n', '', text, flags=re.IGNORECASE)
    if '---' in text and not text.startswith('---'):
        text = '---' + text.split('---', 1)[1]
    return text.strip()


def generate_item_article(safe_name: str, name: str, lat: str, lng: str,
                          address: str, lang: str, features: str, agoda: str = ''):
    if not API_KEY:
        print("❌ GEMINI_API_KEY 없음")
        return

    try:
        from google import genai
        client = genai.Client(api_key=API_KEY)
    except ImportError:
        print("❌ google-genai 패키지가 없습니다: pip install google-genai")
        return

    cat_list = ", ".join(PROMPT_CONFIG["categories"][lang])
    item_type = PROMPT_CONFIG["item_type"] if lang == "en" else PROMPT_CONFIG["item_type_ko"]
    min_len   = PROMPT_CONFIG["min_length"]

    print(f"🚀 [AI] {lang} 기사 생성 중: {name}...")

    prompt = f"""
You are an expert travel writer. Write a detailed, SEO-optimized guide for '{name}'.
The article must be at least {min_len} characters, professional, and engaging.

[Target Info]
- Name: {name}
- Type: {item_type}
- Location: {address}
- Features: {features}
- Language: {lang}

[Categorization Task]
Select the most fitting categories from: [{cat_list}]
(Choose 1-3 that best match the features above)

[Output Format - STRICT]
---
lang: {lang}
title: "Write a compelling SEO title mentioning {name} and {address}"
lat: {lat}
lng: {lng}
categories: ["Category1", "Category2"]
thumbnail: "/static/images/{safe_name}.jpg"
address: "{address}"
date: "{datetime.now().strftime('%Y-%m-%d')}"
agoda: "{agoda}"
summary: "Write a 2-3 sentence summary that hooks readers. Keep it on one line."
image_prompt: "Single-line Imagen prompt IN ENGLISH for a photo of {name}. Include: shot type [overhead/side/45-degree/close-up], lighting [natural/moody/bright], and specific visual details about {features}."
---

[Article Structure]
## Introduction
## Main Feature Analysis (2000+ chars)
## Visitor Experience
## Practical Information (access, hours, tips)
## Conclusion

IMPORTANT: Do NOT use markdown code blocks (```). Start directly with '---'.
IMPORTANT: image_prompt must be a single line inside double quotes.
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        final_text = clean_ai_response(response.text)
        os.makedirs(CONTENT_DIR, exist_ok=True)
        filename = f"{safe_name}_{lang}.md"
        with open(os.path.join(CONTENT_DIR, filename), 'w', encoding='utf-8') as f:
            f.write(final_text)
        print(f"✅ [완료] {filename} ({len(final_text):,} chars)")
    except Exception as e:
        print(f"❌ [실패] {name} ({lang}): {e}")


def run_generator(limit: int = 10):
    csv_path = os.path.join(SCRIPT_DIR, 'csv', 'items.csv')
    if not os.path.exists(csv_path):
        print(f"❌ CSV 없음: {csv_path}")
        return

    tasks = []
    with open(csv_path, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name      = row['Name'].strip()
            safe_name = re.sub(r"[^a-z0-9_]", "", name.lower().replace(" ", "_").replace("'", ""))
            for lang in ['en', 'ko']:
                out_path = os.path.join(CONTENT_DIR, f"{safe_name}_{lang}.md")
                if not os.path.exists(out_path):
                    tasks.append((
                        safe_name, name,
                        row.get('Lat', '0'), row.get('Lng', '0'),
                        row.get('Address', 'Japan'), lang,
                        row.get('Features', ''), row.get('Agoda', '')
                    ))
            if len(tasks) >= limit * 2:
                break

    if not tasks:
        print("✨ 생성할 새 항목이 없습니다.")
        return

    print(f"🔔 {len(tasks)}개 파일 생성 시작...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        ex.map(lambda p: generate_item_article(*p), tasks)


if __name__ == "__main__":
    run_generator(limit=10)
