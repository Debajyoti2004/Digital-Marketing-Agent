import os
from pathlib import Path
from rich import print as rprint
from rich.panel import Panel
import json

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

if __name__ == "__main__":
    rprint(Panel("[bold cyan]--- 📂 Testing `list_files` in current directory ---[/bold cyan]"))
    current_dir_contents = list_files()
    rprint(json.dumps(current_dir_contents, indent=2))
    
    rprint(Panel("\n[bold cyan]--- 📝 Testing `write_text_file` ---[/bold cyan]"))
    
    test_directory = "test_output"
    test_file = os.path.join(test_directory, "my_test_file.txt")
    file_content = "Hello from the test script!\nThis is a test of the write_text_file function."
    
    write_result = write_text_file(test_file, file_content)
    if "error" in write_result:
        rprint(f"[bold red]Error writing file: {write_result['error']}[/bold red]")
    else:
        rprint(f"[green]✅ {write_result['message']}[/green]")

    rprint(Panel(f"\n[bold cyan]--- 📂 Testing `list_files` in new '{test_directory}' directory ---[/bold cyan]"))
    
    new_dir_contents = list_files(test_directory)
    rprint(json.dumps(new_dir_contents, indent=2))
    
    if new_dir_contents.get("contents", {}).get("my_test_file.txt") == "file":
        rprint("[bold green]\n✅ Verification successful: 'my_test_file.txt' was found.[/bold green]")
    else:
        rprint("[bold red]\n❌ Verification failed: 'my_test_file.txt' was NOT found.[/bold red]")