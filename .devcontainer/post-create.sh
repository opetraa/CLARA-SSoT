#!/bin/bash
set -e

echo "🚀 Setting up CLARA-SSoT development environment..."

# Git 설정 (필요시 수정)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Poetry 설정
poetry config virtualenvs.in-project true

# 의존성 설치
if [ -f "pyproject.toml" ]; then
    echo "📦 Installing Python dependencies with Poetry..."
    poetry install
else
    echo "📦 Installing Python dependencies with pip..."
    pip install -r requirements.txt
fi

# DVC 초기화
if [ ! -d ".dvc" ]; then
    echo "📊 Initializing DVC..."
    dvc init
    git add .dvc .dvcignore
fi

# Pre-commit 훅 설치
if [ -f ".pre-commit-config.yaml" ]; then
    echo "🔧 Installing pre-commit hooks..."
    pre-commit install
fi

echo "✅ Development environment setup complete!"
