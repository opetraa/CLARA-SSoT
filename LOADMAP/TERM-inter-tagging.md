# 결정론적 구조화 청킹 및 용어 교차 태깅 방법론

> 고규제 도메인 AI를 위한 환각 없는 시멘틱 청킹의 타당성 및 확장 가능성 평가 보고서


## 핵심 제안

비정형 문서를 SSoT로 변환할 때 **LLM 개입을 최소화**하고, 결정론적 알고리즘으로 메타데이터를 생성하는 두 가지 방법론:

1. **구조적 청킹(Structural Chunking)** — 문서의 시각적·논리적 구조(목차, 대제목, 좌표)로 청크 분할
2. **용어 교차 태깅(Term-Intersection Tagging)** — 청크 내 TERM들의 공통 속성 교집합으로 메타데이터 역추론

---

## 1. 문제: 메타데이터 생성의 역설

### 1.1 SSoT 구축 과정의 딜레마

DOC 스키마는 Dublin Core·JATS 표준에 따른 메타데이터를 요구하지만, 현장의 기술 문서(PSR, 안전성 평가 보고서 등)는 대부분 **비구조화된 PDF 또는 이미지 스캔본**이다.

이 **메타데이터 공백(Metadata Gap)**을 LLM으로 메우면:

- LLM은 사실을 '조회'가 아닌 확률적으로 '생성' → **없는 날짜를 만들어내거나(Confabulation)** 잘못된 분류를 할당
- 오염된 메타데이터가 SSoT에 등록되는 순간, 이에 기반한 모든 검색·추론·답변이 왜곡

> [!CAUTION]
> SSoT 구축 단계에서의 LLM 환각은 시스템 전체 신뢰도를 붕괴시키는 **'독 사과(Poisoned Apple)'**가 된다.

### 1.2 규제적 요구

EU AI Act는 "AI가 왜 그렇게 판단했는가?"에 대해 **결정론적 인과 사슬(Causal Chain)**을 요구한다:

```
"문서 A의 34페이지 두 번째 단락에 근거하였으며,
 해당 단락은 구조적 파싱 규칙 B에 의해 추출되었고,
 용어 사전 C에 정의된 용어 D가 포함되어 있어
 메타데이터 E로 분류되었다"
```

→ 결정론적 방법론은 이런 인과 사슬을 **코드 레벨에서 구현** 가능하므로, 규제 준수 측면에서 LLM 기반 방식보다 **월등히 우월**하다.

---

## 2. 제안 1: 구조적 패턴 기반 청킹 (Structural Chunking)

문서를 단순한 1차원 문자열이 아닌, **2차원 공간에 배치된 계층적 구조체**로 해석한다.

### 2.1 JATS 표준과의 정합성

JATS(Journal Article Tag Suite)는 문서를 `<front>`(메타데이터) → `<body>`(본문) → `<back>`(참고문헌)으로 나누고, 본문을 `<sec>`, `<title>`, `<p>`, `<table-wrap>` 등으로 계층화한다.

**구조적 청킹은 원본 PDF를 JATS XML 트리로 역공학(Reverse Engineering)하는 과정과 일치한다.**

| 입력 신호 | 추론 결과 | 근거 |
|---|---|---|
| 폰트 크기 크고 Bold + 페이지 상단 중앙 | `<title>` (대제목) | BBox 좌표 분석 |
| 들여쓰기 + 숫자/불릿으로 시작 | `<list-item>` (목록 항목) | 텍스트 패턴 매칭 |
| PDF 아웃라인(Bookmark) 또는 목차 페이지 | 문서 뼈대(Skeleton) | 구조적 파싱 |

→ 기계적 토큰 수(500자)가 아닌, **저자가 의도한 의미 단위(섹션)**별로 분할 → **의미적 완결성 보장**


### 2.2 'Lost in the Middle' 문제의 결정론적 해결

