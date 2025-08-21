import os
import asyncio
from mcp.server.fastmcp import FastMCP
from rich.console import Console
from rich.panel import Panel

from tool_definations import get_tool_definitions
from knowledge_graph import KnowledgeGraph
from market_research import MarketResearchAPI
from design_api import DesignAPI
from amazon_api import AmazonAPI
from facebook_api import FacebookAPI
from instagram_api import InstagramAPI
from website_manager import WebsiteManager
from whatsapp_api import WhatsAppAPI
from business_intelligent_api import BusinessIntelligenceAPI
from proactive_monitor import ProactiveMonitor
from chroma_manager import ChromaDBManager
from database_manager import DataManager
from email_api import EmailAPI
from seo_api import SEOAPI
from pinterest_api import PinterestAPI
import file_system_tools

console = Console()
mcp = FastMCP(name="kala-sahayak-tool-server")

console.log("Instantiating all API and manager classes...")
facebook_api = FacebookAPI()
instagram_api = InstagramAPI()
design_api = DesignAPI()
market_api = MarketResearchAPI()
website_manager = WebsiteManager()
bi_api = BusinessIntelligenceAPI()
data_manager = DataManager()
proactive_monitor = ProactiveMonitor(facebook_api, instagram_api)
amazon_api = AmazonAPI()
whatsapp_api = WhatsAppAPI()
email_api = EmailAPI()
seo_api = SEOAPI()
pinterest_api = PinterestAPI()
console.log("All tool classes instantiated successfully.")

@mcp.tool()
async def monitor_check_for_new_comments():
    return await asyncio.to_thread(proactive_monitor.check_for_new_comments)

@mcp.tool()
async def bizintel_generate_content_calendar(topic: str, platforms: list):
    return await asyncio.to_thread(bi_api.generate_content_calendar, topic, platforms)

@mcp.tool()
async def bizintel_predictive_sales_forecast(historical_data: dict):
    return await asyncio.to_thread(bi_api.predictive_sales_forecast, historical_data)

@mcp.tool()
async def bizintel_create_invoice(customer_name: str, items: list, amount: float):
    return await asyncio.to_thread(bi_api.create_invoice, customer_name, items, amount)

@mcp.tool()
async def bizintel_generate_shipping_label(customer_name: str, address: str, order_id: str):
    return await asyncio.to_thread(bi_api.generate_shipping_label, customer_name, address, order_id)

@mcp.tool()
async def bizintel_analyze_customer_feedback(feedback_text: str):
    return await asyncio.to_thread(bi_api.analyze_customer_feedback, feedback_text)

@mcp.tool()
async def design_enhance_product_photo(image_path: str, enhancement_type: str = "auto"):
    return await asyncio.to_thread(design_api.enhance_product_photo, image_path, enhancement_type)

@mcp.tool()
async def design_create_promo_video(image_paths: list, text_overlays: list, audio_track: str):
    return await asyncio.to_thread(design_api.create_promo_video, image_paths, text_overlays, audio_track)

@mcp.tool()
async def design_create_poster(template_id: str, text_elements: dict, image_url: str):
    return await asyncio.to_thread(design_api.create_poster, template_id, text_elements, image_url)

@mcp.tool()
async def design_update_poster(poster_id: str, updates: dict):
    return await asyncio.to_thread(design_api.update_poster, poster_id, updates)

@mcp.tool()
async def display_show_local_image(image_path: str):
    return await asyncio.to_thread(design_api.show_image, image_path)

@mcp.tool()
async def market_analyze_market(product_description: str):
    return await asyncio.to_thread(market_api.analyze_market, product_description)

@mcp.tool()
async def market_suggest_price(product_description: str, competitor_prices: list):
    return await asyncio.to_thread(market_api.suggest_price, product_description, competitor_prices)

@mcp.tool()
async def system_get_current_directory():
    return await asyncio.to_thread(lambda: {"current_directory": os.getcwd()})

@mcp.tool()
async def file_system_list_files(directory: str = "."):
    return await asyncio.to_thread(file_system_tools.list_files, directory)

@mcp.tool()
async def file_system_write_text_file(file_path: str, content: str):
    return await asyncio.to_thread(file_system_tools.write_text_file, file_path, content)

@mcp.tool()
async def email_draft_and_send_promotional_email(recipient_email: str, subject: str, body: str):
    return await asyncio.to_thread(email_api.draft_and_send_promotional_email, recipient_email, subject, body)

@mcp.tool()
async def seo_generate_keyword_ideas(topic: str):
    return await asyncio.to_thread(seo_api.generate_keyword_ideas, topic)

@mcp.tool()
async def seo_write_blog_post(title: str, keywords: list, content_prompt: str):
    return await asyncio.to_thread(seo_api.write_blog_post, title, keywords, content_prompt)

