# RTX 5090 Optimized Version with SageAttention 2.2+
# CUDA 12.8 Required for RTX 5090 (Blackwell SM120)
# Tag: blendx/xicon-dance-scail:5090

FROM nvidia/cuda:12.8.0-cudnn-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV TORCH_CUDA_ARCH_LIST="12.0"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-venv \
    git \
    curl \
    wget \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.10 /usr/bin/python

# Install PyTorch 2.7+ with CUDA 12.8 (RTX 5090 / Blackwell optimized)
RUN pip install --upgrade pip && \
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install SageAttention 2.2+ for RTX 5090 (SageAttention2++ kernels)
RUN pip install sageattention>=2.2.0

# Install other Python packages
RUN pip install -U "huggingface_hub[hf_transfer]" runpod websocket-client

WORKDIR /

# Clone ComfyUI and install requirements
RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git && \
    cd /ComfyUI && \
    pip install -r requirements.txt

# Clone custom nodes
RUN cd /ComfyUI/custom_nodes && \
    git clone --depth 1 https://github.com/Comfy-Org/ComfyUI-Manager.git && \
    cd ComfyUI-Manager && \
    pip install -r requirements.txt

RUN cd /ComfyUI/custom_nodes && \
    git clone --depth 1 https://github.com/kijai/ComfyUI-WanVideoWrapper && \
    cd ComfyUI-WanVideoWrapper && \
    pip install -r requirements.txt

RUN cd /ComfyUI/custom_nodes && \
    git clone --depth 1 https://github.com/kijai/ComfyUI-KJNodes && \
    cd ComfyUI-KJNodes && \
    pip install -r requirements.txt

RUN cd /ComfyUI/custom_nodes && \
    git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite && \
    cd ComfyUI-VideoHelperSuite && \
    pip install -r requirements.txt

RUN cd /ComfyUI/custom_nodes && \
    git clone --depth 1 https://github.com/kijai/ComfyUI-WanAnimatePreprocess && \
    cd ComfyUI-WanAnimatePreprocess && \
    pip install -r requirements.txt

# Install GPU acceleration packages (RTX 5090 optimized)
RUN pip install --upgrade onnxruntime-gpu triton taichi

# Create model directories
RUN mkdir -p /ComfyUI/models/diffusion_models /ComfyUI/models/vae /ComfyUI/models/clip_vision /ComfyUI/models/text_encoders /ComfyUI/models/loras /ComfyUI/models/detection

# Download SCAIL Diffusion Model (VERIFIED)
RUN wget -q https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main/SCAIL/Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors \
    -O /ComfyUI/models/diffusion_models/Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors

# Download SCAIL LoRA (VERIFIED)
RUN wget -q https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Lightx2v/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors \
    -O /ComfyUI/models/loras/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors

# Download VAE (using .pth format as workflow requires) (VERIFIED)
RUN wget -q https://huggingface.co/Wan-AI/Wan2.1-T2V-14B/resolve/main/Wan2.1_VAE.pth \
    -O /ComfyUI/models/vae/Wan2.1_VAE.pth

# Download CLIP Vision (VERIFIED)
RUN wget -q https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/clip_vision/clip_vision_h.safetensors \
    -O /ComfyUI/models/clip_vision/clip_vision_h.safetensors

# Download Text Encoder (VERIFIED)
RUN wget -q https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/umt5-xxl-enc-bf16.safetensors \
    -O /ComfyUI/models/text_encoders/umt5-xxl-enc-bf16.safetensors

# Download Detection Models (VERIFIED)
RUN wget -q https://huggingface.co/Wan-AI/Wan2.2-Animate-14B/resolve/main/process_checkpoint/det/yolov10m.onnx \
    -O /ComfyUI/models/detection/yolov10m.onnx
RUN wget -q https://huggingface.co/Kijai/vitpose_comfy/resolve/main/onnx/vitpose_h_wholebody_model.onnx \
    -O /ComfyUI/models/detection/vitpose_h_wholebody_model.onnx
RUN wget -q https://huggingface.co/Kijai/vitpose_comfy/resolve/main/onnx/vitpose_h_wholebody_data.bin \
    -O /ComfyUI/models/detection/vitpose_h_wholebody_data.bin

# Pre-download NLF Model for warm start (avoid runtime download)
RUN mkdir -p /root/.cache/torch/hub/checkpoints && \
    wget -q https://github.com/isarandi/nlf/releases/download/v0.3.2/nlf_l_multi_0.3.2.torchscript \
    -O /root/.cache/torch/hub/checkpoints/nlf_l_multi_0.3.2.torchscript

COPY . .
# Copy workflow to the path handler.py expects
COPY XiCON_Dance_SCAIL_vFinal.json /XiCON_Dance_SCAIL_api.json

# Copy default dance video for warm start (user only provides prompt + image)
RUN mkdir -p /ComfyUI/input && \
    cp /assets/default_video.mp4 /ComfyUI/input/default_video.mp4
RUN mkdir -p /ComfyUI/user/default/ComfyUI-Manager
COPY config.ini /ComfyUI/user/default/ComfyUI-Manager/config.ini
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
