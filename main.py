import io
import os
import base64
import asyncio
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
    timeout=30.0,   # prevents “infinite loading”
)

@app.get("/")
def root():
    return {"status": "Signature Analyzer API is running"}

def _call_openai(b64: str) -> str:
    prompt = (
        "Analyze this handwritten signature image. "
        "Infer probable personality and communication tendencies. "
        "Avoid absolute or diagnostic claims.\n\n"
        "Output format:\n"
        "- 3 Probable Tendencies\n"
        "- 2 Strengths\n"
        "- 1 Possible Challenge\n"
        "- Confidence: Low/Medium/High\n"
        "- Disclaimer (one line)\n"
    )

  {"type": "text", "text":
"You are an API that returns STRICT JSON.\n"
"Analyze the handwritten signature image and infer probable personality tendencies.\n"
"Do not make diagnostic or absolute claims.\n\n"
"Return ONLY valid JSON with NO markdown, NO explanations, and NO extra text.\n\n"
"The JSON schema MUST be exactly:\n"
"{\n"
"  \"tendencies\": [string, string, string],\n"
"  \"strengths\": [string, string],\n"
"  \"challenge\": string,\n"
"  \"confidence\": \"Low\" | \"Medium\" | \"High\",\n"
"  \"disclaimer\": string\n"
"}"
}

        max_tokens=300,
    )
    return resp.choices[0].message.content

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    img_bytes = await file.read()

    # Resize + compress (keeps Render happy)
    image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    image.thumbnail((512, 512))

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=80)
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Run OpenAI call off the event loop
    text = await asyncio.to_thread(_call_openai, b64)

    return {"analysis": text}
