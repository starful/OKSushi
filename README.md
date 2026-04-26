# OK 시리즈 템플릿

> Flask + Google Maps + Gemini AI 기반 일본 정보 큐레이션 플랫폼 공통 템플릿

---

## 🗂️ 프로젝트 구조

```
oktemplate/
│
├── app/                          # Flask 앱
│   ├── __init__.py               # 라우팅 + 데이터 로드 (공통, 수정 불필요)
│   ├── config.py                 # ✅ 핵심 설정 파일 (여기만 수정!)
│   │
│   ├── content/                  # AI 생성 마크다운 (.gitignore)
│   │   ├── *.md                  # 아이템 상세 (item_generator.py 생성)
│   │   └── guides/
│   │       └── *.md              # 가이드 글 (guide_generator.py 생성)
│   │
│   ├── static/
│   │   ├── css/style.css         # 공통 스타일 (CSS 변수로 테마 변경)
│   │   ├── js/
│   │   │   ├── config.js         # JS 카테고리/색상 설정
│   │   │   ├── main.js           # 앱 진입점 (지도 + 리스트 렌더링)
│   │   │   ├── map-core.js       # Google Maps 핵심 로직
│   │   │   └── utils.js          # 공통 유틸리티
│   │   ├── json/
│   │   │   └── items_data.json   # build_data.py가 생성 (빌드타임)
│   │   └── images/               # GCS에서 서빙 (.gitignore)
│   │
│   └── templates/
│       ├── index.html            # 메인 (지도 + 가이드 + 리스트)
│       ├── header.html           # 공통 헤더 (로고, 언어, 필터)
│       ├── footer.html           # 공통 푸터
│       ├── detail.html           # 아이템 상세 페이지
│       ├── guide_detail.html     # 가이드 상세 페이지
│       ├── guide_list.html       # 가이드 목록 페이지
│       ├── about.html            # 소개 페이지
│       └── privacy.html          # 개인정보 처리방침
│
├── script/
│   ├── item_generator.py         # AI 아이템 컨텐츠 생성
│   ├── guide_generator.py        # AI 가이드 컨텐츠 생성
│   ├── build_data.py             # MD → JSON 빌드
│   ├── fetch_images.py           # Imagen 3 이미지 생성
│   ├── optimize_images.py        # 이미지 최적화
│   └── csv/
│       ├── items.csv             # ✅ 아이템 목록 데이터
│       └── guides.csv            # ✅ 가이드 주제 목록
│
├── Dockerfile
├── cloudbuild.yaml               # ✅ GCP 프로젝트 ID 교체 필요
├── deploy.sh                     # ✅ PROJECT_NAME, SERVICE_URL 교체 필요
├── requirements.txt
└── .env.example                  # → .env 복사 후 API 키 입력
```

---

## 🚀 새 OK 시리즈 만들기 (5단계)

### 1. 프로젝트 복사

```bash
cp -r oktemplate okSomething
cd okSomething
```

### 2. `app/config.py` 수정

```python
SITE_CONFIG = {
    "project_name":  "oksomething",
    "site_name":     "OKSomething",
    "site_url":      "https://oksomething.net",
    "tagline":       "Discover the Best Something in Japan",
    "data_key":      "items",          # JSON 최상위 키
    "ga_id":         os.getenv("GA_ID", "G-XXXXXXXXXX"),
    "maps_api_key":  os.getenv("MAPS_API_KEY", ""),
    "maps_id":       "YOUR_MAP_ID",
    "emoji":         "⛩️",
    "accent_color":  "#2980b9",        # 사이트 대표 색상
    "filter_buttons": [...],           # 카테고리 필터 버튼
    "category_mapping": {...},         # 한→영 카테고리 매핑
    "js_category_map":  {...},         # JS용 영→한 역방향 매핑
    # ... 기타
}
```

### 3. CSV 데이터 입력

**`script/csv/items.csv`** — 아이템 목록:
```
Name,Lat,Lng,Address,Features,Agoda
아이템명,위도,경도,"지역명","특징1, 특징2",예약링크(선택)
```

**`script/csv/guides.csv`** — 가이드 주제:
```
id,topic_en,topic_ko,keywords
guide_001,"English Topic","한국어 주제","keyword1 keyword2"
```

