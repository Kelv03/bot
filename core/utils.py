from urllib.parse import urlparse
import logging

# Configuração de Log que recrutador adora ver
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler("sniper.log"), logging.StreamHandler()]
)

def normalizar_url(url):
    """Remove lixo de marketing das URLs para evitar duplicatas."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return f"https://{parsed.netloc}{path}".lower().strip()

def limpar_texto(texto):
    if not texto: return ""
    return " ".join(texto.split())