기존 단순 청킹은 문맥 소실 문제를 유발한다. 일부 RAG는 LLM에게 "문맥을 요약해달라"고 요청하지만, 이는 다시 환각 위험을 초래한다.

**구조적 청킹의 해법 — 상속(Inheritance) 메커니즘:**

```
청크 내용: "이 밸브는 매주 점검해야 한다."

상속된 메타데이터 (트리 순회 알고리즘으로 자동 생성):
  Section: 4. 비상 냉각 계통
  Subsection: 4.2. 유지보수 지침
```

→ 확률적 추론이 아닌 **트리 순회(Tree Traversal)** 알고리즘에 의한 명확한 논리 연산 → **환각 발생 불가능**


### 2.3 DOC 스키마와의 연결

DOC 스키마가 포함해야 할 필수 필드:

| 필드 | 역할 | 채우는 수단 |
|---|---|---|
| `blockType` | header, paragraph, table 등 분류 | 레이아웃 분석 |
| `level` | 계층 깊이 (h1=1, h2=2...) | 목차/폰트 크기 |
| `parentId` | 상위 섹션 ID | 트리 구조 |
| `bbox` | 원본 좌표 (x0, y0, x1, y1) | PDF 파서 |

→ 모든 값을 **결정론적으로** 채울 수 있는 유일한 수단


### 2.4 구현 도구

| 도구 | 특징 |
|---|---|
| **Docling** (IBM) | 레이아웃 보존 PDF → JSON/MD 변환. 표·다단 처리 강점 |
| **Unstructured** | 'Title', 'NarrativeText', 'Table' 등 요소 분류(Partitioning) |
| **LayoutParser** | 딥러닝 기반 문서 영역 객체 탐지 |

---

## 3. 제안 2: 용어 교차 기반 태깅 (Term-Intersection Tagging)

청크 내 단어를 TERM 스키마와 대조하여, 텍스트가 내포한 **주제·속성을 결정론적으로 도출**한다.

### 3.1 이론적 토대: 집합론 기반

문서 청크 `C`를 포함된 용어 집합 `T_C = {t₁, t₂, ..., tₙ}`으로 정의. 각 용어 `t`는 TERM 스키마에서 속성 집합 `A(t)`를 가진다.

**교집합 로직 (Intersection Logic):**

```
청크 내 발견된 용어:
  • "피로(Fatigue)"
  • "부식(Corrosion)"
  • "균열 성장(Crack Growth)"

세 용어의 공통 상위 개념 (Taxonomy):
  → "경년열화 메커니즘(Aging Mechanism)"

결과:
  Topic: Aging Mechanism  ← 자동 태깅
```

**추론 규칙 (Inference Rule):**

```
IF (Contains "TLAA") AND (Contains "License Renewal")
THEN Tag {RegulatoryContext: "LTO"}
```

→ LLM이 문맥을 '읽고' 판단하는 것이 아니라, 시스템이 정의된 규칙에 따라 **'계산'** → 결과가 항상 일정(Idempotent) + 설명 가능


### 3.2 온톨로지 전파 (Ontology Propagation)

TERM 스키마에 Taxonomy Bindings와 Slots가 정의되어 있으면, **문서에 핵심 단어가 직접 등장하지 않아도** 하위 용어 조합으로 상위 개념을 추론할 수 있다.

```
TERM 스키마 정의:
  "금속 피로", "환경 피로", "LBB 해석" → 모두 TLAA 카테고리

문서에서 발견:
  "금속 피로 해석 결과..."

추론:
  → Category: TLAA  (문서에 "TLAA"라는 단어 없이도 자동 태깅)
```

### 3.3 환각 제로(Zero-Hallucination)와 감사 대응

시스템은 **통제된 용어집(Controlled Vocabulary)**에 존재하는 단어만 인식하고, 정의된 로직으로만 태그를 부여한다. 모르는 단어에 대해서는 "알 수 없음"으로 처리하며, **없는 사실을 지어내지 않는다.**

