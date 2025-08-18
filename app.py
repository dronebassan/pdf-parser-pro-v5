from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
import uvicorn
import os

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>PDF Parser Pro</title></head>
    <body>
        <h1>PDF Parser Pro</h1>
        <form action="/parse" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".pdf" required>
            <button type="submit">Parse PDF</button>
        </form>
    </body>
    </html>
    """

@app.post("/parse")
async def parse_pdf(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return {"status": "success", "message": f"Received {len(content)} bytes"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)