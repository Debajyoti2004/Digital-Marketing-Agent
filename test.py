import google.generativeai as genai
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import sys

try:
    import config
except ImportError:
    print("❌ Error: config.py not found. Make sure it's in the same directory.")
    sys.exit(1)

API_KEY = getattr(config, "GOOGLE_API_KEY", None)

def check_models():
    console = Console()
    console.print(Panel("🔍 [bold cyan]Checking for available Google AI Models...[/bold cyan]"))

    if not API_KEY:
        console.print(Panel("[bold red]Error:[/bold red] GENAI_API_KEY not found or is empty in your config.py file.",
                          title="[red]Configuration Missing[/red]", border_style="red"))
        return

    try:
        genai.configure(api_key=API_KEY)
        console.print("✅ [green]API Key configured successfully.[/green]")

        table = Table(title="✅ Usable Generative Models", show_header=True, header_style="bold magenta")
        table.add_column("Model Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Input Token Limit", style="yellow", justify="right")
        table.add_column("Output Token Limit", style="yellow", justify="right")
        
        usable_models_found = False
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                table.add_row(
                    model.name,
                    model.description,
                    f"{model.input_token_limit:,}",
                    f"{model.output_token_limit:,}"
                )
                usable_models_found = True
        
        if usable_models_found:
            console.print(table)
            console.print("\n💡 [bold]Tip:[/bold] You can use any of the models listed above in your code (e.g., 'gemini-1.5-pro-latest').")
        else:
            console.print(Panel("[bold yellow]Warning:[/bold yellow] No usable generative models were found for your API key.",
                                title="[yellow]No Models Found[/yellow]", border_style="yellow"))

    except Exception as e:
        console.print(Panel(f"[bold red]An error occurred:[/bold red]\n{e}",
                          title="[red]API Error[/red]", border_style="red"))
        console.print("Please check if your Google API key is valid and has the 'Generative Language API' enabled in the Google Cloud Console.")

if __name__ == "__main__":
    check_models()