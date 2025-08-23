import google.generativeai as genai
import config
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
import json

class SEOAPI:
    def __init__(self, model_name="gemini-1.5-flash-latest"):
        try:
            genai.configure(api_key=getattr(config, "GOOGLE_API_KEY", None))
            self.model = genai.GenerativeModel(
                model_name=model_name
            )
            rprint(Panel.fit("✅ [green]SEOAPI Initialized with Gemini Model[/green]"))
        except Exception as e:
            rprint(Panel.fit(f"❌ [red]SEOAPI Initialization failed:[/red] {e}"))
            self.model = None

    def generate_keyword_ideas(self, topic: str) -> dict:
        if not self.model:
            return {"error": "SEO model not initialized."}
            
        prompt = f"""
        **🚀 CREATIVE BRIEF: SEO KEYWORD STRATEGY 🚀**
        **👤 ROLE & PERSONA:**
        Act as a world-class SEO Strategist and Market Research Analyst. Your expertise lies in uncovering the hidden search intent of a target audience and translating it into a comprehensive keyword architecture.
        **🎯 PRIMARY OBJECTIVE:**
        Generate a multi-faceted keyword strategy for the core topic: "**{topic}**". The output must be a structured JSON object designed for a marketing team to immediately act upon.
        **🧠 GUIDING PRINCIPLES:**
        1.  **Full-Funnel Coverage:** Provide keywords that cover the entire user journey, from initial awareness (questions) to high-intent consideration (long-tail) and decision (primary).
        2.  **User Intent is King:** Think about *why* a user is searching. The keywords should reflect different intents (informational, transactional, commercial).
        3.  **Semantic Relevance:** The keywords should be thematically related to create content clusters.
        **📋 MANDATORY EXECUTION DIRECTIVES:**
        You must generate a JSON object with the following three keys, populated with high-quality, relevant keyword lists:
        -   `primary_keywords`: A list of 3-5 high-volume, "head" terms that define the core market.
        -   `long_tail_keywords`: A list of 10-15 more specific, multi-word phrases that capture users with high purchase or engagement intent.
        -   `question_keywords`: A list of 5-7 common questions users would type into Google, perfect for blog post or FAQ content ideas.
        **📌 FINAL OUTPUT FORMAT:**
        Return a **valid JSON object ONLY**. Do not include any other text, markdown, or explanations.
        """
        try:
            response = self.model.generate_content(prompt)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned_response)
        except Exception as e:
            return {"error": f"Failed to generate keyword ideas: {e}"}

    def write_blog_post(self, title: str, keywords: list, tone: str = "professional", target_audience: str = "a general audience") -> dict:
        if not self.model:
            return {"error": "SEO model not initialized."}

        prompt = f"""
        **✍️ CREATIVE BRIEF: SEO BLOG POST CONTENT ✍️**
        **👤 ROLE & PERSONA:**
        Act as a professional Content Writer and on-page SEO expert. You write high-quality, engaging content that is not only valuable to the reader but is also perfectly optimized to rank on search engines.
        **🎯 PRIMARY OBJECTIVE:**
        Write a complete, well-structured, and SEO-optimized blog post based on the provided details.
        **📋 CONTENT DETAILS:**
        *   **Title:** `{title}`
        *   **Target Audience:** `{target_audience}`
        *   **Tone of Voice:** `{tone}`
        *   **Must-Include Keywords:** `{", ".join(keywords)}`
        **📜 MANDATORY EXECUTION DIRECTIVES:**
        1.  **Compelling Introduction:** Start with a strong hook that grabs the reader's attention and clearly states the value they will get from reading the post.
        2.  **Logical Structure:** Structure the body of the post with clear, hierarchical headings (H2s for main sections, H3s for sub-sections).
        3.  **Natural Keyword Integration:** Seamlessly and naturally weave all the `Must-Include Keywords` into the text. The content must flow and never feel "stuffed" with keywords.
        4.  **High Readability:** Use short paragraphs, bullet points, and numbered lists where appropriate to make the content easy to scan and digest.
        5.  **Actionable Conclusion:** End with a strong summary and a clear call-to-action that tells the reader what to do next (e.g., "Shop the collection," "Leave a comment," "Learn more").
        6.  **Length:** The final blog post must be substantial, aiming for at least 500 words.
        **📌 FINAL OUTPUT FORMAT:**
        Return the complete blog post as a single string of text.
        """
        try:
            response = self.model.generate_content(prompt)
            return {"status": "success", "blog_post_content": response.text}
        except Exception as e:
            return {"error": f"Failed to write blog post: {e}"}

if __name__ == "__main__":
    console = Console()
    console.print(Panel("🚀 [bold green]Starting SEOAPI Test Suite[/bold green] 🚀"))
    
    seo_tool = SEOAPI()

    console.rule("[bold]Test Case 1: Generate Keyword Ideas[/bold]")
    topic = "Handmade Ceramic Mugs with unique glazes"
    keyword_result = seo_tool.generate_keyword_ideas(topic=topic)

    if keyword_result.get("error"):
        console.print(Panel(f"[bold red]Error:[/bold red] {keyword_result.get('error')}", title="❌ Error"))
    else:
        console.print(Panel(json.dumps(keyword_result, indent=2), title=f"🔑 Keyword Strategy for '{topic}'"))
        
        console.rule("[bold]Test Case 2: Write SEO Blog Post[/bold]")
        
        blog_title = "5 Reasons Why a Handmade Ceramic Mug is the Perfect Gift"
        keywords_to_use = keyword_result.get("primary_keywords", []) + keyword_result.get("long_tail_keywords", [])[:2]
        
        if not keywords_to_use:
            console.print("[yellow]Skipping blog post test as no keywords were generated.[/yellow]")
        else:
            blog_post_result = seo_tool.write_blog_post(
                title=blog_title,
                keywords=keywords_to_use,
                tone="warm and friendly",
                target_audience="gift shoppers and coffee lovers"
            )
            
            if blog_post_result.get("error"):
                console.print(Panel(f"[bold red]Error:[/bold red] {blog_post_result.get('error')}", title="❌ Error"))
            else:
                console.print(Panel(blog_post_result.get("blog_post_content"), title=f"✍️ Generated Blog Post: '{blog_title}'"))

    console.print(Panel("🏁 [bold green]SEOAPI Test Suite Finished[/bold green] 🏁"))