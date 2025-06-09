from fastapi import FastAPI, Response
from pydantic import BaseModel
import hashlib
import base64
import random
import string
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

# Invisible Unicode markers
ZWJ = '\u200D'  # Zero Width Joiner (1)
ZWNJ = '\u200C'  # Zero Width Non-Joiner (0)

# Common decoy patterns used by detectors
DECOY_MARKERS = ["WMK+", "EE+", "AIWMK+", "HASH+"]
DECOY_CHARS = ['·', '÷', '×', '¬', '‖', ZWJ, ZWNJ]


def hash_to_binary(data: str) -> str:
    h = hashlib.sha256(data.encode()).digest()
    return ''.join(f"{byte:08b}" for byte in h)


def binary_to_unicode(bits: str) -> str:
    mapping = {'0': ZWNJ, '1': ZWJ}
    return ''.join(mapping[b] for b in bits)


def generate_decoy_payload(length: int = 32) -> str:
    return ''.join(random.choices(DECOY_CHARS, k=length))


def insert_invisible_watermark(text: str) -> str:
    metadata = f"prompt_id:{generate_random_id(10)}|model:gpt-4|timestamp:{generate_timestamp()}"
    bits = hash_to_binary(metadata)
    watermark = binary_to_unicode(bits)
    pos = random.randint(len(text) // 4, (len(text) // 4) * 3)
    return text[:pos] + watermark + text[pos:]


def insert_decoy_watermark(text: str) -> str:
    marker = random.choice(DECOY_MARKERS)
    decoy_data = generate_decoy_payload()
    return text[:len(text)//2] + f"{marker}{decoy_data}WMK" + text[len(text)//2:]


def generate_random_id(length: int = 10) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_timestamp() -> str:
    return datetime.now().isoformat()


def obfuscate_with_base64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


class TextInput(BaseModel):
    text: str


@app.post("/bypass")
async def bypass_watermark(data: TextInput):
    try:
        text = data.text
        watermarked_text = insert_invisible_watermark(text)
        final_text = insert_decoy_watermark(watermarked_text)
        obfuscated_text = obfuscate_with_base64(final_text)

        metadata = f"prompt_id:{generate_random_id(10)}|model:gpt-4|timestamp:{generate_timestamp()}"
        bits = hash_to_binary(metadata)
        unicode_hash = binary_to_unicode(bits)

        return {
            "processed_text": obfuscated_text,
            "unicode_hash": base64.b64encode(unicode_hash.encode()).decode()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/download")
async def download_watermarked_file(data: TextInput):
    try:
        text = data.text
        watermarked_text = insert_invisible_watermark(text)
        final_text = insert_decoy_watermark(watermarked_text)
        obfuscated_text = obfuscate_with_base64(final_text)

        return Response(
            content=obfuscated_text,
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=output.txt"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve static files
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="dist", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
