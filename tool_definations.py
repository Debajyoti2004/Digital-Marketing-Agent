from cohere.types import Tool
from typing import List

def get_tool_definitions() -> List[Tool]:
    return [
        Tool(
            name="monitor_check_for_new_comments",
            description="Proactively scans linked social media accounts for new comments since the last check.",
            parameter_definitions={}
        ),
        Tool(
            name="bizintel_generate_content_calendar",
            description="Generates a strategic, multi-day social media content calendar.",
            parameter_definitions={
                "topic": {"type": "string", "description": "The central theme for the content plan.", "required": True},
                "duration_days": {"type": "int", "description": "The number of days the calendar should cover."}
            }
        ),
        Tool(
            name="bizintel_predictive_sales_forecast",
            description="Analyzes historical sales data from a CSV to forecast future sales.",
            parameter_definitions={
                "sales_csv_path": {"type": "string", "description": "The local file path to the sales data CSV.", "required": True},
                "forecast_periods": {"type": "int", "description": "The number of future periods to forecast."}
            }
        ),
        Tool(
            name="bizintel_analyze_customer_feedback",
            description="Analyzes customer comments to identify themes, sentiment, and insights.",
            parameter_definitions={
                "feedback_list": {"type": "array", "description": "A list of customer feedback strings.", "required": True, "items": {"type": "string"}}
            }
        ),
        Tool(
            name="design_enhance_product_photo",
            description="Improves a real product photograph by automatically removing its background, making it suitable for catalogs and promotional materials.",
            parameter_definitions={
                "input_path": {"type": "string", "description": "The local file path of the product photo to be enhanced.", "required": True},
                "save_path": {"type": "string", "description": "The local file path where the enhanced photo with the removed background will be saved.", "required": True}
            }
        ),
        Tool(
            name="design_create_promo_video",
            description="Creates a short promotional video by stitching together a series of images with text overlays. This process runs locally.",
            parameter_definitions={
                "image_paths": {"type": "array", "description": "An ordered list of local file paths for the images to be included in the video.", "items": {"type": "string"}, "required": True},
                "text_overlays": {"type": "array", "description": "A list of text strings to overlay on the corresponding images.", "items": {"type": "string"}, "required": True},
                "save_path": {"type": "string", "description": "The local file path to save the final MP4 video file.", "required": True},
                "duration_per_image": {"type": "int", "description": "The number of seconds each image will be displayed in the video. Defaults to 3.", "required": False}
            }
        ),
        Tool(
            name="design_create_promo_video_with_api",
            description="Creates a promotional video using a cloud-based API (Shotstack). This is a more robust alternative to the local video creation tool.",
            parameter_definitions={
                "image_paths": {"type": "array", "description": "A list of local image file paths. These will be temporarily hosted to be accessible by the API.", "items": {"type": "string"}, "required": True},
                "text_overlays": {"type": "array", "description": "A list of text captions to overlay on each image.", "items": {"type": "string"}, "required": True},
                "save_path": {"type": "string", "description": "The local file path to save the final MP4 video file after it's rendered and downloaded.", "required": True},
                "duration_per_image": {"type": "int", "description": "The duration in seconds for each image clip. Defaults to 3.", "required": False}
            }
        ),
        Tool(
            name="bizintel_create_invoice",
            description="Generates a professional PDF invoice for an order.",
            parameter_definitions={
                "save_path": {"type": "string", "description": "The local file path to save the PDF.", "required": True},
                "order_details": {"type": "object", "description": "A JSON object with order details.", "required": True}
            }
        ),
        Tool(
            name="bizintel_generate_shipping_label",
            description="Generates a formatted PDF shipping label.",
            parameter_definitions={
                "save_path": {"type": "string", "description": "The local file path to save the PDF.", "required": True},
                "shipping_details": {"type": "object", "description": "A JSON object with from and to addresses.", "required": True}
            }
        ),
        Tool(
            name="market_analyze_market",
            description="Performs a comprehensive market analysis for a product query, including competitor research and strategic insights.",
            parameter_definitions={
                "query": {"type": "string", "description": "The product or market to research.", "required": True}
            }
        ),
        Tool(
            name="market_suggest_price",
            description="Performs a full market analysis to suggest a competitive price for a product.",
            parameter_definitions={
                "product_description": {"type": "string", "description": "A detailed description of the product.", "required": True}
            }
        ),
        Tool(
            name="design_create_poster",
            description="Generates a new AI-powered promotional poster from a textual description. This is the first step for creating a new visual asset.",
            parameter_definitions={
                "product_name": {"type": "string", "description": "The name of the product to be featured on the poster.", "required": True},
                "description": {"type": "string", "description": "A short, engaging marketing description of the product.", "required": True},
                "call_to_action": {"type": "string", "description": "The call to action text (e.g., 'Shop Now', 'Learn More').", "required": True},
                "save_path": {"type": "string", "description": "The local file path where the generated poster image will be saved (e.g., 'output/poster_v1.png').", "required": True},
                "target_audience": {"type": "string", "description": "Optional: A brief description of the target audience to tailor the poster's style.", "required": False},
                "brand_colors": {"type": "array", "description": "Optional: A list of brand colors (e.g., ['#FF5733', 'blue']) to influence the poster's color palette.", "items": {"type": "string"}, "required": False}
            }
        ),
        Tool(
            name="design_update_poster",
            description="Updates an existing AI-generated poster based on user feedback to refine the design.",
            parameter_definitions={
                "product_name": {"type": "string", "description": "The name of the product featured on the poster.", "required": True},
                "prompt_used": {"type": "string", "description": "The exact creative prompt that was used to generate the previous version of the poster.", "required": True},
                "user_feedback": {"type": "string", "description": "Specific feedback and instructions for how the poster should be changed (e.g., 'Make the background brighter', 'Use a different font').", "required": True},
                "new_save_path": {"type": "string", "description": "The new local file path to save the updated poster (e.g., 'output/poster_v2.png').", "required": True}
            }
        ),
        Tool(
            name="design_show_image",
            description="Displays a local image file on the user's screen using the default image viewer.",
            parameter_definitions={
                "file_path": {"type": "string", "description": "The local path to the image file you want to display.", "required": True}
            }
        ),
        Tool(
            name="system_get_current_directory",
            description="Returns the current working directory.",
            parameter_definitions={}
        ),
        Tool(
            name="file_system_list_files",
            description="Lists all files and subdirectories within a specified local directory.",
            parameter_definitions={
                "directory_path": {"type": "string", "description": "The path to the directory to inspect.", "required": False}
            }
        ),
        Tool(
            name="file_system_write_text_file",
            description="Creates or overwrites a text file with provided content.",
            parameter_definitions={
                "file_path": {"type": "string", "description": "The full local path for the file.", "required": True},
                "content": {"type": "string", "description": "The text content to write.", "required": True}
            }
        ),
        Tool(
            name="email_draft_and_send_promotional_email",
            description="Drafts a compelling promotional email using AI and sends it to a list of recipients via Gmail.",
            parameter_definitions={
                "recipient_emails": {"type": "array", "description": "A list of recipient email addresses.", "required": True, "items": {"type": "string"}},
                "subject_line": {"type": "string", "description": "The subject line of the email.", "required": True},
                "product_name": {"type": "string", "description": "The name of the product or event being promoted.", "required": True},
                "key_selling_points": {"type": "array", "description": "A list of key features or benefits to highlight.", "required": True, "items": {"type": "string"}},
                "call_to_action_url": {"type": "string", "description": "The URL for the main call-to-action link.", "required": True}
            }
        ),
        Tool(
            name="data_manager_add_product",
            description="Adds a new product to the shop's database.",
            parameter_definitions={
                "name": {"type": "string", "description": "The name of the product.", "required": True},
                "description": {"type": "string", "description": "A short description.", "required": True},
                "price": {"type": "float", "description": "The selling price.", "required": True},
                "stock_quantity": {"type": "int", "description": "The initial stock quantity.", "required": True}
            }
        ),
        Tool(
            name="data_manager_add_customer",
            description="Adds a new customer to the database. If the contact info already exists, it returns the existing customer's ID.",
            parameter_definitions={
                "name": {"type": "string", "description": "The full name of the customer.", "required": True},
                "contact_info": {"type": "string", "description": "The customer's unique contact information, such as an email address.", "required": True}
            }
        ),
        Tool(
            name="data_manager_create_order_and_shipment",
            description="Creates a new order with multiple items and a corresponding shipment record for a customer. It automatically decrements product stock.",
            parameter_definitions={
                "customer_identifier": {"type": "string", "description": "The ID, name, or contact info of the customer placing the order.", "required": True},
                "items": {
                    "type": "array",
                    "description": "A list of dictionaries, each representing a product in the order.",
                    "required": True,
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "int", "description": "The ID of the product."},
                            "quantity": {"type": "int", "description": "The number of units sold."},
                            "price_per_item": {"type": "float", "description": "The price of a single unit."}
                        },
                        "required": ["product_id", "quantity", "price_per_item"]
                    }
                },
                "shipping_address": {"type": "string", "description": "The full shipping address for the order.", "required": True}
            }
        ),
        Tool(
            name="data_manager_get_all_products",
            description="Retrieves a list of all products available in the database.",
            parameter_definitions={}
        ),
        Tool(
            name="data_manager_get_all_customers",
            description="Retrieves a list of all customers in the database.",
            parameter_definitions={}
        ),
        Tool(
            name="data_manager_get_customer_details_and_orders",
            description="Retrieves full details and the complete order history for a specific customer.",
            parameter_definitions={
                "customer_identifier": {"type": "string", "description": "The ID, name, or contact info of the customer to look up.", "required": True}
            }
        ),
        Tool(
            name="data_manager_update_daily_sales",
            description="Aggregates orders into the daily sales summary table for a specific date. Defaults to today if no date is provided. Should be run once at the end of the day.",
            parameter_definitions={
                "for_date": {"type": "string", "description": "The date to summarize sales for, e.g., 'today', 'yesterday'. Defaults to the current day.", "required": False}
            }
        ),
        Tool(
            name="data_manager_export_sales_to_csv",
            description="Exports the daily sales data to a CSV file for analysis.",
            parameter_definitions={
                "file_path": {"type": "string", "description": "The local path to save the CSV file.", "required": True}
            }
        ),
        Tool(
            name="data_manager_get_sales_on_date",
            description="Retrieves a summary of all product sales on a specific date using natural language.",
            parameter_definitions={
                "date_str": {"type": "string", "description": "The date to query, e.g., 'today', 'yesterday', 'last friday', '2025-08-19'.", "required": True}
            }
        ),
        Tool(
            name="data_manager_get_product_sales_on_date",
            description="Retrieves sales data for a specific product on a specific date.",
            parameter_definitions={
                "product_name": {"type": "string", "description": "The name of the product to query.", "required": True},
                "date_str": {"type": "string", "description": "The date to query, e.g., 'today', 'yesterday'.", "required": True}
            }
        ),
        Tool(
            name="data_manager_get_sales_for_date_range",
            description="Retrieves all sales data within a specified date range.",
            parameter_definitions={
                "start_date_str": {"type": "string", "description": "The start date of the range.", "required": True},
                "end_date_str": {"type": "string", "description": "The end date of the range.", "required": True}
            }
        ),
        Tool(
            name="data_manager_get_customers_on_date",
            description="Retrieves a list of customers who placed an order on a specific date.",
            parameter_definitions={
                "date_str": {"type": "string", "description": "The date to check for customer activity.", "required": True}
            }
        ),
        Tool(
            name="data_manager_get_total_sales_summary_on_date",
            description="Calculates the grand total revenue and total items sold for a specific date.",
            parameter_definitions={
                "date_str": {"type": "string", "description": "The date for which to calculate the sales summary.", "required": True}
            }
        ),
        Tool(
            name="facebook_post_text",
            description="Posts a text message to a Facebook Page.",
            parameter_definitions={"content": {"type": "string", "description": "The text content of the post.", "required": True}}
        ),
        Tool(
            name="facebook_post_image",
            description="Posts an image with a caption to a Facebook Page.",
            parameter_definitions={
                "content": {"type": "string", "description": "The caption for the image.", "required": True},
                "image_path": {"type": "string", "description": "Local file path of the image to upload."}
            }
        ),
        Tool(
            name="facebook_post_video",
            description="Posts a video with a description to a Facebook Page.",
            parameter_definitions={
                "description": {"type": "string", "description": "The description for the video.", "required": True},
                "video_path": {"type": "string", "description": "Local file path of the video to upload."}
            }
        ),
        Tool(
            name="facebook_create_event",
            description="Creates a new event on a Facebook Page.",
            parameter_definitions={
                "name": {"type": "string", "description": "The name of the event.", "required": True},
                "start_time": {"type": "string", "description": "The start time in ISO 8601 format.", "required": True},
                "description": {"type": "string", "description": "A detailed description of the event.", "required": True}
            }
        ),
        Tool(
            name="facebook_get_page_feed",
            description="Retrieves recent posts from the configured Facebook Page.",
            parameter_definitions={"limit": {"type": "int", "description": "The number of posts to retrieve."}}
        ),
        Tool(
            name="amazon_create_or_update_listing",
            description="Creates or updates a product listing on Amazon.",
            parameter_definitions={
                "sku": {"type": "string", "description": "The unique Stock Keeping Unit.", "required": True},
                "product_title": {"type": "string", "description": "The official title for the listing.", "required": True},
                "description": {"type": "string", "description": "The detailed product description.", "required": True},
                "bullet_points": {"type": "array", "description": "A list of 5 key feature bullet points.", "items": {"type": "string"}, "required": True},
                "price": {"type": "float", "description": "The selling price.", "required": True},
                "keywords": {"type": "array", "description": "A list of relevant backend search terms.", "items": {"type": "string"}, "required": True}
            }
        ),
        Tool(
            name="amazon_get_listing",
            description="Retrieves details for a product listing from Amazon by its SKU.",
            parameter_definitions={"sku": {"type": "string", "description": "The SKU of the listing to retrieve.", "required": True}}
        ),
        Tool(
            name="amazon_update_price",
            description="Updates the price for a product on Amazon.",
            parameter_definitions={
                "sku": {"type": "string", "description": "The SKU of the product to update.", "required": True},
                "price": {"type": "float", "description": "The new price for the product.", "required": True}
            }
        ),
        Tool(
            name="amazon_update_inventory",
            description="Updates the inventory for a product on Amazon.",
            parameter_definitions={
                "sku": {"type": "string", "description": "The SKU of the product to update.", "required": True},
                "quantity": {"type": "int", "description": "The new inventory quantity.", "required": True}
            }
        ),
        Tool(
            name="amazon_get_orders",
            description="Retrieves a list of recent orders from Amazon.",
            parameter_definitions={"created_after": {"type": "string", "description": "ISO 8601 date string for filtering."}}
        ),
        Tool(
            name="instagram_post_image",
            description="Posts a single image to an Instagram Business account.",
            parameter_definitions={
                "caption": {"type": "string", "description": "The main text content for the post.", "required": True},
                "image_path": {"type": "string", "description": "The local file path or a public URL of the image.", "required": True},
            }
        ),
        Tool(
            name="instagram_post_carousel",
            description="Posts a carousel of multiple images to Instagram.",
            parameter_definitions={
                "caption": {"type": "string", "description": "The caption for the carousel.", "required": True},
                "image_paths": {"type": "array", "description": "A list of local file paths for the images.", "items": {"type": "string"}, "required": True}
            }
        ),
        Tool(
            name="instagram_post_story",
            description="Posts an image as a story to Instagram.",
            parameter_definitions={
                "image_path": {"type": "string", "description": "The local file path of the image for the story.", "required": True},
                "link_url": {"type": "string", "description": "A URL to add as a link sticker to the story."}
            }
        ),
        Tool(
            name="website_generate_full_website",
            description="Generates a complete, multi-page website from a list of page definitions.",
            parameter_definitions={
                "site_title": {"type": "string", "description": "The title of the website and brand.", "required": True},
                "pages": {"type": "array", "description": "A list of dictionaries, each defining a page.", "required": True, "items": {"type": "object"}}
            }
        ),
        Tool(
            name="website_add_or_update_page",
            description="Adds or updates a page on the locally generated website.",
            parameter_definitions={
                "site_title": {"type": "string", "description": "The title of the website for context.", "required": True},
                "page_info": {"type": "object", "description": "A dictionary defining the page to add/update.", "required": True},
                "all_pages": {"type": "array", "description": "A list of all pages for updating navigation.", "required": True, "items": {"type": "object"}}
            }
        ),
        Tool(
            name="website_get_file_structure",
            description="Retrieves the file structure of the generated website.",
            parameter_definitions={}
        ),
        Tool(
            name="website_clear_directory",
            description="Permanently deletes all generated website files.",
            parameter_definitions={}
        ),
        Tool(
            name="website_open_in_browser",
            description="Opens a page from the generated website in a browser.",
            parameter_definitions={
                "page": {"type": "string", "description": "The name of the HTML file to open.", "required": False}
            }
        ),
        Tool(
            name="whatsapp_send_text_message",
            description="Sends a text message to a WhatsApp number.",
            parameter_definitions={
                "recipient_id": {"type": "string", "description": "The recipient's WhatsApp phone number.", "required": True},
                "message": {"type": "string", "description": "The text message to send.", "required": True}
            }
        ),
        Tool(
            name="whatsapp_send_image",
            description="Sends an image to a WhatsApp number.",
            parameter_definitions={
                "recipient_id": {"type": "string", "description": "The recipient's WhatsApp phone number.", "required": True},
                "file_path": {"type": "string", "description": "The local file path of the image.", "required": True},
                "caption": {"type": "string", "description": "A caption for the image."}
            }
        ),
        Tool(
            name="whatsapp_send_document",
            description="Sends a document to a WhatsApp number.",
            parameter_definitions={
                "recipient_id": {"type": "string", "description": "The recipient's WhatsApp phone number.", "required": True},
                "file_path": {"type": "string", "description": "The local path of the document.", "required": True}
            }
        )
    ]