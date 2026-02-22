#!/usr/bin/env bash
set -euo pipefail

echo "=== CLARA-SSoT 개발 환경 설정 시작 ==="

# Git 설정 (이미 있으면 덮어쓰지 않기)
if ! git config --global user.name >/dev/null 2>&1; then
  git config --global user.name "Gibum Lee"
fi

if ! git config --global user.email >/dev/null 2>&1; then
  git config --global user.email "gibum@example.com"
fi

# Poetry PATH
export PATH="$HOME/.local/bin:$PATH"
if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' ~/.bashrc 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

# Poetry 설정
poetry config virtualenvs.in-project true

# 의존성 설치
if [ -f "pyproject.toml" ]; then
    echo "=== Poetry로 Python 의존성 설치 ==="
    poetry install
elif [ -f "requirements.txt" ]; then
    echo "=== pip으로 Python 의존성 설치 ==="
    pip install -r requirements.txt
fi

# 추가 개발 도구 설치 (Poetry 외부)
pip install dvc[s3,gs,azure,ssh,gdrive] black isort pylint pytest pytest-cov pytest-asyncio pre-commit

# DVC 초기화 (poetry 환경 사용)
if [ ! -d ".dvc" ]; then
    echo "=== DVC 초기화 ==="
    poetry run dvc init
    git add .dvc .dvcignore || true
fi

# Pre-commit 훅 설치 (poetry 환경 사용)
if [ -f ".pre-commit-config.yaml" ]; then
    echo "=== Pre-commit 훅 설치 ==="
    poetry run pre-commit install
fi

# Google Cloud 인증 설정 안내
echo ""
echo "============================================"
echo "  Gemini Code Assist 인증 설정"
echo "============================================"
if command -v gcloud &>/dev/null; then
    # gcloud 인증 상태 확인
    if gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q '@'; then
        echo "[OK] gcloud 인증이 이미 설정되어 있습니다."
    else
        echo "[INFO] Gemini Code Assist를 사용하려면 Google 인증이 필요합니다."
        echo ""
        echo "  다음 명령어를 터미널에서 실행하세요:"
        echo ""
        echo "    gcloud auth login"
        echo "    gcloud auth application-default login"
        echo ""
        echo "  또는 서비스 계정 키 파일이 있다면:"
        echo "    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json"
        echo ""
        echo "  인증 정보는 볼륨에 저장되므로 컨테이너를"
        echo "  재빌드해도 유지됩니다."
    fi
else
    echo "[WARN] gcloud CLI가 설치되지 않았습니다."
fi
echo "============================================"
echo ""

echo "=== 개발 환경 설정 완료 ==="
