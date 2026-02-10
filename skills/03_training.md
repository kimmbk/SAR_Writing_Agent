# Skill 03: Training (Finetuning)

## 목적
Mistral-7B를 Wikipedia 선형화 데이터셋으로 LoRA 파인튜닝 (masked loss regularisation 포함)

## 신뢰 소스
- `entrypoint/ollm/train_wikipedia.sh`
- `ollm/experiments/ollm/training/main_weighted.py`
- `ollm/experiments/ollm/training/config.py`

---

## 실행 명령어

```bash
# train_wikipedia.sh (GPU 2장 가정)
accelerate launch --multi_gpu \
    ollm/experiments/ollm/training/main_weighted.py \
    --config ollm/experiments/ollm/training/config.py \
    --config.wandb.notes "Masked loss" \
    --config.model.name mistralai/Mistral-7B-Instruct-v0.2 \
    --config.train.epochs 2 \
    --config.train.batch_size 8 \
    --config.data.train_file out/linearised_datasets/wikipedia/train_dataset.jsonl \
    --config.data.eval_file out/linearised_datasets/wikipedia/eval_dataset.jsonl \
    --config.output_dir out/experiments/ollm/wikipedia/train
```

---

## 하이퍼파라미터 (config.py + train_wikipedia.sh 오버라이드)

### 모델
| 파라미터 | 값 | 출처 |
|---------|-----|------|
| base model | `mistralai/Mistral-7B-Instruct-v0.2` | sh + config.py |
| response_template (token IDs) | `[733, 28748, 16289, 28793]` (_[/INST]) | config.py |
| instruction_template (token IDs) | `[733, 16289, 28793]` (_[INST]) | config.py |

### 학습
| 파라미터 | 값 | 출처 |
|---------|-----|------|
| epochs | 2 | sh 오버라이드 (config: 2.0) |
| batch_size (per device) | 8 | sh 오버라이드 (config: 16) |
| learning_rate | 1e-5 | config.py |
| lr_scheduler | constant_with_warmup | main_weighted.py |
| warmup_steps | 100 | config.py |
| max_seq_length | 2048 | config.py |
| grad_acc_steps | 1 | config.py |
| group_by_length | True | config.py |
| optimizer | adamw_torch_fused | main_weighted.py |
| gradient_checkpointing | True | main_weighted.py |
| fp16/bf16 | auto (bf16 if supported) | main_weighted.py |
| seed | 0 | config.py |

### LoRA
| 파라미터 | 값 | 출처 |
|---------|-----|------|
| rank | 32 | config.py |
| alpha | 16 | config.py |
| dropout | 0 | config.py |
| target_modules | q,k,v,o,gate,up,down_proj | main_weighted.py |
| task_type | CAUSAL_LM | main_weighted.py |

### 데이터
| 파라미터 | 값 | 출처 |
|---------|-----|------|
| train_size | placeholder (전체 사용) | config.py |
| eval_size | 1024 | config.py |
| dataset_num_proc | 16 | main_weighted.py |

### 평가 (학습 중)
| 파라미터 | 값 | 출처 |
|---------|-----|------|
| eval_steps | 500 | config.py |
| save_steps | 500 (= eval_steps) | main_weighted.py |
| logging_steps | 50 | config.py |
| num_generate_samples | 5 | config.py |

---

## Masked Loss Regularisation (핵심 차별점)

### 구현 위치: `main_weighted.py` > `Trainer._prepare_dataset()`

### 로직
1. 전체 학습 데이터에서 edge별 출현 빈도 카운트
   ```python
   edge_counts: defaultdict[tuple, int] = defaultdict(int)
   for example in dataset:
       for path in example["paths"]:
           for u, v in zip(path[:-1], path[1:]):
               edge_counts[(u, v)] += 1
   ```

2. 빈도 역수로 가중치 계산 (평균 빈도로 정규화)
   ```python
   mean_edge_count = np.mean(list(edge_counts.values()))
   edge_weights = {k: mean_edge_count / v for k, v in edge_counts.items()}
   ```

3. 토크나이제이션 시, 각 edge(word pair)에 대해 확률적 마스킹
   ```python
   ignore = random.random() > edge_weights[(prev_word, word)]
   ```
   - edge_weight > 1 (저빈도): 항상 학습
   - edge_weight < 1 (고빈도): 확률적으로 마스킹

4. 두 종류의 label 생성
   - `labels`: 표준 (response 전체 학습) → eval 시 사용
   - `labels_detailed`: masked → train 시 사용

### Custom Trainer
```python
class Trainer(SFTTrainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        if not model.training:
            outputs = model(input_ids=inputs["input_ids"], labels=inputs["labels"])
        else:
            outputs = model(input_ids=inputs["input_ids"], labels=inputs["labels_detailed"])
```

### Custom DataCollator
- `labels`: `torch.where(ignores, -100, input_ids)`
- `labels_detailed`: `torch.where(ignores_detailed, -100, input_ids)`
- padding: `pad_to_multiple_of=8`, right padding

---

## 프롬프트 템플릿

### 입력 (PROMPT_TEMPLATE)
```
Title: {{ title }}
{{ abstract }}
```

### 출력 (RESPONSE_TEMPLATE)
```
{% for path in paths %}
{{ path | join(" -> ") }}
{% endfor %}
```

### Chat 형식 (Mistral)
```
[INST] Title: Quantum computing
Quantum computing is a type of computation... [/INST]
Main topic classifications -> Science -> Physics -> Quantum mechanics
Main topic classifications -> Technology -> Computing
</s>
```

---

## 모델 병합 (학습 후)

```bash
python ollm/experiments/ollm/training/export_model.py \
    --checkpoint_dir out/experiments/ollm/wikipedia/train/checkpoint-final
```
- LoRA adapter를 base model에 병합
- 출력: `checkpoint-final/merged/`

---

## 출력 파일 구조
```
out/experiments/ollm/wikipedia/train/
├── checkpoint-500/
├── checkpoint-1000/
├── ...
├── checkpoint-final/
│   └── merged/        # export_model.py 후 생성
└── runs/              # tensorboard logs
```

## 논문 vs 코드 일치 여부
| 항목 | 논문 | 코드 | 일치 |
|------|------|------|------|
| Model | Mistral-7B-Instruct-v0.2 | 동일 | O |
| LoRA rank | 32 | 32 | O |
| LoRA alpha | 16 | 16 | O |
| Learning rate | 1e-5 | 1e-5 | O |
| Epochs | 2 | 2 | O |
| Batch size | 논문 명시 안됨 | 8 per device (sh), 16 (config default) | 코드 기준 |
| Masked loss | 논문 Section 3.2 수식과 개념 일치 | 구현 일치 | O |
| Regulariser 수식 | max(1-M/n, 0) | `mean/count` (동일 효과) | O (표현 다름) |
| chat template | Mistral format | 하드코딩 token IDs | O |
