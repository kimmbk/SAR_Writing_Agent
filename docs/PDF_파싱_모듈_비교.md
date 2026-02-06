# MinerU PDF 파싱 분석

## 목적

NRC 규정 문서 (SRP, DSRS, RG 1.206, NuScale DCA)를 파싱하여 구조화된 데이터로 변환

---

## 1. MinerU 개요

| 항목 | 내용 |
|------|------|
| GitHub | [opendatalab/MinerU](https://github.com/opendatalab/MinerU) |
| 설치 | `pip install mineru` |
| CPU 지원 | `pipeline` 백엔드 |
| 출력 형식 | Markdown, JSON |

---

## 2. Pipeline 백엔드 아키텍처

### 2.1 사용 모델

| 단계 | 모델 | 역할 |
|------|------|------|
| 레이아웃 감지 | DocLayout-YOLO | 문서 영역 분류 (블록) |
| 수식 감지 | MFD (YOLOv8 계열) | 수식 영역 탐지 |
| 수식 인식 | MFR | 수식 → LaTeX 변환 |
| OCR | PaddleOCR | 텍스트 인식 (스팬) |
| 테이블 인식 | RapidTable / UnetTable | 표 구조 추출 |

### 2.2 실행 플로우

```
PDF 입력
    ↓
┌─────────────────────────────────────────────────────────┐
│  1. PDF → 페이지 이미지 렌더                             │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│  2. Layout Detection (DocLayout-YOLO)                   │
│     → category_id 0(Title), 1(Text), 5(Table) 등 블록   │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│  3. Formula Detection/Recognition (MFD + MFR)           │
│     → category_id 13(InlineEq), 14(InterlineEq)         │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│  4. Table/Image Processing                              │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│  5. OCR / Text Extraction                               │
│     → category_id 15(OcrText) 스팬 생성                 │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│  6. 후처리 (model_json_to_middle_json.py)               │
│     → model.json → middle.json → content_list.json     │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 핵심 개념: 블록 vs 스팬

### 3.1 블록 (Block)

- **정의**: 레이아웃/테이블/수식 모델이 찾은 **"큰 네모"**
- **단위**: 문단, 제목 줄, 표 영역, 수식 영역
- **결정자**: DocLayout-YOLO + 테이블/수식 모델 (딥러닝)
- **category_id**: 0(Title), 1(Text), 2(Abandon), 5(TableBody), 13(InlineEquation) 등

### 3.2 스팬 (Span)

- **정의**: 블록 안의 텍스트를 더 잘게 쪼갠 **"작은 네모 조각들"**
- **단위**: 한 줄, 단어, 글자 조각
- **결정자**: PaddleOCR 또는 PDF 내장 텍스트 추출
- **category_id**: 15(OcrText)

### 3.3 관계

```
┌─────────────────────────────────────────┐
│  블록 (category_id = 1, Text)           │
│                                         │
│  ┌─────────┐ ┌─────────┐ ┌───────────┐ │
│  │ 스팬 15 │ │ 스팬 15 │ │  스팬 15  │ │
│  └─────────┘ └─────────┘ └───────────┘ │
│  ┌─────────────────┐ ┌───────────────┐ │
│  │    스팬 15      │ │    스팬 15    │ │
│  └─────────────────┘ └───────────────┘ │
└─────────────────────────────────────────┘

- 한 문단 블록 안에 여러 줄/단어/조각(span)이 들어감
- 후처리 단계에서 bbox 50% 이상 겹치면 해당 블록에 매칭
```

---

## 4. 출력 파일별 역할

### 4.1 model.json (모델 레벨)

**누가?** 딥러닝 모델들 (레이아웃/테이블/수식/OCR)

**무엇을?** 페이지 안의 "객체"를 찾아 기록

```json
{
  "layout_dets": [
    {"category_id": 0, "poly": [...], "score": 0.95},  // Title 블록
    {"category_id": 1, "poly": [...], "score": 0.92},  // Text 블록
    {"category_id": 15, "poly": [...], "text": "..."}  // OCR 스팬
  ]
}
```

**핵심**: Title/Text/표/수식 구분은 **딥러닝 모델이 직접 결정**하고 `category_id`에 저장

### 4.2 middle.json (룰 기반 후처리)

**누가?** `model_json_to_middle_json.py` 코드

**무엇을?** 블록에 스팬을 채우고, 읽기 순서로 정렬

```python
# 핵심 처리 흐름
text_blocks = magic_model.get_text_blocks()      # category_id=1 블록
title_blocks = magic_model.get_title_blocks()    # category_id=0 블록
spans = magic_model.get_all_spans()              # category_id=15 스팬

# 스팬을 블록에 매칭 (bbox 겹침 비율 ≥ 0.5)
spans = remove_outside_spans(spans, all_bboxes, all_discarded_blocks)
block_with_spans, spans = fill_spans_in_blocks(all_bboxes, spans, 0.5)
fix_blocks = fix_block_spans(block_with_spans)
sorted_blocks = sort_blocks_by_bbox(fix_blocks, page_w, page_h, footnote_blocks)
```

**핵심**: 새 모델을 안 돌림. 블록 합치기/나누기, 스팬 채우기, 읽기 순서 정렬만 수행

**type 결정 방식**:
- category_id=0 블록 → `type: "title"`
- category_id=1 블록 → `type: "text"`
- category_id=5 블록 → `type: "table_body"`

### 4.3 content_list.json (RAG-ready)

**용도**: RAG 인덱싱/LLM 입력에 직접 사용 가능한 플랫 리스트

```json
[
  {"type": "text", "text": "...", "page_idx": 0, "bbox": [...]},
  {"type": "table", "img_path": "...", "table_body": "<table>..."},
  {"type": "discarded", "text": "Page 1"}  // 헤더/푸터/페이지번호
]
```

---

## 5. CategoryId 정의

`mineru/utils/enum_class.py`:

| ID | 이름 | 설명 | 결정자 |
|:--:|------|------|--------|
| 0 | Title | 제목 블록 | Layout 모델 |
| 1 | Text | 본문 블록 | Layout 모델 |
| 2 | Abandon | 버릴 영역 (헤더/푸터) | Layout 모델 |
| 3 | ImageBody | 이미지 본체 | Layout 모델 |
| 4 | ImageCaption | 이미지 캡션 | Layout 모델 |
| 5 | TableBody | 표 본체 | Layout 모델 |
| 6 | TableCaption | 표 캡션 | Layout 모델 |
| 7 | TableFootnote | 표 각주 | Layout 모델 |
| 8 | InterlineEquation_Layout | 블록 수식 (레이아웃) | Layout 모델 |
| 13 | InlineEquation | 인라인 수식 | 수식 모델 |
| 14 | InterlineEquation_YOLO | 블록 수식 (YOLO) | 수식 모델 |
| **15** | **OcrText** | **텍스트 스팬** | **OCR 모델** |
| 16 | LowScoreText | 저신뢰 텍스트 | OCR 모델 |

---

## 6. 핵심 코드 위치

```
mineru/backend/pipeline/
├── model_json_to_middle_json.py   # model.json → middle.json 변환
├── pipeline_magic_model.py        # 블록/스팬 추출 래퍼 (MagicModel 클래스)
└── para_split.py                  # 문단 분리

mineru/utils/
├── enum_class.py                  # CategoryId, ContentType 정의
├── span_block_fix.py              # 스팬-블록 매칭
└── block_sort.py                  # 블록 정렬
```

---

## 7. 테스트 결과: RG 1.206

### 7.1 테스트 환경

| 항목 | 값 |
|------|-----|
| 입력 파일 | Regulatory Guide 1.206 |
| 원본 크기 | 15.7 MB |
| 파싱 방법 | `auto` |
| 백엔드 | `pipeline` (CPU) |

### 7.2 category_id 분포

| ID | 타입 | 개수 | 구분 |
|:--:|------|-----:|:----:|
| 0 | Title | 345 | 블록 |
| 1 | Text | 1,138 | 블록 |
| 2 | Abandon | 172 | 블록 |
| 5 | TableBody | 13 | 블록 |
| 13 | InlineEquation | 37 | 블록 |
| 15 | OcrText | 9,694 | **스팬** |
| **총계** | | **11,412** | |

- **블록**: 0+1+2+5+13 = 1,705개
- **스팬**: 15 = 9,694개
- 블록당 평균 스팬: ~5.7개

**핵심 인사이트**: category_id=15가 많아 보이는 건 "스팬 조각" 개수이기 때문. 실제 Title/Text/표/수식 블록 분류는 모델이 정상 수행함.

### 7.3 파싱 품질

| 항목 | 상태 | 상세 |
|------|:----:|------|
| 섹션/하위섹션 계층 | ✅ | `#` 마커 312개, 계층 정상 인식 |
| 참조 문서/CFR 조항 | ✅ | `10 CFR Part XX` 형식 정상 추출 |
| 목차 구조 | ⚠️ | 점(.)들 불규칙 (`.. . 8`) |
| 표 구조 | ⚠️ | Markdown 아님, HTML `<table>` 태그로 출력 |
| 표 내부 OCR | ⚠️ | 일부 한자 노이즈 (`厂` 등) |
| **§ 기호 인식** | ❌ | `§52.17` → `$\ S 5 2 . 1 7$` 완전 깨짐 |

#### 심각한 문제

**1. 섹션 기호(§) 깨짐**
```
원본: §52.17
출력: $\ S 5 2 . 1 7$
```
- LaTeX 수식으로 잘못 인식
- 글자 사이 공백 삽입

**2. 표가 Markdown 문법 아님**
```html
<!-- 실제 출력 -->
<table><tr><td>APPLICATION PART</td>...

<!-- 기대했던 출력 -->
| APPLICATION PART | COMBINED LICENSE | ...
```

**3. 목차 정렬 불규칙**
```
B. DISCUSSION .. . 8
C. STAFF REGULATORY GUIDANCE . 12
```

---

## 8. 백엔드 옵션

| 백엔드 | 설명 | GPU 필요 |
|--------|------|:--------:|
| **pipeline** | YOLO + OCR + 테이블 모듈 조합 | ❌ CPU 가능 |
| hybrid-auto-engine | pipeline + VLM 결합 (기본값) | ✅ |
| hybrid-http-client | 원격 서버 연결 | ❌ (서버 필요) |
| vlm-auto-engine | VLM 단일 모델 (end-to-end) | ✅ |
| vlm-http-client | VLM 원격 서버 연결 | ❌ (서버 필요) |

### 파싱 방법

| 방법 | 설명 |
|------|------|
| `auto` | 자동 판단 (텍스트/스캔) |
| `txt` | 텍스트 PDF (직접 추출) |
| `ocr` | 강제 OCR 적용 |

---

## 9. 다른 도구 비교

| 도구 | 방식 | CPU 속도 | 장점 | 단점 |
|------|------|:--------:|------|------|
| **MinerU** | 모듈식 (YOLO + OCR) | 보통 | 정밀, 구조 보존 | 설치 복잡 |
| Docling | RT-DETR + 규칙 | 빠름 | 단순 | 멀티모달 아님 |
| Unstructured | 자체 모델 | 느림 | RAG 특화 | 속도 문제 |
| PyMuPDF | 규칙 기반 | 매우 빠름 | 속도 | 구조 보존 약함 |
| pdfplumber | 규칙 기반 | 빠름 | 테이블 특화 | 레이아웃 이해 약함 |

---

## 10. 핵심 요약

### 전체 그림

```
┌─────────────────────────────────────────────────────────────────┐
│  1. 딥러닝 모델 (model.json)                                     │
│     - 레이아웃/표/수식/OCR 모델이 category_id와 bbox/텍스트 결정 │
│     - Title/Text/표/수식 구분은 여기서 완료                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. 룰 기반 후처리 (middle.json)                                 │
│     - 블록에 스팬 매칭 (bbox 겹침 50%)                           │
│     - 읽기 순서 정렬, 문단 분리                                  │
│     - 새 모델 안 돌림, 타입 유지                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. RAG-ready 리스트 (content_list.json)                        │
│     - 플랫 리스트로 변환                                         │
│     - discarded에 헤더/푸터/페이지번호 분리                      │
└─────────────────────────────────────────────────────────────────┘
```

### FAQ

**Q: Title/Text 구분은 누가 하나?**

A: **DocLayout-YOLO 모델**이 딥러닝으로 직접 결정
- category_id = 0 → Title
- category_id = 1 → Text

**Q: category_id=15가 왜 이렇게 많나?**

A: 15는 **OCR 스팬 (글자 조각)**
- 블록(큰 네모)이 아닌 스팬(작은 네모)
- 블록 1개에 스팬 여러 개가 들어감
- 개수가 많은 건 당연

**Q: middle.json의 type은 어떻게 결정되나?**

A: **model.json의 category_id 기반**으로 그대로 매핑
- category_id=0 → `type: "title"`
- category_id=1 → `type: "text"`
- 후처리는 스팬 매칭/정렬만 담당

---

## 참고 자료

- [MinerU GitHub](https://github.com/opendatalab/MinerU)
- [MinerU 문서](https://opendatalab.github.io/MinerU/)
- [MinerU Output Files](https://opendatalab.github.io/MinerU/reference/output_files/)
- [PDF-Extract-Kit](https://github.com/opendatalab/PDF-Extract-Kit)
- [DocLayout-YOLO](https://github.com/opendatalab/DocLayout-YOLO)
