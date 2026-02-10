# Skill 07: Evaluation (Test Metrics)

## 목적
test 데이터셋에서 최종 메트릭 계산 (HP 탐색 결과의 best HP 사용)

## 신뢰 소스
- `entrypoint/ollm/evaluate.sh`
- `ollm/eval/test_metrics.py`
- `ollm/eval/graph_metrics.py`

---

## 실행 명령어

```bash
# Step 1: test 추론 (Skill 04)
python ollm/experiments/ollm/inference.py \
    --test_dataset out/linearised_datasets/wikipedia/test_dataset.jsonl \
    --model andylolu24/ollm-wikipedia \
    --output_dir out/experiments/ollm/wikipedia/test

# Step 2: test 그래프 생성 (Skill 05)
python ollm/experiments/ollm/export_graph.py \
    --hierarchy_file out/experiments/ollm/wikipedia/test/categorised_pages.jsonl \
    --output_dir out/experiments/ollm/wikipedia/test

# Step 3: 최종 메트릭 계산
python ollm/eval/test_metrics.py \
    --graph out/experiments/ollm/wikipedia/test/graph.json \
    --graph_true out/data/wikipedia/final/test_graph.json \
    --hp_search_result out/experiments/ollm/wikipedia/hp_search.jsonl \
    --output_file out/experiments/ollm/wikipedia/test_metrics.json
```

---

## 메트릭 (5종, `graph_metrics.py`)

### 1. Literal F1
```python
literal_prec_recall_f1(G, G_true)
```
- edge를 (parent_title, child_title) 문자열 쌍으로 비교
- 정확히 일치하는 edge만 카운트
- 논문 Table 1의 "Literal F1"

### 2. Continuous F1
```python
fuzzy_and_continuous_precision_recall_f1(G, G_true, match_threshold=0.436)
```
- edge를 (parent_embedding, child_embedding)으로 변환
- edge 간 유사도 = min(cosine_sim(u1,u2), cosine_sim(v1,v2))
- Hungarian algorithm으로 최적 매칭 → 매칭된 유사도 합
- 논문 Table 1의 "Continuous F1"

### 3. Fuzzy F1
- 같은 함수에서 동시 계산
- edge 간 유사도가 threshold(0.436) 이상이면 매칭
- any(axis=1) / any(axis=0)로 precision/recall
- 논문 Table 1의 "Fuzzy F1"

### 4. Graph F1
```python
graph_precision_recall_f1(G, G_true, direction="forward", n_iters=2)
```
- 노드를 embedding → SGConv(K=2, identity weights)로 이웃 정보 집계
- 노드 간 cosine similarity → Hungarian algorithm 매칭
- 논문 Table 1의 "Graph F1"

### 5. Motif Distance
```python
motif_distance(G, G_true, n=3)
```
- graph-tool의 `gt.motifs(G, 3)`: 3-node subgraph 패턴 추출
- 두 그래프의 motif 분포 비교 (L1 distance / 2)
- 논문 Table 1의 "Motif Dist." (낮을수록 좋음)

---

## 평가 파라미터 (코드에 하드코딩)

| 파라미터 | 값 | 출처 |
|---------|-----|------|
| match_threshold | 0.436 | test_metrics.py, 논문 Appendix C |
| embedding_model | sentence-transformers/all-MiniLM-L6-v2 | graph_metrics.py |
| SGConv n_iters | 2 | test_metrics.py |
| SGConv direction | forward | test_metrics.py |
| motif n | 3 | test_metrics.py |
| best_hp_metric | continuous_f1 | test_metrics.py 기본값 |
| skip_if_too_slow | False | test_metrics.py |

---

## Best HP 선택 로직
```python
best_hp = PostProcessHP(
    **max(hp_search_results, key=lambda x: x["continuous_f1"])["hp"]
)
```
- hp_search.jsonl에서 continuous_f1이 가장 높은 HP 선택
- 해당 HP로 test graph를 pruning 후 메트릭 계산

---

## 출력

### test_metrics.json
```json
{
  "num_nodes": ...,
  "num_edges": ...,
  "literal_precision": ...,
  "literal_recall": ...,
  "literal_f1": ...,
  "continuous_precision": ...,
  "continuous_recall": ...,
  "continuous_f1": ...,
  "fuzzy_precision": ...,
  "fuzzy_recall": ...,
  "fuzzy_f1": ...,
  "graph_precision": ...,
  "graph_recall": ...,
  "graph_f1": ...,
  "motif_dist": ...
}
```

### graph_final.json
- pruning 완료 + embedding 제거된 최종 그래프

---

## 논문 보고 결과 (Table 1, Wikipedia)

| 메트릭 | OLLM (논문) |
|--------|------------|
| Literal F1 | 0.093 |
| Fuzzy F1 | 0.570 |
| Continuous F1 | 0.357 |
| Graph F1 | 0.633 |
| Motif Dist. | 0.073 |

## 논문 vs 코드 일치 여부
| 항목 | 논문 | 코드 | 일치 |
|------|------|------|------|
| 5개 메트릭 | Table 1 | 모두 구현 | O |
| match_threshold | 0.436 (Appendix C) | 0.436 | O |
| embedding model | all-MiniLM-L6-v2 | 동일 | O |
| SGConv K | 명시 안됨 | 2 | 코드 기준 |
| best HP 기준 | 명시 안됨 | continuous_f1 | 코드 기준 |
| motif n | 명시 안됨 | 3 | 코드 기준 |
