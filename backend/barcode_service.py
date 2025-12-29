"""
Barcode scanning and product identification service using Google Gemini AI.
Identifies products from images and suggests category, name, and unit.
"""
import os
import base64
from typing import Optional
from io import BytesIO

try:
    import google.generativeai as genai
    from PIL import Image
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .schemas import BarcodeIdentifyResponse


class BarcodeService:
    """
    Service for identifying products from barcode images using Gemini AI.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed")
        
        genai.configure(api_key=self.api_key)
        # Use gemini-2.5-flash for multimodal (image) support
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def identify_product(self, image_base64: str) -> BarcodeIdentifyResponse:
        """
        Identify a product from its image using Gemini AI.
        
        Args:
            image_base64: Base64 encoded image data
        
        Returns:
            BarcodeIdentifyResponse with product details
        """
        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)
            image = Image.open(BytesIO(image_data))
            
            # Prepare prompt for Gemini
            prompt = """Analise esta imagem de um produto e extraia as seguintes informações:

1. Nome do produto (product_name): O nome comercial do produto
2. Categoria sugerida (suggested_category): Uma das seguintes categorias: Alimentos, Limpeza, Higiene, Medicamentos, Pet
3. Unidade sugerida (suggested_unit): Uma das seguintes unidades: un, kg, g, L, ml, pacotes
4. Código de barras (barcode): Se visível na imagem, o número do código de barras

Responda APENAS em formato JSON válido, sem markdown, assim:
{
    "product_name": "Nome do Produto",
    "suggested_category": "Categoria",
    "suggested_unit": "unidade",
    "barcode": "código ou null"
}

Se não conseguir identificar o produto, responda:
{
    "product_name": null,
    "suggested_category": null,
    "suggested_unit": null,
    "barcode": null
}"""
            
            # Call Gemini API
            response = self.model.generate_content([prompt, image])
            
            # Parse response
            response_text = response.text.strip()
            
            # Try to extract JSON from response
            import json
            try:
                # Remove markdown code blocks if present
                if response_text.startswith("```"):
                    lines = response_text.split("\n")
                    json_lines = [l for l in lines if not l.startswith("```")]
                    response_text = "\n".join(json_lines)
                
                data = json.loads(response_text)
                
                if data.get("product_name"):
                    return BarcodeIdentifyResponse(
                        success=True,
                        product_name=data.get("product_name"),
                        suggested_category=data.get("suggested_category"),
                        suggested_unit=data.get("suggested_unit"),
                        barcode=data.get("barcode")
                    )
                else:
                    return BarcodeIdentifyResponse(
                        success=False,
                        error="Não foi possível identificar o produto na imagem"
                    )
            
            except json.JSONDecodeError:
                return BarcodeIdentifyResponse(
                    success=False,
                    error=f"Erro ao processar resposta: {response_text[:100]}"
                )
        
        except Exception as e:
            return BarcodeIdentifyResponse(
                success=False,
                error=f"Erro ao identificar produto: {str(e)}"
            )
    
    def decode_barcode(self, image_base64: str) -> Optional[str]:
        """
        Attempt to decode barcode from image using pyzbar.
        Fallback method if Gemini doesn't extract barcode.
        
        Args:
            image_base64: Base64 encoded image data
        
        Returns:
            Barcode string if found, None otherwise
        """
        try:
            from pyzbar.pyzbar import decode as pyzbar_decode
            
            image_data = base64.b64decode(image_base64)
            image = Image.open(BytesIO(image_data))
            
            barcodes = pyzbar_decode(image)
            if barcodes:
                return barcodes[0].data.decode('utf-8')
            return None
        
        except ImportError:
            # pyzbar not installed, rely on Gemini
            return None
        except Exception:
            return None


# Utility function to create service if available
def get_barcode_service() -> Optional[BarcodeService]:
    """
    Get barcode service instance if properly configured.
    
    Returns:
        BarcodeService instance or None if not configured
    """
    try:
        return BarcodeService()
    except (ValueError, ImportError):
        return None
