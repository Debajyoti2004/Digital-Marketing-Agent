import google.generativeai as genai
import config
import requests
import json
from bs4 import BeautifulSoup
from rich import print as rprint
from rich.panel import Panel
from collections import Counter
import re

genai.configure(api_key=getattr(config, "GENAI_API_KEY", None))

class MarketResearchAPI:
    def __init__(self, model_name="gemini-pro"):
        self.text_model = genai.GenerativeModel(model_name)

    def search_web(self, query: str):
        api_key = getattr(config, "GOOGLE_SEARCH_API_KEY", None)
        cx_id = getattr(config, "GOOGLE_SEARCH_CX_ID", None)
        if not api_key or not cx_id:
            err = "Google Search API key or CX ID is missing in config.py."
            rprint(Panel(f"[bold red]{err}[/bold red]", title="❌ API Config Error", border_style="red"))
            return {"error": err}

        url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx_id}&q={query}"
        try:
            rprint(Panel(f"[bold green]Performing web search for:[/bold green] {query}", title="🔎 Web Search", border_style="green"))
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            items = response.json().get("items", [])[:5]
            results = [
                {"title": item.get("title"), "link": item.get("link"), "snippet": item.get("snippet")}
                for item in items
            ]
            rprint(Panel(f"[bold blue]Top 5 search results returned.[/bold blue]", border_style="blue"))
            return results
        except requests.exceptions.RequestException as e:
            err = f"Web search failed: {e}"
            rprint(Panel(f"[bold red]{err}[/bold red]", title="❌ Web Search Error", border_style="red"))
            return {"error": err}

    def extract_product_info(self, url: str):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            rprint(Panel(f"[bold green]Fetching product page:[/bold green] {url}", title="🌐 Page Fetch", border_style="green"))
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            extracted = {}

            extracted["title"] = soup.title.string.strip() if soup.title else ""
            extracted["price"] = self._extract_price(soup) or 0
            extracted["description"] = self._extract_meta_description(soup) or ""
            extracted["specs"] = self._extract_specs(soup)
            extracted["features"] = self._extract_features(soup)

            rprint(Panel(f"[bold cyan]Extracted Data:[/bold cyan]\n{json.dumps(extracted, indent=2)}", title="📊 Extracted Data", border_style="cyan"))
            return {"url": url, "extracted_data": extracted}
        except Exception as e:
            err = f"Failed to analyze page {url}: {e}"
            rprint(Panel(f"[bold red]{err}[/bold red]", title="❌ Scraping Error", border_style="red"))
            return {"error": err}

    def _extract_price(self, soup):
        selectors = [
            '[itemprop="price"]',
            '[class*="price"]',
            '[id*="price"]',
            '.price',
            '.sale-price',
            '.a-price-whole',
            '[data-price]',
        ]
        for sel in selectors:
            tag = soup.select_one(sel)
            if tag and tag.get_text(strip=True):
                price_text = tag.get_text(strip=True)
                price_num = self._extract_number(price_text)
                if price_num:
                    return price_num
        return None

    def _extract_meta_description(self, soup):
        tag = soup.find("meta", attrs={"name":"description"})
        if tag and tag.get("content"):
            return tag["content"].strip()
        return None

    def _extract_number(self, text):
        cleaned = re.sub(r"[^\d.,]", "", text)
        cleaned = cleaned.replace(",", "")
        try:
            return float(cleaned)
        except:
            return None

    def _extract_specs(self, soup):
        specs = {}
        tables = soup.find_all("table")
        for table in tables:
            for row in table.find_all("tr"):
                cols = row.find_all(["th", "td"])
                if len(cols) >= 2:
                    key = cols[0].get_text(strip=True)
                    value = cols[1].get_text(strip=True)
                    if key and value:
                        specs[key] = value
            if specs:
                break
        return specs

    def _extract_features(self, soup):
        features = []
        ul_tags = soup.find_all("ul")
        for ul in ul_tags:
            lis = ul.find_all("li")
            for li in lis:
                text = li.get_text(strip=True)
                if text and len(text) > 10:
                    features.append(text)
            if features:
                break
        return features

    def summarize_competitor_data(self, competitor_data: list):
        prompt = f"""
📊 You are a seasoned e-commerce market analyst and strategist.

🔍 Analyze the JSON array of competitor product data below with attention to detail:  
- Calculate the average product price with currency precision.  
- Recommend an aggressive yet realistic pricing strategy to capture market share.  
- Extract and rank the most impactful keywords from competitor titles and features.  
- Craft a concise, insightful market summary highlighting trends, gaps, and opportunities.  
- Suggest actionable insights for product positioning and marketing focus.

📈 Competitor data:
{json.dumps(competitor_data, indent=2)}

🧠 Return a valid JSON object with keys:  
- recommended_price (float) — your price recommendation.  
- common_keywords (list of strings) — top 10 keywords sorted by relevance.  
- market_summary (string) — one insightful, market-focused sentence.  
- strategic_insights (string) — brief recommendations for product differentiation.

⚠️ Ensure the response is clean JSON, no additional text or code formatting.
"""
        try:
            rprint(Panel(f"[bold green]Generating advanced competitor data summary...[/bold green]", title="🤖 LLM Analysis", border_style="green"))
            response = self.text_model.generate_content(prompt)
            text = response.text.strip()
            cleaned = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)

            data.setdefault("recommended_price", None)
            data.setdefault("common_keywords", [])
            data.setdefault("market_summary", "")
            data.setdefault("strategic_insights", "")

            rprint(Panel(f"[bold cyan]Advanced Analysis Result:[/bold cyan]\n{json.dumps(data, indent=2)}", title="📈 Market Summary", border_style="cyan"))
            return data
        except Exception as e:
            err = f"LLM summarization failed: {e}"
            rprint(Panel(f"[bold red]{err}[/bold red]", title="❌ LLM Error", border_style="red"))
            return {"error": err, "details": text if 'text' in locals() else "No response"}

    def extract_common_keywords(self, titles: list, top_n=10):
        all_words = []
        for title in titles:
            words = re.findall(r"\b\w+\b", title.lower())
            all_words.extend(words)
        stopwords = {"the", "and", "for", "with", "a", "of", "in", "to", "on", "by", "our", "new"}
        filtered = [w for w in all_words if w not in stopwords and len(w) > 2]
        counts = Counter(filtered)
        common = [word for word, _ in counts.most_common(top_n)]
        return common

    def analyze_market(self, query: str):
        results = self.search_web(query)
        if "error" in results:
            return {"error": results["error"]}

        competitor_data = []
        for item in results:
            info = self.extract_product_info(item["link"])
            if "extracted_data" in info:
                data = info["extracted_data"]
                competitor_data.append({
                    "title": data.get("title", ""),
                    "price": data.get("price", 0),
                    "description": data.get("description", ""),
                    "specs": data.get("specs", {}),
                    "features": data.get("features", [])
                })

        if not competitor_data:
            err = "No competitor data extracted from search results."
            rprint(Panel(f"[bold red]{err}[/bold red]", title="❌ Data Extraction Error", border_style="red"))
            return {"error": err}

        summary = self.summarize_competitor_data(competitor_data)
        return {"competitor_data": competitor_data, "summary": summary}

if __name__ == "__main__":
    mr = MarketResearchAPI()
    search_query = "best wireless earbuds under 2000"

    rprint(Panel(f"[bold yellow]🚀 Starting Market Analysis for query:[/bold yellow] {search_query}", title="🚀 Market Research Start", border_style="yellow"))
    analysis = mr.analyze_market(search_query)

    if "error" in analysis:
        rprint(Panel(f"[bold red]❌ Error:[/bold red] {analysis['error']}", title="❌ Error", border_style="red"))
    else:
        rprint(Panel(f"[bold green]📊 Competitor Data Extracted:[/bold green]\n{json.dumps(analysis['competitor_data'], indent=2)}", title="📊 Competitor Data"))
        rprint(Panel(f"[bold cyan]📈 Market Summary:[/bold cyan]\n{json.dumps(analysis['summary'], indent=2)}", title="📈 Market Analysis"))
