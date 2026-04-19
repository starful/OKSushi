from flask import Flask, jsonify, render_template, abort, send_from_directory, redirect, request
from flask_compress import Compress
import json, os, frontmatter, markdown, re, glob, hashlib, copy
from datetime import datetime

app = Flask(__name__)
Compress(app)

# ==========================================
# ✅ [설정 영역] 새 OK 시리즈 만들 때 여기만 수정
# ==========================================
from app.config import SITE_CONFIG

# ==========================================
# 경로 설정 (수정 불필요)
# ==========================================
BASE_DIR    = app.root_path
STATIC_DIR  = os.path.join(BASE_DIR, 'static')
DATA_FILE   = os.path.join(STATIC_DIR, 'json', 'items_data.json')
CONTENT_DIR = os.path.join(BASE_DIR, 'content')
GUIDE_DIR   = os.path.join(CONTENT_DIR, 'guides')

# ==========================================
# 이미지 매핑 유틸
# ==========================================
GUIDE_IMAGES = SITE_CONFIG['guide_images']

def get_mapped_image(base_id):
    idx = int(hashlib.md5(base_id.encode()).hexdigest(), 16) % len(GUIDE_IMAGES)
    return GUIDE_IMAGES[idx]

# ==========================================
# 데이터 로드 (시작 시 캐싱)
# ==========================================
CACHED_DATA   = {SITE_CONFIG['data_key']: [], "last_updated": ""}
CACHED_GUIDES = {'en': [], 'ko': []}

def load_items():
    global CACHED_DATA
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                CACHED_DATA = json.load(f)
            print(f"✅ 데이터 로드 완료: {len(CACHED_DATA.get(SITE_CONFIG['data_key'], []))}개")
        except Exception as e:
            print(f"❌ 데이터 로드 오류: {e}")

# app/__init__.py (가이드 로드 부분 수정)

def load_guides():
    global CACHED_GUIDES
    if not os.path.exists(GUIDE_DIR):
        print("⚠️ 가이드 디렉토리가 없습니다.")
        return

    all_raw = []
    # 모든 마크다운 파일을 읽습니다.
    for fpath in glob.glob(os.path.join(GUIDE_DIR, '*.md')):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                raw = _clean_md(f.read())
            post = frontmatter.loads(raw)
            
            # 파일명에서 언어와 ID 분리 (예: sushi-etiquette_ko.md)
            filename = os.path.basename(fpath)
            lang = 'ko' if filename.endswith('_ko.md') else 'en'
            base_id = filename.replace('_ko.md', '').replace('_en.md', '').replace('.md', '')
            
            all_raw.append({
                'base_id': base_id, 
                'lang': lang, 
                'full_id': filename.replace('.md', ''),
                'title': str(post.get('title', 'Guide')),
                'summary': str(post.get('summary', '')),
                'date': str(post.get('date', '2025-01-01'))
            })
        except Exception as e:
            print(f"❌ 가이드 로드 실패 ({fpath}): {e}")

    # 이미지 배정 및 언어별 분류
    new_guides = {'en': [], 'ko': []}
    for g in all_raw:
        # base_id를 기반으로 고정된 이미지 인덱스 생성
        img_idx = sum(ord(c) for c in g['base_id']) % len(GUIDE_IMAGES)
        new_guides[g['lang']].append({
            'id': g['full_id'],
            'title': g['title'],
            'summary': g['summary'],
            'thumbnail': GUIDE_IMAGES[img_idx],
            'published': g['date']
        })

    # 날짜순 정렬
    for l in ['en', 'ko']:
        new_guides[l].sort(key=lambda x: x['published'], reverse=True)

    CACHED_GUIDES = new_guides
    print(f"✅ 가이드 로드 완료: EN({len(new_guides['en'])}), KO({len(new_guides['ko'])})")

# app/__init__.py 내의 _clean_md 함수를 아래와 같이 교체

def _clean_md(text):
    """AI 출력물의 포맷 오류를 강제로 교정합니다."""
    text = text.strip()
    # 1. 코드 블록 제거
    text = re.sub(r'^```[a-z]*\n', '', text)
    text = re.sub(r'\n```$', '', text)
    
    # 2. Frontmatter 분리 (첫 번째 --- 앞의 쓰레기 텍스트 제거)
    if '---' in text:
        parts = text.split('---')
        if len(parts) >= 3:
            # 설정값(Frontmatter) + 내용물
            meta = parts[1]
            content = '---'.join(parts[2:])
            # 💡 핵심: 마크다운 문법 교정 (줄바꿈 보강)
            # 헤더(##) 앞에 빈 줄이 없으면 추가
            content = re.sub(r'([^\n])\n##', r'\1\n\n##', content)
            # 불렛포인트(*) 앞에 빈 줄이 없으면 추가
            content = re.sub(r'([^\n])\n\* ', r'\1\n\n* ', content)
            
            text = f"---\n{meta}\n---\n{content}"

    return text.strip()

