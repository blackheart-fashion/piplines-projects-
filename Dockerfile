FROM python:3.12-slim
ARG APP_VERSION=dev
ARG DEMO_BROKEN=0
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION} DEMO_BROKEN=${DEMO_BROKEN} DATABASE_PATH=/data/tasks.db
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --create-home appuser \
    && mkdir /data && chown appuser:appuser /data
COPY app app
USER appuser
EXPOSE 8000
CMD ["waitress-serve", "--host=0.0.0.0", "--port=8000", "--call", "app.api:create_app"]
