# 난이도 기반 승인 정책 및 동적 생명주기 관리 체계

> 고규제 도메인 AI의 데이터 무결성 확보를 위한 타당성 분석 보고서


본 보고서는 Tractara 아키텍처의 SSoT 신뢰성을 유지하기 위한 두 가지 핵심 메커니즘을 분석한다:

1. **난이도 기반 필드 레벨 승인 정책** — 데이터 유입(Ingestion) 단계의 환각 방지
2. **동적 생명주기 관리** — 스키마 변경에 따른 데이터 부패(Data Decay) 방지

---

## 1. 배경: 결정론적 안전성과 확률론적 모델의 충돌

### 1.1 문제의 핵심

고규제 도메인의 규제 프레임워크는 **결정론적 증거**와 명확한 인과관계를 요구하지만, LLM은 본질적으로 **확률론적**이다. Tractara는 이 간극을 메우기 위한 Glass Box 시스템으로, LLM의 생성 능력과 지식 그래프의 구조적 엄밀성을 결합한다.

### 1.2 데이터 품질 위기

| 위험 요소 | 설명 |
|---|---|
| **모델 붕괴** | 합성 데이터 재학습으로 롱테일 정보(예: 가압기 서지라인 열성층화 현상) 소실·왜곡 |
| **LLM 과신** | 틀린 답에도 높은 확신도를 보이는 보정 오류(Calibration Error) |
| **규제 강화** | EU AI Act, FDA AI/ML 가이드라인 등이 데이터 거버넌스·인간 감독 의무화 |

### 1.3 현행 Validator의 한계

기존 JSON Schema 기반 Validator는 **형식적 완결성**만 보장하며, 다음을 보장하지 못한다:

- **의미적 정확성**: `"150MPa"` 추출 시, 원본이 `"1500MPa"` 또는 `"150MPa 이하"`였을 가능성
- **시간적 유효성**: 규제 변경으로 `"허용 온도"`가 필수 정보로 추가되면, 기존 데이터가 규제적으로 불완전해짐

→ **단순 Validator를 넘어선 지능형 정책 엔진이 필요하다.**

---

## 2. 제안 I: 난이도 기반 필드 레벨 승인 정책

LLM 추출 데이터의 승인을 이분법(합격/불합격)이 아닌, **추출 난이도에 따른 차등 검증**으로 전환한다. FDA의 위험 기반 접근(Risk-Based Approach)을 AI 데이터 파이프라인에 적용한 것이다.

### 2.1 '난이도(Difficulty)'의 3차원 정의

#### ① 모델 불확실성 (U_model)

모델 자체가 느끼는 내재적 불확실성. 단순 Logits가 아닌 **자기 일관성(Self-Consistency)** 기법을 활용한다.

**측정 방법**: 동일 프롬프트에 Temperature를 높여 K번 생성 → 결과 분산도 측정

```
예시:
  5/5 "150MPa" → 난이도 낮음 ✅
  "150MPa", "15MPa", "1500kPa" 혼재 → 난이도 높음 ⚠️
```

#### ② 소스 복잡도 (C_source)

원본 문서의 구조적·시각적 난이도.

| 요소 | 낮은 난이도 | 높은 난이도 |
|---|---|---|
| **구조** | 명확한 키-값 표(Table) | 여러 페이지에 걸친 서술형 텍스트, 중첩 표 |
| **시각** | 깨끗한 디지털 PDF | 노이즈 많은 스캔본, 낮은 OCR 신뢰도 |

**측정**: ETL 파서가 DOM 깊이, 텍스트 밀도, OCR 점수 등을 메타데이터로 제공.

#### ③ 의미적 임계성 (R_risk)

해당 필드 자체의 **도메인 특화 중요도**. TERM 스키마 정의 시 사전 할당.

| 등급 | 예시 | 가중치 |
|---|---|---|
| **Critical** | 안전 임계값(온도, 압력), 재질 사양, 규제 코드 번호 | 1.0 |
| **Major** | 제품 모델명, 담당 부서 | 0.5 |
| **Minor** | 비고, 설명 텍스트 | 0.1 |

> [!IMPORTANT]
> `R_risk`가 Critical인 필드는 `U_model`이나 `C_source`가 아무리 낮아도 **자동 승인을 원천 차단**하는 안전 바닥(Safety Floor) 역할을 수행해야 한다.


