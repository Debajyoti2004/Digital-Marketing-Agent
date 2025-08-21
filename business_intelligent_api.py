import os
import json
import traceback
from datetime import datetime, timedelta, UTC
import random

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from fpdf import FPDF

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

import config
from database_manager import DataManager

class ContentCalendarPost(BaseModel):
    day: int = Field(description="The day number in the calendar sequence.")
    platform: str = Field(description="The recommended social media platform.")
    post_type: str = Field(description="The format of the post.")
    content_idea: str = Field(description="A detailed idea for the post.")

class ContentCalendar(BaseModel):
    posts: list[ContentCalendarPost]
    
class FeedbackAnalysis(BaseModel):
    overall_sentiment: str = Field(description="Overall sentiment: Positive, Negative, or Mixed.")
    key_themes: list[str] = Field(description="A list of 3-5 key topics mentioned.")
    actionable_insights: list[str] = Field(description="A list of 2-3 specific business recommendations.")

class BusinessIntelligenceAPI:
    def __init__(self, model_name="gemini-1.5-flash-latest"):
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.7, google_api_key=getattr(config, "GOOGLE_API_KEY", None))
        self.default_font = "Arial"

    def _log_error(self, title, message, exception=None):
        rprint(Panel(f"[bold red]❌ {message}[/bold red]", title=title, border_style="red"))
        if exception:
            rprint(f"[red]Traceback:[/red]\n{traceback.format_exc()}")

    def generate_content_calendar(self, topic: str, duration_days: int = 7) -> dict:
        prompt = f"""
        🚀 **CREATIVE BRIEF: SOCIAL MEDIA CONTENT STRATEGY** 🚀
        **👤 ROLE & PERSONA:**
        Act as a world-class Chief Marketing Officer (CMO) and a viral content strategist.
        **🎯 PRIMARY OBJECTIVE:**
        Craft a dynamic, high-impact {duration_days}-day social media content calendar for the topic: "{topic}".
        """
        try:
            rprint(Panel(f"[cyan]📅 Creating {duration_days}-day calendar for '{topic}'...[/cyan]", title="Content Strategy"))
            structured_llm = self.llm.with_structured_output(ContentCalendar)
            response_model = structured_llm.invoke([HumanMessage(content=prompt)])
            calendar_dict = [post.model_dump() for post in response_model.posts]
            return {"status": "success", "calendar": calendar_dict}
        except Exception as e:
            self._log_error("Content Calendar Error", f"LLM failed to generate structured calendar: {e}", e)
            return {"error": str(e)}

    def predictive_sales_forecast(self, sales_csv_path: str, forecast_periods: int = 3, product_name: str = None):
        try:
            if not os.path.exists(sales_csv_path):
                raise FileNotFoundError(f"CSV not found at {sales_csv_path}")
            
            title = "Overall Sales Forecasting" if not product_name else f"Sales Forecasting for '{product_name}'"
            rprint(Panel(f"[cyan]📈 Reading sales data from '{sales_csv_path}'...[/cyan]", title=title))
            
            df = pd.read_csv(sales_csv_path, parse_dates=['date'])
            
            if product_name:
                df = df[df['product_name'].str.lower() == product_name.lower()]
                if df.empty:
                    raise ValueError(f"No sales data found for product: '{product_name}'")
                sales_column = 'daily_revenue'
            else:
                df = df.groupby('date').sum(numeric_only=True).reset_index()
                sales_column = 'daily_revenue'
            
            if len(df) < 10:
                raise ValueError(f"Not enough data points ({len(df)}) to generate a reliable forecast. At least 10 are needed.")

            df = df.set_index('date')
            df.index = pd.to_datetime(df.index)
            df = df.asfreq('D')
            df[sales_column] = df[sales_column].fillna(0)
            
            model = ARIMA(df[sales_column], order=(5, 1, 0))
            model_fit = model.fit()
            forecast = model_fit.forecast(steps=forecast_periods)
            forecast_data = {str(k.date()): v for k, v in forecast.round(2).to_dict().items()}
            recommendation = (f"Projected sales for the next period: {list(forecast_data.values())[0]}. Adjust inventory accordingly.")
            rprint(Panel(f"[bold green]✅ Forecast complete![/bold green]\n[bold]Forecast:[/bold] {forecast_data}\n[bold]💡 Tip:[/bold] {recommendation}", title=title))
            return {"status": "success", "forecast": forecast_data, "recommendation": recommendation}
        except Exception as e:
            self._log_error("Forecasting Error", f"Failed to generate forecast: {e}", e)
            return {"error": str(e)}

    def create_invoice(self, save_path: str, order_details: dict):
        try:
            required_keys = {"invoice_number", "customer_name", "items", "total"}
            if not required_keys.issubset(order_details): raise ValueError(f"Order details must include {required_keys}")
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font(self.default_font, 'B', 20); pdf.cell(0, 10, 'INVOICE', 0, 1, 'C')
            pdf.set_font(self.default_font, '', 12)
            pdf.cell(0, 10, f"Invoice #: {order_details['invoice_number']}", 0, 1)
            pdf.cell(0, 10, f"Date: {datetime.now(UTC).strftime('%Y-%m-%d')}", 0, 1)
            pdf.cell(0, 10, f"Bill to: {order_details['customer_name']}", 0, 1)
            pdf.ln(5)
            pdf.set_font(self.default_font, 'B', 12)
            pdf.cell(120, 10, 'Item', 1); pdf.cell(30, 10, 'Qty', 1); pdf.cell(40, 10, 'Price', 1, 1)
            pdf.set_font(self.default_font, '', 12)
            for item in order_details['items']:
                pdf.cell(120, 10, item['name'], 1); pdf.cell(30, 10, str(item['quantity']), 1); pdf.cell(40, 10, f"${item['price']:.2f}", 1, 1)
            pdf.set_font(self.default_font, 'B', 12)
            pdf.cell(0, 10, f"Total: ${order_details['total']:.2f}", 0, 1, 'R')
            pdf.output(save_path)
            return {"status": "success", "file_path": save_path}
        except Exception as e:
            self._log_error("Invoice Error", f"Failed to create invoice: {e}", e)
            return {"error": str(e)}

    def generate_shipping_label(self, save_path: str, shipping_details: dict):
        try:
            required_keys = {"from_address", "to_address", "order_id"}
            if not required_keys.issubset(shipping_details): raise ValueError(f"Shipping details must include {required_keys}")
            pdf = FPDF(orientation='L', unit='mm', format=(100, 150))
            pdf.add_page()
            pdf.set_font(self.default_font, 'B', 16); pdf.cell(0, 10, f"ORDER #{shipping_details['order_id']}", border=1, ln=1, align='C')
            pdf.ln(5)
            pdf.set_font(self.default_font, '', 10); pdf.cell(20, 10, "FROM:")
            pdf.set_font(self.default_font, '', 12); pdf.multi_cell(0, 5, shipping_details['from_address'])
            pdf.ln(10)
            pdf.set_font(self.default_font, '', 10); pdf.cell(20, 10, "TO:")
            pdf.set_font(self.default_font, 'B', 16); pdf.multi_cell(0, 7, shipping_details['to_address'])
            pdf.output(save_path)
            return {"status": "success", "file_path": save_path}
        except Exception as e:
            self._log_error("Shipping Label Error", f"Failed to create shipping label: {e}", e)
            return {"error": str(e)}

    def generate_shipping_manifest(self, save_path: str, orders: list):
        try:
            if not orders: raise ValueError("Orders list cannot be empty.")
            doc = SimpleDocTemplate(save_path, pagesize=landscape(letter))
            styles, story = getSampleStyleSheet(), [Paragraph("Shipping Manifest", getSampleStyleSheet()['h1']), Spacer(1, 12)]
            table_data = [["FROM", "TO", "Order ID"]]
            for order in orders:
                details = order.get("shipping_details", {})
                if not {"from_address", "to_address", "order_id"}.issubset(details): continue
                table_data.append([Paragraph(details['from_address'].replace('\n', '<br/>'), styles['BodyText']), Paragraph(details['to_address'].replace('\n', '<br/>'), styles['BodyText']), Paragraph(str(details['order_id']), styles['BodyText'])])
            table = LongTable(table_data, colWidths=[250, 250, 100])
            table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.grey), ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0,0), (-1,0), 12),('BACKGROUND', (0,1), (-1,-1), colors.beige), ('GRID', (0,0), (-1,-1), 1, colors.black)]))
            story.append(table)
            doc.build(story)
            return {"status": "success", "file_path": save_path}
        except Exception as e:
            self._log_error("Manifest Error", f"Failed to create manifest: {e}", e)
            return {"error": str(e)}

    def analyze_customer_feedback(self, feedback_list: list):
        prompt = f"""
        **🧠 CREATIVE BRIEF: CUSTOMER FEEDBACK ANALYSIS** 🧠
        **👤 ROLE & PERSONA:**
        Act as a Senior Data Analyst specializing in qualitative customer intelligence.
        **🎯 PRIMARY OBJECTIVE:**
        Analyze the provided list of customer comments and produce a structured JSON summary.
        **📝 RAW DATA: CUSTOMER COMMENTS**
        ```json
        {json.dumps(feedback_list)}
        ```
        **📋 MANDATORY EXECUTION DIRECTIVES:**
        1.  **Sentiment Analysis:** Determine the `overall_sentiment`.
        2.  **Thematic Grouping:** Identify 3-5 `key_themes`.
        3.  **Actionable Insights:** Extract 2-3 `actionable_insights`.
        """
        try:
            rprint(Panel(f"[cyan]🧠 Analyzing {len(feedback_list)} pieces of feedback...[/cyan]", title="Feedback Analysis"))
            structured_llm = self.llm.with_structured_output(FeedbackAnalysis)
            response_model = structured_llm.invoke([HumanMessage(content=prompt)])
            return {"status": "success", "analysis": response_model.model_dump()}
        except Exception as e:
            self._log_error("Feedback Analysis Error", f"LLM failed to analyze feedback: {e}", e)
            return {"error": str(e)}