```
감사(Audit) 시 소명 예시:

  Q: "이 문서는 왜 '경년열화 관리'로 분류되었는가?"
  A: "청크 내에 'Fatigue', 'Wear', 'Embrittlement'가 검출되었으며,
     이들은 SSoT TERM 스키마 v1.2에서 모두 '경년열화 메커니즘'의
     하위 개념으로 정의되어 있기 때문입니다."
```

### 3.4 구현 도구

| 도구 | 특징 | 성능 |
|---|---|---|
| **FlashText** | 고속 키워드 매칭 | 수만 개 용어를 밀리초 단위 스캔 |
| **Aho-Corasick** | 다중 패턴 동시 매칭 | O(n) 시간 복잡도 |
| **spaCy Rule-based Matcher** | 패턴 기반 NER | 유연한 규칙 정의 |

→ LLM 대비 **압도적 비용 절감** (문서 전체를 LLM으로 읽는 비용 대비)

---

## 4. 확장 가능성: 환각 없는 시멘틱 청킹의 고도화

### 4.1 지식 그래프(KG) + GraphRAG 통합

```
확장 구조:

  청크 A ──[상위 섹션]──→ 청크 B
    │                        │
    └─[용어 '서지라인' 언급]──→ TERM 노드
                                  │
    └─[용어 '피로' 언급]────→ TERM 노드
```

- 각 청크를 KG **노드**로, 구조적·용어 기반 관계를 **엣지**로 연결
- 벡터 유사도 검색 + **그래프 순회(Traversal)**를 결합한 GraphRAG 구현
- LLM 추론 의존 없이 **데이터 구조 자체에서 정답 탐색** → 환각 없음


### 4.2 Parent-Document Retriever (PDR) 이중화

| 계층 | 단위 | 용도 |
|---|---|---|
| **자식 청크** | 문장/문단 단위 | 정밀 검색 (고밀도 메타데이터 태깅) |
| **부모 청크** | JATS `<sec>` 전체 섹션 | LLM 컨텍스트 제공 (원본 그대로) |

- 검색은 자식 청크로 **정밀하게(Precision)**
- LLM에 넘기는 컨텍스트는 부모 청크로 **완전하게(Recall)**
- → 단편적 정보에 의한 LLM 오판 방지


### 4.3 VLM의 제한적 활용 (Layout Analysis Only)

복잡한 표·다단 편집 문서에서 규칙 기반 파서의 한계를 보완:

| 허용 | 차단 |
|---|---|
| VLM(예: LayoutLMv3)이 **좌표(BBox)만** 출력 | VLM이 텍스트를 읽거나 요약 |
| 좌표 내 텍스트 추출은 **결정론적 OCR**(Tesseract) | AI가 내용을 해석·생성 |

→ **AI의 인지 능력은 활용하되 생성 능력은 차단** → 환각 원천 봉쇄


### 4.4 Dublin Core 메타데이터 상속

문서 레벨(Root)에 부여된 신뢰할 수 있는 메타데이터를 하위 모든 청크가 **자동 상속**:

```
문서 Root 메타데이터:
  dc:creator = "한국원자력연구원"
  dc:date    = "2024-05-15"
  dc:rights  = "RESTRICTED"
      │
      ├── 섹션 1 청크 → 동일 메타데이터 상속
      ├── 섹션 2 청크 → 동일 메타데이터 상속
      └── 섹션 3 청크 → 동일 메타데이터 상속
```

→ 청크 단위 파편화 방지 + 출처 투명성(Provenance) 보장

---

## 5. 종합 평가

### 5.1 SWOT 분석

| 구분 | 내용 |
|---|---|
| **강점** | 환각 제로. 완벽한 추적 가능성. EU AI Act 등 규제 준수 |
| **약점** | JATS 파서 + TERM 스키마 구축에 초기 비용. 사전 미정의 신조어·비정형 레이아웃 대응 한계 |
| **기회** | 한번 구축된 파이프라인으로 대량 문서 일관 처리. 지식 그래프 연동으로 추론형 AI 기반 확보 |
| **위협** | OCR 오류(스캔 품질 의존). 동일 용어의 다른 맥락 사용 시 오분류 가능성 |