### 2.2 난이도 점수 산출 및 승인 등급 체계

**최종 난이도 점수**: `D = w₁ × U_model + w₂ × C_source + w₃ × R_risk`

> 고규제 도메인에서는 `w₃`(R_risk)의 가중치를 압도적으로 높게 설정하여 안전성을 우선시.

| 등급 | 난이도 점수 | 정책 | 상태 전이 |
|---|---|---|---|
| **Auto-Pass** | `D < T_low` | 인간 개입 없이 시스템 승인 | Candidate → Anchored |
| **Augmented** | `T_low ≤ D < T_high` | 2차 검증 에이전트(다른 LLM 또는 결정론적 코드)가 교차 검증. 일치 시 승인, 불일치 시 격상 | Candidate → Anchored (if consensus) |
| **Manual Review** | `D ≥ T_high` | 반드시 도메인 전문가(HITL) 승인 필요 | Candidate → Pending Review |


### 2.3 기대 효과

| 관점 | 효과 |
|---|---|
| **운영 효율** | 저위험 데이터 자동 승인 → 전문가 리소스를 고위험 데이터에 집중 |
| **보정된 신뢰성** | 소스 복잡도 + 도메인 중요도를 함께 고려 → '자신감 있는 환각' 방지 |
| **규제 준수** | 자동/수동 승인 건을 명확히 구분 로그 → 감사(Audit) 시 소명 가능 |

---

## 3. 제안 II: 동적 생명주기 관리 (Schema Regression)

데이터의 생명주기를 정적 상태로 두지 않고, **규제·스키마 변경에 따라 동적으로 강등(Regression)**시키는 메커니즘이다.

### 3.1 문제: 스키마 진화와 데이터 부패

기존에 `"밸브"` 데이터에 `"재질"` 정보만 있으면 충분했지만, 새 규제에 따라 `"내진 등급"`이 필수로 추가되면 → 기존 Mature 데이터는 **형식적으로 유효하지만 규제적으로 불완전**해진다.

정적 모델에서는 이 데이터가 그대로 'Mature'로 남아, 사용자에게 **불완전한 데이터를 완전한 것처럼 제공**하는 위험이 발생한다.


### 3.2 데이터 상태 모델 (State Model)

| 상태 | 정의 | RAG 노출 |
|---|---|---|
| **Candidate** | AI 추출 후 미검증. 큐레이션 영역에 존재 | ❌ 제외 |
| **Anchored** | 원본 문서와 연결·검증됨. 현재 스키마 전체 요건 충족은 미보장 | ⚠️ '잠정적(Provisional)' 태그 |
| **Mature** | 현재 최신 스키마(V_current)의 모든 필수 요건 충족 + 최종 승인 | ✅ Ground Truth로 최우선 노출 |


### 3.3 동적 강등 로직 (Auto-Demotion)

```
이벤트 감지
  Schema Registry가 V_n → V_(n+1) 변경 감지
      │
영향도 분석
  ├─ Non-Breaking (설명 수정, 선택 필드 추가) → 강등 없음 ✅
  └─ Breaking (필수 필드 추가, 타입 변경, 규칙 강화) → 강등 ⚠️
      │
일괄 강등
  영향받는 모든 Mature 엔티티 → Anchored로 변경
  + regression_reason 메타데이터 부착
      │
      예: "Schema v1.2: Missing field 'Seismic_Category'"
```


### 3.4 자가 치유 (Self-Healing) 프로세스

강등은 끝이 아니라 **재수화(Re-hydration)**의 시작이다.

1. Orchestrator가 Anchored로 강등된 엔티티 목록을 감지
2. 각 엔티티에 연결된 **원본 문서(Source Document ID)**를 MLOps 저장소에서 조회
3. LLM에게 `"새 스키마 필드(예: 내진_등급)를 해당 문서에서 추가 추출하라"` 지시
4. 추출 결과가 **난이도 기반 승인 정책**을 통과하면 → 다시 **Mature로 자동 복귀**

→ **자가 치유 지식 그래프(Self-Healing Knowledge Graph)** 구현


### 3.5 기대 효과

