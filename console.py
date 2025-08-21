from rich.console import Console
from rich.theme import Theme

custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "success": "green",
    "title": "bold cyan",
    "user": "bold yellow",
    "ai": "bold blue",
    "tool_name": "bold magenta",
    "tool_args": "dim magenta",
    "plan": "bold yellow",
    "kg": "bold green"
})

console = Console(theme=custom_theme)