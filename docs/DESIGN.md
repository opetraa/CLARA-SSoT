# DESIGN

## 목표
규제가 강한 도메인(원자력, 의료, S1000D 항공/방산 등)에서 문서 데이터를 신뢰할 수 있는 단일 진실 공급원(SSoT)으로 관리한다.
LLM이 소비하기 좋은 구조화된 JSON으로 변환하고, 검증 실패 시 LLM이 스스로 보정할 수 있는 에러 정보를 제공한다.

## 현재 구현 범위

### ✅ 구현 완료

- **PDF Ingestion 파이프라인** — 3단계 하이브리드 파서 (Docling → PyMuPDF → Gemini Vision)
- **XML Ingestion 파이프라인** — JATS 학술 논문, S1000D 기술 문서 파싱
- **YAML 카탈로그 기반 파싱 전략** — 포맷별 매핑 규칙을 코드 외부(YAML)로 분리
- **Dublin Core 메타데이터 추출** — 이중 트랙 전략 (Track A: 결정론적 규칙 + Track B: LLM/Gemini)
- **DOC Baseline JSON 생성** — 계층 블록 구조, 추적성 필드(sourceXPath), Fragment Store 포인터
- **TERM 후보 추출** — LLM 기반 CoT + Instructor + Pydantic 구조화 출력
- **TERM 타입 체계** — TERM-CLASS/REL/RULE 강타입 URN 식별자
- **Landing Zone → SSoT 승격 파이프라인** — 검증 → Landing 저장 → 병합 → 필터 → SSoT 저장
- **JSON Schema 검증** — DOC/TERM Baseline Schema (Draft 7, `additionalProperties: false`)
- **TERM 시맨틱 웹 레이어 (인프라)** — Owlready2(OWL/SWRL), RDFLib, pySHACL을 이용한 온톨로지 매핑·추론·검증 인프라 구현 완료. 수동 분류된 TERM-REL/RULE 소비 가능.
- **에러 모델** — RFC 7807 `ProblemDetails` + `MachineReadableError` (LLM-friendly)
- **FastAPI 서버** — PDF/XML 인제스트 엔드포인트 + 에러 핸들링 + trace/span 추적
- **벌크 인제스트 스크립트** — `make ingest` 로 data/ 폴더 내 PDF/XML 일괄 처리
- **아키텍처 헌법** — pytest 기반 golden test + schema gatekeeper (불변식 자동 검증)
- **Fragment Store** — 원본 XML 조각 O(1) 접근 (FileFragmentStore + Redis 전환 대비 Protocol)
- **S1000D 전용 기능** — dmCode 파싱, applic 트리 구조화, 절차 단계(proceduralStep) 중첩 파싱, preliminaryRqmts/closeRqmts 처리

### 🚧 미구현 / 부분 구현

- **S1000D 4.1 → 5.0 마이그레이션** — 3-Layer 아키텍처 설계 완료, 구현 미착수
- **Redis Fragment Store** — Protocol 정의 + Stub 구현 완료, 실제 Redis 연동 미구현
- **TERM-REL / TERM-RULE LLM 자동 분류** — 온톨로지 레이어(OWL/SWRL)는 구현됨, 그러나 `term_mapper.py`의 LLM 추출 시 모든 TERM을 TERM-CLASS로 고정. LLM이 REL/RULE을 구분하여 출력하도록 프롬프트 및 파이프라인 개선 필요 (별도 이슈)
- **LLM 기반 자동 보정 루프** — 에러 모델은 LLM-friendly 설계 완료, 보정 루프 미구현
- **멀티 도큐먼트 충돌 해소** — TERM 병합은 구현, 문서간 충돌 해소 전략 미구현

---

## 기능 요구사항

### Ingestion 파이프라인

