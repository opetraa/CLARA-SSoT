# TERM 스키마의 다단계 성숙도 모델 및 Taxonomy 자동 할당 방법론


본 연구는 Tractara 아키텍처의 핵심인 TERM 스키마 생명주기 관리 전략을 분석하고, **'Candidate-Anchored-Mature'** 3단계 성숙도 모델을 제안한다. 아울러, 'Anchored' 단계 자동화를 위한 **Taxonomy 자동 할당** 방법론을 제시한다.


### 1.2 기존 Landing Zone/SSoT 이분법의 한계

Tractara에서 Landing Zone(원시 데이터)과 SSoT(검증 데이터) 사이의 간극은 심각한 병목을 유발한다.

| 문제 | 설명 |
|---|---|
| **검증 병목** | SSoT 등재를 위해 완벽한 메타데이터를 요구하면, 구조적으로 유의미한 데이터도 Landing Zone에 장기 체류 → RAG 검색 실패 |
| **지식 그래프 단절** | 특정 용어가 SSoT 미진입 시, 해당 용어를 매개로 하는 모든 관계가 단절 → 다단계 추론(Multi-hop Reasoning) 불가 |

**→ 신뢰도(Trustworthiness)와 완성도(Completeness)를 분리하여 관리하는 새로운 모델이 필수적이다.**

---

## 2. 'Candidate-Anchored-Mature' 모델 타당성 분석

### 2.1 데이터 품질의 두 축: 신뢰도 vs. 완성도

고규제 도메인의 지식 그래프 구축에서 이 두 속성은 **서로 다른 운영적 가치**를 지닌다.

| 축 | 정의 | 특성 |
|---|---|---|
| **신뢰도 (Trustworthiness)** | 데이터가 사실인지, 출처가 명확한지 | 타협 불가. 환각을 넘어선 치명적 오안내 유발 가능 |
| **완성도 (Completeness)** | 모든 속성과 관계가 채워졌는지 | **점진적 향상 가능**. 불완전해도 존재하는 속성이 정확하면 제한적 기능 수행 가능 |

→ 두 축을 **직교하는 독립 차원**으로 설정하여 TERM 상태를 정의한다.


### 2.2 3단계 상태 정의 및 운영 전략

| 상태 | 신뢰도 | 완성도 | 정의 | 시스템 역할 |
|---|---|---|---|---|
| **① Candidate** (후보) | 가변적 (Low~Mid) | 낮음 | 자동 파이프라인(OCR, LLM)으로 추출된 미검증 원시 용어 | RAG 검색 대상 **제외**. 큐레이션·빈도 분석용. Landing Zone에 위치 |
| **② Anchored** (앵커링) | 높음 (식별/분류) | 중간 (Partial) | ID 확립 + Taxonomy 할당으로 그래프상 위치 고정. 속성은 미완성 가능 | **구조적 연결(Structural Bridge)** 수행. 그래프 순회 가능. SSoT의 'Beta' 계층 |
| **③ Mature** (성숙) | 매우 높음 (Verified) | 높음 | 모든 필수 필드 완료 + 도메인 전문가(HITL) 검증 완료 | 규제 대응 보고서·최종 판단의 근거. SSoT 핵심(Core). 엄격한 DVC 적용 |


### 2.3 Anchored 단계의 전략적 중요성

'Anchored'는 **"불완전하지만 신뢰할 수 있는 구조(Structure without complete Content)"**를 허용하는 상태이다.

**① 참조 무결성 보장**

문서에서 `"밸브 V-101의 재질은 SUS316이다"`가 추출되었을 때, 'V-101'이 SSoT에 정의되지 않았더라도 Anchored 상태로 등록하면(식별자 부여 + '기기' 분류), 해당 Triple을 즉시 그래프에 적재할 수 있다. → **데이터 유실 방지 + 파이프라인 처리량 극대화.**

**② 검색 경로 확보**

Anchored 노드는 상세 설명이 없어도 그래프상 **'징검다리'** 역할을 수행한다. RAG 시스템은 이 노드를 통해 상위 개념(Taxonomy)이나 연관 기기(`Connected_to`)로 탐색 범위를 확장할 수 있다.


### 2.4 타당성 결론

