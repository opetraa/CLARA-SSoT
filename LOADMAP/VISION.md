<!-- 문서에 담긴 핵심 철학을 요약하고, 실제 개발 과정에서 직관적으로 참고할 수 있도록 정리한 문서입니다. -->

1. Tractara 개발 문서의 핵심 철학 요약

이 시스템의 철학은 **"모델 중심(Model-Centric) AI의 한계를 극복하기 위한    데이터 중심(Data-Centric) AI로의 전환"**입니다. 구체적으로 다음과 같은 원칙을 바탕으로 설계되었습니다.

Glass Box 시스템 구축: 기존 상용 LLM의 블랙박스 구조와 환각(Hallucination) 문제를 해결하기 위해, 탐색 가능한 온톨로지와 지식 그래프를 도입하여 추적 가능성과 설명 가능성을 확보합니다. 이는 EU AI Act 등 고규제 도메인의 필수 요건을 충족하기 위함입니다.

단일 진실 공급원(SSoT) 기반의 결정론적 파생: 모든 데이터는 엄격하게 구조화된 SSoT(Baseline)로 중앙 통제되며, 이 원본 하나로부터 어휘(VE), RAG 청크, 지식 그래프(KG), 사전학습(CPT), 미세조정(SFT) 데이터가 규칙 기반으로 결정론적으로 파생됩니다.

인간 인지 구조의 코드화 (ACT-R): 다단계 추론이 필요한 전문가의 의사결정 과정을 ACT-R 인지 모델의 버퍼-생산 시스템(If-then) 구조로 명문화하여, 데이터 레벨에서 추론의 투명성과 재현성을 보장합니다.

---

## Part 1. 아키텍처 개요 및 End-to-End 파이프라인 (Architecture & Pipeline)

**핵심 설계 원칙**: SSoT로 표준화 $\rightarrow$ 자동 파생 $\rightarrow$ 저장/학습 $\rightarrow$ 신호 기반 검색 및 응답 $\rightarrow$ 로그로 재현성 및 V&V 확보.

### 1.1 거버넌스 및 MLOps (Governance & MLOps)
데이터의 생명주기를 관리하고 규제 요건을 충족하기 위한 기반 레이어입니다.

**버전 관리**: DVC와 Git을 활용하여 데이터와 코드의 버전을 동기화 및 관리합니다.

**품질 통제**: Validator를 통해 JSON Schema 및 Protocol을 검증하여 무결성을 확보합니다.

**추적성 확보**: RFC7807 표준 및 trace_id를 기반으로 구조화된 로그(Structured Logs)를 생성합니다.


### 1.2 데이터 수집 (Data Ingestion) 및 정규화 (Normalization)
다양한 형태의 원자력 도메인 원본 지식을 시스템으로 유입시키는 단계입니다.

**수집 대상**: 원자력 용어집, RAI, PSR, Codes, 논문, LER 등.

**파싱 및 추출**: PDF 파싱, 테이블/이미지 추출, OCR 기술을 활용하여 비정형 데이터를 텍스트로 변환합니다.


### 1.3 SSoT ETL 파이프라인 (Baseline ETL Pipeline)
수집된 데이터를 단일 진실 공급원(SSoT) 규격으로 정규화하고 적재합니다.

**Landing Zone**: 추출된 텍스트를 최소 수준으로 정규화(Normalization)하고 JSON 스키마에 매핑합니다.

**Curation Area**: SSoT 진입 전 임시 대기소 역할을 수행합니다.

**TERM 단계**: 영어 정의(definition_en)와 한국어 목적(purpose_ko) 등 다양한 출처의 속성을 수집 및 병합(Merging)합니다.

**DOC 단계**: 문서 간 1:1 매칭을 통해 구조를 유지합니다 (Bypassing).

**SSoT (단일 진실 공급원)**: 엄격하게 분리된 두 가지 스키마로 영구 보관됩니다.

**TERM Baseline**: 용어의 정의(definition), 슬롯(slot), 부정 키워드(negatives) 등을 포함합니다.

**DOC Baseline**: 메타데이터(metadata), 본문 블록(content[]), 관계(relations[]) 등을 포함합니다.


### 1.4 파생 아티팩트 생성 (Derived Artifacts)

SSoT Baseline으로부터 LLM 학습 및 RAG 구동에 필요한 5가지 핵심 아티팩트를 결정론적으로 자동 파생합니다.

① Vocab Edit: term, headword (en, ko) 데이터를 활용하여 약어 및 전문용어를 1토큰화하고 제어 스페셜 토큰을 정의해 LLM 내부에 등록합니다.

② RAG Chunk: 환각 최소화 및 인용 정확도 향상을 위해 검색/임베딩에 최적화된 청크(text_for_display, text_for_embedding, keyword_for_bm25)를 생성합니다.

③ KG Triples: Node-edges 형태의 관계로, 다단 관계 추론 및 절차적 의존성 이해를 위해 그래프 데이터를 구성합니다.

④ CPT Corpus: 용어와 도메인 언어를 LLM에 내장하기 위한 데이터 재수화(Data rehydration) 목적의 .jsonl 코퍼스입니다.

⑤ SFT Dataset: Instruction-response 구조의 .jsonl 파일로, 지시-따르기 행동 학습 및 논문 등에서 추출한 전문가의 의사결정 과정(ACT-R 생산규칙)을 담고 있습니다.


### 1.5 저장소 및 모델 (Storage & Models)
파생된 데이터를 성격에 맞는 데이터베이스에 적재하고 도메인 LLM을 구성합니다.

* **Database**:

**RAG Store**: 벡터 및 BM25를 지원하는 PostgreSQL Hybrid Index를 사용합니다.

**KG Store**: 그래프 탐색을 위한 Neo4j를 사용합니다.

**Domain LLM**: Vocab Edit(VE), Continual Pre-Training(CPT), Supervised Fine-Tuning(SFT)이 결합된 형태입니다.


### 1.6 런타임 검색 및 응답 (Runtime Retrieval & Answering)
사용자의 질의를 받아 실제 답변을 생성하는 최종 서비스 레이어입니다.

**처리 흐름**: 사용자 질의(User Query) 입력 $\rightarrow$ Orchestrator를 통한 RAG 파이프라인 제어 $\rightarrow$ LLM Generator 구동.

**최종 출력**: 정확한 출처(citations)가 포함된 신뢰할 수 있는 답변을 반환합니다.

---
