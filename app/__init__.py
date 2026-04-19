from flask import Flask, jsonify, render_template, abort, send_from_directory, redirect, request, url_for
from flask_compress import Compress
import json, os, frontmatter, markdown, re, glob, hashlib, copy
from datetime import datetime

# [설정 로드]
try:
    from .config import SITE_CONFIG
except ImportError:
    from config import SITE_CONFIG

app = Flask(__name__)
Compress(app)

# ==========================================
# 1. 경로 설정
# ==========================================
BASE_DIR    = app.root_path
STATIC_DIR  = os.path.join(BASE_DIR, 'static')
DATA_FILE   = os.path.join(STATIC_DIR, 'json', 'items_data.json')
CONTENT_DIR = os.path.join(BASE_DIR, 'content')
GUIDE_DIR   = os.path.join(CONTENT_DIR, 'guides')

CACHED_DATA   = {SITE_CONFIG['data_key']: [], "last_updated": ""}
CACHED_GUIDES = {'en': [], 'ko': []}

# ==========================================
# 2. 유틸리티 (YAML 오류 교정 로직 포함)
# ==========================================

def _clean_md(text):
    """AI가 실수한 YAML 문법 및 마크다운 형식을 강제로 교정합니다."""
    if not text: return ""
    text = text.strip()
    
    # 1. AI 코드 블록 제거
    text = re.sub(r'^```[a-z]*\n', '', text)
    text = re.sub(r'\n```$', '', text)

    # 2. YAML Frontmatter 영역 집중 교정
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            header = parts[1]
            body = parts[2]
            
            # 콜론(:)이 포함된 제목/요약에 따옴표가 없으면 강제로 감싸기
            # (mapping values are not allowed 에러 방지)
            new_header_lines = []
            for line in header.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    val = val.strip()
                    # 따옴표로 감싸져 있지 않은 경우 처리
                    if val and not (val.startswith('"') or val.startswith("'")):
                        # 값 내부에 따옴표가 있으면 이스케이프
                        val = val.replace('"', '\\"')
                        line = f'{key}: "{val}"'
                new_header_lines.append(line)
            
            # 문단 간격 교정 (본문)
            body = re.sub(r'([^\n])\n##', r'\1\n\n##', body)
            body = re.sub(r'([^\n])\n\* ', r'\1\n\n* ', body)
            
            text = f"---\n" + "\n".join(new_header_lines) + f"\n---\n{body}"

    return text.strip()

def get_footer_stats(lang):
    items = CACHED_DATA.get(SITE_CONFIG['data_key'], [])
    lang_count = len([i for i in items if i.get('lang') == lang])
    return {
        'total_items': lang_count if lang_count > 0 else len(items) // 2,
        'last_updated': CACHED_DATA.get('last_updated', ''),
        'site': SITE_CONFIG,
        'lang': lang
    }

# ==========================================
# 3. 데이터 로드 엔진
# ==========================================

def load_items():
    global CACHED_DATA
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                CACHED_DATA = json.load(f)
            print(f"✅ Items Loaded: {len(CACHED_DATA.get(SITE_CONFIG['data_key'], []))}")
        except Exception as e:
            print(f"❌ Items Load Failed: {e}")

