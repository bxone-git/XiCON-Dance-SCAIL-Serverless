# CLAUDE.md

RunPod Serverless 패키지 개발 가이드

## 프로젝트 개요

XiCON Dance SCAIL - SCAIL 14B 기반 댄스 애니메이션 생성
- SCAIL pose embeddings + NLF motion capture
- 이미지 → 댄스 비디오 변환

## 필수 파일 구조

```
├── .runpod/
│   ├── hub.json      # RunPod Hub 설정 (필수)
│   └── tests.json    # 테스트 설정 (Hub 배포 시 필수)
├── Dockerfile        # 컨테이너 빌드
├── entrypoint.sh     # 시작 스크립트
├── handler.py        # RunPod 핸들러
├── *.json            # ComfyUI 워크플로우
└── README.md         # 문서
```

---

## 중요 지침 (꼭 유념할 것)

### 1. hub.json과 tests.json 설정 일치

**반드시 두 파일의 설정이 일치해야 함:**

```json
// hub.json
"gpuIds": "ADA_24,ADA_32_PRO",
"allowedCudaVersions": ["12.8"]

// tests.json - 반드시 일치!
"gpuTypeId": "ADA_24",
"allowedCudaVersions": ["12.8"]
```

❌ **불일치 시**: 테스트가 무한 대기 상태로 빠짐 (로그 없음)

### 2. CUDA 버전 호환성

| 배포 방식 | CUDA 12.8 | CUDA 12.7 | 비고 |
|-----------|-----------|-----------|------|
| RunPod Hub | ❌ 드라이버 미지원 | ✅ | Hub 사용 시 12.7 필수 |
| RunPod Serverless 직접 | ✅ | ✅ | RTX 5090은 12.8 필수 |

### 3. GPU 아키텍처별 요구사항

| GPU | 아키텍처 | 최소 CUDA |
|-----|----------|-----------|
| RTX 4090 | Ada Lovelace | 12.0+ |
| RTX 5090 | Blackwell | **12.8+** |

**RTX 5090 사용 시**: RunPod Hub 불가 → Serverless 직접 배포 필요

### 4. tests.json 필수 (Hub 배포)

RunPod Hub는 `tests.json`이 **mandatory**:
- 빈 배열 `"tests": []`도 가능하지만 권장하지 않음
- timeout 충분히 설정 (모델 로딩 시간 고려: 900000ms+ for SCAIL 14B)

### 5. GitHub Webhook 미감지 시

Push가 감지 안 될 경우 빈 커밋으로 트리거:
```bash
git commit --allow-empty -m "Trigger rebuild" && git push
```

### 6. 모델 다운로드 URL

HuggingFace 토큰이 필요한 경우 Dockerfile에서 ARG로 처리:
```dockerfile
ARG HF_TOKEN
RUN huggingface-cli download ... --token $HF_TOKEN
```

### 7. handler.py 필수 구조

```python
import runpod  # 필수

def handler(job):
    job_input = job.get("input", {})
    # 처리 로직
    return {"video": base64_result}  # 또는 {"error": "..."}

runpod.serverless.start({"handler": handler})  # 필수
```

### 8. 노드 ID 매핑 검증

handler.py에서 주입하는 노드 ID가 워크플로우 JSON과 일치하는지 반드시 확인:
```python
# handler.py
prompt["106"]["inputs"]["image"] = image_path  # LoadImage

# workflow.json에서 노드 "106"이 LoadImage인지 확인!
```

---

## 배포 방식 비교

| 항목 | RunPod Hub | Serverless 직접 |
|------|------------|-----------------|
| GitHub 연동 | 자동 빌드 | 수동 Docker 빌드 |
| CUDA 12.8 | ❌ | ✅ |
| RTX 5090 | ❌ | ✅ |
| tests.json | 필수 | 불필요 |
| 빌드 시간 | Hub에서 처리 | 로컬/CI에서 처리 |

---

## 빌드 & 배포 명령어

### Hub 배포 (CUDA 12.7, Ada GPU)
```bash
git push origin main
# RunPod Hub에서 자동 빌드
```

### Serverless 직접 배포 (CUDA 12.8, RTX 5090)
```bash
# 1. 빌드
docker build --platform linux/amd64 -t blendx/xicon-dance-scail:latest .

# 2. Push
docker push blendx/xicon-dance-scail:latest

# 3. RunPod Serverless → New Endpoint → Custom Image
```

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| 테스트 무한 대기 | hub.json/tests.json 불일치 | 설정 동기화 |
| CUDA 오류 | 드라이버 미지원 | CUDA 버전 다운그레이드 |
| 빌드 미트리거 | Webhook 미감지 | 빈 커밋 push |
| 모델 다운로드 실패 | HF 토큰 필요 | 토큰 설정 또는 공개 URL |
| Cold start 느림 | SCAIL 14B 로딩 | 최소 180초 대기 설정 |
