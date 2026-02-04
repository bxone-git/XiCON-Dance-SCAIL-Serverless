import runpod
import os
import websocket
import base64
import json
import uuid
import logging
import urllib.request
import urllib.parse
import binascii
import subprocess
import time

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server_address = os.getenv('SERVER_ADDRESS', '127.0.0.1')
client_id = str(uuid.uuid4())

# Default video path (embedded in Docker for warm start)
DEFAULT_VIDEO_PATH = "/ComfyUI/input/default_video.mp4"

def queue_prompt(prompt):
    """Queue a prompt to ComfyUI"""
    url = f"http://{server_address}:8188/prompt"
    logger.info(f"Queueing prompt to: {url}")
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    """Get execution history from ComfyUI"""
    url = f"http://{server_address}:8188/history/{prompt_id}"
    logger.info(f"Getting history from: {url}")
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())

def get_videos(ws, prompt):
    """Execute workflow and retrieve output videos"""
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_videos = {}

    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        videos_output = []
        if 'gifs' in node_output:
            for video in node_output['gifs']:
                # Read file and encode to base64
                with open(video['fullpath'], 'rb') as f:
                    video_data = base64.b64encode(f.read()).decode('utf-8')
                videos_output.append(video_data)
        output_videos[node_id] = videos_output

    return output_videos

def load_workflow(workflow_path):
    """Load workflow JSON file"""
    with open(workflow_path, 'r') as file:
        return json.load(file)