이분법 모델은 데이터 품질을 'All or Nothing'으로 취급하여 막대한 데이터가 사장된다. 반면 3단계 모델은 **구조적 신뢰성**과 **내용적 완성도**를 분리하여:

- 시스템 초기 구축 속도를 높이고
- **점진적 지식 성숙(Ontology Maturing)**을 가능하게 한다

---

## 3. Taxonomy 자동 할당을 위한 기술적 방법론

'Candidate' → 'Anchored' 승격의 필수 조건은 **고유 식별(Identity Resolution)** + **분류 할당(Taxonomy Assignment)**이다.

### 3.1 문제 정의: Zero-Shot Hierarchical Entity Typing

추출된 용어(예: `"잔열제거 펌프"`)를 훈련 데이터에 없더라도, 사전 정의된 계층적 분류체계(예: `기기 > 회전기기 > 펌프`)의 말단 노드에 정확히 할당하는 문제.

- 단순 분류 모델로는 계층 구조의 깊이와 복잡성을 처리 불가
- → **LLM 추론 능력 + 구조적 제약 결합** 필요


### 3.2 방법론 1: Chain-of-Layer (CoL) 프롬프팅

> 분류를 상위→하위로 단계적으로 좁혀가는 방식

**구현 절차:**

```
Step 1 — 루트 레벨 분류
  문맥: "작업자는 1차측 펌프를 점검했다."
  용어: "1차측 펌프"
  상위분류: [System, Component, Document]
  → Output: Component

Step 2 — 하위 탐색
  상위: Component
  후보: [Mechanical, Electrical, I&C]
  → Output: Mechanical

Step 3 — 말단 도달까지 재귀 반복
```

**장점:**

- LLM의 탐색 공간(Search Space)을 획기적으로 축소 → **분류 정확도 향상**
- 분류 경로(Reasoning Path)가 명시적으로 남음 → **EU AI Act 설명 가능성 충족**


### 3.3 방법론 2: 제약된 디코딩 (Constrained Decoding)

> LLM의 토큰 생성 자체를 제어하여 분류체계에 없는 출력을 원천 차단

**구현 절차:**

1. **Taxonomy Trie 구축**: 허용 가능한 모든 분류 경로(예: `Component.Mechanical.Pump`)를 Trie(Prefix Tree)로 컴파일
2. **Logit Masking**: LLM이 토큰을 예측할 때, Trie상 유효한 토큰의 Logit만 남기고 나머지는 `-∞`로 마스킹
3. **결정론적 출력**: LLM은 반드시 Taxonomy Trie 내 경로만 생성 가능 → **수학적 보장**

**장점:**

- LLM 할루시네이션을 **구조적으로 100% 차단** → 스키마 준수율 보장
- 'Anchored' 상태의 핵심 조건인 *구조적 무결성* 확보에 결정적
- 구현 도구: `guidance`, `llama.cpp`의 grammar 기능 등


### 3.4 방법론 3: 임베딩 기반 의미론적 정렬

> 벡터 유사도를 활용하여 LLM 추론 비용을 절감하고 대규모 배치를 처리

**구현 절차:**

1. **Taxonomy Embedding**: 분류체계 각 노드의 이름+정의를 도메인 특화 임베딩 모델(예: Fine-tuned BERT, `text-embedding-3-large`)로 벡터화 → Vector DB 저장
2. **Term Embedding**: 추출된 용어 + 주변 문맥을 동일 모델로 임베딩
3. **Hybrid Search**: 코사인 유사도로 가장 가까운 Taxonomy 노드 Top-K 추출 → CoL 프롬프팅의 후보군으로 제공


### 3.5 통합 파이프라인: Neuro-Symbolic 하이브리드 접근법

단일 기법의 한계를 보완하기 위해 위 방법론들을 결합한다.

```
Step 1  Candidate Ingestion
        텍스트에서 용어 추출 + 문맥 벡터화
            │
Step 2  Vector Filtering                          ← 방법론 3
        임베딩 유사도로 관련 서브트리 후보군 식별
            │
Step 3  CoL Classification + Constrained Decoding  ← 방법론 1 + 2
        서브트리 내에서 LLM이 단계적 분류 수행
        + 제약 디코딩으로 유효 노드 ID만 출력 강제
            │
Step 4  Neuro-Symbolic Check
        온톨로지 논리적 제약(예: Pump → Pressure 속성 가능)
        과 모순 없는지 기호 논리(Symbolic Reasoning) 검증
            │
Step 5  Promotion
        검증 통과 시 'Anchored' 상태 승격 + 고유 ID 부여
```

