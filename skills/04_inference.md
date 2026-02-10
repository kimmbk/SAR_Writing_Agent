# Skill 04: Inference

## 목적
파인튜닝된 모델로 test/eval 데이터셋에 대해 온톨로지 경로 생성

## 신뢰 소스
- `entrypoint/ollm/evaluate.sh` (inference 부분)
- `entrypoint/ollm/hp_search.sh` (inference 부분)
- `ollm/experiments/ollm/inference.py`

---

## 실행 명령어

### eval 데이터에 대한 추론 (HP 탐색용)
```bash
python ollm/experiments/ollm/inference.py \
    --test_dataset out/linearised_datasets/wikipedia/eval_dataset.jsonl \
    --model andylolu24/ollm-wikipedia \
    --output_dir out/experiments/ollm/wikipedia/eval
```

### test 데이터에 대한 추론 (최종 평가용)
```bash
python ollm/experiments/ollm/inference.py \
    --test_dataset out/linearised_datasets/wikipedia/test_dataset.jsonl \
    --model andylolu24/ollm-wikipedia \
    --output_dir out/experiments/ollm/wikipedia/test
```

### 직접 학습한 모델 사용 시
```bash
python ollm/experiments/ollm/inference.py \
    --test_dataset out/linearised_datasets/wikipedia/test_dataset.jsonl \
    --model out/experiments/ollm/wikipedia/train/checkpoint-final/merged \
    --output_dir out/experiments/ollm/wikipedia/test
```

---

## vLLM 설정 (`inference.py`)

| 파라미터 | 값 | 출처 |
|---------|-----|------|
| tensor_parallel_size | `torch.cuda.device_count()` | inference.py |
| max_num_batched_tokens | 4096 | inference.py |
| max_model_len | 8192 | inference.py |
| max_seq_len_to_capture | 4096 | inference.py |
| max_num_seqs | 512 | inference.py |
| block_size | 32 | inference.py |
| enable_chunked_prefill | True | inference.py |

## Sampling 파라미터

| 파라미터 | 값 | 출처 |
|---------|-----|------|
| temperature | 0.1 | inference.py |
| top_p | 0.9 | inference.py |
| max_tokens | 1024 | inference.py |
| seed | 0 | inference.py |
| stop | `["\n\n"]` | inference.py |

---

## 프롬프트 구성

```python
messages = [{"role": "user", "content": PROMPT_TEMPLATE.render(title=page["title"], abstract=page["abstract"])}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
```

### PROMPT_TEMPLATE
```
Title: {{ title }}
{{ abstract }}
```

---

## 입력
- `test_dataset.jsonl` 또는 `eval_dataset.jsonl`
- 각 줄: `{"id", "title", "abstract", "paths"}`
- 추론 시 `paths`는 사용하지 않음 (title, abstract만 사용)

## 출력
- `categorised_pages.jsonl`
- 각 줄: `{"id", "title", "abstract", "hierarchy"}`
- `hierarchy`: 모델이 생성한 텍스트 (예: `"Main topic classifications -> Science -> Physics\nMain topic classifications -> ..."`)

## Idempotent
- 스크립트 상단 주석: "This script is idempotent"
- 이미 처리된 ID는 건너뜀 (out_file에서 computed set 로드)
- 배치 크기: 5000 페이지씩 처리

---

## 사전 학습된 모델 (HuggingFace)
- Wikipedia: `andylolu24/ollm-wikipedia`
- arXiv: `andylolu24/ollm-arxiv`

## 논문 vs 코드 일치 여부
| 항목 | 논문 | 코드 | 일치 |
|------|------|------|------|
| temperature | 0.1 | 0.1 | O |
| top_p | 0.9 | 0.9 | O |
| max_tokens | 명시 안됨 | 1024 | 코드 기준 |
| stop token | 명시 안됨 | `\n\n` | 코드 기준 |
| vLLM 사용 | 명시 안됨 | vLLM | 코드 기준 |
