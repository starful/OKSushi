#!/bin/bash

# ============================================================
#  🍣 OKSushi - 전문 배포 시스템 (Safe Sync Version)
# ============================================================

# [설정 정보]
PROJECT_ID="starful-258005"
REGION="us-central1"
SERVICE_NAME="oksushi"
REPO_NAME="oksushi-repo"
BUCKET_NAME="ok-project-assets"

# 컬러 출력 설정
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}   🍣 OKSushi 배포 파이프라인 가동 (Safe Sync v2.1) ${NC}"
echo -e "${BLUE}=======================================================${NC}"

# 1. 환경 검사 (Pre-flight Checks)
echo -e "🔍 [1단계] 환경 검사 중..."

if [ ! -f .env ]; then
    echo -e "${RED}❌ 에러: .env 파일이 없습니다. GEMINI_API_KEY 설정이 필요합니다.${NC}"
    exit 1
fi

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ 에러: gcloud SDK가 설치되어 있지 않습니다.${NC}"
    exit 1
fi

# ------------------------------------------------------------
# 🛡️ [추가 단계] 알바생이 올린 최신 사진 보호 (Reverse Sync)
# ------------------------------------------------------------
echo -e "📥 [보호단계] 클라우드(GCS)에서 최신 이미지 가져오기..."
# 로컬 폴더가 없으면 생성
mkdir -p app/static/images/
# GCS에 있는 사진들을 로컬로 복사 (로컬에 없는 파일만 가져오거나 최신 파일로 갱신)
gsutil -m rsync -r gs://${BUCKET_NAME}/${SERVICE_NAME}/ app/static/images/
echo -e "${GREEN}✅ 클라우드 사진 동기화 완료 (알바생 업로드분 보호됨)${NC}"
# ------------------------------------------------------------

# 2. AI 콘텐츠 생성 (Item & Guide)
echo -e "📝 [2단계] AI 마크다운 콘텐츠 생성 중..."
python3 script/item_generator.py
python3 script/guide_generator.py
echo -e "${GREEN}✅ 콘텐츠 생성 완료${NC}"

# 3. 이미지 엔진 가동 (Imagen 3 & Optimization)
echo -e "🎨 [3단계] AI 이미지 엔진 가동..."
# 주의: fetch_images.py가 로컬에 이미 파일이 있으면 생성을 건너뛰도록 설계되어 있어야 합니다.
python3 script/fetch_images.py
python3 script/optimize_images.py
echo -e "${GREEN}✅ 이미지 프로세싱 완료${NC}"

# 4. 데이터 빌드 (Build JSON)
echo -e "🔨 [4단계] 데이터 통합 빌드 (JSON 생성) 중..."
python3 script/build_data.py
echo -e "${GREEN}✅ items_data.json 생성 완료${NC}"

# 5. GCS 이미지 최종 동기화 (Static Assets serving)
echo -e "☁️  [5단계] Google Cloud Storage 이미지 최종 전송 중..."
# 위에서 로컬로 사진을 다 가져왔기 때문에, 이제 로컬을 기준으로 올려도 안전합니다.
gsutil -m rsync -r app/static/images/ gs://${BUCKET_NAME}/${SERVICE_NAME}/
echo -e "${GREEN}✅ GCS 최종 동기화 완료 (Bucket: ${BUCKET_NAME}/${SERVICE_NAME})${NC}"

# 6. GitHub 소스 동기화
echo -e "📤 [6단계] GitHub 저장소 업데이트 중..."
if [ -d .git ]; then
    git add .
    if ! git diff-index --quiet HEAD --; then
        git commit -m "Auto-build & Deploy: $(date +'%Y-%m-%d %H:%M:%S') (Admin sync included)"
        git push origin main
        echo -e "${GREEN}✅ GitHub 푸시 완료 (최신 사진 정보 포함)${NC}"
    else
        echo -e "ℹ️ 변경된 소스코드가 없어 커밋을 건너뜁니다."
    fi
else
    echo -e "${RED}⚠️ Git 저장소가 설정되지 않았습니다.${NC}"
fi

# 7. Google Cloud Build 기반 배포 (cloudbuild.yaml 사용)
echo -e "🏗️  [7단계] Google Cloud Build 시작 (cloudbuild.yaml 기반)..."
gcloud builds submit \
  --config cloudbuild.yaml \
  --project ${PROJECT_ID} \
  .

echo -e "${BLUE}=======================================================${NC}"
echo -e "${GREEN}🎉 모든 배포 공정이 성공적으로 종료되었습니다!${NC}"
echo -e "🌐 사이트 주소: https://oksushi.net"
echo -e "📅 완료 시간: $(date)"
echo -e "${BLUE}=======================================================${NC}"