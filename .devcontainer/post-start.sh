#!/usr/bin/env bash
# post-start.sh: 컨테이너가 시작될 때마다 실행
# Gemini Code Assist 확장 설치 확인 및 인증 상태 점검

echo "=== 컨테이너 시작 점검 ==="

# Gemini Code Assist 확장 설치 확인 및 강제 설치
# devcontainer.json의 extensions 목록에서 설치에 실패하는 경우를 대비한 폴백
install_extension_if_missing() {
    local ext_id="$1"
    local ext_lower
    ext_lower=$(echo "$ext_id" | tr '[:upper:]' '[:lower:]')

    # code 또는 code-server CLI로 확장 설치 여부 확인
    if command -v code &>/dev/null; then
        if ! code --list-extensions 2>/dev/null | tr '[:upper:]' '[:lower:]' | grep -q "$ext_lower"; then
            echo "[INFO] $ext_id 확장이 감지되지 않았습니다. 설치 시도 중..."
            code --install-extension "$ext_id" --force 2>/dev/null || \
                echo "[WARN] $ext_id 확장 설치에 실패했습니다. VS Code에서 수동으로 설치해 주세요."
        else
            echo "[OK] $ext_id 확장이 설치되어 있습니다."
        fi
    fi
}

# Gemini Code Assist 확장 확인
install_extension_if_missing "Google.gemini-code-assist"

# gcloud 인증 상태 확인
if command -v gcloud &>/dev/null; then
    ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || true)
    if [ -n "$ACTIVE_ACCOUNT" ]; then
        echo "[OK] gcloud 인증 활성: $ACTIVE_ACCOUNT"
    else
        echo "[INFO] gcloud 인증이 필요합니다. 'gcloud auth login'을 실행하세요."
    fi

    # application-default credentials 확인
    ADC_FILE="$HOME/.config/gcloud/application_default_credentials.json"
    if [ -f "$ADC_FILE" ]; then
        echo "[OK] Application Default Credentials가 설정되어 있습니다."
    else
        echo "[INFO] Gemini Code Assist 자동 인증을 위해 다음을 실행하세요:"
        echo "       gcloud auth application-default login"
    fi
fi

# GOOGLE_APPLICATION_CREDENTIALS 환경 변수 확인
if [ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]; then
    if [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "[OK] GOOGLE_APPLICATION_CREDENTIALS가 설정되었습니다: $GOOGLE_APPLICATION_CREDENTIALS"
    else
        echo "[WARN] GOOGLE_APPLICATION_CREDENTIALS 파일을 찾을 수 없습니다: $GOOGLE_APPLICATION_CREDENTIALS"
    fi
fi

echo "=== 컨테이너 시작 점검 완료 ==="
