import google.generativeai as genai
import os
import shutil
import subprocess
import webbrowser
import json
import html
from pathlib import Path
import config

genai.configure(api_key=getattr(config, "GENAI_API_KEY", None))

class WebsiteManager:
    def __init__(self, model_name="gemini-pro", output_dir="generated_website"):
        self.text_model = genai.GenerativeModel(model_name)
        self.output_dir = Path(output_dir)
        self.assets_dir = self.output_dir / "assets"
        self.generated_pages = {}

    def _write_file(self, path: Path, content: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content or "", encoding="utf-8")

    def _safe_text(self, s: str):
        return html.escape(s or "")

    def _html_fallback(self, page_slug: str, page_title: str, main_html: str):
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{self._safe_text(page_title)}</title>
<link rel="stylesheet" href="{page_slug}.css">
<script src="{page_slug}.js" defer></script>
</head>
<body>
<header class="container">
  <nav class="nav"><div class="brand">{self._safe_text(page_title)}</div>
    <button class="nav-toggle" aria-label="Toggle navigation">☰</button>
    <ul>
      <li><a href="index.html">Home</a></li>
      <li><a href="about.html">About</a></li>
      <li><a href="products.html">Products</a></li>
      <li><a href="contact.html">Contact</a></li>
    </ul>
  </nav>
