import os
import asyncio
from mcp.server.fastmcp import FastMCP
from rich.console import Console
from rich.panel import Panel

from market_research import MarketResearchAPI
from design_api import DesignAPI
from amazon_api import AmazonAPI
from facebook_api import FacebookAPI
from instagram_api import InstagramAPI
from website_manager import WebsiteManager
from whatsapp_api import WhatsAppAPI
from business_intelligent_api import BusinessIntelligenceAPI
from proactive_monitor import ProactiveMonitor
from database_manager import DataManager
from email_api import EmailAPI
from seo_api import SEOAPI
from pinterest_api import PinterestAPI
import file_system_tools

console = Console()
mcp = FastMCP(name="kala-sahayak-tool-server",
              host="0.0.0.0",
              port=8080
             )

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
async def bizintel_generate_content_calendar(topic: str, duration_days: int):
    return await asyncio.to_thread(bi_api.generate_content_calendar, topic, duration_days)

@mcp.tool()
async def bizintel_predictive_sales_forecast(sales_csv_path: str, forecast_periods: int):
    return await asyncio.to_thread(bi_api.predictive_sales_forecast, sales_csv_path, forecast_periods)

@mcp.tool()
async def bizintel_create_invoice(save_path: str, order_details: dict):
    return await asyncio.to_thread(bi_api.create_invoice, save_path, order_details)

@mcp.tool()
async def bizintel_generate_shipping_label(save_path: str, shipping_details: dict):
    return await asyncio.to_thread(bi_api.generate_shipping_label, save_path, shipping_details)

@mcp.tool()
async def bizintel_analyze_customer_feedback(feedback_list: list):
    return await asyncio.to_thread(bi_api.analyze_customer_feedback, feedback_list)

@mcp.tool()
async def design_enhance_product_photo(input_path: str, save_path: str):
    return await asyncio.to_thread(design_api.enhance_product_photo, input_path, save_path)

@mcp.tool()
async def design_create_promo_video(image_paths: list, text_overlays: list, save_path: str):
    return await asyncio.to_thread(design_api.create_promo_video, image_paths, text_overlays, save_path)

@mcp.tool()
async def design_create_poster(product_name: str, description: str, call_to_action: str, save_path: str):
    return await asyncio.to_thread(design_api.create_poster, product_name, description, call_to_action, save_path)

@mcp.tool()
async def design_update_poster(product_name: str, prompt_used: str, user_feedback: str, new_save_path: str):
    return await asyncio.to_thread(design_api.update_poster, product_name, prompt_used, user_feedback, new_save_path)

@mcp.tool()
async def display_show_local_image(file_path: str):
    return await asyncio.to_thread(design_api.show_image, file_path)

@mcp.tool()
async def market_analyze_market(query: str):
    return await asyncio.to_thread(market_api.analyze_market, query)

@mcp.tool()
async def market_suggest_price(product_description: str):
    return await asyncio.to_thread(market_api.suggest_price, product_description)

@mcp.tool()
async def system_get_current_directory():
    return await asyncio.to_thread(lambda: {"current_directory": os.getcwd()})

@mcp.tool()
async def file_system_list_files(directory_path: str = "."):
    return await asyncio.to_thread(file_system_tools.list_files, directory_path)

@mcp.tool()
async def file_system_write_text_file(file_path: str, content: str):
    return await asyncio.to_thread(file_system_tools.write_text_file, file_path, content)

@mcp.tool()
async def email_draft_and_send_promotional_email(recipient_emails: list, subject_line: str, product_name: str, key_selling_points: list, call_to_action_url: str):
    return await asyncio.to_thread(email_api.draft_and_send_promotional_email, recipient_emails, subject_line, product_name, key_selling_points, call_to_action_url)

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
async def facebook_post_text(content: str):
    return await asyncio.to_thread(facebook_api.post_text, content=content)

@mcp.tool()
async def facebook_post_image(content: str, image_path: str):
    return await asyncio.to_thread(facebook_api.post_image, content=content, image_path=image_path)

@mcp.tool()
async def facebook_post_video(description: str, video_path: str):
    return await asyncio.to_thread(facebook_api.post_video, description=description, video_path=video_path)

@mcp.tool()
async def facebook_create_event(name: str, start_time: str, description: str):
    return await asyncio.to_thread(facebook_api.create_event, name=name, start_time=start_time, description=description)

@mcp.tool()
async def facebook_get_page_feed(limit: int = 10):
    return await asyncio.to_thread(facebook_api.get_page_feed, limit=limit)

@mcp.tool()
async def amazon_create_or_update_listing(sku: str, product_title: str, description: str, bullet_points: list, price: float, keywords: list):
    return await asyncio.to_thread(amazon_api.create_or_update_listing, sku, product_title, description, bullet_points, price, keywords)

@mcp.tool()
async def amazon_get_listing(sku: str):
    return await asyncio.to_thread(amazon_api.get_listing, sku)

