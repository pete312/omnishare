
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
import shutil
import os

os.chdir(Path(__file__).parent)
print('cwd', Path('.').resolve())
app = FastAPI()
storage_dir = Path("storage").resolve()  # Make it absolute from the start
storage_dir.mkdir(exist_ok=True)

def sanitize_path(file_path: str) -> Path:
    """Sanitize and validate file path to prevent directory traversal attacks."""
    # Remove any leading slashes and resolve the path
    clean_path = Path(file_path.lstrip('/'))
    # Ensure the path doesn't try to escape storage_dir
    full_path = (storage_dir / clean_path).resolve()
    if not str(full_path).startswith(str(storage_dir.resolve())):
        raise HTTPException(status_code=400, detail="Invalid path")
    return full_path

@app.post("/files/")
async def upload_file(file: UploadFile = File(...), path: Optional[str] = Form(None)):
    # If path is provided, use it; otherwise use just the filename
    if path:
        file_path = sanitize_path(f"{path}/{file.filename}")
    else:
        file_path = storage_dir / file.filename

    if file_path.exists():
        raise HTTPException(status_code=400, detail="File already exists")

    # Create parent directories if they don't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    relative_path = file_path.relative_to(storage_dir)
    return {"message": f"File '{relative_path}' uploaded successfully"}

@app.put("/files/{file_path:path}")
async def replace_file(file_path: str, file: UploadFile = File(...)):
    full_path = sanitize_path(file_path)
    # Create parent directories if they don't exist
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with full_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": f"File '{file_path}' replaced successfully"}

@app.get("/files/{file_path:path}")
async def get_file(file_path: str):
    full_path = sanitize_path(file_path)
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return {"file_name": file_path, "content": full_path.read_text()}

@app.delete("/files/{file_path:path}")
async def delete_file(file_path: str):
    full_path = sanitize_path(file_path)
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    full_path.unlink()
    return {"message": f"File '{file_path}' deleted successfully"}

@app.get("/list/")
async def list_files(path: Optional[str] = None):
    """List files and directories. If path is provided, list that directory."""
    if path:
        list_path = sanitize_path(path)
    else:
        list_path = storage_dir

    if not list_path.exists():
        raise HTTPException(status_code=404, detail="Directory not found")

    if not list_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    # Build recursive file tree
    def get_file_tree(dir_path: Path) -> list:
        items = []
        for item in sorted(dir_path.iterdir()):
            rel_path = item.relative_to(storage_dir)
            if item.is_file():
                items.append(str(rel_path))
            elif item.is_dir():
                items.extend(get_file_tree(item))
        return items

    files = get_file_tree(list_path)
    return {"files": files}

@app.get("/pull/{file_path:path}")
async def pull_file(file_path: str):
    full_path = sanitize_path(file_path)
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    # Use just the filename for download, not the full path
    filename = full_path.name
    return FileResponse(full_path, media_type="application/octet-stream", filename=filename)



if __name__ == "__main__":
    this_file = Path(__file__).stem
    # Launch the Uvicorn server programmatically
    uvicorn.run(
        f"{this_file}:app",  # Module name and app instance
        host="0.0.0.0",  # Bind to all interfaces
        port=2425,       # Port number
        reload=True      # Enable auto-reload for development
    )