| 기능 | 상태 | 구현 위치 |
|---|---|---|
| PDF 파싱 (하이브리드 3단계) | ✅ | `parsing/pdf_parser.py` |
| XML 파싱 (JATS + S1000D) | ✅ | `parsing/xml_parser.py` |
| YAML 카탈로그 포맷 감지 | ✅ | `catalogs/catalog_loader.py` |
| 변환 함수 레지스트리 | ✅ | `catalogs/transforms.py` |
| 메타데이터 추출 (Track A + B) | ✅ | `parsing/metadata_extractor.py` |
| DOC Baseline JSON 변환 | ✅ | `normalization/doc_mapper.py` |
| TERM 후보 추출 (LLM CoT) | ✅ | `normalization/term_mapper.py` |
| JSON Schema 검증 | ✅ | `validation/json_schema_validator.py` |
| TERM 승격 검증 | ✅ | `validation/term_validator.py` |
| TERM 시맨틱 검증 (pySHACL) | ✅ | `validation/shacl_validator.py` |
| 온톨로지 동적 매핑 (OWL) | ✅ | `ontology/term_ontology.py` |
| 논리 규칙 추론기 (SWRL) | ✅ | `ontology/term_rules.py` |
| Landing Zone 저장 | ✅ | `landing/landing_repository.py` |
| TERM 병합/중복 제거 | ✅ | `curation/term_curation_service.py` |
| DOC/TERM SSoT 저장 | ✅ | `ssot/doc_ssot_repository.py`, `ssot/term_ssot_repository.py` |
| Fragment Store (원본 XML) | ✅ | `ssot/fragment_store.py` |

### API 서버

| 기능 | 상태 | 구현 위치 |
|---|---|---|
| PDF 업로드 + Ingestion | ✅ | `api/main.py` POST `/ingest` |
| XML 자동 감지 + Ingestion | ✅ | `api/pipeline.py` |
| 온톨로지 로드 및 추론 (제어점) | ✅ | `api/ontology_router.py` POST `/ontology/...` |
| 헬스체크 | ✅ | `api/main.py` GET `/health` |
| 스키마 검증 에러 핸들링 | ✅ | `api/main.py` exception handler |
| 분산 트레이싱 (trace/span) | ✅ | `tracing.py` |
| SSoT DOC/TERM 조회 엔드포인트 | 🚧 | 미구현 (파일 직접 접근만 가능) |

### 에러 모델

| 기능 | 상태 |
|---|---|
| RFC 7807 ProblemDetails | ✅ |
| MachineReadableError (code/target/detail/meta) | ✅ |
| error_class 분류 (user_input / system_bug / dependency) | ✅ |
| LLM-friendly 필드 힌트 (expected/actual/path) | ✅ |

---

## 파싱 아키텍처 상세

### PDF 파서 계층 (3-Tier Hybrid)

```
┌────────────────────────────────────────────────┐
│ 1. DoclingParser (메인)                         │
│    - 표, 레이아웃, 계층 구조 전문               │
│    - GPU 가속 지원 (CUDA, MPS)                  │
│    - 표 구조 자동 추출 (DataFrame → Markdown)    │
├────────────────────────────────────────────────┤
│ 2. PyMuPDFParser (보조)                         │
│    - SectionClassifier 기반 블록 분류           │
│    - 수식 탐지/분할 (인라인 수식 분리)          │
│    - 누락 수식 보충 (surgical supplement)       │
├────────────────────────────────────────────────┤
│ 3. GeminiVisionParser (백업)                    │
│    - 스캔 문서 / OCR 필요 문서                  │
│    - 수식 영역 크롭 후 LaTeX 변환               │
└────────────────────────────────────────────────┘
```

### XML 파서 전략 패턴

```
parse_xml(file_path)
  │
  ├── catalog_loader.detect_catalog(root_tag)
  │     → YAML 매핑 발견 시: CatalogDrivenStrategy
  │     → 미발견 시:          GenericXmlStrategy
  │
  ├── CatalogDrivenStrategy
  │     - YAML 규칙 기반 블록 생성 (section, paragraph, note, warning, caution, procedureStep 등)
  │     - 메타데이터 추출: _apply_catalog_metadata()
  │     - 관계 추출: relations[] (CITES, GOVERNED_BY_APPLIC, COMPLIES_WITH 등)
  │     - S1000D 전용: applic 트리, dmCode, preliminaryRqmts/closeRqmts
  │
  └── GenericXmlStrategy
        - 전체 텍스트를 하나의 paragraph로 처리 (fallback)
```

### 메타데이터 추출 (Dual-Track)

