# Skill 06: Hyperparameter Search (Post-processing HP)

## 목적
eval 데이터셋에서 최적의 post-processing hyperparameter를 탐색

## 신뢰 소스
- `entrypoint/ollm/hp_search.sh`
- `ollm/eval/hp_search.py`

---

## 실행 명령어

```bash
# Step 1: eval 추론 (Skill 04에서 이미 수행했을 수 있음)
python ollm/experiments/ollm/inference.py \
    --test_dataset out/linearised_datasets/wikipedia/eval_dataset.jsonl \
    --model andylolu24/ollm-wikipedia \
    --output_dir out/experiments/ollm/wikipedia/eval

# Step 2: eval 그래프 생성
python ollm/experiments/ollm/export_graph.py \
    --hierarchy_file out/experiments/ollm/wikipedia/eval/categorised_pages.jsonl \
    --output_dir out/experiments/ollm/wikipedia/eval

# Step 3: HP 탐색
python ollm/eval/hp_search.py \
    --graph out/experiments/ollm/wikipedia/eval/graph.json \
    --graph_true out/data/wikipedia/final/eval_graph.json \
    --num_samples 21 \
    --output_dir out/experiments/ollm/wikipedia
```

---

## HP 탐색 공간 (`hp_search.py`)

```python
absolute_percentiles = 1 - np.geomspace(1 / G.number_of_edges(), 1, num_samples)
# → 0에 가까운 값부터 ~1까지 21개 (기하급수적 간격)

relative_percentiles = 1 - np.geomspace(0.1, 1, num_samples) + 0.1
# → 0.1에서 1.0까지 21개

# 모든 조합: 21 × 21 = 441 조합
```

### 고정 파라미터
- `remove_self_loops`: True (기본값)
- `remove_inverse_edges`: True (기본값)

### 평가 메트릭
각 조합에 대해 `fuzzy_and_continuous_precision_recall_f1` 계산:
- `match_threshold=0.436`
- Continuous F1, Fuzzy F1 기록

---

## 파라미터
| 파라미터 | 값 | 출처 |
|---------|-----|------|
| num_samples | 21 | hp_search.sh |
| match_threshold | 0.436 | hp_search.py |
| embedding model | sentence-transformers/all-MiniLM-L6-v2 | graph_metrics.py |

---

## 출력
- `hp_search.jsonl`
- 각 줄:
```json
{
  "continuous_precision": 0.xxx,
  "continuous_recall": 0.xxx,
  "continuous_f1": 0.xxx,
  "fuzzy_precision": 0.xxx,
  "fuzzy_recall": 0.xxx,
  "fuzzy_f1": 0.xxx,
  "hp": {
    "absolute_percentile": 0.xxx,
    "relative_percentile": 0.xxx,
    "remove_self_loops": true,
    "remove_inverse_edges": true
  }
}
```

## 논문 vs 코드 일치 여부
| 항목 | 논문 | 코드 | 일치 |
|------|------|------|------|
| HP 탐색 존재 | Section 4.2에 언급 | 구현 있음 | O |
| 탐색 공간 크기 | 명시 안됨 | 21×21=441 | 코드 기준 |
| match_threshold | 0.436 (Appendix C) | 0.436 | O |
| embedding model | all-MiniLM-L6-v2 (Appendix C) | 동일 | O |
