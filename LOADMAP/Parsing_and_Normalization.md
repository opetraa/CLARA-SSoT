
## Part 2. 데이터 수집 (Data Ingestion) 및 정규화 (Normalization)

Part 1의 1.2~1.3 단계를 구현 수준에서 상세화합니다. 현재 프로토타입은 **PDF 1개 → DOC/TERM Baseline JSON → Landing/SSoT 저장**까지의 엔드투엔드 Ingestion 파이프라인을 제공합니다.


### 2.1 파이프라인 오케스트레이터 (Pipeline Orchestrator)

전체 Ingestion을 단일 함수(`ingest_single_document`)로 제어합니다.

**실행 순서**: ① PDF 파싱 → ② DOC Baseline 생성 + 스키마 검증 → ③ Landing Zone 저장 + DOC SSoT 저장 → ④ TERM 후보 추출 + Landing 저장 → ⑤ TERM 병합 + 승격 필터링 + TERM SSoT 저장 → ⑥ 결과 요약 반환.

**진입점**: FastAPI 서버(`api/main.py`)에서 PDF 업로드 엔드포인트를 통해 트리거됩니다.


### 2.2 PDF 파싱 (Parsing)

비정형 PDF를 구조화된 `ParsedDocument`(블록 리스트 + 메타데이터)로 변환합니다.

#### 2.2.1 하이브리드 파서 전략 (Hybrid Parser Strategy)

안정성과 품질을 동시에 확보하기 위해 3-tier Fallback 전략을 적용합니다.

**① Docling (최우선)**: 표(table), 레이아웃, 계층 구조를 완벽하게 지원합니다. 자체 계층 정보를 제공하므로 SectionClassifier를 우회합니다.

**② PyMuPDF (텍스트 기반 fallback)**: Docling 실패 시 PyMuPDF(`pymupdf`)로 텍스트를 추출합니다. 다중 단계 파싱 파이프라인을 수행합니다: Phase 0(본문 폰트 크기 추정, PDF 북마크 수집) → Phase 1(페이지별 블록 추출 + SectionClassifier 적용) → Phase 2(ToC 페이지 탐지 및 섹션 엔트리 파싱).

**③ Gemini Vision (스캔본 전용)**: 스캔된 문서나 복잡한 표 처리를 위한 VLM(Vision-Language Model) 백업입니다. PDF를 이미지로 변환 후 `gemini-3-flash-preview`에게 구조화를 요청합니다 (비용 발생).

#### 2.2.2 섹션 분류기 (Section Classifier)

PyMuPDF 파서와 함께 동작하며, 각 텍스트 블록을 제목/본문/표 등으로 분류합니다.

**입력**: 블록의 시각적·텍스트적 특징(`SectionFeatures` — 폰트 크기, 볼드 여부, 좌표, 폰트명 등).

**분류 전략**: 다중 힌트(북마크, ToC 매칭, 폰트 크기, 섹션 번호 패턴) 가중합 스코어링 방식을 사용합니다. 임계치(score ≥ 70) 이상이면 heading으로 분류하고, 문장부호(-50)·긴 텍스트(-30) 패널티를 적용합니다.

**섹션 번호 패턴**: 숫자형(`1.2.3`), 한국어형(`제1장`), 알파숫자형(`A.1`), 영문 부록(`Appendix A`), 한글 목록(`가.`) 5종을 지원합니다.

#### 2.2.3 메타데이터 추출기 (Metadata Extractor)

Dublin Core 기반 메타데이터를 **듀얼트랙(Dual-Track)** 방식으로 추출합니다.

**Phase 1 — Front-Matter Isolation**: 처음 4페이지 + 마지막 2페이지만 대상으로 분리합니다.

**Phase 2 — 병렬 추출**:

**Track A (결정론적 규칙 엔진)**: 제목은 폰트 크기·볼드·중앙 정렬·위치 등 다중 특징 스코어링으로 선택합니다. 문서 번호(identifier)는 정규식 기반으로 표지 전체 또는 이후 페이지의 헤더/푸터 영역에서 추출합니다. 주 언어 판별은 한글 문자 비율로 Early Exit 방식 감지합니다.

**Track B (LLM 의미론적 추출)**: Gemini + Instructor로 creator, publisher, date, subject, coverage, document type 등 의미론적 메타데이터를 Pydantic 모델(`LLMMetadata`)에 구조화하여 추출합니다. 실패 시 Track A 결과만으로 graceful fallback 합니다.

**Phase 3 — 결과 병합**: title/identifier는 Track A 우선, creator/publisher/date/language/type/subject/coverage는 Track B 전담. enum 범위 이탈 값과 날짜 형식 오류는 무효 처리합니다.


### 2.3 정규화 (Normalization)

