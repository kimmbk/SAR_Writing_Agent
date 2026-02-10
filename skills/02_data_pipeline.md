# Skill 02: Data Pipeline

## 목적
Wikipedia 데이터셋 구축 (카테고리 수집 → 페이지 수집 → 그래프 생성 → 분할 → 선형화)

## 신뢰 소스
- `entrypoint/dataset/download_wikipedia.sh`
- `entrypoint/dataset/build_wikipedia.sh`
- `entrypoint/dataset/linearise_wikipedia.sh`

---

## 방법 A: 사전 빌드된 데이터 다운로드 (권장)

### 명령어
```bash
# download_wikipedia.sh
huggingface-cli download --revision v2 --repo-type dataset andylolu24/wiki-ol \
    train_eval_split/train_graph.json \
    train_eval_split/test_graph.json \
    train_test_split/test_graph.json

mkdir -p out/data/wikipedia/final
ln -s <download_path>/train_eval_split/train_graph.json out/data/wikipedia/final/train_graph.json
ln -s <download_path>/train_eval_split/test_graph.json out/data/wikipedia/final/eval_graph.json
ln -s <download_path>/train_test_split/test_graph.json out/data/wikipedia/final/test_graph.json
```

### 출력 파일 구조
```
out/data/wikipedia/final/
├── train_graph.json    # 학습용 (train_eval_split의 train)
├── eval_graph.json     # HP 탐색용 (train_eval_split의 test)
└── test_graph.json     # 최종 평가용 (train_test_split의 test)
```

---

## 방법 B: 처음부터 빌드 (build_wikipedia.sh)

### Step 1: 카테고리 수집
```bash
python ollm/dataset/wikipedia/build_categories.py \
    --max_depth 3 \
    --output_dir out/data/wikipedia/categories
```
- Wikipedia API로 "Main topic classifications" 루트에서 depth 3까지 카테고리 수집
- 출력: `raw_categories.jsonl`

### Step 2: 페이지 수집
```bash
python ollm/dataset/wikipedia/build_pages.py \
    --categories_file out/data/wikipedia/categories/raw_categories.jsonl \
    --output_dir out/data/wikipedia/pages
```
- 각 카테고리에 속한 Wikipedia 페이지의 title, abstract 수집
- 출력: `raw_pages.jsonl`

### Step 3: 그래프 생성
```bash
python ollm/dataset/wikipedia/export_graph.py \
    --categories_file out/data/wikipedia/categories/raw_categories.jsonl \
    --pages_file out/data/wikipedia/pages/raw_pages.jsonl \
    --output_dir out/data/wikipedia/full
```
- NetworkX DiGraph 생성
- 노드: {id, title, pages: [{id, title, abstract}]}
- 출력: `graph_depth_3.json`

### Step 4: Train/Test 분할
```bash
# 1차 분할: 50:50 (split_depth=1)
python ollm/dataset/train_test_split.py \
    --graph_file out/data/wikipedia/full/graph_depth_3.json \
    --split_depth 1 \
    --split_prop 0.5 \
    --output_dir out/data/wikipedia/train_test_split

# 2차 분할: train에서 다시 70:30
python ollm/dataset/train_test_split.py \
    --graph_file out/data/wikipedia/train_test_split/train_graph.json \
    --split_depth 1 \
    --split_prop 0.3 \
    --output_dir out/data/wikipedia/train_eval_split
```
- `split_depth=1`: 루트 바로 아래 subtree 단위로 분할
- `split_prop=0.5`: depth-1 노드의 50%를 test로
- `seed=0` (기본값)

### Step 5: 심볼릭 링크
```bash
mkdir -p out/data/wikipedia/final
ln -s out/data/wikipedia/train_eval_split/train_graph.json out/data/wikipedia/final/train_graph.json
ln -s out/data/wikipedia/train_eval_split/test_graph.json out/data/wikipedia/final/eval_graph.json
ln -s out/data/wikipedia/train_test_split/test_graph.json out/data/wikipedia/final/test_graph.json
```

---

## Step 6: 선형화 (linearise_wikipedia.sh)

```bash
for split in train eval test; do
    python ollm/experiments/build_linearised_dataset.py \
        --graph_file out/data/wikipedia/final/${split}_graph.json \
        --cutoff 5 \
        --num_workers 16 \
        --output_file out/linearised_datasets/wikipedia/${split}_dataset.jsonl
done
```

### 파라미터
| 파라미터 | 값 | 출처 |
|---------|-----|------|
| cutoff | 5 | `linearise_wikipedia.sh` |
| num_workers | 16 | `linearise_wikipedia.sh` |
| seed | 0 | `build_linearised_dataset.py` 기본값 |

### 출력 포맷 (JSONL, 한 줄 예시)
```json
{
  "id": 12345,
  "title": "Quantum computing",
  "abstract": "Quantum computing is ...",
  "paths": [
    ["Main topic classifications", "Science", "Physics", "Quantum mechanics", "Quantum computing"],
    ["Main topic classifications", "Technology", "Computing", "Quantum computing"]
  ]
}
```

### 핵심 로직 (`build_linearised_dataset.py`)
- graph-tool의 `all_paths(root → page_categories, cutoff=5)` 사용
- 페이지 노드를 임시로 그래프에 추가, 경로 탐색 후 제거
- 경로를 랜덤 셔플하여 저장

## 출력 파일 구조
```
out/linearised_datasets/wikipedia/
├── train_dataset.jsonl
├── eval_dataset.jsonl
└── test_dataset.jsonl
```

## 논문 vs 코드 일치 여부
| 항목 | 논문 | 코드 | 일치 |
|------|------|------|------|
| max_depth | 3 | 3 | O |
| split 방식 | depth-1에서 50:50, 다시 70:30 | 동일 | O |
| cutoff | 명시 안됨 | 5 | 코드 기준 |
| num_workers | 명시 안됨 | 16 | 코드 기준 |

## 데이터 규모 (논문 Table 7 기준)
| | Concepts | Relations | Documents |
|---|---------|-----------|-----------|
| Full | 13,886 | 28,375 | 362,067 |
| Train | 7,057 | 13,738 | 180,785 |
| Eval | 3,103 | 6,073 | 79,189 |
| Test | 7,053 | 14,760 | 185,057 |
