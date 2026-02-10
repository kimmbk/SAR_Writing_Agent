# Skill 05: Export Graph (Post-processing)

## 목적
모델 생성 텍스트를 파싱하여 NetworkX DiGraph로 변환

## 신뢰 소스
- `entrypoint/ollm/evaluate.sh` (export_graph 부분)
- `ollm/experiments/ollm/export_graph.py`
- `ollm/experiments/post_processing.py`

---

## 실행 명령어

```bash
# eval용
python ollm/experiments/ollm/export_graph.py \
    --hierarchy_file out/experiments/ollm/wikipedia/eval/categorised_pages.jsonl \
    --output_dir out/experiments/ollm/wikipedia/eval

# test용
python ollm/experiments/ollm/export_graph.py \
    --hierarchy_file out/experiments/ollm/wikipedia/test/categorised_pages.jsonl \
    --output_dir out/experiments/ollm/wikipedia/test
```

---

## 파싱 로직 (`export_graph.py`)

### 정규식 패턴
```python
pattern = re.compile(r"Main topic classifications( -> ((?!(\n|->)).)+)+")
```
- "Main topic classifications"으로 시작
- " -> "로 구분된 경로
- 유효하지 않은 줄은 카운트만 하고 건너뜀

### 그래프 구성
```python
for (parent, child), count in hypernyms.items():
    G.add_node(parent, title=parent)
    G.add_node(child, title=child)
    G.add_edge(parent, child, weight=count)
```
- edge의 `weight` = 해당 (parent, child) 쌍이 전체 추론 결과에서 등장한 횟수
- 노드의 `id` = 노드의 `title` (문자열 그 자체)

---

## Post-processing (`post_processing.py`)

### 5단계 pruning (evaluate 시 적용)

export_graph.py 자체는 pruning을 하지 않음.
Pruning은 hp_search.py와 test_metrics.py에서 `post_process()` 함수로 수행.

```python
@dataclass
class PostProcessHP:
    absolute_percentile: float = 0      # 하위 X% edge 제거
    relative_percentile: float = 1      # 각 노드에서 상위 X% edge만 유지
    remove_self_loops: bool = True
    remove_inverse_edges: bool = True
```

### Pruning 순서
1. **absolute_percentile_edges**: weight 기준 하위 percentile 제거
2. **relative_percentile_edges**: 각 노드의 outgoing edges에서 nucleus pruning
3. **inverse_edges**: (u,v)와 (v,u) 둘 다 존재 시 weight 작은 쪽 제거
4. **self_loops**: u==v인 edge 제거
5. **root 보정**: root 노드 없으면 "Main topic classifications" 추가, in-degree 0인 노드에 edge 연결

---

## 입력
- `categorised_pages.jsonl` (Skill 04의 출력)

## 출력
- `graph.json` (NetworkX node_link_data 포맷)

## 논문 vs 코드 일치 여부
| 항목 | 논문 | 코드 | 일치 |
|------|------|------|------|
| 파싱 정규식 | 명시 안됨 | `Main topic classifications( -> ...)+ ` | 코드 기준 |
| edge weight | 출현 빈도 | 동일 | O |
| pruning 종류 | Section 3.3에 기술 | 코드와 일치 | O |
| pruning 순서 | 명시 안됨 | 코드 순서대로 | 코드 기준 |
