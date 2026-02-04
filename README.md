# XiCON Dance SCAIL - RunPod Serverless

XiCON Dance SCAIL animates characters using SCAIL pose embeddings and NLF motion capture from reference videos.

**GitHub**: https://github.com/bxone-git/XiCON-Dance-SCAIL-Serverless

---

## 빌드 및 배포 가이드

### Step 1: RunPod Hub 접속

1. https://www.runpod.io/console/serverless 접속
2. 로그인 (계정: wlsdml1114)

### Step 2: GitHub 연동 및 빌드

1. **"New Template"** 클릭
2. **"Build from GitHub"** 선택
3. GitHub 계정 연동 (bxone-git)
4. 저장소 선택: `bxone-git/XiCON-Dance-SCAIL-Serverless`
5. **"Build"** 클릭

### Step 3: 빌드 대기

- 빌드 시간: **약 15-20분** (모델 다운로드 포함)
- 빌드 로그에서 진행 상황 확인 가능
- 성공 시 "Build complete" 메시지 표시

### Step 4: 엔드포인트 생성

1. 빌드 완료 후 **"Deploy"** 클릭
2. GPU 선택: **ADA_24** 또는 **ADA_32_PRO** (RTX 5090의 경우 적절한 옵션 선택)
3. Worker 설정:
   - Min Workers: 0 (비용 절감)
   - Max Workers: 1-3 (트래픽에 따라)
4. **"Create Endpoint"** 클릭

### Step 5: 테스트

```bash
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "image_url": "https://example.com/person.jpg",
      "prompt": "a person dancing gracefully"
    }
  }'
```

---

## 주요 특징

- **Default Video 내장**: 사용자는 이미지와 프롬프트만 입력하면 됨
- **Warm Start 최적화**: NLF 모델 및 default video가 Docker에 포함
- **SageAttention 가속**: RTX 5090/4090에서 최적화된 성능

---

## API 사용법

### 필수 파라미터

| Parameter | Type | Description |
|-----------|------|-------------|
| `image_url` / `image_base64` / `image_path` | string | 참조 이미지 (필수) |
| `prompt` | string | 애니메이션 설명 |

### 선택 파라미터 (모두 기본값 있음)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_url` / `video_base64` / `video_path` | string | Docker 내장 | 커스텀 댄스 영상 |
| `negative_prompt` | string | (중국어 기본값) | 제외할 요소 |
| `width` | int | 416 | 출력 너비 |
| `height` | int | 672 | 출력 높이 |
| `fps` | int | 24 | 프레임 레이트 |
| `cfg` | float | 1.0 | CFG 스케일 |
| `steps` | int | 6 | 디노이징 스텝 |
| `seed` | int | 0 | 랜덤 시드 |

### 최소 요청 예시

```json
{
  "input": {
    "image_url": "https://example.com/person.jpg",
    "prompt": "a person dancing gracefully"
  }
}
```

### 전체 파라미터 요청 예시

```json
{
  "input": {
    "image_url": "https://example.com/character.jpg",
    "video_url": "https://example.com/custom_dance.mp4",
    "prompt": "A person dancing gracefully",
    "negative_prompt": "blurry, distorted",
    "seed": 12345,
    "width": 416,
    "height": 672,
    "fps": 24,
    "cfg": 1.0,
    "steps": 6
  }
}
```

### 응답

```json
{
  "video": "<base64-encoded-mp4-video>"
}
```

---

## 기술 사양

| 항목 | 값 |
|------|-----|
| Base Image | `wlsdml1114/multitalk-base:1.7` |
| CUDA | 12.8 |
| GPU | ADA_24, ADA_32_PRO |
| Container Disk | 50GB |
| onnxruntime-gpu | **1.22.0** (NOT 1.23.x) |
| Default Resolution | 416x672 (Portrait) |
| Default FPS | 24 |
| Default Steps | 6 |

## 모델 목록 (Docker에 포함)

| Model | File |
|-------|------|
| Diffusion | `Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors` |
| VAE | `Wan2.1_VAE.pth` |
| LoRA | `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors` |
| CLIP Vision | `clip_vision_h.safetensors` |
| Text Encoder | `umt5-xxl-enc-bf16.safetensors` |
| Detection | `yolov10m.onnx`, `vitpose_h_wholebody_model.onnx` |
| NLF | `nlf_l_multi_0.3.2.torchscript` (미리 다운로드) |

---

## 워크플로우 노드 ID 매핑

| Node ID | Class | Parameter |
|---------|-------|-----------|
| 106 | LoadImage | `image` |
| 130 | VHS_LoadVideo | `video`, `force_rate` |
| 203 | INTConstant | `value` (width) |
| 204 | INTConstant | `value` (height) |
| 238 | FloatConstant | `value` (cfg) |
| 348 | WanVideoSamplerv2 | `seed` |
| 349 | WanVideoSchedulerv2 | `steps` |
| 368 | WanVideoTextEncodeCached | `positive_prompt`, `negative_prompt` |
| 139 | VHS_VideoCombine | `frame_rate` |

---

## 트러블슈팅

### 빌드 실패: onnxruntime 오류
- `onnxruntime-gpu==1.22.0`를 사용하고 있는지 확인
- 1.23.x 버전은 호환성 문제가 있음

### VAE 로드 실패
- `Wan2.1_VAE.pth` 형식을 사용하고 있는지 확인
- `.safetensors` 형식이 아닌 `.pth` 형식 필요

### ComfyUI 시작 실패
- `--use-sage-attention` 플래그가 entrypoint.sh에 있는지 확인
- GPU가 ADA/Blackwell 아키텍처인지 확인

### 비디오 출력 없음
- `XiCON_Dance_SCAIL_api.json`에서 Node 139의 `save_output: true` 확인

---

## 로컬 개발

```bash
# Docker 빌드
cd XiCON_Wan_Animate_Serverless
docker build -t xicon-dance-scail:latest .

# 로컬 테스트
docker run --gpus all -p 8188:8188 xicon-dance-scail:latest
```

---

## GitHub 업데이트 방법

```bash
cd /path/to/XiCON_Wan_Animate_Serverless

# 변경사항 커밋
git add .
git commit -m "Update: description"

# bxone-git에 push
git push bxone main
```

RunPod Hub에서 자동으로 새 빌드가 트리거됩니다.

---

*XiCON Dance SCAIL - Powered by Wan2.1 SCAIL & ComfyUI*


[![Runpod](https://api.runpod.io/badge/bxone-git/XiCON-Dance-SCAIL-Serverless)](https://console.runpod.io/hub/bxone-git/XiCON-Dance-SCAIL-Serverless)