---

## 4. 데이터 생명주기 관리 및 MLOps 통합

### 4.1 상태 전이 로직과 Validator의 역할

#### Candidate → Anchored (자동화 중심)

| 항목 | 내용 |
|---|---|
| **Trigger** | 신규 용어 추출 |
| **중복 검사** | 기존 SSoT 동의어 사전 + 벡터 유사도로 기존 용어 일치 여부 확인 |
| **분류 타당성** | 3.5절 파이프라인을 통해 유효한 Taxonomy ID 할당 확인 |
| **형식 검사** | JSON Schema 최소 필수 필드(`Label`, `Type`, `Source ID`) 충족 여부 |
| **Outcome** | 성공 시 고유 URI 발급 + Graph DB에 노드 생성 (속성은 비어있을 수 있음) |

#### Anchored → Mature (인간 개입 중심)

| 항목 | 내용 |
|---|---|
| **Trigger** | 전문가 검토 완료 또는 Trust Score 임계치 초과 |
| **완전성 검사** | 필수 메타데이터(다국어 정의, 표준 참조, 예문 등) 100% 충족 |
| **검증 로그** | 도메인 전문가 승인 서명 또는 합의 알고리즘 통과 |
| **Outcome** | 'Verified' 태그 부여, 프로덕션 RAG 인덱스에 전체 메타데이터 공개 |


### 4.2 'Anchored' 데이터의 시스템 내 처리

**검색(Retrieval) 시:**

Anchored 노드는 그래프 순회를 위한 경로로서 활성화된다. 예를 들어 `"보조급수펌프의 전원 공급 경로"`를 질의할 때, 중간 경로의 차단기가 Anchored 상태라도 연결 정보(Edge)를 통해 전원 소스를 추적할 수 있다.

**생성(Generation) 시:**

LLM이 Anchored 노드의 정의나 속성을 설명해야 할 때, 시스템은 **"정보 부족"** 또는 **"검증 중"** 메타데이터를 함께 제공하여 답변 신뢰도를 조정한다. → **할루시네이션 방지 안전장치(Safety Rail)**.

---

## 5. 결론 및 제언

### 핵심 결론

- **3단계 모델의 타당성 확인**: 'Candidate-Anchored-Mature' 모델은 데이터 가용성과 신뢰성 딜레마를 해결하는 타당한 접근이다.
- **'Anchored'의 전략적 가치**: 구조적 데이터(지식 그래프)의 연결성을 유지하는 핵심 기제로 작동한다.
- **Constrained Decoding의 실용성**: AI의 확률적 불확실성을 시스템의 구조적 제약으로 통제하는 최적의 솔루션이다.

### 향후 과제

1. Anchored 데이터가 RAG 답변 정확도·환각률에 미치는 영향 정량 검증 (Ablation Study)
2. 다수 LLM 에이전트가 협업하여 Taxonomy를 동적으로 확장하는 멀티 에이전트 시스템 연구

---

## 참고 자료