def load_guides():
    global CACHED_GUIDES
    if not os.path.exists(GUIDE_DIR): return

    all_raw = []
    md_files = glob.glob(os.path.join(GUIDE_DIR, '*.md'))

    for fpath in md_files:
        filename = os.path.basename(fpath)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            # 교정 후 파싱
            cleaned = _clean_md(raw_content)
            post = frontmatter.loads(cleaned)
            
            lang = 'ko' if filename.endswith('_ko.md') else 'en'
            base_id = filename.replace('_ko.md', '').replace('_en.md', '').replace('.md', '')
            
            all_raw.append({
                'base_id': base_id, 'lang': lang, 'full_id': filename.replace('.md', ''),
                'title': str(post.get('title', 'Sushi Guide')),
                'summary': str(post.get('summary', '')),
                'date': str(post.get('date', '2025-01-01'))
            })
        except Exception as e:
            # 💡 실패한 파일이 무엇인지, 에러 원인이 무엇인지 더 정확히 출력
            print(f"⚠️ Failed parsing {filename}: {e}")

    new_guides = {'en': [], 'ko': []}
    guide_images = SITE_CONFIG.get('guide_images', [])
    
    for g in all_raw:
        img_idx = int(hashlib.md5(g['base_id'].encode()).hexdigest(), 16) % len(guide_images)
        new_guides[g['lang']].append({
            'id': g['full_id'], 'title': g['title'], 'summary': g['summary'],
            'thumbnail': guide_images[img_idx], 'published': g['date']
        })

    for l in ['en', 'ko']:
        new_guides[l].sort(key=lambda x: x['published'], reverse=True)

    CACHED_GUIDES = new_guides
    print(f"✅ Guides Loaded: EN({len(new_guides['en'])}), KO({len(new_guides['ko'])})")

# 앱 초기화 시 로드
load_items()
load_guides()

# ==========================================
# 4. 라우팅
# ==========================================

@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    stats = get_footer_stats(lang)
    top_guides = CACHED_GUIDES.get(lang, [])[:3]
    return render_template('index.html', top_guides=top_guides, guides=CACHED_GUIDES, **stats)

@app.route('/api/items')
def api_items():
    lang = request.args.get('lang', 'en')
    items = CACHED_DATA.get(SITE_CONFIG['data_key'], [])
    filtered = [i for i in items if i.get('lang') == lang]
    if not filtered: filtered = [i for i in items if i.get('lang') == 'en']
    return jsonify({SITE_CONFIG['data_key']: filtered, "last_updated": CACHED_DATA.get('last_updated')})

@app.route('/guide')
def guide_list():
    lang = request.args.get('lang', 'en')
    return render_template('guide_list.html', guides=CACHED_GUIDES, **get_footer_stats(lang))

@app.route('/guide/<guide_id>')
def guide_detail(guide_id):
    path = os.path.join(GUIDE_DIR, f"{guide_id}.md")
    if not os.path.exists(path): return redirect(url_for('guide_list'))
    with open(path, 'r', encoding='utf-8') as f:
        cleaned = _clean_md(f.read())
    post = frontmatter.loads(cleaned)
    lang = 'ko' if '_ko' in guide_id else 'en'
    base_id = guide_id.replace('_ko', '').replace('_en', '')
    img_idx = int(hashlib.md5(base_id.encode()).hexdigest(), 16) % len(SITE_CONFIG['guide_images'])
    content_html = markdown.markdown(post.content, extensions=['tables', 'fenced_code'])
    return render_template('guide_detail.html', title=post.get('title'), content=content_html, 
                           post=post, image_url=SITE_CONFIG['guide_images'][img_idx], **get_footer_stats(lang))

@app.route('/item/<item_id>')
def item_detail(item_id):
    md_path = os.path.join(CONTENT_DIR, f"{item_id}.md")
    if not os.path.exists(md_path): abort(404)
    with open(md_path, 'r', encoding='utf-8') as f:
        cleaned = _clean_md(f.read())
    post = frontmatter.loads(cleaned)
    post['id'] = item_id
    content_html = markdown.markdown(post.content, extensions=['tables', 'fenced_code'])
    return render_template('detail.html', post=post, content=content_html, **get_footer_stats(post.get('lang', 'en')))

@app.route('/static/images/<path:filename>')
def serve_images(filename):
    if filename in ['logo.png', 'favicon.ico', 'default.jpg', 'og_image.png']:
        return send_from_directory(STATIC_DIR, f"images/{filename}")
    return redirect(f"https://storage.googleapis.com/ok-project-assets/{SITE_CONFIG['project_name']}/{filename}")

@app.route('/robots.txt')
def robots_txt(): return send_from_directory(STATIC_DIR, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap_xml(): return send_from_directory(STATIC_DIR, 'sitemap.xml')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)