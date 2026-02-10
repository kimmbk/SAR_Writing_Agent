# OLLM 재현 실행 가이드 (A100 서버)

## 사전 조건
- Linux + CUDA GPU (A100 권장)
- conda 설치됨
- 인터넷 접속 가능

---

## 전체 실행 명령어

```bash
# === 1. 작업 디렉토리 ===
mkdir -p ~/ollm && cd ~/ollm

# === 2. 코드 클론 ===
git clone https://github.com/andylolu2/ollm.git
cd ollm

# === 3. 환경 설치 ===
conda create -n ollm python=3.11 -y
conda activate ollm
conda install -c conda-forge graph-tool numba -y
pip install -e .

# === 4. 로그인 (필요시) ===
wandb login
huggingface-cli login

# === 5. GPU 확인 ===
nvidia-smi

# === 6. 데이터 다운로드 ===
bash entrypoint/dataset/download_wikipedia.sh

# === 7. 선형화 ===
bash entrypoint/dataset/linearise_wikipedia.sh

# === 8. 학습 ===
# ※ GPU 2장 기준. 1장이면 batch_size 조정 필요
bash entrypoint/ollm/train_wikipedia.sh

# === 9. 모델 병합 ===
python ollm/experiments/ollm/training/export_model.py \
    --checkpoint_dir out/experiments/ollm/wikipedia/train/checkpoint-final

# === 10. HP 탐색 (eval set) ===
bash entrypoint/ollm/hp_search.sh wikipedia

# === 11. 최종 평가 (test set) ===
bash entrypoint/ollm/evaluate.sh wikipedia

# === 12. 결과 확인 ===
cat out/experiments/ollm/wikipedia/test_metrics.json
```

---

## 학습 건너뛰기 (저자 공개 모델 사용)

직접 학습 없이 저자가 HuggingFace에 공개한 모델로 평가만 하려면:

```bash
# Step 6, 7 실행 후 바로:
bash entrypoint/ollm/hp_search.sh wikipedia
bash entrypoint/ollm/evaluate.sh wikipedia
cat out/experiments/ollm/wikipedia/test_metrics.json
```

hp_search.sh와 evaluate.sh가 `andylolu24/ollm-wikipedia` 모델을 자동으로 사용함.

---

## GPU 수에 따른 batch_size 조정

`train_wikipedia.sh`의 주석: "Assume 2 GPUs. Adjust batch size if using less/more GPUs."

| GPU 수 | batch_size (per device) | 변경 방법 |
|--------|------------------------|----------|
| 2장 | 8 (기본값) | 변경 불필요 |
| 1장 | 8 또는 4 | `--config.train.batch_size 8` |
| 4장 | 4 | `--config.train.batch_size 4` |

총 effective batch size = GPU 수 × per_device_batch_size × grad_acc_steps

---

## 기대 결과 (논문 Table 1)

| 메트릭 | OLLM (논문 보고값) |
|--------|-------------------|
| Literal F1 | 0.093 |
| Fuzzy F1 | 0.570 |
| Continuous F1 | 0.357 |
| Graph F1 | 0.633 |
| Motif Dist. | 0.073 |

---

## 트러블슈팅

### graph-tool 설치 실패
```bash
# pip 아닌 conda-forge에서만 설치 가능
conda install -c conda-forge graph-tool -y
```

### vLLM GPU 메모리 부족
```bash
# inference.py의 max_model_len 줄이기 (기본 8192)
# 또는 tensor_parallel_size가 GPU 수와 맞는지 확인
```

### wandb 안 쓰려면
```bash
export WANDB_MODE=disabled
```

### Mistral 모델 접근 권한
- https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2 에서 accept license
- `huggingface-cli login` 후 토큰 입력

---

## 상세 파라미터 참조
- 각 단계별 파라미터: `skills/01~07_*.md`
- 파이프라인 총괄: `skills/00_pipeline_overview.md`
