import google.generativeai as genai
import os
import shutil
import subprocess
import webbrowser
import json
import html
import time
import threading
import queue
import re
import tkinter as tk
from tkinter import scrolledtext, font
from pathlib import Path
import config
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


genai.configure(api_key=getattr(config, "GOOGLE_API_KEY", None))


class LiveCodeViewer:
    def __init__(self, msg_queue):
        self.queue = msg_queue
        self.root = tk.Tk()
        self.root.title("Live Code Generation")

        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(family="Consolas", size=10)
        self.root.option_add("*Font", default_font)
        
        self.filename_label = tk.Label(self.root, text="Initializing...", anchor="w", padx=10, pady=5, bg="#2b2b2b", fg="#cccccc")
        self.filename_label.pack(fill="x")

        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
        self.text_area.pack(expand=True, fill="both")

    def process_queue(self):
        try:
            message = self.queue.get_nowait()
            if message.get("type") == "start":
                self.filename_label.config(text=f"Generating: {message.get('filename')}")
                self.text_area.delete("1.0", tk.END)
            elif message.get("type") == "chunk":
                self.text_area.insert(tk.END, message.get("text"))
                self.text_area.see(tk.END)
            elif message.get("type") == "end":
                self.filename_label.config(text=f"Finished: {message.get('filename')}")
            elif message.get("type") == "done":
                self.root.destroy()
                return
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def start(self):
        self.process_queue()
        self.root.mainloop()


