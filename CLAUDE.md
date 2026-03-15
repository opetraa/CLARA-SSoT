<!-- ⚠️  자동 생성 파일 — 직접 편집하지 마세요.
     원본: .ai-rules/main.md + .ai-rules/claude/overrides.md
     수정 방법: 해당 파일을 편집한 뒤 `make sync-rules` 실행 -->

<!-- 
워크플로우:
.ai-rules/main.md 또는 overrides 편집
make sync-rules 실행 → CLAUDE.md + GEMINI.md 동시 업데이트
.ai-rules/ 파일이 포함된 commit 시 pre-commit 훅이 자동으로 sync 실행 — 생성 파일이 다르면 훅 실패 (git add 후 재커밋)
스크립트 특징:

stdlib만 사용 (poetry 환경 불필요)
내용이 바뀌지 않으면 파일을 건드리지 않음 (git diff 오염 방지)
--check 플래그로 pre-commit 훅에서 변경 감지 시 exit 1 
-->

# 프로젝트 개요
규제 도메인(원자력, 의료 등)용 데이터 중심 AI 아키텍처. PDF → JSON SSoT 파이프라인 + FastAPI 서버.

# 워크플로우 원칙
- IMPORTANT: 코드 생성 전 반드시 자연어로 의사결정 논리를 먼저 작성하고 확인받을 것
- 한 번에 하나의 함수/모듈만 구현. 모놀리식 출력 금지
- 새 기능은 반드시 테스트와 함께 작성
- 아키텍처 변경 전 반드시 질문할 것
- 코드 변경 완료 후 아래 문서 동기화 표를 참조해 관련 docs/ 업데이트 여부 확인

| 변경 대상 | 업데이트 대상 |
|---|---|
| 모듈 추가/삭제, 데이터 흐름 변경 | `docs/ARCHITECTURE.md` |
| 기능 추가/제거, 설계 목표 변경 | `docs/DESIGN.md` |
| 커맨드/의존성 변경 | `.ai-rules/main.md # 커맨드` |
| 환경 변수/인프라 변경 | `docker-compose.yml` + `.env.example` |
| AI 지시사항 추가 | `.ai-rules/main.md` 편집 후 `make sync-rules` 실행 |

# 시스템/설정 변경 시 에이전트 체크리스트
에이전트는 코드/설정 변경 시 **반드시** 아래 항목을 스스로 점검해야 합니다:
- [ ] Dockerfile에 새 시스템 패키지가 필요한가? (`libxml2-dev` 등 C 확장)
- [ ] `.devcontainer/devcontainer.json`의 `postCreateCommand`에도 동일하게 패키지를 추가했는가?
- [ ] `pyproject.toml`에 새 의존성 추가 시, `poetry lock` 또는 `make install`을 통해 lock 파일을 갱신했는가?
- [ ] 기존 import 경로나 함수명을 변경했다면, 프로젝트 전체(`src/tractara`, `tests/`)를 검색하여 참조하는 곳을 모두 수정했는가?
- [ ] glob 패턴 등 파일 시스템 접근 시 리눅스의 대소문자 구분을 고려했는가? (예: `*.xml` vs `*.XML`)
- [ ] 기존 스키마(`DOC_baseline_schema.json` 등)와 충돌하지 않는가?

# 코드 스타일
- Python 3.11+
- 포매터: black (line-length 88), isort (profile=black)
- 린터: pylint, mypy
- 타입 힌트 필수 (mypy strict 기준)

# 커맨드
```bash
make install      # 의존성 설치 (poetry install)
make test         # 테스트 실행 (pytest + coverage)
make lint         # pylint + mypy
make format       # black + isort
make run          # FastAPI 서버 실행 (port 8000)
make ingest       # 벌크 PDF 인제스트
make docker-up    # Docker Compose 실행
make sync-all     # DVC + Git 전체 동기화 (권장)
make sync-rules   # AI 규칙 동기화 (.ai-rules/ → CLAUDE.md, GEMINI.md)
```

# 참고 문서
docs/ARCHITECTURE.md 와 docs/DESIGN.md를 항상 참고하세요.

# 아키텍처 헌법 (Architecture Constitution)

아래 규칙은 AI 에이전트가 코드를 수정할 때 **절대 위반해서는 안 되는** 불변식입니다.
위반 시 pytest가 fail 하도록 `tests/test_golden_s1000d.py`와 `tests/test_schema_gatekeeper.py`에 대응하는 테스트가 존재합니다.
AI는 `make test`를 실행하여 모든 테스트가 통과(All Pass)할 때까지 코드를 수정해야 합니다.

## 금지 규칙 (MUST NOT)
1. `extensions` 필드에 데이터를 넣지 마라 — 스키마에서 제거됨
2. 스키마에 정의되지 않은 새로운 최상위 필드를 추가하지 마라 (`additionalProperties: false`)
3. `<note>` 태그를 `paragraph`로 매핑하지 마라 — 반드시 `blockType: "note"`
4. `<warning>` 태그를 `paragraph`로 매핑하지 마라 — 반드시 `blockType: "warning"`
5. `<caution>` 태그를 `paragraph`로 매핑하지 마라 — 반드시 `blockType: "caution"`
6. 빈 `<proceduralStep>`(텍스트/조건/액션 없음)은 블록으로 생성하지 마라

## 매핑 규칙 (MUST)
7. `structuredContent` 내 허용 키: `conditions`, `actions`, `acceptanceCriteria`, `applicTree`, `applicRefId`, `s1000d_dmCode`
8. `relationType`은 스키마 enum 또는 `custom:` 접두사 필수
9. `dc:language`는 BCP-47 형식 (예: `en`, `ko`, `en-US`)
10. 모든 `parentId`는 동일 문서 내 유효한 `blockId`를 참조해야 함

# 참고 문서
@docs/ARCHITECTURE.md
@docs/DESIGN.md
