#!/bin/bash
# ============================================================
#  OK 시리즈 통합 자동 배포 파이프라인
#  실행: ./deploy.sh
#  수정: PROJECT_NAME, SERVICE_URL 을 새 프로젝트에 맞게 변경
# ============================================================
set -e

# ── 색상 정의 ─────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

print_step() { echo ""; echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${BOLD}${CYAN}  $1${NC}"; echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }
print_ok()   { echo -e "${GREEN}  ✅ $1${NC}"; }
print_warn() { echo -e "${YELLOW}  ⚠️  $1${NC}"; }
print_err()  { echo -e "${RED}  ❌ $1${NC}"; }
print_info() { echo -e "  ℹ️  $1"; }

# ============================================================
# ✅ 프로젝트별 설정 (여기만 수정)
PROJECT_NAME="oksushi"
SERVICE_URL="https://oktemplate.net"
GCS_BUCKET="ok-project-assets"
# ============================================================

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
COMMIT_MSG="update: auto-generated content $(date '+%Y-%m-%d %H:%M')"
START_TIME=$SECONDS

clear
echo ""
echo -e "${BOLD}${CYAN}  🚀 ${PROJECT_NAME} 통합 배포 파이프라인${NC}"
echo -e "  $(date '+%Y년 %m월 %d일 %H:%M:%S') 시작"
echo ""

# ── STEP 0: 환경 체크 ─────────────────────────────────────
print_step "STEP 0 / 6  |  환경 체크"
cd "$PROJECT_ROOT"

[ ! -f ".env" ]                        && { print_err ".env 없음"; exit 1; }
grep -q "GEMINI_API_KEY" .env          || { print_err "GEMINI_API_KEY 없음"; exit 1; }
command -v python3 &>/dev/null         || { print_err "python3 없음"; exit 1; }
command -v gcloud  &>/dev/null         || { print_err "gcloud CLI 없음"; exit 1; }
command -v git     &>/dev/null         || { print_err "git 없음"; exit 1; }
[ ! -f "script/csv/items.csv"  ]       && { print_err "items.csv 없음"; exit 1; }
[ ! -f "script/csv/guides.csv" ]       && { print_err "guides.csv 없음"; exit 1; }
print_ok "환경 체크 완료"

# ── STEP 1: 아이템 컨텐츠 생성 ───────────────────────────
print_step "STEP 1 / 6  |  아이템 컨텐츠 생성 (Gemini)"

CONTENT_DIR="app/content"
BEFORE=$(find "$CONTENT_DIR" -maxdepth 1 -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
print_info "생성 전: ${BEFORE}개"

python3 script/item_generator.py

AFTER=$(find "$CONTENT_DIR" -maxdepth 1 -name "*.md" | wc -l | tr -d ' ')
NEW_ITEMS=$(( AFTER - BEFORE ))
print_ok "아이템 생성 완료 (총 ${AFTER}개, 신규 +${NEW_ITEMS}개)"

# ── STEP 2: 가이드 생성 ───────────────────────────────────
print_step "STEP 2 / 6  |  가이드 생성 (Gemini)"

GUIDE_DIR="app/content/guides"
mkdir -p "$GUIDE_DIR"
G_BEFORE=$(find "$GUIDE_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

python3 script/guide_generator.py

G_AFTER=$(find "$GUIDE_DIR" -name "*.md" | wc -l | tr -d ' ')
NEW_GUIDES=$(( G_AFTER - G_BEFORE ))
print_ok "가이드 생성 완료 (총 ${G_AFTER}개, 신규 +${NEW_GUIDES}개)"

# ── STEP 3: 이미지 생성 및 최적화 ────────────────────────
print_step "STEP 3 / 6  |  이미지 생성 (Imagen 3) & 최적화"

IMAGES_DIR="app/static/images"
MISSING=0
for md in "$CONTENT_DIR"/*_en.md; do
    [ -f "$md" ] || continue
    base=$(basename "$md" _en.md)
    if [ ! -f "${IMAGES_DIR}/${base}.jpg" ] && [ ! -f "${IMAGES_DIR}/${base}.jpeg" ]; then
        MISSING=$((MISSING + 1))
    fi
done

if [ "$MISSING" -eq 0 ]; then
    print_ok "모든 이미지 존재 → 스킵"
else
    print_info "이미지 없는 항목: ${MISSING}개 → Imagen 3 생성 중..."
    python3 script/fetch_images.py
    python3 script/optimize_images.py
    print_ok "이미지 생성 및 최적화 완료"
fi

# ── STEP 4: 데이터 빌드 & Git Push ────────────────────────
print_step "STEP 4 / 6  |  데이터 빌드 및 GitHub Push"

python3 script/build_data.py

GIT_STATUS=$(git status --porcelain)
if [ -z "$GIT_STATUS" ]; then
    print_warn "변경 사항 없음 → Git skip"
else
    print_info "변경된 파일: $(echo "$GIT_STATUS" | wc -l | tr -d ' ')개"
    git add .
    git commit -m "$COMMIT_MSG"
    git push origin main
    print_ok "GitHub push 완료"
fi

# ── STEP 5: GCS 이미지 동기화 & Cloud Run 배포 ────────────
print_step "STEP 5 / 6  |  GCS 업로드 및 Cloud Run 배포"

print_info "GCS 이미지 동기화 중..."
gsutil -m rsync -d "$IMAGES_DIR" "gs://${GCS_BUCKET}/${PROJECT_NAME}"
print_ok "GCS 업로드 완료"

print_info "Cloud Build 시작 (약 3~5분)..."
gcloud builds submit
print_ok "Cloud Run 배포 완료"

# ── STEP 6: 완료 요약 ─────────────────────────────────────
print_step "STEP 6 / 6  |  최종 요약"

ELAPSED=$(( SECONDS - START_TIME ))
echo ""
echo -e "${BOLD}${GREEN}  🎉 배포 완료!${NC}"
echo ""
echo -e "  ⏱️  총 소요 시간  : $(( ELAPSED / 60 ))분 $(( ELAPSED % 60 ))초"
echo -e "  📦 신규 아이템   : +${NEW_ITEMS}개 (전체 ${AFTER}개)"
echo -e "  📖 신규 가이드   : +${NEW_GUIDES}개 (전체 ${G_AFTER}개)"
echo -e "  🖼️  생성 이미지  : ${MISSING}개"
echo -e "  🌐 라이브 URL    : ${SERVICE_URL}"
echo ""

# Mac 알림 (선택)
osascript -e "display notification \"배포 완료! 아이템 ${NEW_ITEMS}개, 가이드 ${NEW_GUIDES}개 추가\" with title \"${PROJECT_NAME} 파이프라인\"" 2>/dev/null || true

echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
