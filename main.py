import os
import re
import time
import json
import random
import sqlite3
import logging
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
import google.generativeai as genai

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler("sniper.log"), logging.StreamHandler()]
)

# Carregar variáveis de ambiente
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

TERMOS_INTERESSE = ["python", "bot", "automação", "scraping", "dados", "planilha", "api", "n8n", "ia"]
REGEX_STACK = re.compile(r'\b(' + '|'.join(map(re.escape, TERMOS_INTERESSE)) + r')\b', re.IGNORECASE)

# ==========================================
# BANCO DE DADOS SÊNIOR (SQLite WAL)
# ==========================================
class DatabaseManager:
    def __init__(self, db_path="estudio_kelv.db"):
        self.conn = sqlite3.connect(db_path, timeout=30)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute('''CREATE TABLE IF NOT EXISTS projetos (
            url TEXT PRIMARY KEY, titulo TEXT, score INTEGER, status TEXT, data INTEGER)''')
        self.conn.commit()

    def projeto_visto(self, url):
        return bool(self.conn.execute('SELECT 1 FROM projetos WHERE url = ?', (url,)).fetchone())

    def salvar_projeto(self, url, titulo, score):
        self.conn.execute('INSERT INTO projetos VALUES (?, ?, ?, ?, ?)', 
                         (url, titulo, score, 'aberto', int(time.time())))
        self.conn.commit()

db = DatabaseManager()

# ==========================================
# O CÉREBRO (Score + Gemini JSON)
# ==========================================
def calcular_score(dados):
    score = 50.0
    desc = dados['descricao'].lower()
    
    # Sinais Positivos
    if REGEX_STACK.search(desc): score += 20
    if any(x in desc for x in ["api", "github", "json", "webhook"]): score += 15
    if "urgente" in desc: score += 10
    
    # Penalidade / Bónus por concorrência
    p = dados.get('propostas_int', 0)
    if p > 30: score *= 0.4
    elif p <= 5: score *= 1.3
    
    return min(max(int(score), 0), 100)

