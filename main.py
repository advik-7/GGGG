# main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from operations import send_operation, receive_operation

app = FastAPI()

# Mount the static directory for front-end files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models for request bodies
class SendRequest(BaseModel):
    warehouse_id: str
    address: str
    n: int  # number of items to scan

class ReceiveRequest(BaseModel):
    warehouse_id: str
    address: str
    n: int  # number of boxes/items received

@app.post("/send")
async def send_api(request: SendRequest):
    try:
        result = await send_operation(request.warehouse_id, request.address, request.n)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/receive")
async def receive_api(request: ReceiveRequest):
    try:
        result = await receive_operation(request.warehouse_id, request.address, request.n)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r") as f:
        return f.read()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