| 관점 | 효과 |
|---|---|
| **데이터 무결성** | 최신 스키마 준수 데이터만 Mature → "오래된 진실"을 "현재의 진실"로 오인하는 환각 차단 |
| **유지보수 비용** | 변경된 Delta에 대해서만 LLM이 자동 재추출 → 전수 조사 불필요 |
| **구현 가능성** | Kafka + Schema Registry(이벤트), Neo4j(그래프 상태 관리)로 실현 가능 |

---

## 4. 통합 아키텍처: 데이터 품질 상태 머신 (DQSM)

두 제안을 결합하면 Tractara는 정적 저장소가 아닌, **살아있는 데이터 품질 상태 머신**으로 진화한다.

### 4.1 통합 상태 전이

| 상태 | 진입 조건 | Mature 승격 조건 | 강등 조건 |
|---|---|---|---|
| **Candidate** | LLM 추출 직후 | 난이도 `D < T_low` 또는 인간 승인 | 유효성 검사 실패 시 삭제(Rejected) |
| **Anchored** | 1차 검증 완료 + 원본 연결 | 현재 스키마(V_current) 전체 필수 요건 충족 | 원본 문서 폐기·개정 시 |
| **Mature** | 완전성 검사 통과 | N/A (최종 상태) | **스키마 변경(V_current 업데이트) 시 Anchored로 회귀** |


### 4.2 3단계 품질 보장

```
┌─────────────────────────────────────────────────────┐
│  입구 (Ingestion)                                    │
│  난이도 기반 승인 → 불확실/위험 데이터 유입 차단      │
│  → Accuracy 보장                                     │
├─────────────────────────────────────────────────────┤
│  중심 (Storage)                                      │
│  동적 생명주기 → 스키마 변경 시 상태 자동 갱신        │
│  → Timeliness & Completeness 보장                    │
├─────────────────────────────────────────────────────┤
│  출구 (Retrieval)                                    │
│  Mature만 참조 / Anchored는 경고 태그 제공            │
│  → Transparency 보장                                 │
└─────────────────────────────────────────────────────┘
```

### 4.3 구현 요건

| 컴포넌트 | 역할 |
|---|---|
| **Validator (정책 엔진)** | LLM Logits 접근 + OCR 신뢰도 조회가 가능한 Python 미들웨어. Pydantic 확장으로 `x-risk-level`, `x-complexity` 커스텀 메타데이터 처리 |
| **Schema Registry** | TERM/DOC 스키마 버전 관리 + Breaking Change 감지 → Regression 트리거 |
| **Knowledge Graph Store** | Neo4j에서 엔티티 상태(`:Mature`, `:Anchored`)를 라벨/속성으로 관리. Cypher 일괄 업데이트 |
| **MLOps Pipeline** | 모든 상태 전이(승격·강등)를 로그 기록 + DVC 연동 버전 관리 |

### 4.4 구축 로드맵

| 단계 | 내용 |
|---|---|
| **1단계** Schema Enrichment | TERM 스키마에 `Criticality`, `Extraction_Difficulty` 메타데이터 필드 추가 |
| **2단계** Validator Upgrade | 모델 확신도 + 소스 복잡도 계산 기능 확장 |
| **3단계** Schema Registry Integration | 스키마 변경 감지 → 그래프 DB 상태 업데이트 트리거 (이벤트 기반) |
| **4단계** Self-Healing Agent | 강등 데이터를 원본 문서로 자동 보강하는 재수화 에이전트 개발 |

---

## 5. 결론

| 제안 | 핵심 가치 |
|---|---|
| **난이도 기반 승인** | LLM의 확률적 불확실성을 '위험(Risk)' 언어로 변환 → 맹목적 자동화와 비효율적 수동 검토 사이의 **최적점** 확보 |
| **동적 생명주기** | SSoT가 시간이 지나도 '진실'로 남도록 보장 → 규제 변경 시 스키마만 업데이트하면 **자동화된 컴플라이언스** 달성 |

### 제언

1. TERM 스키마 설계 시 각 필드에 **Criticality 메타데이터를 필수 포함**
2. Validator를 단순 필터가 아닌 **상태 결정 + 라우팅 오케스트레이터**로 고도화
3. 스키마 변경 시 **호환성 모드(Compatibility Mode)** 정교 설정 → Non-breaking 변경은 강등 미유발

---

## 참고 자료

