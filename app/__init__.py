from flask import Flask, jsonify, render_template, abort, send_from_directory, redirect, request, url_for
from flask_compress import Compress
import json, os, frontmatter, markdown, re, glob, hashlib, copy
from datetime import datetime
from flask import Response, make_response

# [설정 로드]
try:
    from .config import SITE_CONFIG
except ImportError:
    from config import SITE_CONFIG

app = Flask(__name__)
Compress(app)

# ==========================================
# 1. 경로 및 전역 설정
# ==========================================
BASE_DIR    = app.root_path
STATIC_DIR  = os.path.join(BASE_DIR, 'static')
DATA_FILE   = os.path.join(STATIC_DIR, 'json', 'items_data.json')
CONTENT_DIR = os.path.join(BASE_DIR, 'content')
GUIDE_DIR   = os.path.join(CONTENT_DIR, 'guides')

CACHED_DATA   = {SITE_CONFIG['data_key']: [], "last_updated": ""}
CACHED_GUIDES = {'en': [], 'ko': []}

# ==========================================
# 2. 유틸리티 함수
# ==========================================

def _clean_md(text):
    """AI가 실수한 YAML 문법 및 마크다운 형식을 강제로 교정합니다."""
    if not text: return ""
    text = text.strip()
    
    # AI 코드 블록 제거
    text = re.sub(r'^```[a-z]*\n', '', text)
    text = re.sub(r'\n```$', '', text)

    # YAML Frontmatter 영역 교정
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            header = parts[1]
            body = parts[2]
            
            new_header_lines = []
            for line in header.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    val = val.strip()
                    if val and not (val.startswith('"') or val.startswith("'")):
                        val = val.replace('"', '\\"')
                        line = f'{key}: "{val}"'
                new_header_lines.append(line)
            
            # 본문 줄바꿈 교정
            body = re.sub(r'([^\n])\n##', r'\1\n\n##', body)
            body = re.sub(r'([^\n])\n\* ', r'\1\n\n* ', body)
            text = f"---\n" + "\n".join(new_header_lines) + f"\n---\n{body}"
    return text.strip()

def get_footer_stats(lang):
    """푸터용 통계 데이터 생성"""
    items = CACHED_DATA.get(SITE_CONFIG['data_key'], [])
    lang_count = len([i for i in items if i.get('lang') == lang])
    return {
        'total_items': lang_count if lang_count > 0 else len(items) // 2,
        'last_updated': CACHED_DATA.get('last_updated', ''),
        'site': SITE_CONFIG,
        'lang': lang
    }

def _slugify_category(value):
    if not value:
        return ""
    return re.sub(r'[^a-z0-9]+', '-', str(value).strip().lower()).strip('-')

def _collect_categories(items):
    category_map = {}
    for item in items:
        for raw in item.get('categories', []):
            label = str(raw).strip()
            if not label:
                continue
            slug = _slugify_category(label)
            if slug and slug not in category_map:
                category_map[slug] = label
    return category_map

# ==========================================
# 3. 데이터 로드 로직
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

# 시작 시 실행
load_items()
load_guides()

# ==========================================
# 4. 라우팅 (페이지)
# ==========================================

@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    stats = get_footer_stats(lang)
    top_guides = CACHED_GUIDES.get(lang, [])[:3]
    all_items = CACHED_DATA.get(SITE_CONFIG['data_key'], [])
    latest_items = [i for i in all_items if i.get('lang') == lang][:24]
    if not latest_items:
        latest_items = [i for i in all_items if i.get('lang') == 'en'][:24]
    return render_template(
        'index.html',
        top_guides=top_guides,
        guides=CACHED_GUIDES,
        latest_items=latest_items,
        **stats
    )

@app.route('/api/items')
def api_items():
    lang = request.args.get('lang', 'en')
    all_items = CACHED_DATA.get(SITE_CONFIG['data_key'], [])
    filtered = [i for i in all_items if i.get('lang') == lang]
    
    if not filtered:
        filtered = [i for i in all_items if i.get('lang') == 'en']

    # 💡 [추가] 한국어 데이터인 경우, JS 필터가 인식할 수 있게 영어 카테고리명을 주입하거나 매핑 유지
    # (이미 main.js에서 CATEGORY_MAP을 추가했으므로 이 단계는 필수는 아니지만, 
    # 데이터 자체가 정확해야 필터 버튼 클릭 시 리스트가 잘 바뀝니다.)

    return jsonify({
        SITE_CONFIG['data_key']: filtered, 
        "last_updated": CACHED_DATA.get('last_updated')
    })

@app.route('/guide')
def guide_list():
    lang = request.args.get('lang', 'en')
    return render_template('guide_list.html', guides=CACHED_GUIDES, **get_footer_stats(lang))

@app.route('/explore')
def explore_all():
    lang = request.args.get('lang', 'en')
    all_items = CACHED_DATA.get(SITE_CONFIG['data_key'], [])
    items = [i for i in all_items if i.get('lang') == lang]
    if not items:
        items = [i for i in all_items if i.get('lang') == 'en']
    category_map = _collect_categories(items)
    return render_template(
        'explore.html',
        items=items[:120],
        page_title='Explore All Sushi Spots',
        category_slug='all',
        category_label='All',
        categories=category_map,
        **get_footer_stats(lang)
    )

