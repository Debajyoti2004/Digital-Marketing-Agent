from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from typing import Literal
import os

class IntentResponse(BaseModel):
    intent: Literal["tool_use", "general_conversation"]

class IntentClassifier:
    def __init__(self, model_name="gemini-1.5-pro"):
        self.model = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=os.getenv("GENAI_API_KEY"),
            temperature=0
        )
        self.structured_model = self.model.with_structured_output(IntentResponse)

    def classify_intent(self, user_message):
        prompt = f"""
        🤖 You are an **Expert Intent Classifier** for an AI system that can either:
        - 🛠️ Use specialized tools  
        - 💬 Engage in general conversation  

        ===============================
        🛠️ AVAILABLE TOOLS (with short definitions):
        - monitor_check_for_new_comments → Scan social media accounts for new comments.
        - bizintel_generate_content_calendar → Create multi-day social media content plans.
        - bizintel_predictive_sales_forecast → Forecast future sales from CSV data.
        - design_enhance_product_photo → Remove backgrounds and enhance product photos.
        - design_create_promo_video → Create promotional videos with text + images.
        - bizintel_create_invoice → Generate PDF invoices for customer orders.
        - bizintel_generate_shipping_label → Generate formatted PDF shipping labels.
        - market_search_for_products → Web search for competitor products & trends.
        - market_extract_product_details → Extract price, features, specs from a product page.
        - market_analyze_competitors → Summarize competitor data for strategy.
        - design_create_poster → Generate new promotional posters.
        - design_update_poster → Update posters based on user feedback.
        - display_show_local_image → Display saved local images to the user.
        - system_get_current_directory → Get the system’s current working directory.
        - facebook_post_text → Post simple text on Facebook pages.
        - facebook_post_image → Post image + caption on Facebook.
        - facebook_post_video → Post video + description on Facebook.
        - facebook_create_event → Create new events on Facebook pages.
        - facebook_get_page_feed → Get recent posts from a Facebook page.
        - amazon_create_or_update_listing → Create/update Amazon product listings.
        - amazon_get_listing → Retrieve details of an Amazon listing.
        - amazon_update_price → Update Amazon product price.
        - amazon_update_inventory → Update Amazon product inventory.
        - amazon_get_orders → Retrieve Amazon orders.
        - instagram_post_image → Post an image with caption + hashtags on Instagram.
        - instagram_post_carousel → Post multiple images as a carousel on Instagram.
        - instagram_post_story → Post an Instagram story with image + link.
        - website_generate_full_website → Generate full multi-page static websites.
        - website_add_or_update_page → Add/update a website page with HTML content.
        - website_get_file_structure → Retrieve website file/directory structure.
        - website_clear_directory → Delete all generated website files.
        - whatsapp_send_text_message → Send text messages over WhatsApp.
        - whatsapp_send_image → Send images + captions over WhatsApp.
        - whatsapp_send_document → Send documents over WhatsApp.

        ===============================
        ⚡ CLASSIFICATION RULES:
        - If the message clearly requires a tool (above list), classify as **tool_use**.  
        - If the message is casual talk, greetings, opinions, or chit-chat → **general_conversation**.  
        - If user mixes both → choose **tool_use**.  
        - If ambiguous → lean towards **tool_use**.  
        - Ignore irrelevant filler (emojis, random text).  

        ===============================
        🎯 OUTPUT FORMAT:
        Respond with only one of:
        - tool_use
        - general_conversation  

        ===============================
        👤 USER MESSAGE:
        "{user_message}"
        """

        return self.structured_model.invoke(prompt)
