import google.generativeai as genai
import config
import requests
import json
from bs4 import BeautifulSoup
from rich import print as rprint
from rich.panel import Panel
from rich.console import Console
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options

genai.configure(api_key=getattr(config, "GOOGLE_API_KEY", None))

class MarketResearchAPI:
    def __init__(self, model_name="gemini-pro"):
        self.text_model = genai.GenerativeModel(model_name)

    def search_web(self, query: str):
        api_key = getattr(config, "GOOGLE_SEARCH_API_KEY", None)
        cx_id = getattr(config, "GOOGLE_SEARCH_CX_ID", None)
        if not api_key or not cx_id:
            return {"error": "Google Search API key or CX ID is missing."}

        url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx_id}&q={query}"
        try:
            rprint(Panel(f"🔎 [green]Searching for:[/green] {query}", title="Web Search"))
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            items = response.json().get("items", [])[:5]
            results = [
                {"title": item.get("title"), "link": item.get("link"), "snippet": item.get("snippet")}
                for item in items if item.get("link")
            ]
            rprint(Panel(f"[blue]Found {len(results)} search results.[/blue]"))
            return results
        except requests.exceptions.RequestException as e:
            return {"error": f"Web search failed: {e}"}

    def _scrape_with_api(self, url: str):
        scrapeops_api_key = getattr(config, "SCRAPEOPS_API_KEY", None)
        if not scrapeops_api_key:
            return None, "ScrapeOps API key is missing."
        
        rprint(Panel(f"Attempting scrape of [green]{url}[/green] with ScrapeOps...", title="[bold cyan]Step 1: Professional Scraping Engine[/bold cyan]"))
        try:
            response = requests.get(
                url='https://proxy.scrapeops.io/v1/',
                params={'api_key': scrapeops_api_key, 'url': url, 'render_js': 'true'},
                timeout=60
            )
            response.raise_for_status()
            return response.json().get('data', {}), None
        except requests.exceptions.RequestException as e:
            return None, f"ScrapeOps API failed: {e}"

    def _scrape_with_selenium(self, url: str):
        rprint(Panel(f"Professional API failed. Falling back to Selenium headless browser for [yellow]{url}[/yellow]...", title="[bold yellow]Step 2: Fallback to Selenium Headless Browser[/bold yellow]"))
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            html_content = driver.page_source
            driver.quit()
            return html_content, None
        except Exception as e:
            return None, f"Selenium headless browser failed: {e}"

    def _scrape_with_direct_request(self, url: str):
        rprint(Panel(f"Selenium failed. Falling back to direct request for [yellow]{url}[/yellow]...", title="[bold yellow]Step 3: Fallback to Direct Scraping[/bold yellow]"))
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response.text, None
        except requests.exceptions.RequestException as e:
            return None, f"Direct request failed: {e}"

    def _extract_with_llm(self, html_content: str):
        rprint(Panel("Direct scraping failed. Falling back to AI-powered extraction...", title="[bold red]Step 4: Fallback to LLM Extraction[/bold red]"))
        prompt = f"""
        Analyze the following raw HTML content from an e-commerce product page. Your task is to act as a web scraper and extract the following information:
        1.  **Product Name/Title**: The main title of the product.
        2.  **Price**: The numerical price. Ignore currency symbols.
        Return ONLY a valid JSON object with the keys "title" and "price".
        HTML Content:
        ```html
        {html_content[:8000]}
        ```
        """
        try:
            response = self.text_model.generate_content(prompt)
            cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned_text)
        except Exception:
            return None

    def extract_product_info(self, url: str):
        data, error = self._scrape_with_api(url)
        if data:
            extracted = {"title": data.get("name") or data.get("title"), "price": self._extract_number(data.get("price") or data.get("price_string")), "description": data.get("description"), "features": data.get("features", [])[:5]}
            rprint(Panel(f"[cyan]Extracted Data via API:[/cyan]\n{json.dumps(extracted, indent=2)}", title="📊 Structured Data Received"))
            return {"url": url, "extracted_data": extracted}
        
        last_error = error
        html_content, error = self._scrape_with_selenium(url)
        if error: last_error = error
        
        if not html_content:
            html_content, error = self._scrape_with_direct_request(url)
            if error: last_error = error

        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            extracted = {"title": soup.title.string.strip() if soup.title else "", "price": self._extract_price(soup), "description": self._extract_meta_description(soup), "features": self._extract_features(soup)}
            if extracted.get("price"):
                rprint(Panel(f"[cyan]Extracted Data via Local Scraping:[/cyan]\n{json.dumps(extracted, indent=2)}", title="📊 Data Extracted"))
                return {"url": url, "extracted_data": extracted}
            
            llm_extracted = self._extract_with_llm(html_content)
            if llm_extracted and llm_extracted.get("price"):
                extracted["title"] = llm_extracted.get("title", extracted["title"])
                extracted["price"] = self._extract_number(llm_extracted.get("price"))
                rprint(Panel(f"[cyan]Extracted Data via LLM Fallback:[/cyan]\n{json.dumps(extracted, indent=2)}", title="📊 Data Extracted by AI"))
                return {"url": url, "extracted_data": extracted}

        rprint(Panel(f"[bold red]All scraping attempts failed for {url}. Last error: {last_error}[/bold red]", title="❌ Total Scraping Failure"))
        return {"error": f"All scraping attempts failed for {url}. Last error: {last_error}"}

    def _extract_price(self, soup):
        selectors = ['[itemprop="price"]', '[class*="price"]', '[id*="price"]', '.price', '.sale-price', '.a-price-whole', '.a-offscreen']
        for sel in selectors:
            tag = soup.select_one(sel)
            if tag:
                price_num = self._extract_number(tag.get_text(strip=True))
                if price_num: return price_num
        return None

    def _extract_meta_description(self, soup):
        tag = soup.find("meta", attrs={"name":"description"})
        return tag["content"].strip() if tag and tag.get("content") else None

    def _extract_number(self, text):
        if text is None: return None
        if isinstance(text, (int, float)): return float(text)
        cleaned = re.sub(r"[^\d.]", "", str(text))
        try:
            return float(cleaned) if cleaned else None
        except (ValueError, TypeError):
            return None
            
    def _extract_features(self, soup):
        features = []
        for ul in soup.find_all("ul"):
            for li in ul.find_all("li", limit=10):
                text = li.get_text(strip=True)
                if 10 < len(text) < 200: features.append(text)
            if features: break
        return features

    def summarize_competitor_data(self, competitor_data: list):
        prompt = f"""
        **📈 CREATIVE BRIEF: COMPETITOR ANALYSIS & STRATEGY**
        **👤 ROLE & PERSONA**
        Act as "Strat-AI," a hyper-analytical market intelligence AI. Your mission is to convert messy, real-world competitor data into a precise, actionable strategic brief.
        **🎯 CORE MISSION**
        Analyze the provided competitor data and generate a strategic summary in a structured JSON format.
        **📊 INPUT DATA: COMPETITOR ANALYSIS (JSON)**
        ```json
        {json.dumps(competitor_data, indent=2)}
        ```
        **🚨 CRITICAL DIRECTIVES & DATA HANDLING RULES**
        - **💰 Pricing:** If a product has a price of `0` or `null`, EXCLUDE it from price calculations. Your `recommended_price` should be a strategic market entry point, likely near the **median** of the valid competitor prices, not a simple average which can be skewed by outliers.
        - **🧹 Data Cleaning:** If the data contains irrelevant items, focus your analysis on the most common product type.
        - **⚠️ Insufficient Data:** If the data is empty or insufficient, you MUST return a JSON object where the `market_summary` explicitly states this and other fields are null or empty.
        **📋 MANDATORY EXECUTION PLAN**
        1.  **Price Analysis:** Calculate a strategic `recommended_price`.
        2.  **Keyword Analysis:** Extract the top 10 most impactful `common_keywords`.
        3.  **Market Summary:** Write a single, powerful `market_summary` sentence.
        4.  **Strategic Insights:** Provide brief, actionable advice in `strategic_insights`.
        **📌 FINAL OUTPUT FORMAT**
        Return a **valid JSON object ONLY** with keys: `recommended_price` (float or null), `common_keywords` (list), `market_summary` (string), `strategic_insights` (string).
        """
        try:
            rprint(Panel("[green]Generating advanced competitor data summary...[/green]", title="🤖 LLM Analysis"))
            response = self.text_model.generate_content(prompt)
            text = response.text.strip()
            cleaned = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            return data
        except Exception as e:
            return {"error": f"LLM summarization failed: {e}"}

    def analyze_market(self, query: str):
        results = self.search_web(query)
        if "error" in results or not results:
            return {"error": results.get("error", "No relevant search results found.")}
            
        competitor_data = []
        for item in results:
            info = self.extract_product_info(item["link"])
            if "extracted_data" in info and info["extracted_data"].get("price"):
                competitor_data.append(info["extracted_data"])
                
        if not competitor_data:
            return {"error": "Could not extract valid product data from any of the search results."}
            
        summary = self.summarize_competitor_data(competitor_data)
        return {"competitor_data": competitor_data, "summary": summary}

    def suggest_price(self, product_description: str):
        rprint(Panel(f"💰 Researching a suggested price for '{product_description}'...", title="Dynamic Pricing"))
        market_analysis = self.analyze_market(f"price of {product_description}")

        if "error" in market_analysis:
            rprint(Panel(f"[bold red]❌ Could not determine a price. Reason:[/bold red] {market_analysis['error']}", title="Pricing Error"))
            return market_analysis

        summary = market_analysis.get("summary", {})
        recommended_price = summary.get("recommended_price")

        if recommended_price is None or recommended_price == 0.0:
            err_msg = summary.get("market_summary", "Market analysis was successful, but a specific price could not be recommended.")
            rprint(Panel(f"[bold yellow]⚠️ {err_msg}[/bold yellow]", title="Pricing Warning"))
            return {"error": err_msg}

        result = {
            "status": "success",
            "suggested_price": recommended_price,
            "justification": summary.get("market_summary")
        }
        
        rprint(Panel(
            f"[bold green]✅ Price Suggestion Complete![/bold green]\n\n"
            f"Based on competitor data, you should price your product at:\n\n"
            f"[bold cyan]${result['suggested_price']:.2f}[/bold cyan]\n\n"
            f"[italic]Justification: {result['justification']}[/italic]",
            title="💰 Your Recommended Price"
        ))
        
        return result