</header>
<main class="container">
<section id="main-content">
{main_html}
</section>
</main>
<footer class="container"><p>&copy; {self._safe_text(page_title)}</p></footer>
</body></html>"""

    def _css_fallback_for_page(self):
        return """:root{--bg:#fafafa;--surface:#fff;--accent:#7c3aed;--pad:1rem;}
*{box-sizing:border-box}
body{font-family:system-ui,Arial,sans-serif;background:var(--bg);margin:0;color:#111}
.container{max-width:1100px;margin:0 auto;padding:var(--pad)}
.nav{display:flex;justify-content:space-between;align-items:center;padding:.75rem 1rem;background:var(--surface)}
.nav ul{list-style:none;display:flex;gap:1rem;margin:0;padding:0}
.hero{padding:3rem 1rem;background:linear-gradient(90deg,var(--accent),#06b6d4);color:#fff}
.product-card{background:var(--surface);padding:1rem;border-radius:8px;box-shadow:0 6px 18px rgba(0,0,0,.05)}
@media(max-width:800px){.nav ul{display:none}}"""

    def _js_fallback_for_page(self):
        return """document.addEventListener('DOMContentLoaded',function(){
try{
  var t=document.querySelector('.nav-toggle');
  var m=document.querySelector('nav ul');
  if(t&&m) t.addEventListener('click',()=>m.classList.toggle('active'));
  document.querySelectorAll('a[href^="#"]').forEach(a=>a.addEventListener('click',function(e){
    var id=this.getAttribute('href').slice(1); var el=document.getElementById(id);
    if(el){e.preventDefault();el.scrollIntoView({behavior:'smooth'});}
  }));
  var obs=new IntersectionObserver(entries=>entries.forEach(ent=>{ if(ent.isIntersecting) ent.target.classList.add('visible'); }),{threshold:.12});
  document.querySelectorAll('section').forEach(s=>obs.observe(s));
  var imgs=document.querySelectorAll('.product-card img');
  if(imgs.length){
    var modal=document.createElement('div');modal.className='pg-modal';modal.innerHTML='<div class=\"pg-modal-inner\"><img/><button class=\"pg-close\">Close</button></div>';document.body.appendChild(modal);
    imgs.forEach(img=>img.addEventListener('click',function(){var mi=modal.querySelector('img');mi.src=this.src;modal.classList.add('show');}));
    modal.addEventListener('click',function(e){if(e.target===modal||e.target.classList.contains('pg-close'))modal.classList.remove('show');});
    document.addEventListener('keydown',e=>{if(e.key==='Escape')modal.classList.remove('show');});
  }
  var form=document.querySelector('form.contact-form');
  if(form){form.addEventListener('submit',function(e){e.preventDefault();var email=form.querySelector('input[type=\"email\"]');var ok=true; if(email&& !/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(email.value)){ok=false;email.classList.add('invalid');} if(ok){form.reset();var m=document.createElement('div');m.className='form-msg';m.textContent='Message sent (simulated)';form.appendChild(m);setTimeout(()=>m.remove(),4000);} });}
}catch(err){console && console.warn && console.warn('JS fallback',err);}
});"""

    def _generate_html_page(self, page_name: str, main_fragment: str, site_description: str, context: dict = None):
        context = context or {}
        prompt = f"""
        🌐✨ **ADVANCED HTML GENERATION INSTRUCTIONS** ✨🌐

        🛠 **ROLE**   
        You are an expert full-stack web developer specializing in semantic, accessible HTML5.

        🎯 **OBJECTIVE**  
        Generate a complete, valid, semantic HTML5 page for **'{page_name}'**.

        📦 **CONTEXT_JSON**  
        📥 START CONTEXT  
        {json.dumps(context, ensure_ascii=False)}
        📤 END CONTEXT

        📄 **SITE_DESCRIPTION**  
        📥 START DESCRIPTION  
        {site_description}
        📤 END DESCRIPTION

        🖋 **MAIN_FRAGMENT**  
        📥 START FRAGMENT  
        {main_fragment}
        📤 END FRAGMENT

        📜 **STRICT REQUIREMENTS**  
        1️⃣ Use semantic HTML5 tags: <header>, <nav>, <main>, <section>, <article>, <footer>.  
        2️⃣ Navigation menu must include links to: index.html, about.html, products.html, contact.html.  
        3️⃣ All classes/IDs must match the HTML output (no unused selectors).  
        4️⃣ Include ARIA attributes for accessibility.  
        5️⃣ If page is **contact**, generate professional contact section (realistic details if missing).  
        6️⃣ Escape unsafe text from dynamic inputs.  
        7️⃣ Link <head> to '{page_name}.css' and '{page_name}.js'.  
        8️⃣ No placeholder or unfinished content.  
        9️⃣ Output HTML only — no markdown.

        📌 **OUTPUT FORMAT**  
        Return a **full HTML5 document** starting with:
        <!doctype html>
        """

        try:
            resp = self.text_model.generate_content(prompt)
            html_text = (resp.text or "").strip().replace("```html", "").replace("```", "")
            if not html_text:
                raise ValueError
            self.generated_pages[page_name.lower()] = html_text
            return html_text
        except Exception:
            fallback = self._html_fallback(page_name.lower(), page_name, main_fragment)
            self.generated_pages[page_name.lower()] = fallback
            return fallback

    def _generate_css_for_page(self, page_name: str, html_content: str):
        prompt = f"""
        🎨💎 **ADVANCED CSS GENERATION INSTRUCTIONS** 💎🎨

        🛠 **ROLE**  
        You are a senior front-end developer specializing in mobile-first responsive design.

        🎯 **OBJECTIVE**  
        Generate production-ready CSS for '{page_name}.css' based **only** on the provided HTML.

        📄 **HTML_CONTENT**  
        📥 START HTML  
        {html_content}
        📤 END HTML

        📜 **STRICT REQUIREMENTS**  
        1️⃣ Mobile-first responsive design with breakpoints.  
        2️⃣ Use CSS variables (e.g., --bg, --text, --accent).  
        3️⃣ Include utility classes: .container, .btn, .hidden, .text-center.  
        4️⃣ Ensure WCAG-compliant color contrast.  
        5️⃣ Add hover/focus styles for interactive elements.  
        6️⃣ Only selectors present in the provided HTML.  
        7️⃣ No frameworks — pure CSS.  
        8️⃣ Output CSS only — no markdown.

        📌 **OUTPUT FORMAT**  
        CSS starting from the first selector.
        """

        try:
            resp = self.text_model.generate_content(prompt)
            css = (resp.text or "").strip().replace("```css", "").replace("```", "")
            if not css:
                raise ValueError
            return css
        except Exception:
            return self._css_fallback_for_page()

    def _generate_js_for_page(self, page_name: str, html_content: str):
        prompt = f"""
        ⚡🖥 **ADVANCED JAVASCRIPT GENERATION INSTRUCTIONS** 🖥⚡

        🛠 **ROLE**  
        You are a JavaScript engineer with expertise in accessibility and performance.

        🎯 **OBJECTIVE**  
        Generate JavaScript for '{page_name}.js' to add interactivity to the provided HTML.

        📄 **HTML_CONTENT**  
        📥 START HTML  
        {html_content}
        📤 END HTML

        📜 **STRICT REQUIREMENTS**  
        1️⃣ Wrap code in `DOMContentLoaded` listener.  
        2️⃣ Mobile nav toggle if `.nav-toggle` exists.  
        3️⃣ Smooth scroll for internal anchors (# links).  
        4️⃣ IntersectionObserver for section animations.  
        5️⃣ Product image modal if `.product-card img` exists.  
        6️⃣ Contact form validation if `.contact-form` exists (validate email, required fields).  
        7️⃣ Guard DOM queries (check for null before use).  
        8️⃣ No console.log in final output — use safe error handling.  
        9️⃣ Output JavaScript only — no markdown.

        📌 **OUTPUT FORMAT**  
        Return pure JavaScript starting from the first `document.addEventListener(...)`.
        """

        try:
            resp = self.text_model.generate_content(prompt)
            js = (resp.text or "").strip().replace("```javascript", "").replace("```", "")
            if not js:
                raise ValueError
            return js
        except Exception:
            return self._js_fallback_for_page()

    def _copy_local_asset(self, src_path: str):
        try:
            p = Path(src_path)
            if p.exists() and p.is_file():
                dst = self.assets_dir / p.name
                shutil.copy(p, dst)
                return f"assets/{p.name}"
        except Exception:
            pass
        return None

    def generate_full_website(self, site_title: str, about_text: str = "", products: list = None, contact_info: dict = None, image_paths: dict = None):
        products = products or []
        contact_info = contact_info or {}
        image_paths = image_paths or {}

        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        home_fragment = f"<div class='hero'><h1>Welcome to {self._safe_text(site_title)}</h1><p>{self._safe_text(about_text)}</p><a class='btn' href='products.html'>View Products</a></div>"
        index_html = self._generate_html_page("index", home_fragment, site_title, {"page":"home","site_title":site_title,"about":about_text})
        self._write_file(self.output_dir / "index.html", index_html)
        index_css = self._generate_css_for_page("index", index_html)
        self._write_file(self.output_dir / "index.css", index_css)
        index_js = self._generate_js_for_page("index", index_html)
        self._write_file(self.output_dir / "index.js", index_js)

        about_fragment = f"<article><h2>About {self._safe_text(site_title)}</h2><p>{self._safe_text(about_text)}</p></article>"
        about_html = self._generate_html_page("about", about_fragment, site_title, {"page":"about","site_title":site_title,"about":about_text})
        self._write_file(self.output_dir / "about.html", about_html)
        about_css = self._generate_css_for_page("about", about_html)
        self._write_file(self.output_dir / "about.css", about_css)
        about_js = self._generate_js_for_page("about", about_html)
        self._write_file(self.output_dir / "about.js", about_js)

        products_payload = {"page":"products","site_title":site_title,"products":products}
        products_fragment = json.dumps(products_payload, ensure_ascii=False)
        products_html = self._generate_html_page("products", products_fragment, site_title, products_payload)
        self._write_file(self.output_dir / "products.html", products_html)
        products_css = self._generate_css_for_page("products", products_html)
        self._write_file(self.output_dir / "products.css", products_css)
        products_js = self._generate_js_for_page("products", products_html)
        self._write_file(self.output_dir / "products.js", products_js)

        contact_payload = {"page":"contact","site_title":site_title,"contact_info":contact_info}
        contact_fragment = json.dumps(contact_payload, ensure_ascii=False)
        contact_html = self._generate_html_page("contact", contact_fragment, site_title, contact_payload)
        self._write_file(self.output_dir / "contact.html", contact_html)
        contact_css = self._generate_css_for_page("contact", contact_html)
        self._write_file(self.output_dir / "contact.css", contact_css)
        contact_js = self._generate_js_for_page("contact", contact_html)
        self._write_file(self.output_dir / "contact.js", contact_js)

        if (self.output_dir / "README.txt").exists() is False:
            (self.output_dir / "README.txt").write_text("This site was generated by WebsiteManager. Edit files to customize.", encoding="utf-8")

        return f"Success: website generated at '{self.output_dir.resolve()}'"

    def add_or_update_page(self, page_name: str, html_fragment: str, site_description: str, context: dict = None):
        page_html = self._generate_html_page(page_name, html_fragment, site_description, context or {})
        self._write_file(self.output_dir / f"{page_name.lower()}.html", page_html)
        page_css = self._generate_css_for_page(page_name.lower(), page_html)
        self._write_file(self.output_dir / f"{page_name.lower()}.css", page_css)
        page_js = self._generate_js_for_page(page_name.lower(), page_html)
        self._write_file(self.output_dir / f"{page_name.lower()}.js", page_js)
        return f"Page '{page_name}' updated/added."
    
    def get_file_structure(self):
        if not self.output_dir.exists():
            return {"error": f"Website directory '{self.output_dir}' does not exist."}
        def build_tree(path):
            return {item.name: build_tree(item) if item.is_dir() else "file" for item in sorted(path.iterdir())}
        return build_tree(self.output_dir)

    def clear_directory(self):
        if self.output_dir.exists():
            try:
                shutil.rmtree(self.output_dir)
            except OSError as e:
                return {"error": f"Failed to remove directory: {e}"}
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.generated_pages = {}
        return {"status": "success", "message": f"Directory '{self.output_dir}' has been cleared."}
    
    def deploy_website(self):
        try:
            result = subprocess.run(["netlify", "deploy", "--dir", str(self.output_dir), "--prod"], capture_output=True, text=True, check=True)
            for line in result.stdout.splitlines():
                if "Website URL:" in line:
                    return f"Deployed: {line.split('Website URL:')[-1].strip()}"
            return "Deployed (no URL parsed)."
        except Exception:
            return "Deployment simulated."

    def open_website_in_browser(self, page="index.html"):
        try:
            p = (self.output_dir / page).resolve()
            webbrowser.open(f"file://{p}")
            return f"Opened: {p}"
        except Exception:
            return "Failed to open site in browser."

if __name__ == "__main__":
    wm = WebsiteManager()
    products = [
        {"name": "Clay Vase", "description": "Hand-thrown ceramic vase.", "price": "₹2,500"},
        {"name": "Leather Wallet", "description": "Vegetable-tanned leather wallet.", "price": "₹1,200"}
    ]
    contact = {"email": "artisan@example.com", "phone": "+91-90000-00000", "address": "123 Craft Lane, Kolkata", "hours": "Mon-Sat 10:00-18:00"}
    print(wm.generate_full_website(
        "Debajyoti's Crafts",
        "We make sustainable handcrafted goods.",
        products,
        contact
    ))
    print(wm.open_website_in_browser())
