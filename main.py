from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import openai
import os
import base64

app = FastAPI()

# Allow requests from anywhere (fine for a project)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.get("/")
def root():
    return {"status": "Signature Analyzer API is running"}

@app.post("/analyze")
async def analyze_signature(file: UploadFile = File(...)):
    # Read image bytes
    image_bytes = await file.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    # Prompt that defines your system intelligence
    prompt = """
You are an AI system analyzing a handwritten signature image.

Rules:
- Analyze only visible structural cues in the signature
- Infer probable personality and communication tendencies
- Avoid absolute or diagnostic claims
- Keep output concise and neutral
- Do not mention psychology or mental health
- End with a disclaimer

Output format:
- 3 Probable Tendencies
- 2 Strengths
- 1 Possible Challenge
- Confidence Level (Low / Medium / High)
- Disclaimer
"""

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        },
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    return {
        "analysis": response["choices"][0]["message"]["content"]
    }