def _get_footer_stats(lang):
    items = CACHED_DATA.get(SITE_CONFIG['data_key'], [])
    count = len([i for i in items if i.get('lang') == lang])
    return {
        'total_items':   count if count > 0 else len(items) // 2,
        'last_updated':  CACHED_DATA.get('last_updated', ''),
        'site':          SITE_CONFIG
    }

# 앱 시작 시 로드
load_items()
load_guides()

# ==========================================
# 카테고리 한→영 매핑 (API spoofing)
# ==========================================
CATEGORY_MAPPING = SITE_CONFIG.get('category_mapping', {})

# ==========================================
# 라우팅
# ==========================================
@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    top_guides = CACHED_GUIDES.get(lang, [])[:3]
    stats = _get_footer_stats(lang)
    return render_template('index.html', lang=lang, guides=CACHED_GUIDES,
                           top_guides=top_guides, **stats)

# app/__init__.py 내의 api_items 함수 부분

@app.route('/api/items')
def api_items():
    # 1. 클라이언트가 요청한 언어 확인 (기본값 en)
    lang = request.args.get('lang', 'en')
    
    # 2. 전체 데이터 로드
    all_items = CACHED_DATA.get(SITE_CONFIG['data_key'], [])
    
    # 3. 해당 언어의 아이템만 필터링
    filtered = [i for i in all_items if i.get('lang') == lang]
    
    # 만약 해당 언어 데이터가 하나도 없다면 영어라도 보여주기 (Fallback)
    if not filtered:
        filtered = [i for i in all_items if i.get('lang') == 'en']

    return jsonify({
        SITE_CONFIG['data_key']: filtered, 
        "last_updated": CACHED_DATA.get('last_updated')
    })

@app.route('/guide')
def guide_list():
    lang = request.args.get('lang', 'en')
    stats = _get_footer_stats(lang)
    return render_template('guide_list.html', guides=CACHED_GUIDES, lang=lang, **stats)

@app.route('/guide/<guide_id>')
def guide_detail(guide_id):
    path = os.path.join(GUIDE_DIR, f"{guide_id}.md")
    if not os.path.exists(path):
        return redirect('/guide')

    with open(path, 'r', encoding='utf-8') as f:
        raw = _clean_md(f.read())
    post  = frontmatter.loads(raw)
    body  = re.sub(r'---.*?---', '', post.content, flags=re.DOTALL)
    body  = body.replace('```markdown', '').replace('```', '').strip()

    title   = str(post.get('title') or guide_id)
    lang    = str(post.get('lang', 'en'))
    base_id = guide_id.rsplit('_', 1)[0]
    image   = get_mapped_image(base_id)
    stats   = _get_footer_stats(lang)

    content_html = markdown.markdown(body, extensions=['tables', 'toc', 'fenced_code'])
    return render_template('guide_detail.html',
                           title=title, content=content_html, lang=lang,
                           guide_id=guide_id, base_id=base_id,
                           image_url=image, post=post, **stats)

@app.route('/item/<item_id>')
def item_detail(item_id):
    md_path = os.path.join(CONTENT_DIR, f"{item_id}.md")
    if not os.path.exists(md_path):
        abort(404)

    with open(md_path, 'r', encoding='utf-8') as f:
        raw = _clean_md(f.read())
    post = frontmatter.loads(raw)
    post['id'] = item_id

    if isinstance(post.get('categories'), str):
        post['categories'] = [c.strip() for c in post['categories'].split(',')]

    content_html = markdown.markdown(post.content, extensions=['tables', 'fenced_code'])
    lang  = str(post.get('lang', 'en'))
    stats = _get_footer_stats(lang)
    return render_template('detail.html', post=post, content=content_html, **stats)

# 정적 파일 / SEO
# app/__init__.py 내의 서빙 로직

@app.route('/static/images/<path:filename>')
def serve_images(filename):
    # 로고나 파비콘은 로컬(컨테이너 안)에서 직접 서빙
    if filename in ['logo.png', 'favicon.ico', 'default.jpg']:
        return send_from_directory(STATIC_DIR, f"images/{filename}")
    
    # 나머지는 무조건 GCS로 리다이렉트 (캐시 방지를 위해 랜덤 쿼리 추가 가능)
    project_name = SITE_CONFIG['project_name']
    return redirect(f"https://storage.googleapis.com/ok-project-assets/{project_name}/{filename}")

@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(STATIC_DIR, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap_xml():
    return send_from_directory(STATIC_DIR, 'sitemap.xml')

@app.route('/about.html')
def about():
    lang  = request.args.get('lang', 'en')
    stats = _get_footer_stats(lang)
    return render_template('about.html', **stats)

@app.route('/privacy.html')
def privacy():
    return render_template('privacy.html', site=SITE_CONFIG)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
