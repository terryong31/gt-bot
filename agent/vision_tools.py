"""
Vision Tools - Image processing capabilities using Gemini Vision.
Extracts structured data from images (receipts, documents, etc.).
"""
from typing import List, Any
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

def get_vision_tools() -> List[Any]:
    """Get vision-related tools."""
    
    @tool
    def analyze_receipt(image_id: str) -> str:
        """
        Analyze a receipt image to extract date, merchant, total, and category.
        The image_id is usually provided in the conversation context.
        """
        try:
            # In a real implementation, we would fetch the image content from Telegram
            # For this demo, we'll assume the LLM has already "seen" the image in the chat history
            # or we simulate extraction.
            
            # Since the main LLM (Gemini 2.5 Flash Lite) is multimodal, it can see the image directly.
            # This tool is a helper to format that data specifically for the expense sheet.
            
            return """
            To process this receipt:
            1. Just look at the image I sent you.
            2. Extract: Date, Merchant Name, Total Amount, and Category (Food, Transport, etc.).
            3. Then call the 'add_expense_row' tool with these values.
            """
            
        except Exception as e:
            return f"Error analyzing receipt: {str(e)}"

    return [analyze_receipt]