def download_file_from_url(url, output_path):
    """Download file from URL using wget"""
    try:
        result = subprocess.run([
            'wget', '-O', output_path, '--no-verbose', url
        ], capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"✅ Successfully downloaded file from URL: {url} -> {output_path}")
            return output_path
        else:
            logger.error(f"❌ wget download failed: {result.stderr}")
            raise Exception(f"URL download failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        logger.error("❌ Download timeout")
        raise Exception("Download timeout")
    except Exception as e:
        logger.error(f"❌ Download error: {e}")
        raise Exception(f"Download error: {e}")

def save_base64_to_file(base64_data, temp_dir, output_filename):
    """Save base64 data to file"""
    try:
        decoded_data = base64.b64decode(base64_data)
        os.makedirs(temp_dir, exist_ok=True)

        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        with open(file_path, 'wb') as f:
            f.write(decoded_data)

        logger.info(f"✅ Saved base64 input to '{file_path}'")
        return file_path
    except (binascii.Error, ValueError) as e:
        logger.error(f"❌ Base64 decoding failed: {e}")
        raise Exception(f"Base64 decoding failed: {e}")

def process_input(input_data, temp_dir, output_filename, input_type):
    """Process input data and return file path"""
    if input_type == "path":
        logger.info(f"📁 Processing path input: {input_data}")
        return input_data
    elif input_type == "url":
        logger.info(f"🌐 Processing URL input: {input_data}")
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        return download_file_from_url(input_data, file_path)
    elif input_type == "base64":
        logger.info(f"🔢 Processing base64 input")
        return save_base64_to_file(input_data, temp_dir, output_filename)
    else:
        raise Exception(f"Unsupported input type: {input_type}")

def handler(job):
    """Main handler for SCAIL workflow"""
    job_input = job.get("input", {})
    logger.info(f"Received job input: {job_input}")
    task_id = f"task_{uuid.uuid4()}"

    # Process image input (image_path, image_url, or image_base64)
    image_path = None
    if "image_path" in job_input:
        image_path = process_input(job_input["image_path"], task_id, "input_image.jpg", "path")
    elif "image_url" in job_input:
        image_path = process_input(job_input["image_url"], task_id, "input_image.jpg", "url")
    elif "image_base64" in job_input:
        image_path = process_input(job_input["image_base64"], task_id, "input_image.jpg", "base64")

    # Process video input (video_path, video_url, or video_base64)
    # If not provided, use default video (embedded in Docker for warm start)
    video_path = None
    if "video_path" in job_input:
        video_path = process_input(job_input["video_path"], task_id, "input_video.mp4", "path")
    elif "video_url" in job_input:
        video_path = process_input(job_input["video_url"], task_id, "input_video.mp4", "url")
    elif "video_base64" in job_input:
        video_path = process_input(job_input["video_base64"], task_id, "input_video.mp4", "base64")
    else:
        # Use default dance video (warm start)
        video_path = DEFAULT_VIDEO_PATH
        logger.info(f"📹 Using default video: {video_path}")

    # Validate required inputs (only image is required, video has default)
    if image_path is None:
        raise Exception("Image input is required. Provide image_path, image_url, or image_base64")

    # Load SCAIL workflow
    prompt = load_workflow('/XiCON_Dance_SCAIL_api.json')

    # Extract parameters with defaults (matched to workflow defaults)
    width = job_input.get("width", 416)                    # Default: 416 (portrait)
    height = job_input.get("height", 672)                  # Default: 672 (portrait)
    steps = job_input.get("steps", 6)                      # Default: 6
    cfg = job_input.get("cfg", 1.0)                        # Default: 1.0
    seed = job_input.get("seed", 0)                        # Default: 0 (random)
    fps = job_input.get("fps", 24)                         # Default: 24
    positive_prompt = job_input.get("prompt", "the human starts to dance")
    negative_prompt = job_input.get("negative_prompt", "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走")

    # Inject parameters into SCAIL workflow nodes
    prompt["106"]["inputs"]["image"] = image_path                          # LoadImage
    prompt["130"]["inputs"]["video"] = video_path                          # VHS_LoadVideo
    prompt["130"]["inputs"]["force_rate"] = fps                            # VHS_LoadVideo - force_rate
    prompt["203"]["inputs"]["value"] = width                               # INTConstant - width
    prompt["204"]["inputs"]["value"] = height                              # INTConstant - height
    prompt["238"]["inputs"]["value"] = cfg                                 # FloatConstant - cfg
    prompt["348"]["inputs"]["seed"] = seed                                 # WanVideoSamplerv2 - seed
    prompt["349"]["inputs"]["steps"] = steps                               # WanVideoSchedulerv2 - steps
    prompt["368"]["inputs"]["positive_prompt"] = positive_prompt           # WanVideoTextEncodeCached
    prompt["368"]["inputs"]["negative_prompt"] = negative_prompt           # WanVideoTextEncodeCached
    prompt["139"]["inputs"]["frame_rate"] = fps                            # VHS_VideoCombine

    # WebSocket connection with HTTP health check
    ws_url = f"ws://{server_address}:8188/ws?clientId={client_id}"
    logger.info(f"Connecting to WebSocket: {ws_url}")

    # HTTP health check (max 180 attempts = 3 minutes)
    http_url = f"http://{server_address}:8188/"
    logger.info(f"Checking HTTP connection to: {http_url}")

    max_http_attempts = 180
    for http_attempt in range(max_http_attempts):
        try:
            response = urllib.request.urlopen(http_url, timeout=5)
            logger.info(f"HTTP connection successful (attempt {http_attempt+1})")
            break
        except Exception as e:
            logger.warning(f"HTTP connection failed (attempt {http_attempt+1}/{max_http_attempts}): {e}")
            if http_attempt == max_http_attempts - 1:
                raise Exception("Cannot connect to ComfyUI server. Please ensure server is running.")
            time.sleep(1)

    # WebSocket connection with retry (max 36 attempts = 3 minutes)
    ws = websocket.WebSocket()
    max_attempts = 36
    for attempt in range(max_attempts):
        try:
            ws.connect(ws_url)
            logger.info(f"WebSocket connection successful (attempt {attempt+1})")
            break
        except Exception as e:
            logger.warning(f"WebSocket connection failed (attempt {attempt+1}/{max_attempts}): {e}")
            if attempt == max_attempts - 1:
                raise Exception("WebSocket connection timeout (3 minutes)")
            time.sleep(5)

    # Execute workflow and get videos
    videos = get_videos(ws, prompt)
    ws.close()

    # Return first video found
    for node_id in videos:
        if videos[node_id]:
            return {"video": videos[node_id][0]}

    return {"error": "No video output found"}

runpod.serverless.start({"handler": handler})
