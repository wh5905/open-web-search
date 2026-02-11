# Open-Web-Search: 사용 시나리오 및 설정 가이드

## 1. 개요
**FlashRanker (v0.8.0)**의 도입으로 `open-web-search`는 초고속 응답부터 심층적인 정밀 검색까지 폭넓은 성능 스펙트럼을 제공하게 되었습니다.

본 문서는 다양한 사용자 니즈를 분석하고 그에 맞는 최적의 설정을 안내합니다.

## 2. 설정의 3대 축 (Configuration Dimensions)
검색 엔진의 동작은 다음 세 가지 주요 축에 의해 결정됩니다:

| 구분 | 옵션 A (경량/고속) | 옵션 B (중량/고품질) | 트레이드오프 (Trade-off) |
| :--- | :--- | :--- | :--- |
| **Search Mode** | `fast` | `deep` | 속도 vs 깊이/재현율 |
| **Reranker** | `fast` (Bi-Encoder) | `flash` (Cross-Encoder) | 지연시간 vs 정확도 |
| **Reader** | `trafilatura` (HTTP) | `browser` (Playwright) | 속도 vs 호환성 (JS) |

---

## 3. 추천 시나리오 (Recommended Scenarios)

### 시나리오 A: 실시간 RAG (챗봇)
**목표**: 사용자와 대화 중이며, 즉각적인 팩트 체크나 간단한 답변이 필요함. 지연시간은 3초 미만이어야 함.
- **프로필**: "지금 당장 답이 필요해. 깊게 파고들 필요는 없어."
- **추천 설정**:
  - `mode`: **"fast"** (제한시간 3초, 최대 증거 3개)
  - `reranker_type`: **"fast"** (일반적인 정보 검색에는 Bi-Encoder로 충분)
  - `reader_type`: **"trafilatura"** (무거운 브라우저 사용 안 함)
- **이유**: FlashRanker (Cross-Encoder)는 하드웨어에 따라 0.5~2초의 지연이 발생하여 "대화형" 경험을 해칠 수 있습니다.

### 시나리오 B: "심층 사고" 에이전트 (o1/DeepSeek-R1 스타일)
**목표**: AI가 복잡한 문제(코딩, 수학, 논리)를 풀고 있으며, 특정 세부 사항을 검증해야 함. 시간보다는 *정확성*이 생명.
- **프로필**: "생각 중입니다... 이 API 파라미터가 맞는지 100% 확신이 필요해."
- **추천 설정**:
  - `mode`: **"balanced"** (제한시간 10초)
  - `reranker_type`: **"flash"** (여기서 핵심입니다. "사과(과일)"와 "애플(주식)"을 정확히 구분해야 합니다.)
  - `reader_type`: **"trafilatura"** (스크래핑 실패 시에만 `browser`로 에스컬레이션)
- **이유**: CoT (Chain of Thought) 과정은 10-20초의 "사고 시간"을 허용합니다. FlashRanker의 정밀함은 환각(Hallucination)을 방지합니다.

### 시나리오 C: 자동화된 시장 조사 / 애널리스트
**목표**: 특정 분야(예: "2026년 AI 트렌드")에 대한 포괄적인 보고서 작성.
- **프로필**: "10분 동안 뒤져서 관련된 건 다 찾아와."
- **추천 설정**:
  - `mode`: **"deep"** (제한시간 30초, 최대 증거 10개, 재귀적 크롤링)
  - `reranker_type`: **"flash"** (100개 이상의 원문 청크를 정렬하려면 필수)
  - `reader_type`: **"browser"** (유료 뉴스나 JS가 많은 사이트를 뚫기 위해 필요)
- **이유**: 높은 재현율(Deep mode) + 높은 정밀도(FlashRanker)는 최고의 조합입니다. 응답 속도는 중요하지 않습니다.

### 시나리오 D: 기업/인트라넷 검색 (Enterprise)
**목표**: 비즈니스 의사결정에 영향을 주는 내부 문서나 특정 고가치 도메인 검색.
- **프로필**: "경쟁사의 공개 약관에서 해당 조항을 찾아줘."
- **추천 설정**:
  - `mode`: **"balanced"**
  - `reranker_type`: **"flash"**
  - `security.network_profile`: **"enterprise"**
  - `security.allowed_domains`: ["competitor.com"]
- **이유**: FlashRanker는 키워드 검색이 놓치는 미세한 문맥(예: 특정 법률 조항 찾기)을 찾아내는 데 탁월합니다.

---

## 4. 향후 로드맵 및 분석

### 4.1. 적응형 파이프라인 (Adaptive Pipeline, v0.9.0)
현재는 사용자가 선택해야 하지만, 미래 버전은 스스로 적응해야 합니다:
1.  **Auto-Rerank**: `fast`로 시작. 상위 점수가 0.3 미만이면 자동으로 `flash` 가동.
2.  **Auto-Browser**: `trafilatura`로 시작. 내용이 없거나 차단되면 `browser`로 즉시 전환 (현재의 Stealth Escalation을 더 스마트하게 발전).

### 4.2. 로컬 vs 클라우드
FlashRanker는 현재 로컬(`BAAI/bge-reranker-v2-m3`)에서 구동됩니다.
- **엣지 디바이스**: 4GB VRAM이 없는 노트북을 위해 `quantized` 모델 (ONNX) 필요.
- **서버**: 더 큰 모델(`bge-reranker-large`) 사용 가능.

---

## 5. 개발자를 위한 요약 매트릭스

| 필요 (Need) | 설정 프리셋 (Config) | 리랭커 (Reranker) | 예상 지연시간 | 품질 (Quality) |
| :--- | :--- | :--- | :--- | :--- |
| **채팅 / Q&A** | `fast` | `fast` | ~1.5초 | ⭐⭐ |
| **CoT 검증** | `balanced` | `flash` | ~5.0초 | ⭐⭐⭐⭐ |
| **심층 연구** | `deep` | `flash` | ~30초+ | ⭐⭐⭐⭐⭐ |