```
PDF 파일 → _extract_frontmatter_blocks() → 처음 4p + 마지막 2p
  ├── Track A (결정론적)
  │     - dc:title: 폰트 크기/볼드/위치 스코어링
  │     - dc:identifier: 정규식 패턴 매칭 (NUREG, DOI 등)
  │
  └── Track B (LLM/Gemini)
        - dc:creator, dc:publisher, dc:date 등 의미론적 필드
        - Instructor + Pydantic 구조화 출력
        - 실패 시 Track A로 graceful fallback

XML 파일 → _apply_catalog_metadata()
  ├── YAML 카탈로그 규칙 적용
  └── Dublin Core 네임스페이스 dc: 요소 추출 → merge
```

---

## TERM 타입 체계

```
TERM
 ├── TERM-CLASS  개념 (명사)        term:class:<name>
 │     예) OperatingTemperature, AMP, SCC
 ├── TERM-REL    관계 (동사/서술어)  term:rel:<name>
 │     예) exceeds_threshold, requires_inspection
 └── TERM-RULE   규칙 (조건-결과형)  term:rule:<name>
       예) amp_inspection_interval_rule
```

- 강타입 URN prefix로 외래 키 참조 시 타입 안전성 보장
- Pydantic `TermClassReference` / `TermRelReference` / `TermRuleReference` 모델
- 현재 LLM 추출 시 모든 TERM은 TERM-CLASS로 기본 설정 (온톨로지 인프라는 준비됨, `term_mapper.py` LLM 프롬프트 개선으로 자동 분류 예정)

---

## 아키텍처 헌법 (불변식)

코드 변경 시 반드시 `make test`로 검증해야 하는 규칙:

| # | 규칙 | 검증 테스트 |
|---|---|---|
| 1 | `extensions` 필드 사용 금지 | `test_schema_gatekeeper.py` |
| 2 | 스키마 미정의 최상위 필드 추가 금지 | `test_schema_gatekeeper.py` |
| 3 | `<note>` → `blockType: "note"` | `test_golden_s1000d.py` |
| 4 | `<warning>` → `blockType: "warning"` | `test_golden_s1000d.py` |
| 5 | `<caution>` → `blockType: "caution"` | `test_golden_s1000d.py` |
| 6 | 빈 `<proceduralStep>` 블록 생성 금지 | `test_golden_s1000d.py` |
| 7 | `structuredContent` 허용 키 제한 | `test_schema_gatekeeper.py` |
| 8 | `relationType` enum 또는 `custom:` prefix 필수 | `test_schema_gatekeeper.py` |
| 9 | `dc:language` BCP-47 형식 | `test_golden_s1000d.py` |
| 10 | `parentId` 동일 문서 내 유효 `blockId` 참조 | `test_golden_s1000d.py` |

---

## 설계 결정

| 결정 | 이유 |
|---|---|
| JSON Schema 기반 검증 | 규제 도메인 특성상 스키마 엄격성 필요 |
| Landing Zone 분리 | 원본 보존 + SSoT 품질 보장 |
| TERM 승격 단계 분리 | 자동 추출과 신뢰 가능한 SSoT 사이의 품질 게이트 |
| ProblemDetails 에러 모델 | LLM 기반 자동 보정 루프 설계 고려 |
| DVC + Git 이중 관리 | 대용량 데이터(PDF, 모델)는 DVC, 코드/스키마는 Git |
| YAML 카탈로그 분리 | 새 XML 포맷 추가 시 코드 수정 없이 YAML만 추가 |
| 3-Tier PDF 파서 | 정확도/속도 균형 + 스캔 문서 지원 |
| Dual-Track 메타데이터 | 결정론적 정확도(title/id) + LLM 의미론적 추출 이점 결합 |
| Fragment Store Protocol | SSoT JSON 경량화 + 원본 추적성 양립, Redis 전환 용이 |
| 강타입 TERM URN | 외래 키 레벨에서 타입 불일치 원천 방지 |
| 아키텍처 헌법 (pytest) | AI 에이전트의 스키마 위반을 자동 감지 및 차단 |

## 미결 과제 (TODO)

- S1000D 4.1 → 5.0 마이그레이션 레이어 구현
- Redis Fragment Store 연동
- TERM-REL / TERM-RULE 자동 분류 (LLM 기반)
- LLM 기반 자동 보정 루프 (ProblemDetails → 수정 요청 → 재검증)
- 멀티 도큐먼트 충돌 해소 전략
- SSoT DOC/TERM 조회 API 엔드포인트
- FormulaVariable / FormulaConstraint 도메인 모델 (formula_parser 단계)
