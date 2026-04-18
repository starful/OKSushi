FROM python:3.10-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

# 데이터 빌드 (content/*.md → items_data.json)
# 배포 전 로컬에서 script/item_generator.py 등을 실행해 md파일을 생성해두어야 합니다.
RUN python script/build_data.py

ENV PORT=8080
EXPOSE 8080

CMD exec gunicorn --bind :$PORT --workers 2 --threads 8 --timeout 120 app:app