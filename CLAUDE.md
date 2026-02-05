# CLAUDE.md

XiCON Dance SCAIL - RTX 5090 Serverless 패키지

## Project Overview

XiCON Dance SCAIL - SCAIL 14B 기반 댄스 애니메이션 생성
- SCAIL pose embeddings + NLF motion capture
- 이미지 → 댄스 비디오 변환
- **RTX 5090 (Blackwell SM120) 전용**

## Key Specifications

| Component | Version |
|-----------|---------|
| Base Image | nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04 |
| PyTorch | 2.7+ |
| CUDA | **12.8 (Required)** |
| Target GPU | RTX 5090 (SM120, Compute Capability 12.0) |
| SageAttention | 2.2+ (SageAttention2++ kernels) |
| Docker Tag | `blendx/xicon-dance-scail:5090` |

## Build & Deploy Commands

```bash
# Build Docker image (must use linux/amd64 for RunPod)
docker build --platform linux/amd64 -t blendx/xicon-dance-scail:5090 .

# Push to Docker Hub
docker push blendx/xicon-dance-scail:5090

# Deploy to RunPod Serverless
# 1. Go to RunPod Console → Serverless → New Endpoint
# 2. Select "Custom Image"
# 3. Image: blendx/xicon-dance-scail:5090
# 4. GPU: RTX 5090 (BLACKWELL_24)
```

## File Structure

```
├── Dockerfile           # CUDA 12.8 + PyTorch 2.7+ + SageAttention 2.2+
├── entrypoint.sh        # SageAttention2++ 활성화
├── handler.py           # RunPod serverless handler
├── XiCON_Dance_SCAIL_vFinal.json  # ComfyUI workflow
├── config.ini           # ComfyUI Manager config
├── assets/
│   └── default_video.mp4  # Default dance video
└── .runpod/
    ├── hub.json         # RunPod Hub 설정 (참조용)
    └── tests.json       # 테스트 설정 (참조용)
```

## Deployment Method

**GitHub → Docker Hub → RunPod Serverless 직접 배포**

1. GitHub에 코드 푸시
2. 로컬에서 Docker 이미지 빌드 (`docker build --platform linux/amd64 ...`)
3. Docker Hub에 푸시
4. RunPod Serverless에서 Custom Image로 배포

## Key Model Files

| Model | Path | Source |
|-------|------|--------|
| SCAIL Diffusion | `Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors` | Kijai/WanVideo_comfy_fp8_scaled |
| LoRA | `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors` | Kijai/WanVideo_comfy |
| VAE | `Wan2.1_VAE.pth` | Wan-AI/Wan2.1-T2V-14B |
| Text Encoder | `umt5-xxl-enc-bf16.safetensors` | Kijai/WanVideo_comfy |
| CLIP Vision | `clip_vision_h.safetensors` | Comfy-Org/Wan_2.1_ComfyUI_repackaged |

## handler.py Node ID Mapping

```python
prompt["106"]["inputs"]["image"] = image_path           # LoadImage
prompt["130"]["inputs"]["video"] = video_path           # VHS_LoadVideo
prompt["130"]["inputs"]["force_rate"] = fps             # force_rate
prompt["203"]["inputs"]["value"] = width                # INTConstant - width
prompt["204"]["inputs"]["value"] = height               # INTConstant - height
prompt["238"]["inputs"]["value"] = cfg                  # FloatConstant - cfg
prompt["348"]["inputs"]["seed"] = seed                  # WanVideoSamplerv2 - seed
prompt["349"]["inputs"]["steps"] = steps                # WanVideoSchedulerv2 - steps
prompt["368"]["inputs"]["positive_prompt"] = prompt     # WanVideoTextEncodeCached
prompt["368"]["inputs"]["negative_prompt"] = neg        # WanVideoTextEncodeCached
prompt["139"]["inputs"]["frame_rate"] = fps             # VHS_VideoCombine
```

## RTX 5090 Optimizations

1. **CUDA 12.8**: RTX 5090 (Blackwell) 필수
2. **SageAttention 2.2+**: SageAttention2++ 커널 활성화
3. **TORCH_CUDA_ARCH_LIST="12.0"**: SM120 아키텍처 최적화
4. **entrypoint.sh**: `SAGEATTENTION_ENABLED=1` 환경변수

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| CUDA error: no kernel image | 다른 GPU에서 실행 | RTX 5090 전용 이미지, 다른 GPU는 별도 이미지 필요 |
| SageAttention 오류 | 버전 불일치 | sageattention>=2.2.0 확인 |
| 모델 로딩 실패 | 파일명 불일치 | workflow JSON과 다운로드 경로 확인 |
| Cold start 느림 | SCAIL 14B 로딩 | 최소 180초 대기 설정 |

## API Input Format

```json
{
  "input": {
    "image_url": "https://example.com/image.jpg",
    "video_url": "https://example.com/dance.mp4",
    "prompt": "the person starts to dance",
    "width": 416,
    "height": 672,
    "steps": 6,
    "cfg": 1.0,
    "seed": 0,
    "fps": 24
  }
}
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 5090-v1.0.0 | 2026-02-05 | RTX 5090 + CUDA 12.8 + SageAttention2++ 초기 릴리스 |
