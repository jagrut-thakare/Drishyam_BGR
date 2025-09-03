import uvicorn
from PIL import Image
import os, uuid, sys
from dotenv import load_dotenv
from inpaint import run_inpainting
from birefnet_model import generate_mask
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, UploadFile, File, Form

load_dotenv()

sys.path.append(os.getcwd())

app = FastAPI()

# Ensure critical variables are present
REQUIRED_ENV_VARS = ["RESULTS_DIR", "BASE_SIGNED_URL", "AI_TOOL_ID"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]

if missing_vars:
    print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

# Access env vars (now guaranteed to be non-None)
RESULTS_DIR = os.getenv("RESULTS_DIR")
BASE_SIGNED_URL = os.getenv("BASE_SIGNED_URL")
AI_TOOL_ID = os.getenv("AI_TOOL_ID")


# RESULTS_DIR = "static/results"
# BASE_SIGNED_URL = "http://localhost:8003"  # replace with S3 signed base URL in prod
# AI_TOOL_ID = "93ee5d74-b3c6-4cdf-96ab-e1decb7a39f7"

os.makedirs(RESULTS_DIR, exist_ok=True) 
generation_status = {}  # generation_id → {"status": "...", "output": ..., "dimensions": ...}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/health")
async def health_check():
    try:
        import birefnet_model, inpaint
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "unhealthy", "error": str(e)})
    return {"status": "healthy"}

@app.post("/background-change")
async def background_change(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    user_id: str = Form(...),
    template_id: str = Form(None)  # Optional field
):
    gen_id = str(uuid.uuid4())
    generation_status[gen_id] = {"status": "processing"}

    input_path = f"{RESULTS_DIR}/input_{gen_id}.png"
    mask_path = f"{RESULTS_DIR}/mask_{gen_id}.png"
    output_path = f"{RESULTS_DIR}/result_{gen_id}_0.png"

    # Save image
    with open(input_path, "wb") as f:
        f.write(await image.read())

    # Get original dimensions
    with Image.open(input_path) as im:
        width, height = im.size
        orientation = "landscape" if width >= height else "portrait"

    try:
        generate_mask(input_path, mask_path)
        run_inpainting(input_path, mask_path, output_path, prompt)

        # Update status dict
        generation_status[gen_id] = {
            "status": "completed",
            "output": output_path,
            "dimensions": {
                "width": width,
                "height": height,
                "orientation": orientation
            }
        }

    except Exception as e:
        generation_status[gen_id] = {
            "status": "failed",
            "error": str(e),
            "dimensions": {
                "width": width,
                "height": height,
                "orientation": orientation
            }
        }

    return JSONResponse({
        "message": "Background change request accepted and is being processed",
        "generation_id": gen_id,
        "status": "processing",
        "status_url": f"/backgroundchange/status/{gen_id}",
        "width": width,
        "height": height
    })


@app.get("/backgroundchange/status/{generation_id}")
def get_status(generation_id: str):
    data = generation_status.get(generation_id)

    if not data:
        return JSONResponse(
            status_code=404,
            content={"message": "generation_id not found"}
        )

    status = data["status"]

    if status == "completed":
        return JSONResponse({
            "generation_id": generation_id,
            "progress": 100,
            "status": "completed",
            "message": "Background change completed successfully",
            "signed_result_url": f"{BASE_SIGNED_URL}/{data['output']}",
            "error": None,
            "result_image_dimensions": data["dimensions"],
            "content_id": generation_id,
            "credits_used": 10,
            "ai_tool_id": AI_TOOL_ID
        })

    elif status == "failed":
        return JSONResponse({
            "generation_id": generation_id,
            "progress": 100,
            "status": "failed",
            "message": "Background change failed",
            "signed_result_url": None,
            "error": data.get("error"),
            "result_image_dimensions": data["dimensions"],
            "content_id": generation_id,
            "credits_used": 0,
            "ai_tool_id": AI_TOOL_ID
        })

    else:
        return JSONResponse({
            "generation_id": generation_id,
            "progress": 10,
            "status": "processing",
            "message": "Still processing background change",
            "status_url": f"/backgroundchange/status/{generation_id}",
            "width": data["dimensions"]["width"],
            "height": data["dimensions"]["height"]
        })


if __name__=="__main__":
    
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