### 5.2 결정론적 vs 확률론적 방식 비교

| 비교 항목 | 결정론적 (제안 방식) | 확률론적 (LLM 방식) | 우위 |
|---|---|---|---|
| **메타데이터 생성** | 문서 내 구조/용어 존재 여부의 사실 기반 추출 | 확률적 추측 | 결정론 ✅ |
| **환각 위험** | 0% — 없는 태그는 생성 불가 | 높음 — 없는 날짜/저자 생성 가능 | 결정론 ✅ |
| **일관성** | 언제 실행해도 동일 결과 (Idempotent) | 실행 시점/프롬프트에 따라 가변 | 결정론 ✅ |
| **추적 가능성** | 태그 생성 원인 명확히 설명 가능 | 내부 가중치 연산으로 Black Box | 결정론 ✅ |
| **구현 비용** | 초기 높음, 운영 낮음 | 초기 낮음, 토큰·검증 비용 높음 | 장기적 결정론 ✅ |
| **유연성** | 스키마 범위 외 문서에 취약 | 다양한 형식에 유연 대응 | LLM ✅ |


### 5.3 권장 ETL 기술 스택

| 단계 | 기능 | 권장 기술 | 비고 |
|---|---|---|---|
| Ingestion | 문서 파싱 + 레이아웃 분석 | Docling, Unstructured | LLM 배제, BBox 추출 필수 |
| Normalization | 구조적 변환 | JATS XML | 계층 구조 `<sec>` 표준화 |
| Chunking | 시멘틱 분할 | Structural Chunking (Code) | 좌표 + 목차 기반 |
| Enrichment | 메타데이터 태깅 | FlashText, spaCy Rule-based | TERM 스키마 매칭 + 교차 분석 |
| Storage | 데이터 저장 | Vector DB + Graph DB | 하이브리드 저장소 |
| Validation | 무결성 검증 | JSON Schema Validator | 타입 + 필수 필드 검증 |

---

## 6. 제언

1. **DOC 스키마 구체화**: JATS 표준 준수하여 `section_level`, `parent_id`, `bbox` 필드를 필수 포함
2. **TERM 스키마 온톨로지화**: 단순 용어 목록 → 용어 간 위계(Hierarchy)와 관계(Relation)가 정의된 **SKOS/OWL** 형태로 고도화 → 교차 태깅 추론 능력 강화
3. **ETL 파이프라인 역할 분리**: 텍스트 추출·메타데이터 생성은 **결정론적 코드**, LLM은 최종 단계의 자연어 질의 해석·답변 생성(Interface)으로만 제한 → **Separation of Concerns** 원칙 적용

---

## 참고 자료