파싱 결과를 DOC/TERM 두 가지 스키마로 변환합니다.

#### 2.3.1 DOC Mapper

`ParsedDocument` → DOC Baseline JSON을 생성합니다.

**메타데이터 매핑**: `metadata_extractor.extract_metadata()`를 호출하여 Dublin Core 메타데이터를 채웁니다. 필수 필드(`dc:title`, `dc:type`, `dc:language`)에는 fallback 값을 설정합니다.

**콘텐츠 변환**: 각 `ParsedBlock`을 `blockId`, `parentId`, `blockType`, `text`, `contextPath`, `level`, `sectionLabel`, `sectionTitle` 등의 필드를 가진 content 배열로 변환합니다. 스키마 enum에 없는 blockType은 `"paragraph"`로 강제합니다.

**Provenance 기록**: 원본 파일 경로, 파서 버전, 추출 날짜, OCR 적용 여부, 신뢰도 등을 기록합니다.

#### 2.3.2 TERM Mapper

`ParsedDocument`에서 TERM 후보를 추출하고 Baseline JSON으로 변환합니다.

**추출 전략 (LLM 기반)**: Gemini + Instructor를 사용하여 CoT(Chain of Thought) + Pydantic 구조화 출력(`TermExtractionResult`)으로 전문용어를 추출합니다. 각 청크별로 `term`, `headword_en`, `definition_en`, `definition_ko`, `domain`, `context` 필드를 수집합니다.

**모델 선택**: API 키로 접근 가능한 모델 중 최적의 모델을 자동 선택합니다.

**termId 생성**: 강타입 URN 형식(`term:class:{normalized_headword_en}`)으로 생성합니다. 영문 소문자 + 언더스코어 정규화를 적용하며, TERM-CLASS / TERM-REL / TERM-RULE 타입별로 prefix가 결정됩니다.


### 2.4 검증 (Validation)

정규화된 데이터가 SSoT에 진입하기 전에 품질을 보증합니다.

#### 2.4.1 JSON Schema 검증

`DOC_baseline_schema.json`과 `TERM_baseline_schema.json`을 기반으로 Draft7 표준 검증을 수행합니다.

**에러 모델**: 검증 실패 시 `ProblemDetails` + `MachineReadableError` 구조로 반환합니다. 각 에러에 `validator`, `expected`, `actual`, `path`, `errorClass` 정보를 포함하여 LLM이 누락 필드와 수정 방법을 파악할 수 있도록 합니다.

#### 2.4.2 TERM 승격 검증

TERM이 SSoT로 승격될 수 있는지 **필수 필드 검증 + 스키마 검증** 2단계로 판단합니다.

**필수 필드**: `definition_en` (최소 10자). `[PENDING...]` 플레이스홀더도 미충족으로 간주합니다.

**상태 결정 매트릭스**: 신뢰도(x축) × 완성도(y축) 기반으로 `candidate` → `anchored` → `mature` | `rejected` 4단계 상태를 결정합니다.


### 2.5 Landing Zone 저장

스키마 검증을 통과한 원본 JSON을 보관합니다.

**DOC 저장**: `data/landing/docs/{documentId}.json` 형식으로 저장합니다.

**TERM 저장**: `termType`별 서브디렉토리로 분리합니다 (`data/landing/terms/class/`, `rel/`, `rule/`). 파일명은 `C_{TERM}_{termId segment}.json` 형식입니다.


### 2.6 TERM 큐레이션 (Curation)

여러 문서에서 나온 TERM 후보를 병합하고 중복을 제거합니다.

**그룹핑 키**: `(term, termType)` 복합 키를 사용합니다. 같은 단어가 CLASS(개념)와 REL(관계)로 다르게 분류될 수 있으므로 타입별로 분리 병합합니다.

**병합 규칙**: `definition_en/ko`가 비어있거나 `[PENDING...]`이면 다른 후보의 값으로 채워넣고, `slots.*`은 '없으면 채우기' 방식으로 병합합니다.

**파일명 생성**: `[상태]_[TermID]_v[버전].json` 규칙을 따릅니다 (예: `M_AMP_v1.1.json`).


### 2.7 SSoT 적재 (SSoT Promotion)

승격된 데이터를 단일 진실 공급원에 영구 저장합니다.

**DOC SSoT**: `data/ssot/docs/{documentId}.json`에 upsert(저장/갱신) 합니다.

**TERM SSoT**: `termType`별 서브디렉토리(`data/ssot/terms/class/`, `rel/`, `rule/`)에 `{termId segment}.json` 파일명으로 upsert 합니다.


### 2.8 DVC 파이프라인 (Reproducibility)

전체 파이프라인이 DVC(`dvc.yaml`)로 재현 가능하게 관리됩니다.

