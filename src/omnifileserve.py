
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
import os

os.chdir(Path(__file__).parent)
print('cwd', Path('.').resolve())
app = FastAPI()

storage_dir = Path("storage")
storage_dir.mkdir(exist_ok=True)

@app.post("/files/")
async def upload_file(file: UploadFile = File(...)):
    file_path = storage_dir / file.filename
    if file_path.exists():
        raise HTTPException(status_code=400, detail="File already exists")
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": f"File '{file.filename}' uploaded successfully"}

@app.put("/files/{file_name}")
async def replace_file(file_name: str, file: UploadFile = File(...)):
    file_path = storage_dir / file_name
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": f"File '{file_name}' replaced successfully"}

@app.get("/files/{file_name}")
async def get_file(file_name: str):
    file_path = storage_dir / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return {"file_name": file_name, "content": file_path.read_text()}

@app.delete("/files/{file_name}")
async def delete_file(file_name: str):
    file_path = storage_dir / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    file_path.unlink()
    return {"message": f"File '{file_name}' deleted successfully"}

@app.get("/list/")
async def list_files():
    files = [f.name for f in storage_dir.iterdir() if f.is_file()]
    return {"files": files}

@app.get("/pull/{file_name}")
async def pull_file(file_name:str):
    file_path = storage_dir / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/octet-stream", filename=file_name)



if __name__ == "__main__":
    this_file = Path(__file__).stem
    # Launch the Uvicorn server programmatically
    uvicorn.run(
        f"{this_file}:app",  # Module name and app instance
        host="0.0.0.0",  # Bind to all interfaces
        port=2425,       # Port number
        reload=True      # Enable auto-reload for development
    )

