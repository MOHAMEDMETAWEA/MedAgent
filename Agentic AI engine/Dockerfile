# Phase 14: Hospital-Grade Deployment (Dockerfile)
FROM python:3.10-slim-bullseye as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.10-slim-bullseye
WORKDIR /app

# Hardened Runtime
RUN groupadd -r medagent && useradd -r -g medagent medagent

COPY --from=builder /root/.local /home/medagent/.local
COPY . .

ENV PATH=/home/medagent/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

EXPOSE 5000
USER medagent

# Healthcheck for Hospital Reliability
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/system/capabilities || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "5000", "--workers", "4"]