if __name__ == "__main__":
    console = Console()
    console.print(Panel("🚀 [bold yellow]Starting Ultimate Resilient Market Research Test Suite[/bold yellow] 🚀", expand=False))

    mr = MarketResearchAPI(model_name="gemini-1.5-flash-latest")
    
    console.rule("[bold]Test Case 1: Full Market Analysis for 'Handmade Leather Wallet'[/bold]")
    market_query = "handmade leather bifold wallet"
    market_analysis = mr.analyze_market(market_query)
    
    if market_analysis.get("error"):
        console.print(Panel(f"[bold red]❌ Analysis Failed:[/bold red] {market_analysis.get('error')}", title="❌ Error"))
    else:
        summary = market_analysis.get("summary", {})
        console.print(Panel(
            f"[bold green]✅ Market Analysis Successful![/bold green]\n\n"
            f"💰 [bold]Recommended Price:[/bold] ${summary.get('recommended_price', 0.0):.2f}\n"
            f"🔑 [bold]Common Keywords:[/bold] {', '.join(summary.get('common_keywords', []))}\n"
            f"📈 [bold]Market Summary:[/bold] {summary.get('market_summary')}\n"
            f"💡 [bold]Strategic Insights:[/bold] {summary.get('strategic_insights')}",
            title="📈 Final Market Summary"
        ))

    console.rule("[bold]Test Case 2: Direct Price Suggestion for 'Linen Totes'[/bold]")
    price_query = "durable linen tote bag with inner pocket"
    price_suggestion = mr.suggest_price(price_query)

    if price_suggestion.get("error"):
        console.print(Panel(f"[bold red]❌ Pricing Failed:[/bold red] {price_suggestion.get('error')}", title="❌ Error"))
    else:
        console.print(Panel(
            f"Based on the analysis, the suggested price for a '{price_query}' is [bold green]${price_suggestion.get('suggested_price', 0.0):.2f}[/bold green].",
            title="✅ Final Price Suggestion"
        ))

    console.print(Panel("🏁 [bold yellow]Market Research Test Suite Finished[/bold yellow] 🏁", expand=False))