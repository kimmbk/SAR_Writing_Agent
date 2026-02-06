# SAR Writing Agent

SMR(소형모듈원자로) SAR(안전분석보고서) 문서 자동화 시스템

## 목표

설계 데이터를 입력하면 SAR 문서를 자동 생성/검토하는 에이전트 시스템 구축

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   설계 데이터    │ ──▶ │  SAR 에이전트   │ ──▶ │   SAR 문서      │
│  (도면, 사양)   │     │  (LLM + Tools)  │     │   (초안)        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     지식그래프       │
                    │  (규정, 패턴, 매핑)  │
                    └─────────────────────┘
```

## 프로젝트 구조

```
SAR_Writing_Agent/
├── docs/                    # 프로젝트 문서
│   ├── NRC_규제체계_공부노트.md
│   ├── SMR_SAR_가이드.md
│   ├── SAR_자동화시스템_RFP.md
│   ├── 문서목록.md
│   ├── 개발자_질문지.md
│   └── PDF_파싱_모듈_비교.md
├── documents/               # 원본 문서
│   ├── 규정문서/
│   │   └── RG_1.206/
│   └── 국내자료/
│       └── DSRS_보고서/
├── MinerU/                  # MinerU PDF 파싱
│   └── output/
└── pdfplumber_test/         # pdfplumber 테스트
```

## 핵심 기능

| 기능 | 설명 |
|------|------|
| SAR 섹션 자동 생성 | 설계 데이터 + 템플릿 → SAR 초안 |
| 일관성 검증 | 챕터 간 수치/용어 불일치 탐지 |
| 요구사항 추적 | SRP 요구사항 ↔ SAR 섹션 매핑 |
| 설계 변경 관리 | 변경 시 영향받는 섹션 자동 식별 |
| RAI 대응 지원 | 규제 질의에 대한 근거 문서 검색 |

## 기술 스택

- **지식그래프**: Neo4j
- **RAG**: GraphRAG + VectorDB
- **온톨로지**: DIAMOND (원자력 도메인)
- **PDF 파싱**: MinerU, pdfplumber
- **LLM**: TBD

## 참고 문서

| 문서 | 설명 |
|------|------|
| [RG 1.206](https://www.nrc.gov/docs/ML1813/ML18131A181.pdf) | SAR 작성 가이드 |
| [SRP (NUREG-0800)](https://www.nrc.gov/reading-rm/doc-collections/nuregs/staff/sr0800/index) | NRC 검토 기준 |
| [DIAMOND](https://github.com/idaholab/DIAMOND) | 원자력 온톨로지 |

## 진행 상황

- [x] NRC 규제체계 분석
- [x] PDF 파싱 테스트 (MinerU, pdfplumber)
- [x] 시스템 아키텍처 설계
- [x] 에이전트 Tool 설계
- [ ] 규정문서 VectorDB 적재
- [ ] 지식그래프 스키마 구현
- [ ] 에이전트 개발

## License

TBD
