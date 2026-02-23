import re
from decimal import Decimal, InvalidOperation
from bs4 import BeautifulSoup
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class ContentComparer:
    def __init__(self, template_path: str = "Almacenamiento/plantilla.html"):
        self.template_path = template_path
        self._template_content = self._load_template()

    def _load_template(self) -> str:
        """Carga el HTML de la plantilla de referencia."""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"La plantilla {self.template_path} no fue encontrada.")
            return ""
        except Exception as e:
            logger.error(f"Error cargando la plantilla: {e}")
            return ""

    def snapshot_scraping(self, html_obtenido: str) -> List[Dict]:
        """
        Extrae todos los pares de divisas presentes en el HTML (ej. de Google Finance).
        Retorna una lista de diccionarios con la estructura:
        [
            {
                "codigo": "EUR",
                "valor_comparacion": "USD",
                "valor_actual": Decimal("1.1826")
            }, ...
        ]
        """
        if not html_obtenido:
            logger.warning("HTML obtenido está vacío.")
            return []

        soup = BeautifulSoup(html_obtenido, 'html.parser')
        lis = soup.find_all('li')
        divisas = []

        for li in lis:
            textos = [t for t in li.stripped_strings]
            
            # Buscamos elementos que tengan al menos 4 textos y contengan un par de divisas (ej. 'EUR / USD')
            if len(textos) >= 4 and '/' in textos[1]:
                par = textos[1].split('/')
                if len(par) == 2:
                    codigo = par[0].strip()
                    comparacion = par[1].strip()
                    
                    valor_str = textos[2]
                    
                    valor_decimal = self._parse_decimal(valor_str)
                    
                    if valor_decimal > Decimal('0'):
                        divisas.append({
                            "codigo": codigo,
                            "valor_comparacion": comparacion,
                            "valor_actual": valor_decimal
                        })

        logger.info(f"Se extrajeron {len(divisas)} pares de divisas exitosamente.")
        return divisas

    def _parse_decimal(self, numero_str: str) -> Decimal:
        """Normaliza y convierte una cadena a Decimal de forma segura."""
        # Limpiar caracteres indeseados que no sean dígitos, puntos o comas
        cleaned_str = re.sub(r'[^\d.,]', '', numero_str)
        
        if not cleaned_str:
            return Decimal('0')

        if ',' in cleaned_str and '.' not in cleaned_str:
             cleaned_str = cleaned_str.replace(',', '.')
        elif ',' in cleaned_str and '.' in cleaned_str:
             # Formato US (1,234.56) vs Formato EU (1.234,56)
             if cleaned_str.rfind(',') < cleaned_str.rfind('.'):
                 cleaned_str = cleaned_str.replace(',', '')
             else:
                 cleaned_str = cleaned_str.replace('.', '').replace(',', '.')

        try:
            return Decimal(cleaned_str)
        except InvalidOperation:
            logger.error(f"No se pudo convertir '{cleaned_str}' (original: '{numero_str}') a Decimal.")
            return Decimal('0')

    def calculate_relative_value(self, valor_actual: Decimal, factor: Decimal = Decimal('1')) -> Decimal:
        """Aplica un factor de corrección si es necesario preservando alta precisión."""
        return valor_actual * factor
