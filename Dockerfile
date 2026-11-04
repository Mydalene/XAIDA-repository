FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd --system --gid 10001 xaida \
    && useradd --system --uid 10001 --gid 10001 \
        --home-dir /app --no-create-home --shell /usr/sbin/nologin xaida \
    && mkdir -p /app/.streamlit \
    && chown 10001:10001 /app/.streamlit

COPY --chown=10001:10001 . .

USER 10001:10001

EXPOSE 8080

CMD ["sh", "-c", "exec streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0"]