def pensar_como_kelv(titulo, descricao):
    """A IA avalia a vaga e cria a proposta, garantindo o formato JSON."""
    logging.info("🧠 Cérebro processando estratégia...")
    prompt = f"""
    Você é especialista em automação e Python. Avalie esta vaga:
    Título: {titulo} | Descrição: {descricao[:800]}
    
    Responda APENAS em JSON com esta estrutura exata:
    {{
      "probabilidade": "Alta, Média ou Baixa",
      "estrategia": "Breve frase sobre como fechar o projeto",
      "preco_sugerido": "Valor sugerido em R$",
      "proposta_kelv": "Proposta técnica de 3 parágrafos focada na dor do cliente"
    }}
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        # Força a resposta a ser um JSON válido
        res = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(res.text)
    except Exception as e:
        logging.error(f"Erro na IA: {e}")
        return {
            "probabilidade": "Desconhecida", 
            "estrategia": "Avaliação manual necessária", 
            "preco_sugerido": "A definir", 
            "proposta_kelv": "Olá! Tenho interesse no projeto e posso ajudar utilizando Python."
        }

# ==========================================
# TELEGRAM VIP NOTIFIER
# ==========================================
def enviar_alerta(titulo, link, score, analise_ia):
    preco = analise_ia.get('preco_sugerido', 'A definir')
    proposta_pronta = analise_ia.get('proposta_kelv', 'Proposta não gerada.')
    probabilidade = analise_ia.get('probabilidade', 'Pendente')
    estrategia = analise_ia.get('estrategia', 'Pendente')

    msg = (
        f"🎯 *VAGA DETETADA* (Score: {score})\n"
        f"🔥 *{titulo}*\n\n"
        f"📊 *Probabilidade:* {probabilidade}\n"
        f"💡 *Estratégia:* {estrategia}\n"
        f"💰 *Cobrar:* {preco}\n\n"
        f"📋 *PROPOSTA GERADA:*\n"
        f"```text\n{proposta_pronta}\n```\n\n"
        f"🔗 [Acessar Projeto]({link})"
    )
    
    url_api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url_api, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        if r.status_code != 200: # Fallback sem formatação se falhar
            requests.post(url_api, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except Exception as e:
        logging.error(f"Erro Telegram: {e}")

# ==========================================
# AS AÇÕES DO ROBÔ NO NAVEGADOR
# ==========================================
def verificar_mensagens_novas(pagina):
    try:
        pagina.goto("https://www.99freelas.com.br/messages", timeout=40000)
        time.sleep(3)
        if pagina.locator(".unread, .new-message-badge").count() > 0:
            msg = "🚨 *CLIENTE RESPONDEU!* Verifique o 99Freelas!"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except Exception as e:
        logging.debug(f"Aviso ao checar mensagens: {e}")

def rodar_sniper(pagina):
    try:
        pagina.goto("https://www.99freelas.com.br/projects", timeout=60000)
        pagina.wait_for_selector("li.result-item", timeout=10000)
        vagas = pagina.locator("li.result-item")
        
        for i in range(min(vagas.count(), 5)):
            vaga = vagas.nth(i)
            titulo = vaga.locator(".title").inner_text()
            link = "https://www.99freelas.com.br" + vaga.locator(".title a").get_attribute("href")
            
            # Limpar URL para evitar duplicações
            parsed = urlparse(link)
            link_limpo = f"https://{parsed.netloc}{parsed.path.rstrip('/')}".lower().strip()
            
            if not db.projeto_visto(link_limpo) and any(t in titulo.lower() for t in TERMOS_INTERESSE):
                logging.info(f"Analisando: {titulo}")
                pagina.goto(link_limpo, timeout=40000)
                time.sleep(2)
                
                desc = pagina.locator(".description-text").inner_text() if pagina.locator(".description-text").count() > 0 else ""
                texto_body = pagina.inner_text("body")
                
                m = re.search(r'[Pp]ropostas[\s:]*(\d+)|(\d+)\s*[Pp]ropostas', texto_body)
                p_int = int(m.group(1) or m.group(2)) if m else 0
                
                score = calcular_score({"descricao": desc, "propostas_int": p_int})
                
                if score >= 50:
                    analise_ia = pensar_como_kelv(titulo, desc)
                    enviar_alerta(titulo, link_limpo, score, analise_ia)
                
                db.salvar_projeto(link_limpo, titulo, score)
                
                # Voltar para a lista
                pagina.goto("https://www.99freelas.com.br/projects")
                pagina.wait_for_selector("li.result-item", timeout=10000)
                
    except Exception as e:
        logging.error(f"Erro na caçada: {e}")

def iniciar_estudio_kelv():
    eh_windows = os.name == 'nt'
    user_path = r"C:\Users\breno\AppData\Local\Google\Chrome\User Data" if eh_windows else "./perfil_nuvem"
    modo_fantasma = not eh_windows

    print("\n" + "="*50)
    print("🚀 ESTÚDIO KELV - SISTEMA AUTÔNOMO V10.PRO")
    print(f"🌍 Ambiente: {'Windows (Local)' if eh_windows else 'Linux (Nuvem)'}")
    print("="*50 + "\n")

    with sync_playwright() as p:
        try:
            # Requer que o Chrome/Edge não esteja aberto localmente na mesma diretoria
            contexto = p.chromium.launch_persistent_context(
                user_data_dir=user_path,
                channel="chrome" if eh_windows else None, # Usa chromium padrão no Linux
                headless=modo_fantasma,
                args=["--disable-blink-features=AutomationControlled"]
            )
            pagina = contexto.pages[0] if contexto.pages else contexto.new_page()
            
            if modo_fantasma:
                logging.info("⚠️ Lembre-se: No modo headless pode ser necessário fazer o login na plataforma manualmente primeiro.")

            while True:
                logging.info("📩 A verificar mensagens...")
                verificar_mensagens_novas(pagina)
                
                logging.info("🔎 A analisar o mercado...")
                rodar_sniper(pagina)
                
                delay = random.randint(120, 300)
                logging.info(f"😴 Pausa de {delay//60} minutos...")
                time.sleep(delay)
                
        except Exception as e:
            logging.error(f"❌ Falha crítica: {e}")
            if eh_windows: print("💡 DICA: Feche o seu navegador Chrome normal antes de executar a automação!")

if __name__ == "__main__":
    iniciar_estudio_kelv()