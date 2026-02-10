# OLLM 재현 파이프라인 총괄

## 논문
- **Title**: End-to-End Ontology Learning with Large Language Models
- **Venue**: NeurIPS 2024
- **Authors**: Andy Lo, Albert Jiang, et al.
- **GitHub**: https://github.com/andylolu2/ollm
- **HuggingFace**: andylolu24/wiki-ol (데이터), andylolu24/ollm-wikipedia (모델)

---

## 전체 실행 순서

```
Skill 01: Environment Setup
    │
    ▼
Skill 02: Data Pipeline
    │   download_wikipedia.sh 또는 build_wikipedia.sh
    │   → linearise_wikipedia.sh
    │   출력: train/eval/test_dataset.jsonl
    │
    ▼
Skill 03: Training
    │   train_wikipedia.sh
    │   → export_model.py
    │   출력: checkpoint-final/merged/
    │
    ▼
Skill 04: Inference (eval)          Skill 04: Inference (test)
    │   inference.py (eval)              │   inference.py (test)
    │   출력: eval/categorised.jsonl     │   출력: test/categorised.jsonl
    │                                    │
    ▼                                    ▼
Skill 05: Export Graph (eval)       Skill 05: Export Graph (test)
    │   export_graph.py                  │   export_graph.py
    │   출력: eval/graph.json            │   출력: test/graph.json
    │                                    │
    ▼                                    │
Skill 06: HP Search                      │
    │   hp_search.py                     │
    │   출력: hp_search.jsonl            │
    │                                    │
    └──────────────┬─────────────────────┘
                   │
                   ▼
            Skill 07: Evaluation
                │   test_metrics.py
                │   출력: test_metrics.json
                │         graph_final.json
```

---

## 실행 명령어 요약 (전체 파이프라인)

```bash
# === 01. 환경 설정 ===
pixi install  # 또는 conda + pip

# === 02. 데이터 ===
bash entrypoint/dataset/download_wikipedia.sh
bash entrypoint/dataset/linearise_wikipedia.sh

# === 03. 학습 ===
bash entrypoint/ollm/train_wikipedia.sh
python ollm/experiments/ollm/training/export_model.py \
    --checkpoint_dir out/experiments/ollm/wikipedia/train/checkpoint-final

# === 04-05. 추론 + 그래프 (eval) ===
bash entrypoint/ollm/hp_search.sh wikipedia

# === 04-05. 추론 + 그래프 (test) + 06-07. HP탐색 + 평가 ===
bash entrypoint/ollm/evaluate.sh wikipedia
```

---

## 사전 학습 모델로 Skill 03 건너뛰기 (빠른 재현)

저자가 HuggingFace에 학습 완료 모델을 공개함:
- `andylolu24/ollm-wikipedia`
- `andylolu24/ollm-arxiv`

이 모델을 사용하면 Skill 03(학습)을 건너뛰고 Skill 04부터 시작 가능.
`hp_search.sh`와 `evaluate.sh`가 이미 이 모델을 기본으로 사용.

---

## 논문 Figure/Table ↔ 스크립트 매핑

| 논문 항목 | 내용 | 생성 스크립트 | 설정 |
|----------|------|-------------|------|
| **Table 1** | Wikipedia 메트릭 비교 | `test_metrics.py` | best HP from hp_search |
| **Table 2** | arXiv 메트릭 비교 | `test_metrics.py` | dataset=arxiv |
| **Table 7** | 데이터셋 통계 | `build_wikipedia.sh` 출력 로그 | - |
| **Figure 2** | 파이프라인 다이어그램 | 해당 없음 (개념도) | - |
| **Figure 3** | Ground truth vs 생성 비교 | `graph_final.json` 시각화 | 논문/코드에 시각화 스크립트 명시 안됨 |
| **Figure 4** | Ablation (masked loss) | `train_wikipedia.sh` 변형 | `main.py`(no mask) vs `main_weighted.py`(mask) |
| **Figure 5** | HP sensitivity | `hp_search.py` 결과 | 441개 조합의 continuous_f1 |

---

## 재현 시 알려진 제약사항

1. **OS**: Linux-64 필수 (graph-tool, vLLM)
2. **GPU**: 최소 1장 (추론), 2장 권장 (학습)
3. **디스크**: Wikipedia 데이터 + 모델 + 체크포인트 ≈ 50GB+
4. **메모리**: vLLM 추론 시 GPU VRAM 16GB+ 필요
5. **시간**: 학습 ~수시간 (A100 2장 기준, 논문/코드에 명시 안됨)
6. **graph-tool**: conda-forge에서만 설치 가능, pip 불가

---

## 파일 구조 (skills/)

```
skills/
├── 00_pipeline_overview.md     ← 이 파일 (총괄)
├── 01_environment_setup.md     ← 환경 설정
├── 02_data_pipeline.md         ← 데이터 수집/전처리/선형화
├── 03_training.md              ← Mistral-7B LoRA 파인튜닝
├── 04_inference.md             ← vLLM 추론
├── 05_export_graph.md          ← 텍스트→그래프 변환
├── 06_hp_search.md             ← Post-processing HP 탐색
└── 07_evaluation.md            ← 최종 메트릭 계산
```