if __name__ == "__main__":
    db_file = "bi_test_shop.db"
    if os.path.exists(db_file): os.remove(db_file)
    output_dir = "output_files"
    if not os.path.exists(output_dir): os.makedirs(output_dir, exist_ok=True)

    console = Console()
    console.print(Panel("🚀 [bold green]Starting Business Intelligence API Full Test Suite[/bold green]", expand=False))
    
    bi_tool = BusinessIntelligenceAPI()
    
    with DataManager(db_file) as db:
        console.rule("\n[bold]Setup: Populating Database with Realistic Sales Data[/bold]")
        p1 = db.add_product("Leather Wallet", "Hand-stitched", 49.99, 100)
        c1 = db.add_customer("Alex Wilton", "alex@example.com")
        
        for i in range(90):
            day = datetime.now(UTC) - timedelta(days=i)
            quantity = 5 + (day.weekday() // 4) * 3 + random.randint(-2, 2) 
            if quantity > 0:
                db.create_order_and_shipment(c1, [{"product_id": p1, "quantity": quantity, "price_per_item": 49.99}], "Addr 1", order_date=day)
                db.update_daily_sales(for_date=day)
        
        console.print("✅ Database populated with 90 days of sales history.")
        
        console.rule("\n[bold]Step 1: Content Calendar Generation[/bold]")
        bi_tool.generate_content_calendar(topic="new line of handcrafted pottery", duration_days=3)

        console.rule("\n[bold]Step 2: Sales Forecasting[/bold]")
        sales_csv_file = os.path.join(output_dir, "sales_data_from_db.csv")
        db.export_sales_to_csv(sales_csv_file)
        bi_tool.predictive_sales_forecast(sales_csv_path=sales_csv_file)
        bi_tool.predictive_sales_forecast(sales_csv_path=sales_csv_file, product_name="Leather Wallet")

        console.rule("\n[bold]Step 3: Document Generation[/bold]")
        invoice_path = os.path.join(output_dir, "invoice_DEMO-001.pdf")
        invoice_details = {"invoice_number": "DEMO-001", "customer_name": "Alex Wilton", "items": [{"name": "Leather Wallet", "quantity": 1, "price": 49.99}], "total": 49.99}
        bi_tool.create_invoice(save_path=invoice_path, order_details=invoice_details)
        console.print(f"✅ Invoice created at: {invoice_path}")
        
        label_path = os.path.join(output_dir, "shipping_label_DEMO-001.pdf")
        shipping_details = {"from_address": "My Shop\n123 Artisan Way", "to_address": "Alex Wilton\n456 Tech Avenue\nLondon", "order_id": "DEMO-001"}
        bi_tool.generate_shipping_label(save_path=label_path, shipping_details=shipping_details)
        console.print(f"✅ Shipping Label created at: {label_path}")

        console.rule("\n[bold]Step 4: Customer Feedback Analysis[/bold]")
        feedback = ["The leather wallet was amazing!", "Shipping was a bit slow, but the product quality is top-notch.", "I wish there were more color options for the mugs."]
        analysis_result = bi_tool.analyze_customer_feedback(feedback)
        if analysis_result.get("status") == "success":
            console.print(Panel(json.dumps(analysis_result.get("analysis"), indent=2), title="Feedback Analysis Results"))

    console.print(Panel("🏁 [bold green]Test Suite Finished[/bold green] 🏁", title="Final Summary"))