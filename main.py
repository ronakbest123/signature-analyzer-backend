import io
import os
import base64
import asyncio
import json

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from openai import OpenAI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=30.0,
)

@app.get("/")
def root():
    return {"status": "Signature Analyzer API is running"}

def _call_openai(b64: str) -> dict:
    prompt = (
        "You are an API that returns STRICT JSON only.\n"
        "Analyze the handwritten signature image and infer probable personality tendencies.\n"
        "Avoid absolute or diagnostic claims.\n\n"
        "Return ONLY valid JSON with NO markdown, NO explanations, and NO extra text.\n"
        "JSON schema MUST be exactly:\n"
        "{\n"
        "  \"tendencies\": [\"...\", \"...\", \"...\"],\n"
        "  \"strengths\": [\"...\", \"...\"],\n"
        "  \"challenge\": \"...\",\n"
        "  \"confidence\": \"Low\" | \"Medium\" | \"High\",\n"
        "  \"disclaimer\": \"...\"\n"
        "}\n"
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},   # <-- forces valid JSON output
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    content = resp.choices[0].message.content
    return json.loads(content)

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    img_bytes = await file.read()

    # Resize + compress (Render-friendly)
    image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    image.thumbnail((512, 512))

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=80)
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Run model call off the event loop
    result = await asyncio.to_thread(_call_openai, b64)

    # Return structured JSON directly (best for Webflow)
    return result