@mcp.tool()
async def amazon_update_price(sku: str, price: float):
    return await asyncio.to_thread(amazon_api.update_price, sku, price)

@mcp.tool()
async def amazon_update_inventory(sku: str, quantity: int):
    return await asyncio.to_thread(amazon_api.update_inventory, sku, quantity)

@mcp.tool()
async def amazon_get_orders(created_after: str):
    return await asyncio.to_thread(amazon_api.get_orders, created_after)

@mcp.tool()
async def instagram_post_image(caption: str, image_path: str):
    return await asyncio.to_thread(instagram_api.post_image, caption, image_path)

@mcp.tool()
async def instagram_post_carousel(caption: str, image_paths: list):
    return await asyncio.to_thread(instagram_api.post_carousel, caption, image_paths)

@mcp.tool()
async def instagram_post_story(image_path: str, link_url: str = None):
    return await asyncio.to_thread(instagram_api.post_story, image_path, link_url)

@mcp.tool()
async def website_generate_full_website(site_title: str, pages: list):
    return await asyncio.to_thread(website_manager.generate_full_website, site_title, pages)

@mcp.tool()
async def website_add_or_update_page(site_title: str, page_info: dict, all_pages: list):
    return await asyncio.to_thread(website_manager.add_or_update_page, site_title, page_info, all_pages)

@mcp.tool()
async def website_get_file_structure():
    return await asyncio.to_thread(website_manager.get_file_structure)

@mcp.tool()
async def website_clear_directory():
    return await asyncio.to_thread(website_manager.clear_directory)

@mcp.tool()
async def website_open_in_browser(page: str = None):
    return await asyncio.to_thread(website_manager.open_website_in_browser, page)

@mcp.tool()
async def whatsapp_send_text_message(recipient_id: str, message: str):
    return await asyncio.to_thread(whatsapp_api.send_text_message, recipient_id, message)

@mcp.tool()
async def whatsapp_send_image(recipient_id: str, file_path: str, caption: str = None):
    return await asyncio.to_thread(whatsapp_api.send_image, recipient_id, file_path, caption)

@mcp.tool()
async def whatsapp_send_document(recipient_id: str, file_path: str):
    return await asyncio.to_thread(whatsapp_api.send_document, recipient_id, file_path)

@mcp.tool()
async def data_manager_add_product(name: str, description: str, price: float, stock_quantity: int):
    return await asyncio.to_thread(data_manager.add_product, name, description, price, stock_quantity)

@mcp.tool()
async def data_manager_add_customer(name: str, contact_info: str):
    return await asyncio.to_thread(data_manager.add_customer, name, contact_info)

@mcp.tool()
async def data_manager_create_order_and_shipment(customer_identifier: str, items: list, shipping_address: str):
    return await asyncio.to_thread(data_manager.create_order_and_shipment, customer_identifier, items, shipping_address)

@mcp.tool()
async def data_manager_get_all_products():
    return await asyncio.to_thread(data_manager.get_all_products)

@mcp.tool()
async def data_manager_get_all_customers():
    return await asyncio.to_thread(data_manager.get_all_customers)

@mcp.tool()
async def data_manager_get_customer_details_and_orders(customer_identifier: str):
    return await asyncio.to_thread(data_manager.get_customer_details_and_orders, customer_identifier)

@mcp.tool()
async def data_manager_update_daily_sales(for_date: str = None):
    return await asyncio.to_thread(data_manager.update_daily_sales, for_date)

@mcp.tool()
async def data_manager_export_sales_to_csv(file_path: str):
    return await asyncio.to_thread(data_manager.export_sales_to_csv, file_path)

@mcp.tool()
async def data_manager_get_sales_on_date(date_str: str):
    return await asyncio.to_thread(data_manager.get_sales_on_date, date_str)

@mcp.tool()
async def data_manager_get_product_sales_on_date(product_name: str, date_str: str):
    return await asyncio.to_thread(data_manager.get_product_sales_on_date, product_name, date_str)

@mcp.tool()
async def data_manager_get_sales_for_date_range(start_date_str: str, end_date_str: str):
    return await asyncio.to_thread(data_manager.get_sales_for_date_range, start_date_str, end_date_str)

@mcp.tool()
async def data_manager_get_customers_on_date(date_str: str):
    return await asyncio.to_thread(data_manager.get_customers_on_date, date_str)

@mcp.tool()
async def data_manager_get_total_sales_summary_on_date(date_str: str):
    return await asyncio.to_thread(data_manager.get_total_sales_summary_on_date, date_str)


if __name__ == "__main__":
    console.print(Panel("[bold green]🚀 Kala-Sahayak MCP Tool Server is Online[/]",
                        title="🖥️ Server Status", border_style="green"))
    transport="sse"
    console.print(f"🌍 Listening on http://localhost:8080 (transport: {transport})")
    if transport=="stdio":
        mcp.run(transport="stdio")
    elif transport=="sse":
        mcp.run(transport="sse")