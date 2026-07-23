FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ▼ Render用のポート（PORT環境変数）を公開する設定を追加 ▼
ENV PORT 10000
EXPOSE $PORT

CMD ["python", "main.py"]
