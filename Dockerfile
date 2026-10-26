FROM node:22-alpine@sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402 AS ui
WORKDIR /src/frontend
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 ROADSCAN_HOST=0.0.0.0 ROADSCAN_PORT=8000
WORKDIR /app
COPY requirements.txt requirements-lock.txt ./
RUN pip install --no-cache-dir -r requirements.txt -c requirements-lock.txt
ARG ROADSCAN_WITH_DETECTOR=0
LABEL io.roadscan.detector="${ROADSCAN_WITH_DETECTOR}"
COPY requirements-detector.txt requirements-detector-lock.txt ./
RUN if [ "$ROADSCAN_WITH_DETECTOR" = "1" ]; then \
      apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
      rm -rf /var/lib/apt/lists/* && \
      pip install --no-cache-dir torch==2.11.0+cpu torchvision==0.26.0+cpu --index-url https://download.pytorch.org/whl/cpu -c requirements-detector-lock.txt -c requirements-lock.txt && \
      pip install --no-cache-dir -r requirements-detector.txt -c requirements-lock.txt -c requirements-detector-lock.txt && \
      pip check; \
    fi
COPY third_party/ ./third_party/
COPY tools/fetch_dinov2.py ./tools/fetch_dinov2.py
COPY build_assets/ /opt/roadscan-models/
RUN if [ "$ROADSCAN_WITH_DETECTOR" = "1" ]; then \
      pip install --no-cache-dir faiss-cpu==1.15.1 -c requirements-detector-lock.txt -c requirements-lock.txt && \
      python tools/fetch_dinov2.py /opt/roadscan-models/dinov2_vits14_pretrain.pth && pip check; \
    fi
LABEL io.roadscan.release="2026-10-26.2"
COPY roadscan/ ./roadscan/
COPY runpod/ ./runpod/
COPY priority.py duplicate_finder.py accuracy_report.py ./
COPY static/ ./static/
COPY --from=ui /src/frontend/dist/ ./frontend/dist/
RUN useradd --create-home --uid 10001 roadscan && \
    mkdir -p /data /tmp/roadscan-ultralytics/Ultralytics /tmp/roadscan-matplotlib && \
    chown -R roadscan:roadscan /data /tmp/roadscan-ultralytics /tmp/roadscan-matplotlib
USER roadscan
WORKDIR /data
ENV DATABASE_URL=sqlite:////data/roadscan.db ROADSCAN_STORAGE=/data/private_uploads PYTHONPATH=/app:/app/third_party \
    ROADSCAN_DINO_WEIGHTS=/opt/roadscan-models/dinov2_vits14_pretrain.pth \
    YOLO_CONFIG_DIR=/tmp/roadscan-ultralytics MPLCONFIGDIR=/tmp/roadscan-matplotlib YOLO_AUTOINSTALL=false
EXPOSE 8000
CMD ["python","-m","roadscan.web_server"]
