import os
from pathlib import Path

def list_files(directory_path: str = None) -> dict:
    if directory_path is None:
        directory_path = os.getcwd()
    
    path_obj = Path(directory_path)
    if not path_obj.is_dir():
        return {"error": f"Path '{directory_path}' is not a valid directory."}
        
    try:
        structure = {"directory": str(path_obj.resolve()), "contents": {}}
        for item in sorted(path_obj.iterdir()):
            if item.is_dir():
                structure["contents"][item.name] = "directory"
            else:
                structure["contents"][item.name] = "file"
        return structure
    except Exception as e:
        return {"error": f"Failed to list files: {e}"}

def write_text_file(file_path: str, content: str) -> dict:
    try:
        path_obj = Path(file_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        path_obj.write_text(content, encoding="utf-8")
        return {"status": "success", "message": f"File written to '{path_obj.resolve()}'"}
    except Exception as e:
        return {"error": f"Failed to write file: {e}"}