class WebsiteManager:
    def __init__(self, model_name="gemini-1.5-flash-latest", output_dir="generated_website", live_generation=False):
        self.text_model = genai.GenerativeModel(model_name)
        self.output_dir = Path(output_dir)
        self.assets_dir = self.output_dir / "assets"
        self.live_generation = live_generation
        self.console = Console()

    def _write_file(self, path: Path, content: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content or "", encoding="utf-8")

    def _clean_response(self, text: str, language: str) -> str:
        text = re.sub(r'.*?', '', text, flags=re.DOTALL)
        
        text = text.strip()
        if text.startswith(f"```{language}"):
            text = text[len(f"```{language}"):]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    def _get_html_prompt(self, page_name: str, main_fragment: str, site_description: str, context: dict = None) -> str:
        context = context or {}
        return f"""
        🌐✨ **ADVANCED HTML ARCHITECTURE DIRECTIVE** ✨🌐

        **👤 ROLE & PERSONA:**
        You are a world-class Senior Web Engineer and UI/UX Architect. Your specialties are creating beautiful, high-performance, accessible (A11Y), and SEO-optimized websites that convert users. You have a deep understanding of user psychology, Core Web Vitals, and modern design patterns.

        **🎯 PRIMARY OBJECTIVE:**
        Generate a complete, production-ready HTML5 page for the '{page_name}' page. This is not just about writing tags; it's about crafting a superior user experience. Interpret the user's intent from the `MAIN_FRAGMENT` and elevate it with your expertise.

        **GUIDING PRINCIPLES:**
        1.  **User-Centric Design:** The layout must be intuitive and guide the user towards the page's primary goal (e.g., viewing products, making contact). The design should be clean, modern, and aesthetically pleasing.
        2.  **Accessibility (A11Y) First:** All elements MUST be accessible. Use ARIA roles where appropriate (e.g., `aria-current="page"` for the active navigation link), ensure descriptive `alt` text for all images, and use semantic HTML to define the structure.
        3.  **SEO & Performance:** Structure the page for optimal search engine ranking. Use a logical and strict heading hierarchy (one `<h1>`, followed by `<h2>`s, etc.). All `<img>` tags must have `loading="lazy"` and appropriate `width` and `height` attributes to prevent layout shift.
        4.  **Defensive Design:** Your code must anticipate edge cases. If context data (like a product list) is empty, you MUST render a user-friendly message (e.g., "No products available at this time.") instead of an empty component.

        **PROJECT CONTEXT:**
        - **Site Description:** {site_description}
        - **Page Context (JSON):** {json.dumps(context, ensure_ascii=False)}

        **📝 TASK: EXPAND THE MAIN FRAGMENT:**
        This is the core creative task. Transform the following fragment into a rich, fully-featured page section.
        - **Main Fragment:** {main_fragment}

        **📜 STRICT TECHNICAL REQUIREMENTS:**
        1.  **Thinking Process:** Before writing any HTML, you MUST add a comment block at the very top outlining your plan. Use the format `...plan...`.
        2.  **Bootstrap 5:** The entire layout MUST use Bootstrap 5. Include its CSS CDN in `<head>` and the JS Bundle CDN before `</body>`.
        3.  **Navigation:** Create a responsive Bootstrap navbar. Links MUST point to: `index.html`, `about.html`, `products.html`, `contact.html`. The link for the current page ('{page_name}') MUST have the `active` class and `aria-current="page"`.
        4.  **Creative Expansion:** You are encouraged to creatively add sections that an expert would recommend. For a homepage, this might be a testimonials or features section. For a contact page, a map.
        5.  **File Links:** The `<head>` MUST link to the local stylesheet `./{page_name.lower()}.css` and the `<body>` must link to `./{page_name.lower()}.js` (before the Bootstrap JS).
        6.  **Output Format:** Output a single, complete HTML document starting with `<!doctype html>`. Do not include any markdown formatting.
        """

    def _get_css_prompt(self, page_name: str, html_content: str) -> str:
        return f"""
        🎨💎 **ADVANCED CSS DESIGN DIRECTIVE** 💎🎨

        **👤 ROLE & PERSONA:**
        You are a Creative Front-End Designer specializing in modern CSS, elegant micro-interactions, and creating unique visual identities that complement established frameworks like Bootstrap.

        **🎯 PRIMARY OBJECTIVE:**
        Generate a custom stylesheet (`{page_name}.css`) that elevates the provided Bootstrap 5 HTML with a unique, premium, and branded feel.

        **DESIGN PHILOSOPHY:**
        1.  **Fluidity & Responsiveness:** Use modern CSS like `clamp()` for fluid typography that scales smoothly between breakpoints. Ensure all custom styles are fully responsive.
        2.  **Subtle Sophistication:** Add delightful but unobtrusive hover effects, focus states, and transitions. Animate performant properties like `transform` and `opacity`.
        3.  **Visual Hierarchy:** Use color, font-weight, and spacing strategically to guide the user's eye to the most important elements.

        **📄 REFERENCE HTML:**
        (HTML content is provided below)
        {html_content}

        **📜 STRICT TECHNICAL REQUIREMENTS:**
        1.  **Theme, Don't Rebuild:** The HTML uses Bootstrap 5. Your task is to customize it. Do NOT redefine core Bootstrap layout classes like `.container` or `.row`.
        2.  **CSS Variables:** Your primary method of customization MUST be defining CSS variables in `:root`. Override Bootstrap's theme colors (e.g., `--bs-primary`, `--bs-body-bg`, `--bs-font-family-sans-serif`) to establish a new color palette and typography.
        3.  **Animation Utilities:** Create a small set of reusable animation utility classes that the JavaScript can use for on-scroll effects. For example:
            `.animation-fade-in {{ opacity: 0; transition: opacity 0.8s ease-out; }}`
            `.is-visible {{ opacity: 1; }}`
        4.  **Output Format:** Output pure CSS only. Do not include markdown like ` ```css ` or any commentary.
        """

    def _get_js_prompt(self, page_name: str, html_content: str) -> str:
        return f"""
        ⚡🖥 **ADVANCED JAVASCRIPT ENGINEERING DIRECTIVE** 🖥⚡

        **👤 ROLE & PERSONA:**
        You are a Senior JavaScript Engineer focused on writing clean, performant, and maintainable vanilla JS for the modern web. You enhance user experience through meaningful, non-blocking interactivity.

        **🎯 PRIMARY OBJECTIVE:**
        Generate a custom JavaScript file (`{page_name}.js`) that adds high-value interactivity to the provided HTML, going beyond what Bootstrap's default JS bundle offers.

        **INTERACTIVITY STRATEGY:**
        1.  **Asynchronous Form Submission:** If a contact form (`<form>`) exists, you MUST intercept its `submit` event. Prevent the default page reload. Use the `fetch` API to simulate the submission. On completion, dynamically display a user-friendly success or error message within the page itself (e.g., by adding a `<div>` with a message).
        2.  **Dynamic Content Filtering:** If a filterable set of elements exists (like a product grid with category data-attributes), you MUST add a simple client-side filtering UI and logic.
        3.  **Performance First:** Ensure all event listeners are efficient. Use event delegation for lists of items where appropriate.

        **📄 REFERENCE HTML:**
        (HTML content is provided below)
        {html_content}

        **📜 STRICT TECHNICAL REQUIREMENTS:**
        1.  **No Redundancy:** Do NOT write JS for features Bootstrap's JS already handles (e.g., mobile navbar toggle).
        2.  **Initialization:** All code must be wrapped in a `DOMContentLoaded` event listener.
        3.  **Animations on Scroll:** Use the `IntersectionObserver` API to add a visibility class (e.g., `.is-visible`) to elements with an animation class (e.g., `.animation-fade-in`) when they enter the viewport.
        4.  **Defensive Coding:** Always check if an element exists before adding an event listener to it.
        5.  **Output Format:** Output pure, production-ready JavaScript only. Do not include markdown like ` ```javascript ` or any commentary.
        """

    def _generate_html_page(self, page_name: str, main_fragment: str, site_description: str, context: dict = None) -> str:
        prompt = self._get_html_prompt(page_name, main_fragment, site_description, context)
        resp = self.text_model.generate_content(prompt)
        html_text = self._clean_response(resp.text, "html")
        if not html_text.lower().startswith("<!doctype html>"):
            raise ValueError("Generated text is not a valid HTML document.")
        return html_text

    def _generate_css_for_page(self, page_name: str, html_content: str) -> str:
        prompt = self._get_css_prompt(page_name, html_content)
        resp = self.text_model.generate_content(prompt)
        css = self._clean_response(resp.text, "css")
        if not css:
            raise ValueError("Empty CSS response.")
        return css

    def _generate_js_for_page(self, page_name: str, html_content: str) -> str:
        prompt = self._get_js_prompt(page_name, html_content)
        resp = self.text_model.generate_content(prompt)
        js = self._clean_response(resp.text, "javascript")
        if not js:
            raise ValueError("Empty JS response.")
        return js

    def _worker_generate_assets(self, msg_queue, page_name, main_fragment, site_description, context):
        try:
            page_slug = page_name.lower()
            html_path = self.output_dir / f"{page_slug}.html"
            css_path = self.output_dir / f"{page_slug}.css"
            js_path = self.output_dir / f"{page_slug}.js"
            
            msg_queue.put({"type": "start", "filename": html_path.name})
            html_prompt = self._get_html_prompt(page_name, main_fragment, site_description, context)
            html_stream = self.text_model.generate_content(html_prompt, stream=True)
            full_html = ""
            for chunk in html_stream:
                full_html += chunk.text
                msg_queue.put({"type": "chunk", "text": chunk.text})
            cleaned_html = self._clean_response(full_html, "html")
            self._write_file(html_path, cleaned_html)
            msg_queue.put({"type": "end", "filename": html_path.name})

            msg_queue.put({"type": "start", "filename": css_path.name})
            css_prompt = self._get_css_prompt(page_slug, cleaned_html)
            css_stream = self.text_model.generate_content(css_prompt, stream=True)
            full_css = ""
            for chunk in css_stream:
                full_css += chunk.text
                msg_queue.put({"type": "chunk", "text": chunk.text})
            cleaned_css = self._clean_response(full_css, "css")
            self._write_file(css_path, cleaned_css)
            msg_queue.put({"type": "end", "filename": css_path.name})

            msg_queue.put({"type": "start", "filename": js_path.name})
            js_prompt = self._get_js_prompt(page_slug, cleaned_html)
            js_stream = self.text_model.generate_content(js_prompt, stream=True)
            full_js = ""
            for chunk in js_stream:
                full_js += chunk.text
                msg_queue.put({"type": "chunk", "text": chunk.text})
            cleaned_js = self._clean_response(full_js, "javascript")
            self._write_file(js_path, cleaned_js)
            msg_queue.put({"type": "end", "filename": js_path.name})

        except Exception as e:
            self.console.print(f"[bold red]An error occurred during generation: {e}[/bold red]")
        finally:
            msg_queue.put({"type": "done"})

    def _generate_page_assets_gui_live(self, page_name, main_fragment, site_desc, context):
        msg_queue = queue.Queue()
        
        worker_thread = threading.Thread(
            target=self._worker_generate_assets,
            args=(msg_queue, page_name, main_fragment, site_desc, context)
        )
        worker_thread.start()

        viewer = LiveCodeViewer(msg_queue)
        viewer.start()
        worker_thread.join()

    def _generate_and_write_page(self, page_name: str, fragment: str, site_desc: str, context: dict = None):
        if self.live_generation:
            self.console.rule(f"[bold]Live Generating '{page_name}' in GUI Window[/bold]")
            self._generate_page_assets_gui_live(page_name, fragment, site_desc, context)
        else:
            self.console.print(f"Generating page: [bold cyan]{page_name}[/bold cyan]...")
            page_slug = page_name.lower()
            page_html = self._generate_html_page(page_name, fragment, site_desc, context)
            self.console.print("  - Generating CSS...")
            page_css = self._generate_css_for_page(page_slug, page_html)
            self.console.print("  - Generating JavaScript...")
            page_js = self._generate_js_for_page(page_slug, page_html)
            self._write_file(self.output_dir / f"{page_slug}.html", page_html)
            self._write_file(self.output_dir / f"{page_slug}.css", page_css)
            self._write_file(self.output_dir / f"{page_slug}.js", page_js)
        self.console.print(f"[green]✓ Successfully generated files for '{page_name}'.[/green]")

    def generate_full_website(self, site_title: str, about_text: str = "", products: list = None, contact_info: dict = None):
        products = products or []
        contact_info = contact_info or {}
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        home_fragment = f"A welcoming hero section for {site_title} with a call-to-action to view products. Also include a section showcasing a few featured products from the list."
        self._generate_and_write_page("index", home_fragment, site_title, {"page": "home", "site_title": site_title, "about": about_text, "products": products[:2]})
        
        about_fragment = f"A page detailing the story and mission of {site_title}. The text content should be based on: '{about_text}'. Consider adding team member photos or a timeline."
        self._generate_and_write_page("about", about_fragment, site_title, {"page": "about", "site_title": site_title, "about": about_text})
        
        products_payload = {"page": "products", "site_title": site_title, "products": products}
        products_fragment = f"A full product showcase page. Display all products in a responsive grid of Bootstrap Cards. Include filtering controls for product categories if applicable."
        self._generate_and_write_page("products", products_fragment, site_title, products_payload)
        
        contact_payload = {"page": "contact", "site_title": site_title, "contact_info": contact_info}
        contact_fragment = "A professional contact page. It must feature a two-column layout: one for a contact form and one for displaying contact details (address, phone, email) with icons. Consider adding an embedded map."
        self._generate_and_write_page("contact", contact_fragment, site_title, contact_payload)
        
        (self.output_dir / "README.md").write_text(f"# {site_title}\n\nGenerated by Gemini API.", encoding="utf-8")
        return f"Success: Website generated at '{self.output_dir.resolve()}'"

    def add_or_update_page(self, page_name: str, html_fragment: str, site_description: str, context: dict = None):
        self._generate_and_write_page(page_name, html_fragment, site_description, context)
        return f"Page '{page_name}' has been successfully added/updated."

    def get_file_structure(self):
        if not self.output_dir.exists():
            return {"error": f"Website directory '{self.output_dir}' does not exist."}
        def build_tree(path):
            return {item.name: build_tree(item) if item.is_dir() else "file" for item in sorted(path.iterdir())}
        return build_tree(self.output_dir)

    def clear_directory(self):
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return {"status": "success", "message": f"Directory '{self.output_dir}' has been cleared."}

    def open_website_in_browser(self, page="index.html"):
        p = (self.output_dir / page).resolve()
        if p.exists():
            webbrowser.open(f"file://{p}")
            return f"Opened: {p}"
        return f"Error: Page '{page}' not found at {p}"

    def deploy_to_netlify(self):
        self.console.print("\n[bold]Attempting to deploy to Netlify...[/bold]")
        if not shutil.which("netlify"):
            self.console.print("[bold red]Error:[/] Netlify CLI not found. Install with: [cyan]npm install -g netlify-cli[/cyan]")
            return {"status": "error", "message": "Netlify CLI not found."}
        if not self.output_dir.exists() or not any(self.output_dir.iterdir()):
             self.console.print(f"[bold red]Error:[/] Output directory '{self.output_dir}' is empty.")
             return {"status": "error", "message": "Output directory is empty."}
        self.console.print(f"Deploying files from: [cyan]{self.output_dir.resolve()}[/cyan]")
        try:
            command = ["netlify", "deploy", "--dir", str(self.output_dir.resolve()), "--prod"]
            process = subprocess.run(command, capture_output=True, text=True, check=True, encoding="utf-8")
            output = process.stdout
            live_url = None
            for line in output.splitlines():
                if "Website URL:" in line or "Live URL:" in line:
                    live_url = line.split(":")[-1].strip()
                    break
            if live_url:
                self.console.print(Panel(f"🚀 [bold green]Deployment Successful![/bold green] 🚀\n\nLive URL: [link={live_url}]{live_url}[/link]", expand=False))
                webbrowser.open(live_url)
                return {"status": "success", "url": live_url}
            else:
                self.console.print("[bold red]Error:[/] Could not parse deployment URL from output.")
                self.console.print(f"Full output:\n{output}")
                return {"status": "error", "message": "Could not parse deployment URL."}
        except subprocess.CalledProcessError as e:
            self.console.print("[bold red]Deployment Error[/bold]")
            self.console.print(f"STDERR:\n{e.stderr}")
            return {"status": "error", "message": f"Netlify CLI failed: {e.stderr}"}
        except Exception as e:
            self.console.print(f"[bold red]An unexpected error occurred: {e}[/bold]")
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    console = Console()
    console.print(Panel("🚀 [bold green]Starting WebsiteManager Test Suite (Advanced GUI Edition)[/bold green] 🚀", expand=False))

    show_code_generation = True
    site_title = "Debajyoti's Artisan Crafts"
    wm = WebsiteManager(live_generation=show_code_generation)

    console.print("\n[bold]Step 1: Clearing output directory...[/bold]")
    result = wm.clear_directory()
    console.print(Panel(f"✅ [green]Result:[/green] {result['message']}", expand=False))

    console.print(f"\n[bold]Step 2: Generating website (Live in GUI: {show_code_generation})...[/bold]")
    if show_code_generation:
        console.print("[yellow]Hint: A new window will open to show the live code generation![/yellow]")

    products_data = [
        {"id": "p1", "name": "Terracotta Horse", "description": "Classic Bankura terracotta horse.", "price": "₹3,500"},
        {"id": "p2", "name": "Kantha Quilt", "description": "Beautiful quilt with intricate Kantha embroidery.", "price": "₹7,800"},
        {"id": "p3", "name": "Patachitra Scroll", "description": "Vibrant narrative scroll painting of myths.", "price": "₹5,200"},
    ]
    contact_data = {
        "email": "contact@debajyoticrafts.in",
        "phone": "+91-98765-43210",
        "address": "123 Artist Colony, Dhanbad, Jharkhand",
    }

    result = wm.generate_full_website(
        site_title=site_title,
        about_text="Discover the rich heritage of Indian craftsmanship. Sustainable, handcrafted goods made with love, care, and generations of skill.",
        products=products_data,
        contact_info=contact_data,
    )
    console.print(Panel(f"✅ [green]Result:[/green] {result}", expand=False))

    console.print("\n[bold]Step 3: Verifying file structure...[/bold]")
    structure = wm.get_file_structure()
    console.print(Panel(json.dumps(structure, indent=2), title="File Structure"))

    console.print("\n[bold]Step 4: Adding a 'blog' page...[/bold]")
    blog_fragment = "<h2>Our Artisan Stories</h2><article><h3 class='text-primary'>The Potter's Wheel</h3><p>Meet Ram Kumar, the master potter behind our exquisite terracotta collection...</p><img src='https://picsum.photos/seed/pottery/800/400' class='img-fluid rounded' alt='Pottery making'></article>"
    result = wm.add_or_update_page("blog", blog_fragment, site_title)
    console.print(Panel(f"✅ [green]Result:[/green] {result}", expand=False))

    console.print("\n[bold]Step 5: Verifying updated file structure...[/bold]")
    structure = wm.get_file_structure()
    console.print(Panel(json.dumps(structure, indent=2), title="Updated File Structure"))

    console.print("\n[bold]Step 6: Opening pages in browser...[/bold]")
    result_index = wm.open_website_in_browser("index.html")
    console.print(Panel(f"✅ [green]Result:[/green] {result_index}", expand=False))
    time.sleep(1)
    result_products = wm.open_website_in_browser("products.html")
    console.print(Panel(f"✅ [green]Result:[/green] {result_products}", expand=False))

    console.print("\n[bold]Step 7: Deploying website to Netlify...[/bold]")
    wm.deploy_to_netlify()

    console.print(Panel("🏁 [bold green]WebsiteManager Test Suite Finished[/bold green] 🏁", expand=False))