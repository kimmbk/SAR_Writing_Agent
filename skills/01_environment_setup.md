# Skill 01: Environment Setup

## 목적
OLLM 논문 재현을 위한 실행 환경 구축

## 신뢰 소스
- GitHub: https://github.com/andylolu2/ollm
- 파일: `pyproject.toml`

## 실험 환경 (논문/코드 기준)

### 플랫폼
- **OS**: Linux-64 (pixi.toml에 `platforms = ["linux-64"]`로 명시)
- **Python**: 3.11.*
- **패키지 매니저**: pixi (conda-forge 채널)

### GPU 요구사항
- 학습: GPU 2장 가정 (`train_wikipedia.sh`: `accelerate launch --multi_gpu`, batch_size 8)
- 추론: vLLM, `tensor_parallel_size=torch.cuda.device_count()`
- 논문/코드에 GPU 모델 명시되지 않음

### 핵심 의존성
```
# conda-forge (pixi)
python=3.11.*
graph-tool
numba

# pip (pyproject.toml)
torch>=2.2
vllm>=0.3
transformers
peft
trl
accelerate
torch-geometric
ml-collections
networkx
datasets
absl-py
wandb
tensorboardx
scikit-learn
evaluate
kaggle
arxiv-base
scienceplots
```

### graph-tool 설치 주의
- pip으로 설치 불가, conda-forge 전용
- Windows 미지원 → **Linux 필수**
- 평가 단계(hp_search, test_metrics)의 motif_distance에서 사용

## 실행 명령어

```bash
# pixi 설치 (저자 권장 방식)
curl -fsSL https://pixi.sh/install.sh | bash

# 프로젝트 환경 구축
cd ollm
pixi install

# 또는 conda로 수동 설치
conda create -n ollm python=3.11
conda activate ollm
conda install -c conda-forge graph-tool numba
pip install -e .
```

## 환경 변수
```bash
# .env 파일 (모든 sh 스크립트가 로드)
# 논문/코드에 필수 환경변수 명시되지 않음
# wandb, huggingface token이 필요할 수 있음
WANDB_API_KEY=<your_key>
HF_TOKEN=<your_token>
```

## 논문 vs 코드 일치 여부
| 항목 | 논문 | 코드 | 일치 |
|------|------|------|------|
| Python 버전 | 명시 안됨 | 3.11 | 코드 기준 |
| GPU 수 | 명시 안됨 | 2 (주석) | 코드 기준 |
| 패키지 매니저 | 명시 안됨 | pixi | 코드 기준 |
| OS | 명시 안됨 | linux-64 | 코드 기준 |