### 4. `app/static/js/config.js` 수정

`CATEGORY_MAP`과 `THEME_COLORS`를 `config.py`와 일치하도록 수정.

### 5. `deploy.sh` / `cloudbuild.yaml` 수정

- `deploy.sh`: `PROJECT_NAME`, `SERVICE_URL` 변경
- `cloudbuild.yaml`: `YOUR_PROJECT_ID`, `REPO_NAME`, `SERVICE_NAME` 교체

---

## 🔄 배포 파이프라인

```bash
chmod +x deploy.sh
./deploy.sh
```

내부 실행 순서:
1. 환경 체크 (.env, CSV, 도구)
2. `item_generator.py` — 아이템 마크다운 생성 (Gemini)
3. `guide_generator.py` — 가이드 마크다운 생성 (Gemini)
4. `fetch_images.py` — 이미지 생성 (Imagen 3)
5. `optimize_images.py` — 이미지 압축
6. `build_data.py` — JSON 빌드
7. Git push → GCS 이미지 동기화 → Cloud Run 배포

---

## ☁️ Cloud Build에서 Maps API Key 주입

- 지도 렌더링용 키는 `cloudbuild.yaml`에서 **`MAPS_API_KEY` Secret**으로 Cloud Run에 주입합니다.
- `GOOGLE_PLACES_API_KEY`와 용도가 다르므로 동일 변수로 사용하지 않습니다.
- Cloud Build에서 사용하는 Secret 이름은 `MAPS_API_KEY`입니다.

예시(최초 1회):

```bash
gcloud secrets create MAPS_API_KEY --replication-policy="automatic"
echo -n "YOUR_MAPS_API_KEY" | gcloud secrets versions add MAPS_API_KEY --data-file=-
gcloud projects add-iam-policy-binding starful-258005 \
  --member="serviceAccount:starful-258005@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 📱 반응형/가이드 레이아웃 기본 정책

- `OKSushi Guides`는 기본적으로:
  - 데스크탑: 3열
  - 태블릿: 2열
  - 모바일: 1열
- 모바일 화면에서 헤더/지도/카드/상세 페이지 레이아웃이 자동으로 축소/재배치됩니다.
- 관련 스타일은 `app/static/css/style.css`의 `.guide-grid` 및 media query에서 조정합니다.

---

## 🔎 SEO/색인 정책

- 메인/가이드/상세 템플릿에 `robots`/`canonical` 메타를 설정합니다.
- `/sitemap.xml`은 다음을 포함하도록 동적 생성됩니다.
  - 고정 페이지(메인, 가이드, 소개, 개인정보) en/ko
  - 아이템 상세 페이지
  - 가이드 상세 페이지
  - 다국어 `hreflang` alternate 링크
- 메인 페이지에는 서버 렌더 내부 링크(`Quick Index Links`)를 제공해 크롤러 색인성을 보강합니다.

---

## 🎨 테마 변경 (CSS)

`app/static/css/style.css`의 CSS 변수만 변경:

```css
:root {
    --accent-color: #2980b9;   /* 대표 강조색 */
    --accent-hover: #1a6fa0;
    --bg-color: #f0f8ff;
    --bg-dot-color: #85c1e9;   /* 배경 도트 패턴 색상 */
}
```

---

## 📦 기존 프로젝트와의 차이점

| 항목 | 기존 (okramen 등) | 이 템플릿 |
|------|-----------------|----------|
| 설정 | 각 파일에 분산 | `config.py` 한 곳에 집중 |
| 라우팅 | `/ramen/`, `/onsen/` 등 | `/item/` 로 통일 |
| 데이터 키 | ramens / onsens | `data_key` 변수로 지정 |
| 스크립트 | 프로젝트별 별도 | `item_generator.py` 공통화 |
| JS 설정 | 하드코딩 | `config.js`로 분리 |
| 마커 타입 | 사진 원형 마커 | `renderPhotoMarkers` / `renderDotMarkers` 선택 가능 |

---

## 📝 환경 변수

`.env.example`을 `.env`로 복사 후 입력:

```
GEMINI_API_KEY=실제_API_키
GOOGLE_PLACES_API_KEY=실제_API_키
MAPS_API_KEY=실제_지도_API_키
GA_ID=G-XXXXXXXXXX
```