| # | 출처 |
|---|---|
| 1 | [Threshold-based Approach for Computational Model Validation](https://cdrh-rst.fda.gov/threshold-based-approach-determining-acceptance-criterion-computational-model-validation) — FDA |
| 2 | [FDA's AI Guidance: 7-Step Credibility Framework](https://intuitionlabs.ai/articles/fda-ai-drug-development-guidance) — IntuitionLabs |
| 3 | [Risk-Based Quality Management in Clinical Data Management](https://www.quanticate.com/blog/risk-based-quality-management-in-clinical-data-management) — Quanticate |
| 4 | [Confidence Scoring for LLM-generated SQL](https://www.amazon.science/publications/confidence-scoring-for-llm-generated-sql-in-supply-chain-data-extraction) — Amazon Science |
| 5 | [A Confidence Score for LLM Answers](https://medium.com/wbaa/a-confidence-score-for-llm-answers-c668844d52c8) — Medium |
| 6 | [AI Data Extraction: Everything You Need to Know](https://blog.box.com/ai-data-extraction) — Box |
| 7 | [Automated Data Extraction & Validation](https://www.abbyy.com/ai-document-processing/data-extraction-and-validation/) — ABBYY |
| 8 | [Risk Key in Validation of Automated Systems](https://idisl.info/en/riesgo-clave-validacion-sistemas-automatizados/) — IDI |
| 9 | [Scoring Framework for Knowledge Graphs](https://www.elucidata.io/blog/knowledge-graph-scoring-drug-discovery) — Elucidata |
| 10 | [Risk Based Quality Management in Clinical Trials](https://cluepoints.com/risk-based-quality-management-its-now-a-question-of-how-rather-than-if/) — CluePoints |
| 11 | [LLMs for Scientific Information Extraction (SciEx)](https://arxiv.org/html/2512.10004v2) — arXiv |
| 12 | [Entity Maturity in SEO](https://jasonbarnard.com/digital-marketing/articles/articles-by/entity-maturity-in-seo-what-you-need-to-know/) — Jason Barnard |
| 13 | [State vs Status: Lifecycle in Domain Modeling](https://masoudbahrami.medium.com/dont-confuse-state-with-status-lifecycle-vs-context-in-domain-modeling-601bc91f326a) — Medium |
| 14 | [Knowledge Anchoring Framework](https://www.emergentmind.com/topics/knowledge-anchoring-framework) — Emergent Mind |
| 15 | [Schema Evolution in Data Pipelines](https://dataengineeracademy.com/module/best-practices-for-managing-schema-evolution-in-data-pipelines/) — Data Engineer Academy |
| 16 | [Schema Evolution in Databricks](https://docs.databricks.com/aws/en/data-engineering/schema-evolution) — Databricks |
| 17 | [6 Data Quality Dimensions with Examples](https://www.montecarlodata.com/blog-6-data-quality-dimensions-examples/) — Monte Carlo |
| 18 | [Schema Evolution and Compatibility](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html) — Confluent |
| 19 | [Schema Evolution in CDC Pipelines](https://www.decodable.co/blog/schema-evolution-in-change-data-capture-pipelines) — Decodable |
| 20 | [Event-driven Architecture Pattern](https://developer.ibm.com/articles/advantages-of-an-event-driven-architecture/) — IBM |
| 21 | [Data Quality Dimensions](https://www.ibm.com/think/topics/data-quality-dimensions) — IBM |
| 22 | [Top 12 Data Quality Dimensions in 2026](https://dagster.io/learn/data-quality-dimensions) — Dagster |
| 23 | [Knowledge Graph Designer](https://www.servicenow.com/docs/r/x7YYxCVARboMBfN2zKAZsA/fVv16guVugBv6w6B~TTsxQ) — ServiceNow |
| 24 | [Risk-Based Approaches to CSV](https://jafconsulting.com/understanding-risk-based-approaches-to-computer-system-validation-csv/) — JAF Consulting |
| 25 | [Delta Lake: Schema Enforcement & Evolution](https://www.databricks.com/blog/2019/09/24/diving-into-delta-lake-schema-enforcement-evolution.html) — Databricks |
| 26 | [Tracking Data Lifecycle Using Knowledge Graphs](https://ci-compass.org/resource-library/tech-notes-tracking-community-access-to-data-lifecycle-data-using-knowledge-graphs/) — CI Compass |