| # | 출처 |
|---|---|
| 1 | [Proposal] Developing a Data-Centric AI Architecture for Highly Regulated Domains v1.1.2 |
| 2 | [Human Oversight Solves RAG's Biggest Challenges](https://labelstud.io/blog/how-human-oversight-solves-rag-s-biggest-challenges-for-business-success/) |
| 3 | [ReGraphRAG: Reorganizing Fragmented...](https://aclanthology.org/2025.findings-emnlp.290.pdf) — ACL Anthology |
| 4 | [How to Solve 5 Common RAG Failures with Knowledge Graphs](https://www.freecodecamp.org/news/how-to-solve-5-common-rag-failures-with-knowledge-graphs/) — freeCodeCamp |
| 5 | [Data Quality Dimensions](https://www.ibm.com/think/topics/data-quality-dimensions) — IBM |
| 6 | [The 6 Data Quality Dimensions](https://www.collibra.com/blog/the-6-dimensions-of-data-quality) — Collibra |
| 7 | [Data Quality Dimensions](https://ies.ed.gov/rel-central/2025/01/data-quality-dimensions) — IES |
| 8 | [Quality Metrics for Knowledge Graph on Digital NOTAMs](https://ojs.aaai.org/index.php/AAAI-SS/article/download/36888/39026/40965) — AAAI |
| 9 | [Knowledge Graphs: A Comprehensive Guide](https://medium.com/agile-lab-engineering/knowledge-graphs-a-comprehensive-guide-24f4609c8ff5) — Medium |
| 10 | [Check Pending Status in Referential Constraints](https://www.ibm.com/docs/en/i/7.4.0?topic=constraints-check-pending-status-in-referential) — IBM |
| 11 | [Ontology Maturing Approach](https://www.researchgate.net/publication/221467162) — ResearchGate |
| 12 | [Zero-Shot Open Entity Typing as Type-Compatible Grounding](https://aclanthology.org/D18-1231/) — ACL Anthology |
| 13 | [Description-Based Zero-shot Fine-Grained Entity Typing](https://liner.com/review/descriptionbased-zeroshot-finegrained-entity-typing) — Liner |
| 14 | [Automated Taxonomy Construction Using LLMs](https://www.mdpi.com/2673-4117/6/11/283) — MDPI |
| 15 | [Chain-of-Layer: Iteratively Prompting LLMs for Taxonomy Induction](https://arxiv.org/html/2402.07386v1) — arXiv |
| 16 | [Guiding LLMs The Right Way: Constrained Generation](https://arxiv.org/html/2403.06988v1) — arXiv |
| 17 | [Grammar-Constrained Decoding for Structured NLP](https://openreview.net/forum?id=KkHY1WGDII) — OpenReview |
| 18 | [DELM: Data Extraction with Language Models](https://arxiv.org/html/2509.20617v1) — arXiv |
| 19 | [Ultra-fine Entity Typing with Indirect Supervision from NLI](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00479/111220) — MIT Press |
| 20 | [Enhancing RAG with Knowledge Graphs](https://medium.com/neo4j/enhancing-the-accuracy-of-rag-applications-with-knowledge-graphs-ad5e2ffab663) — Neo4j |
| 21 | [LLM-based Zero-shot Triple Extraction for Ontology Generation](https://arxiv.org/html/2509.00140v2) — arXiv |
| 22 | [Intelligent Knowledge Mining Framework](https://arxiv.org/html/2512.17795v1) — arXiv |
| 23 | [Enhanced KG Embedding Based on Negative Sample Analogical Reasoning](https://pmc.ncbi.nlm.nih.gov/articles/PMC12019208/) — PMC |
| 24 | [FinOps Maturity Model](https://www.finops.org/framework/maturity-model/) — FinOps Foundation |
| 25 | [Maturity Models](https://therrinstitute.com/oe-solution-set-2/maturity-models/) — THERR Institute |
| 26 | [Implementing Global GraphRAG with Neo4j and LangChain](https://neo4j.com/blog/developer/global-graphrag-neo4j-langchain/) — Neo4j |
| 27 | [Improved Knowledge Graphs with Entity Resolution](https://senzing.com/knowledge-graph/) — Senzing |
| 28 | [Understanding Foreign Keys in Databases](https://www.pingcap.com/article/understanding-foreign-keys-in-databases/) — TiDB |
| 29 | [How to Integrate Graph Database into RAG Pipeline](https://www.datarobot.com/blog/how-to-integrate-graph-database-rag-pipeline/) — DataRobot |
| 30 | [PROPEX-RAG: Enhanced GraphRAG](https://arxiv.org/html/2511.01802v1) — arXiv |
| 31 | [SKOS Use Cases and Requirements](https://www.w3.org/TR/skos-ucr/) — W3C |
| 32 | [Best Practice in Formalizing a SKOS Vocabulary](https://www.researchgate.net/publication/262936929) — ResearchGate |
| 33 | [ZERONER: Fueling Zero-Shot NER via Entity Type Descriptions](https://aclanthology.org/2025.findings-acl.805.pdf) — ACL Anthology |