@app.route('/explore/<category_slug>')
def explore_by_category(category_slug):
    lang = request.args.get('lang', 'en')
    all_items = CACHED_DATA.get(SITE_CONFIG['data_key'], [])
    items = [i for i in all_items if i.get('lang') == lang]
    if not items:
        items = [i for i in all_items if i.get('lang') == 'en']
    category_map = _collect_categories(items)
    if category_slug != 'all' and category_slug not in category_map:
        return redirect(url_for('explore_all', lang=lang))
    if category_slug == 'all':
        filtered = items
        category_label = 'All'
    else:
        filtered = [
            item for item in items
            if any(_slugify_category(cat) == category_slug for cat in item.get('categories', []))
        ]
        category_label = category_map.get(category_slug, category_slug)
    return render_template(
        'explore.html',
        items=filtered[:120],
        page_title=f"Explore: {category_label}",
        category_slug=category_slug,
        category_label=category_label,
        categories=category_map,
        **get_footer_stats(lang)
    )

@app.route('/site-index')
def site_index():
    lang = request.args.get('lang', 'en')
    all_items = CACHED_DATA.get(SITE_CONFIG['data_key'], [])
    items = [i for i in all_items if i.get('lang') == lang]
    if not items:
        items = [i for i in all_items if i.get('lang') == 'en']
    guides = CACHED_GUIDES.get(lang, [])
    categories = _collect_categories(items)
    return render_template(
        'site_index.html',
        items=items[:200],
        guides=guides[:100],
        categories=categories,
        **get_footer_stats(lang)
    )

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

# ==========================================
# 5. 정적 자원 & SEO (통합 관리)
# ==========================================

# 제안하신 파비콘 및 루트 아이콘 통합 서빙
@app.route('/favicon.ico')
@app.route('/favicon-32x32.png')
@app.route('/favicon-48x48.png')
@app.route('/apple-touch-icon.png')
def serve_favicons():
    """브라우저가 루트에서 찾는 아이콘들을 로컬에서 직접 서빙합니다."""
    # request.path[1:]를 통해 '/favicon.ico' -> 'favicon.ico'로 변환하여 탐색
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'images'), 
        request.path[1:]
    )

@app.route('/static/images/<path:filename>')
def serve_images(filename):
    protected_files = ['logo.png', 'favicon.ico', 'default.jpg', 'og_image.png']
    if filename in protected_files:
        return send_from_directory(STATIC_DIR, f"images/{filename}")
    
    # 💡 디버깅을 위한 출력 (서버 로그에서 확인 가능)
    project_name = SITE_CONFIG['project_name']
    target_url = f"https://storage.googleapis.com/ok-project-assets/{project_name}/{filename}"
    # print(f"DEBUG: Redirecting {filename} to {target_url}") # 로컬 테스트 시 확인용
    
    return redirect(target_url)

@app.route('/robots.txt')
def robots_txt(): return send_from_directory(STATIC_DIR, 'robots.txt')

# ==========================================
# 5. 정적 자원 & SEO (동적 사이트맵 포함)
# ==========================================

@app.route('/sitemap.xml')
def sitemap_xml():
    """
    아이템 및 가이드 데이터를 기반으로 XML 사이트맵을 동적으로 생성합니다.
    """
    site_url = SITE_CONFIG['site_url']
    pages = []
    seen = set()
    today = datetime.now().strftime('%Y-%m-%d')

    def add_page(loc, lastmod, priority, alternates=None):
        if loc in seen:
            return
        seen.add(loc)
        pages.append({
            'loc': loc,
            'lastmod': lastmod,
            'priority': priority,
            'alternates': alternates or []
        })

    # 1. 고정 페이지 (메인, 가이드 목록, 소개, 개인정보) - 한/영 버전
    static_routes = ['', '/guide', '/about.html', '/privacy.html', '/explore', '/site-index']
    for route in static_routes:
        en_loc = f"{site_url}{route}"
        ko_loc = f"{site_url}{route}?lang=ko"
        alternates = [('en', en_loc), ('ko', ko_loc)]
        add_page(en_loc, today, '1.0' if route == '' else '0.8', alternates)
        add_page(ko_loc, today, '1.0' if route == '' else '0.8', alternates)

    # 2. 아이템 상세 페이지 (JSON 데이터 기반)
    items = CACHED_DATA.get(SITE_CONFIG['data_key'], [])
    # 2-1. 카테고리 색인 페이지
    for lang in ['en', 'ko']:
        lang_items = [i for i in items if i.get('lang') == lang]
        if not lang_items:
            continue
        for category_slug in _collect_categories(lang_items).keys():
            add_page(
                f"{site_url}/explore/{category_slug}?lang={lang}",
                today,
                '0.7'
            )

    # 2-2. 아이템 상세 페이지
    for item in items:
        add_page(
            f"{site_url}/item/{item['id']}",
            item.get('published', today),
            '0.6'
        )

    # 3. 가이드 상세 페이지 (캐시된 가이드 기반)
    for lang in ['en', 'ko']:
        for guide in CACHED_GUIDES.get(lang, []):
            add_page(
                f"{site_url}/guide/{guide['id']}",
                guide.get('published', today),
                '0.7'
            )

    # XML 생성
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
    sitemap_xml += 'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    
    for page in pages:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{page["loc"]}</loc>\n'
        sitemap_xml += f'    <lastmod>{page["lastmod"]}</lastmod>\n'
        sitemap_xml += f'    <priority>{page["priority"]}</priority>\n'
        for hreflang, alt_loc in page.get('alternates', []):
            sitemap_xml += f'    <xhtml:link rel="alternate" hreflang="{hreflang}" href="{alt_loc}" />\n'
        sitemap_xml += '  </url>\n'
    
    sitemap_xml += '</urlset>'

    return Response(sitemap_xml, mimetype='application/xml')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)