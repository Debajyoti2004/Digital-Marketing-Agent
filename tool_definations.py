from cohere.types import Tool
import os

def get_tool_definitions():
    return [
        Tool(
            name="market_search_for_products",
            description="Performs a web search to find competitor product links, articles, and market trends. This is the first step for market research.",
            parameter_definitions={"query": {"type": "string", "description": "The search query for finding competitor products, e.g., 'best handmade leather wallets'.", "required": True}}
        ),
        Tool(
            name="market_extract_product_details",
            description="Extracts detailed information (price, features, specs) from a specific competitor's product page URL.",
            parameter_definitions={"url": {"type": "string", "description": "The full URL of the competitor's product page to analyze.", "required": True}}
        ),
        Tool(
            name="market_analyze_competitors",
            description="Analyzes a collection of scraped competitor data to generate a strategic summary, including recommended pricing and keywords.",
            parameter_definitions={"competitor_data": {"type": "list[object]", "description": "A list where each object contains the extracted data for one competitor product.", "required": True}}
        ),
        Tool(
            name="design_create_poster",
            description="Generates a new promotional poster from scratch using an LLM to create an artistic prompt and another LLM to generate the image. Saves the poster to a local file.",
            parameter_definitions={
                "product_name": {"type": "string", "description": "The name of the product for the poster.", "required": True},
                "description": {"type": "string", "description": "A short, compelling marketing description of the product.", "required": True},
                "call_to_action": {"type": "string", "description": "The call to action text, e.g., 'Shop Now'.", "required": True},
                "save_path": {"type": "string", "description": "The local filename for the new poster, e.g., 'poster_v1.png'.", "required": True},
                "target_audience": {"type": "string", "description": "Optional: Describe the target audience to influence the visual style."},
                "brand_colors": {"type": "list[string]", "description": "Optional: A list of brand colors as hex codes."}
            }
        ),
        Tool(
            name="design_update_poster",
            description="Updates a poster based on specific user feedback. Uses an LLM to translate feedback into a new visual direction for the image generation AI.",
            parameter_definitions={
                "product_name": {"type": "string", "description": "The name of the product to maintain context.", "required": True},
                "prompt_used": {"type": "string", "description": "The original creative prompt used to generate the previous poster.", "required": True},
                "user_feedback": {"type": "string", "description": "Specific user recommendations for the update.", "required": True},
                "new_save_path": {"type": "string", "description": "The new file path for the updated poster, e.g., 'poster_v2.png'.", "required": True}
            }
        ),
        Tool(
            name="display_show_local_image",
            description="Displays a locally saved image file on the screen for the user to review.",
            parameter_definitions={"file_path": {"type": "string", "description": "The exact local path to the image file to be shown.", "required": True}}
        ),
        Tool(
            name="system_get_current_directory",
            description="Returns the current working directory of the system.",
            parameter_definitions={}
        ),
        Tool(
            name="facebook_post_text",
            description="Posts a simple text message to a configured Facebook Page.",
            parameter_definitions={"content": {"type": "string", "description": "The main text content of the post.", "required": True}}
        ),
        Tool(
            name="facebook_post_image",
            description="Posts an image to a Facebook Page with a caption.",
            parameter_definitions={
                "content": {"type": "string", "description": "The caption for the image.", "required": True},
                "image_path": {"type": "string", "description": "Local file path of the image to upload."}
            }
        ),
        Tool(
            name="facebook_post_video",
            description="Posts a video to a Facebook Page with a description.",
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
            description="Retrieves the most recent posts from the configured Facebook Page.",
            parameter_definitions={"limit": {"type": "int", "description": "The number of posts to retrieve."}}
        ),
        Tool(
            name="amazon_create_or_update_listing",
            description="Creates or updates a product listing on Amazon.",
            parameter_definitions={
                "sku": {"type": "string", "description": "The unique Stock Keeping Unit.", "required": True},
                "product_title": {"type": "string", "description": "The official title for the listing.", "required": True},
                "description": {"type": "string", "description": "The detailed product description.", "required": True},
                "bullet_points": {"type": "list[string]", "description": "A list of 5 key feature bullet points.", "required": True},
                "price": {"type": "float", "description": "The selling price.", "required": True},
                "keywords": {"type": "list[string]", "description": "A list of relevant backend search terms.", "required": True}
            }
        ),
        Tool(
            name="amazon_get_listing",
            description="Retrieves details for a specific product listing from Amazon by its SKU.",
            parameter_definitions={"sku": {"type": "string", "description": "The SKU of the listing to retrieve.", "required": True}}
        ),
        Tool(
            name="amazon_update_price",
            description="Updates the price for a specific product on Amazon.",
            parameter_definitions={
                "sku": {"type": "string", "description": "The SKU of the product to update.", "required": True},
                "price": {"type": "float", "description": "The new price for the product.", "required": True}
            }
        ),
        Tool(
            name="amazon_update_inventory",
            description="Updates the inventory quantity for a specific product on Amazon.",
            parameter_definitions={
                "sku": {"type": "string", "description": "The SKU of the product to update.", "required": True},
                "quantity": {"type": "int", "description": "The new inventory quantity.", "required": True}
            }
        ),
        Tool(
            name="amazon_get_orders",
            description="Retrieves a list of recent orders from Amazon.",
            parameter_definitions={"created_after": {"type": "string", "description": "ISO 8601 date string to get orders created after this time."}}
        ),
        Tool(
            name="instagram_post_image",
            description="Posts a single image to an Instagram Business account.",
            parameter_definitions={
                "caption": {"type": "string", "description": "The main text content for the post.", "required": True},
                "image_path": {"type": "string", "description": "The local file path or a public URL of the image.", "required": True},
                "hashtags": {"type": "list[string]", "description": "A list of hashtags without the '#' symbol."},
                "user_tags": {"type": "list[string]", "description": "A list of usernames to tag without the '@' symbol."}
            }
        ),
        Tool(
            name="instagram_post_carousel",
            description="Posts a carousel of multiple images to Instagram.",
            parameter_definitions={
                "caption": {"type": "string", "description": "The caption for the carousel.", "required": True},
                "image_paths": {"type": "list[string]", "description": "A list of local file paths for the images.", "required": True}
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
            description="Generates a complete, multi-page static website from scratch and saves it locally.",
            parameter_definitions={
                "site_title": {"type": "string", "description": "The title of the website and brand.", "required": True},
                "about_text": {"type": "string", "description": "A paragraph describing the brand or person."},
                "products": {"type": "list[object]", "description": "A list of product objects, each with 'name', 'description', 'price'."},
                "contact_info": {"type": "object", "description": "An object with contact details like 'email', 'phone', 'address'."}
            }
        ),
        Tool(
            name="website_add_or_update_page",
            description="Adds a new page or updates an existing one on the locally generated website.",
            parameter_definitions={
                "page_name": {"type": "string", "description": "The name of the page (e.g., 'blog'), which becomes the filename.", "required": True},
                "html_fragment": {"type": "string", "description": "The HTML content for the main area of the page.", "required": True},
                "site_description": {"type": "string", "description": "A brief description of the entire site for context.", "required": True}
            }
        ),
        Tool(
            name="website_get_file_structure",
            description="Retrieves the file and directory structure of the generated website.",
            parameter_definitions={}
        ),
        Tool(
            name="website_clear_directory",
            description="Permanently deletes all generated website files and clears the project directory.",
            parameter_definitions={}
        ),
        Tool(
            name="whatsapp_send_text_message",
            description="Sends a text message to a WhatsApp number.",
            parameter_definitions={
                "recipient_id": {"type": "string", "description": "The recipient's WhatsApp phone number with country code.", "required": True},
                "message": {"type": "string", "description": "The text message to send.", "required": True}
            }
        ),
        Tool(
            name="whatsapp_send_image",
            description="Uploads and sends an image to a WhatsApp number.",
            parameter_definitions={
                "recipient_id": {"type": "string", "description": "The recipient's WhatsApp phone number with country code.", "required": True},
                "file_path": {"type": "string", "description": "The local file path of the image to send.", "required": True},
                "caption": {"type": "string", "description": "A caption to send with the image."}
            }
        ),
        Tool(
            name="whatsapp_send_document",
            description="Sends a document (e.g., PDF) to a WhatsApp number.",
            parameter_definitions={
                "recipient_id": {"type": "string", "description": "The recipient's WhatsApp phone number.", "required": True},
                "file_path": {"type": "string", "description": "The local path of the document.", "required": True}
            }
        )
    ]

def system_get_current_directory():
    return {"current_directory": os.getcwd()}