@mcp.tool()
async def pinterest_create_pin(image_url: str, board_id: str, title: str, description: str):
    return await asyncio.to_thread(pinterest_api.create_pin, image_url, board_id, title, description)

@mcp.tool()
async def facebook_post_text(message: str, page_id: str = None):
    return await asyncio.to_thread(facebook_api.post_text, message=message, page_id=page_id)

@mcp.tool()
async def facebook_post_image(image_path: str, caption: str, page_id: str = None):
    return await asyncio.to_thread(facebook_api.post_image, image_path=image_path, caption=caption, page_id=page_id)

@mcp.tool()
async def facebook_post_video(video_path: str, description: str, page_id: str = None):
    return await asyncio.to_thread(facebook_api.post_video, video_path=video_path, description=description, page_id=page_id)

@mcp.tool()
async def facebook_create_event(name: str, start_time: str, end_time: str, description: str, page_id: str = None):
    return await asyncio.to_thread(facebook_api.create_event, name=name, start_time=start_time, end_time=end_time, description=description, page_id=page_id)

@mcp.tool()
async def facebook_get_page_feed(page_id: str = None, limit: int = 10):
    return await asyncio.to_thread(facebook_api.get_page_feed, page_id=page_id, limit=limit)

@mcp.tool()
async def amazon_create_or_update_listing(product_id: str, title: str, description: str, price: float, image_url: str):
    return await asyncio.to_thread(amazon_api.create_or_update_listing, product_id, title, description, price, image_url)

@mcp.tool()
async def amazon_get_listing(product_id: str):
    return await asyncio.to_thread(amazon_api.get_listing, product_id)

@mcp.tool()
async def amazon_update_price(product_id: str, new_price: float):
    return await asyncio.to_thread(amazon_api.update_price, product_id, new_price)

@mcp.tool()
async def amazon_update_inventory(product_id: str, new_quantity: int):
    return await asyncio.to_thread(amazon_api.update_inventory, product_id, new_quantity)

@mcp.tool()
async def amazon_get_orders(status: str = "unshipped"):
    return await asyncio.to_thread(amazon_api.get_orders, status)

@mcp.tool()
async def instagram_post_image(image_path: str, caption: str):
    return await asyncio.to_thread(instagram_api.post_image, image_path, caption)

@mcp.tool()
async def instagram_post_carousel(image_paths: list, caption: str):
    return await asyncio.to_thread(instagram_api.post_carousel, image_paths, caption)

@mcp.tool()
async def instagram_post_story(image_path: str):
    return await asyncio.to_thread(instagram_api.post_story, image_path)

@mcp.tool()
async def website_generate_full_website(business_name: str, business_description: str):
    return await asyncio.to_thread(website_manager.generate_full_website, business_name, business_description)

@mcp.tool()
async def website_add_or_update_page(file_name: str, content: str):
    return await asyncio.to_thread(website_manager.add_or_update_page, file_name, content)

@mcp.tool()
async def website_get_file_structure():
    return await asyncio.to_thread(website_manager.get_file_structure)

@mcp.tool()
async def website_clear_directory():
    return await asyncio.to_thread(website_manager.clear_directory)

@mcp.tool()
async def website_open_in_browser():
    return await asyncio.to_thread(website_manager.open_website_in_browser)

@mcp.tool()
async def whatsapp_send_text_message(recipient_number: str, message: str):
    return await asyncio.to_thread(whatsapp_api.send_text_message, recipient_number, message)

@mcp.tool()
async def whatsapp_send_image(recipient_number: str, image_url: str, caption: str):
    return await asyncio.to_thread(whatsapp_api.send_image, recipient_number, image_url, caption)

@mcp.tool()
async def whatsapp_send_document(recipient_number: str, document_url: str):
    return await asyncio.to_thread(whatsapp_api.send_document, recipient_number, document_url)

@mcp.tool()
async def data_manager_update_daily_sales(date: str, sales_amount: float):
    return await asyncio.to_thread(data_manager.update_daily_sales, date, sales_amount)

@mcp.tool()
async def data_manager_export_sales_to_csv(file_path: str):
    return await asyncio.to_thread(data_manager.export_sales_to_csv, file_path)

@mcp.tool()
async def data_manager_get_sales_on_date(date: str):
    return await asyncio.to_thread(data_manager.get_sales_on_date, date)

@mcp.tool()
async def data_manager_add_product(product_name: str, category: str, price: float):
    return await asyncio.to_thread(data_manager.add_product, product_name, category, price)

if __name__ == "__main__":
    console.print(Panel("[bold green]🚀 Kala-Sahayak MCP Tool Server is Online[/]", 
                        title="🖥️ Server Status", border_style="green"))
    console.print(f"🌍 Listening on http://localhost:8080")
    mcp.run(transport="http", host="0.0.0.0", port=8080)