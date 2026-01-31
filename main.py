@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    img_bytes = await file.read()

    # Resize & compress image
    image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    image.thumbnail((512, 512))

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=80)
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": 
                        "Analyze this handwritten signature image. "
                        "Infer probable personality and communication tendencies. "
                        "Avoid absolute or diagnostic claims.\n\n"
                        "Output format:\n"
                        "- 3 Probable Tendencies\n"
                        "- 2 Strengths\n"
                        "- 1 Possible Challenge\n"
                        "- Confidence: Low/Medium/High\n"
                        "- Disclaimer (one line)\n"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64}"
                        }
                    }
                ]
            }
        ],
        max_tokens=300,
        timeout=20
    )

    return {"analysis": response["choices"][0]["message"]["content"]}