| # | 출처 |
|---|---|
| 1 | [Deterministic vs. Probabilistic Models](https://www.rudderstack.com/blog/deterministic-vs-probabilistic/) — RudderStack |
| 2 | [From Valid XML to Valuable XML](https://www.ncbi.nlm.nih.gov/books/NBK611679/) — JATS-Con / NCBI |
| 3 | [Production-Grade RAG System for Real PDFs](https://medium.com/codex/i-built-a-production-grade-rag-system-for-real-pdfs-text-tables-images-scans-heres-the-0b6accbd1044) — Medium |
| 4 | [Layout-Aware RAG with Evidence Pins (Docling + Neo4j)](https://vipulmshah.medium.com/layout-aware-rag-with-evidence-pins-building-clickable-citations-for-pdfs-using-docling-neo4j-5305769759f0) — Medium |
| 5 | [Chunking Strategies for RAG](https://weaviate.io/blog/chunking-strategies-for-rag) — Weaviate |
| 6 | [Turning PDFs into Hierarchical Structure for RAG](https://www.reddit.com/r/LangChain/comments/1dpbc4g/how_we_chunk_turning_pdfs_into_hierarchical/) — Reddit |
| 7 | [5 RAG Chunking Strategies](https://www.lettria.com/blogpost/5-rag-chunking-strategies-for-better-retrieval-augmented-generation) — Lettria |
| 8 | [Introduction to Docling](https://heidloff.net/article/docling/) — Niklas Heidloff |
| 9 | [PDF Parsers for Air-Gapped RAG](https://dev.to/ashokan/from-pdfs-to-markdown-evaluating-document-parsers-for-air-gapped-rag-systems-58eh) — DEV Community |
| 10 | [Document AI Layout Parser + Vertex AI RAG](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/layout-parser-integration) — Google Cloud |
| 11 | [Automated Extraction of Semantic Legal Metadata](https://orbilu.uni.lu/bitstream/10993/46243/1/SSSBCD-EMSE2020Rev.3.pdf) — ORBilu |
| 12 | [OG-RAG: Ontology-Grounded RAG](https://arxiv.org/html/2412.15235v1) — arXiv |
| 13 | [Mining Information Using Knowledge Graph](https://medium.com/@samuel7.ag.gis/mining-information-from-text-using-knowledge-graph-and-semantic-intelligence-fb3df20c6cea) — Medium |
| 14 | [What is Graph RAG](https://www.ontotext.com/knowledgehub/fundamentals/what-is-graph-rag/) — Ontotext |
| 15 | [GraphRAG with Amazon Bedrock](https://aws.amazon.com/blogs/machine-learning/build-graphrag-applications-using-amazon-bedrock-knowledge-bases/) — AWS |
| 16 | [Efficient Chunking for PDF Extraction](https://www.reddit.com/r/LangChain/comments/1acudx2/efficient_chunking_strategies_for_pdf_information/) — Reddit |
| 17 | [Comparative Analysis of Chunking Strategies](https://www.reddit.com/r/Rag/comments/1gcf39v/comparative_analysis_of_chunking_strategies_which/) — Reddit |
| 18 | [Best PDF Parsing Tools](https://medium.com/data-science-collective/pdf-parsing-processing-tools-you-should-know-ea1563e7308f) — Medium |
| 19 | [Best PDF Extractor for RAG](https://levelup.gitconnected.com/whats-the-best-pdf-extractor-for-rag-i-tried-llamaparse-unstructured-and-vectorize-4abbd57b06e0) — Level Up Coding |
| 20 | [Best Practices for Sharable Metadata](https://help.oclc.org/Metadata_Services/CONTENTdm/Get_started/best_practices) — OCLC |
| 21 | [Chunk and Vectorize by Document Layout](https://learn.microsoft.com/en-us/azure/search/search-how-to-semantic-chunking) — Microsoft |
| 22 | [Advanced RAG: Layout Aware Parsing and Chunking](https://viraajkadam.medium.com/advanced-rag-layout-aware-and-multi-document-rag-f45cb0d5838d) — Medium |
| 23 | [Docling: Custom XML Conversion](https://docling-project.github.io/docling/examples/backend_xml_rag/) — Docling |
| 24 | [PDF to JATS Conversion](https://www.ncbi.nlm.nih.gov/books/NBK100490/) — NCBI |
| 25 | [Efficient Knowledge Indexing for RAG LLMs](https://arxiv.org/html/2412.05547v1) — arXiv |
| 26 | [Hallucination-Free? Reliability of AI Legal Research Tools](https://reglab.stanford.edu/publications/hallucination-free-assessing-the-reliability-of-leading-ai-legal-research-tools/) — Stanford RegLab |
| 27 | [Hallucination-Free Legal AI (Full Paper)](https://law.stanford.edu/publications/hallucination-free-assessing-the-reliability-of-leading-ai-legal-research-tools/) — Stanford Law |
| 28 | [Ontology-based Text Mining for Process-Structure-Property](https://pmc.ncbi.nlm.nih.gov/articles/PMC11467320/) — PMC |
