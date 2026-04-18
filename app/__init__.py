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

def load_guides():
    global CACHED_GUIDES
    if not os.path.exists(GUIDE_DIR):
        return

    all_raw = []
    for fpath in glob.glob(os.path.join(GUIDE_DIR, '*.md')):
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                raw = f.read().strip()
            raw = _clean_md(raw)
            post    = frontmatter.loads(raw)
            lang    = 'ko' if '_ko.md' in fpath else 'en'
            base_id = os.path.basename(fpath).rsplit('_', 1)[0]
            full_id = os.path.basename(fpath).replace('.md', '')
            all_raw.append({
                'base_id': base_id, 'lang': lang, 'full_id': full_id,
                'title':   str(post.get('title', 'Guide')),
                'summary': str(post.get('summary', '')),
                'date':    str(post.get('date', '2026-01-01'))
            })
        except:
            continue

    # 날짜순 정렬 후 이미지 인덱스 배정 (연속 중복 방지)
    ref_en = sorted([g for g in all_raw if g['lang'] == 'en'], key=lambda x: x['date'], reverse=True)
    last_idx = -1
    id_to_img = {}
    for g in ref_en:
        idx = int(hashlib.md5(g['base_id'].encode()).hexdigest(), 16) % len(GUIDE_IMAGES)
        if idx == last_idx:
            idx = (idx + 1) % len(GUIDE_IMAGES)
        id_to_img[g['base_id']] = GUIDE_IMAGES[idx]
        last_idx = idx

    new_guides = {'en': [], 'ko': []}
    for g in all_raw:
        new_guides[g['lang']].append({
            'id':        g['full_id'],
            'title':     g['title'],
            'summary':   g['summary'],
            'thumbnail': id_to_img.get(g['base_id'], GUIDE_IMAGES[0]),
            'published': g['date']
        })
    for lang in ['en', 'ko']:
        new_guides[lang].sort(key=lambda x: x['published'], reverse=True)

    CACHED_GUIDES = new_guides
    total = sum(len(v) for v in new_guides.values())
    print(f"✅ 가이드 로드 완료: {total}개")

def _clean_md(text):
    """AI 출력 잔재 제거"""
    text = re.sub(r'^```[a-z]*\n', '', text)
    text = re.sub(r'\n```$', '', text)
    text = re.sub(r'^(##\s*)?yaml\n', '', text, flags=re.IGNORECASE)
    if '---' in text and not text.startswith('---'):
        text = '---' + text.split('---', 1)[1]
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

@app.route('/api/items')
def api_items():
    lang = request.args.get('lang', 'en')
    items = CACHED_DATA.get(SITE_CONFIG['data_key'], [])
    filtered = [i for i in items if i.get('lang') == lang]
    if not filtered:
        filtered = [i for i in items if i.get('lang') == 'en']

    spoofed = []
    for item in filtered:
        s = copy.deepcopy(item)
        s['lang'] = 'en'  # JS spoofing
        new_cats = [CATEGORY_MAPPING.get(c.strip(), c.strip()) for c in s.get('categories', [])]
        s['categories'] = list(set(new_cats))
        spoofed.append(s)

    return jsonify({SITE_CONFIG['data_key']: spoofed, "last_updated": CACHED_DATA.get('last_updated')})

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
@app.route('/static/images/<path:filename>')
def serve_images(filename):
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
