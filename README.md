# XiCON Dance SCAIL - RunPod Serverless

XiCON Dance SCAIL animates characters using SCAIL pose embeddings and NLF motion capture from reference videos.

## Quick Start: RunPod Hub 배포

### Step 1: GitHub 리포지토리 생성

1. https://github.com/new 접속
2. Repository name: `XiCON_Dance_SCAIL_Runpod`
3. **"Add a README file" 체크 해제**
4. Create repository 클릭

### Step 2: GitHub에 푸시

```bash
cd /Users/blendx/Documents/XiCON/runpod/Wan_Animate_Runpod_hub_v2/XiCON_Wan_Animate_Serverless

# GitHub 리포지토리 연결 (YOUR_USERNAME을 실제 사용자명으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/XiCON_Dance_SCAIL_Runpod.git

# 푸시
git push -u origin main
```

### Step 3: RunPod Hub에서 빌드

1. https://www.runpod.io/console/hub 접속
2. "Create Template" 또는 "Add Serverless" 클릭
3. "From GitHub" 선택
4. 방금 생성한 리포지토리 연결
5. 빌드가 자동으로 시작됩니다 (약 30-60분 소요)

### Step 4: 엔드포인트 생성

1. 빌드 완료 후 "Deploy" 클릭
2. GPU 선택: ADA_24 또는 ADA_32_PRO
3. 엔드포인트 생성

---

## 기술 사양

| 항목 | 값 |
|------|-----|
| Base Image | `wlsdml1114/multitalk-base:1.7` |
| CUDA | 12.8 |
| GPU | ADA_24, ADA_32_PRO |
| Container Disk | 50GB |
| onnxruntime-gpu | **1.22.0** (NOT 1.23.x) |

## 모델 (자동 다운로드)

- SCAIL Diffusion: `Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors`
- VAE: `Wan2.1_VAE.pth` (반드시 .pth 형식)
- LoRA: `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors`
- CLIP Vision: `clip_vision_h.safetensors`
- Text Encoder: `umt5-xxl-enc-bf16.safetensors`

## API 사용법

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `image_path` / `image_url` / `image_base64` | string | Yes | - | 참조 이미지 |
| `video_path` / `video_url` / `video_base64` | string | Yes | - | 댄스 영상 |
| `prompt` | string | Yes | - | 애니메이션 설명 |
| `negative_prompt` | string | No | - | 제외할 요소 |
| `seed` | int | Yes | - | 랜덤 시드 |
| `width` | int | Yes | 416 | 출력 너비 |
| `height` | int | Yes | 672 | 출력 높이 |
| `fps` | int | Yes | 24 | 프레임 레이트 |
| `cfg` | float | Yes | 1.0 | CFG 스케일 |
| `steps` | int | No | 6 | 디노이징 스텝 |

### Example Request

```json
{
  "input": {
    "image_url": "https://example.com/character.jpg",
    "video_url": "https://example.com/dance.mp4",
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

### Response

```json
{
  "video": "<base64-encoded-video>"
}
```

## 워크플로우 노드 ID

| Node ID | Purpose | Parameter |
|---------|---------|-----------|
| 106 | LoadImage | `image` |
| 130 | VHS_LoadVideo | `video`, `force_rate` |
| 203 | Width | `value` |
| 204 | Height | `value` |
| 238 | CFG | `value` |
| 348 | Sampler | `seed` |
| 349 | Scheduler | `steps` |
| 368 | Text Encoder | `positive_prompt`, `negative_prompt` |
| 139 | Video Output | `frame_rate` |

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
- GPU가 ADA 아키텍처인지 확인

---

*Based on successful Wan_Animate_Runpod_hub_v2 implementation*