**파이프라인 스테이지**: `prepare_data` → `parse_documents` → `validate_terms` → `normalize_data` → `build_ssot`. 각 스테이지별로 `deps`(의존 파일), `params`(하이퍼파라미터), `outs`(출력 디렉토리)가 정의되어 있습니다.

**데이터 흐름**: `data/raw` → `data/prepared` → `data/parsed` → `data/validated` → `data/normalized` → `data/ssot`.


### 2.9 향후 비전 (Future Vision) (추후 스킬로 옮기기)

1. 블록 단위의 초정밀 추적성 확보 (Granular Traceability for Compliance)
규제 기관 심사(예: 원자력안전위원회, KINS) 및 EU AI Act의 투명성 요구에 대응하기 위해, 파싱 단계부터 원본과의 완벽한 맵핑을 구현하는 방향으로 진화해야 합니다.

- 원본 PDF의 페이지 번호와 X,Y 좌표를 DOC Baseline의 메타데이터에 기록하였으니 이를 이용하여 나중에 환각(Hallucination) 검증 시 원본 문서의 정확한 위치를 시각적으로 하이라이트할 수 있어야 합니다.

- 다단 파생 이력 추적 (Multi-hop Lineage): 비정형 데이터가 Landing Zone을 거쳐 RAG Chunk나 KG Triples로 쪼개질 때, 최초 부모 블록의 trace_id를 꼬리표처럼 끝까지 물고 가도록 DVC 파이프라인과 연동해야 합니다. 이를 통해 최종 답변에서 오류가 나도 어떤 파싱 단계에서 잘못되었는지 역추적할 수 있습니다.

2. ACT-R 인지 모델을 위한 절차적 지식 추출 (Procedural Knowledge Extraction)
단순한 문서 구조화(제목/본문/표)를 넘어, 에이전트(Tractara-Agent)가 파괴역학 기반의 다단계 추론을 할 수 있도록 파서가 규칙 자체를 뜯어내야 합니다.

절차적 블록(procedureStep) 인식: 파서의 Section Classifier를 고도화하여, 피로 평가나 결함성장평가 같은 맥락이 등장할 때 조건(If)과 결과(Then)를 식별하고 이를 TERM-RULE 스키마에 맞춰 자동 구조화하는 로직이 추가되어야 합니다.

변수 및 제약 조건 매핑: 파싱 단계에서 온도, 응력, 재질(예: 316SS) 같은 핵심 파라미터를 LLM 기반 추출기(Metadata Extractor)가 식별하여, 단순 텍스트가 아닌 domain_constraints나 range_constraints 필드에 엄격히 매핑하는 정규화 과정이 필요합니다.

3. 지식 그래프(KG) 전개를 위한 관계망 선제 구축 (Proactive Relational Mapping)
문서가 SSoT에 적재된 후 RAG 단계에서 고민하는 것이 아니라, 파싱되어 들어오는 시점부터 관계(Relation)를 식별하여 Neo4j 적재 준비를 마쳐야 합니다.

내/외부 참조의 구조화 (Cross-reference Parsing): 문서 내부의 "표 1.2 참조"나 "ASME Code Sec. XI에 따라" 같은 문구를 정규식이나 LLM으로 감지하여, DOC Baseline의 relations 배열에 sourceBlockId와 target으로 즉시 연결하는 로직을 파이프라인에 추가해야 합니다.

동적 분류체계(Taxonomy) 바인딩: 규제 문서나 평가 보고서가 유입될 때, 미리 정의된 어휘집(Vocab)과 대조하여 이 문서가 어떤 계통이나 설비에 대한 것인지 태깅하는 작업을 Metadata Extractor의 Track B(의미론적 추출)의 필수 과제로 굳혀야 합니다.

4. 인간-AI 협업 기반의 적응형 SSoT (Adaptive SSoT with HITL)
파이프라인이 한 번 파싱하고 끝나는 일방향 흐름을 넘어, 전문가의 검수 피드백이 시스템 전체를 진화시키는 루프를 만들어야 합니다.

전문가 개입 핫스팟(HITL) 설계: Validator에서 승격이 거부되거나 파싱 신뢰도가 낮은 엣지 케이스가 발생했을 때, 도메인 전문가가 개입해 교정할 수 있는 API 엔드포인트와 인터페이스를 파이프라인 중간(Curation Area)에 공식적으로 설계해야 합니다.

피드백 역전파 (Feedback Backpropagation): MVP 테스트나 실제 심사 과정에서 오류가 발견되어 수정된 로직이나 메타데이터가 단발성으로 끝나지 않도록 해야 합니다. 수정 사항이 파이프라인을 역류해 파서의 규칙 모음집이나 LLM 프롬프트를 자동 업데이트하도록 MLOps 아키텍처를 진화시켜야 합니다.
