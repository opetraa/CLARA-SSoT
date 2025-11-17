FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    vim \
    wget \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-kor \
    libmagic1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# DVC 설치
RUN pip install --no-cache-dir dvc[s3,gs,azure,ssh,gdrive]==3.30.1

# Poetry 설치 (의존성 관리 도구)
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && echo 'export PATH="/home/vscode/.local/bin:$PATH"' >> /home/vscode/.bashrc

# 작업 디렉토리 설정
WORKDIR /workspace

# Python 개발 도구 설치
RUN pip install --no-cache-dir \
    black \
    isort \
    pylint \
    pytest \
    pytest-cov \
    pytest-asyncio \
    pre-commit

# DVC 캐시 디렉토리 생성
RUN mkdir -p /home/vscode/.dvc/cache && \
    chown -R vscode:vscode /home/vscode/.dvc

USER vscode
