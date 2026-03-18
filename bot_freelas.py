import os
import re
import time
import json
import sqlite3
import logging
import requests
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# ==========================================
# 1. SETUP DE IA E TELEGRAM
# ==========================================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TERMOS_INTERESSE = ["python", "bot", "automação", "scraping", "dados", "planilha", "api", "n8n", "ia"]
REGEX_STACK = re.compile(r'\b(' + '|'.join(map(re.escape, TERMOS_INTERESSE)) + r')\b', re.IGNORECASE)

# ==========================================
# 2. BANCO DE DADOS SÊNIOR (SQLite WAL)
# ==========================================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("estudio_kelv.db", timeout=30)
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

db = Database()

# ==========================================
# 3. O CÉREBRO (Score + Gemini JSON)
# ==========================================
def calcular_score(dados):
    score = 50.0
    desc = dados['descricao'].lower()
    
    if REGEX_STACK.search(desc): score += 20
    if any(x in desc for x in ["api", "github", "json", "webhook"]): score += 15
    if "urgente" in desc: score += 10
    
    p = dados.get('propostas_int', 0)
    if p > 30: score *= 0.4
    elif p <= 5: score *= 1.3
    
    return min(max(int(score), 0), 100)

def pensar_como_kelv(titulo, descricao):
    """A IA avalia a vaga, calcula o risco e cria a proposta."""
    logging.info("🧠 Cérebro Kelv processando estratégia...")
    prompt = f"""
    Você é Breno (Estúdio Kelv), especialista em automação e Python. Avalie esta vaga:
    Título: {titulo} | Descrição: {descricao[:600]}
    
    Responda EXATAMENTE neste formato JSON:
    {{
      "probabilidade": "Alta/Média/Baixa",
      "estrategia": "Uma frase de como fechar esse projeto",
      "preco_sugerido": "Ex: R$ 800 a R$ 1200",
      "proposta": "Proposta técnica de 3 parágrafos focada na dor do cliente."
    }}
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        res = model.generate_content(prompt)
        texto_limpo = res.text.replace('```json', '').replace('```', '').strip()
        return json.loads(texto_limpo)
    except Exception as e:
        logging.error(f"Erro na IA: {e}")
        return {"probabilidade": "?", "estrategia": "Manual", "preco_sugerido": "?", "proposta": "Olá! Posso ajudar com isso em Python."}

# ==========================================
# 4. TELEGRAM VIP NOTIFIER
# ==========================================
def enviar_alerta(titulo, link, score, analise_ia):
    msg = (
        f"🎯 *VAGA DE ELITE* (Score: {score})\n"
        f"🔥 *{titulo}*\n\n"
        f"📊 *Chances:* {analise_ia.get('probabilidade')}\n"
        f"💡 *Estratégia:* {analise_ia.get('estrategia')}\n"
        f"💰 *Cobrar:* {analise_ia.get('preco_sugerido')}\n\n"
        f"📋 *PROPOSTA PRONTA:*\n"
        f"```text\n{analise_ia.get('proposta')}\n```\n\n"
        f"🔗 [Acessar Projeto]({link})"
    )
    url_api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url_api, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        if r.status_code != 200:
            requests.post(url_api, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}) # Fallback sem formatação
    except Exception as e:
        logging.error(f"Erro Telegram: {e}")

# ==========================================
# 5. AS AÇÕES DO ROBÔ NO NAVEGADOR
# ==========================================
def verificar_mensagens_novas(pagina):
    try:
        pagina.goto("https://www.99freelas.com.br/messages", timeout=40000)
        time.sleep(3)
        if pagina.locator(".unread, .new-message-badge").count() > 0:
            msg = "🚨 *CLIENTE RESPONDEU!* Corre no 99Freelas!"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except: pass

def rodar_sniper(pagina):
    try:
        pagina.goto("https://www.99freelas.com.br/projects", timeout=40000)
        vagas = pagina.locator("li.result-item")
        
        for i in range(min(vagas.count(), 5)):
            vaga = vagas.nth(i)
            titulo = vaga.locator(".title").inner_text()
            link = "https://www.99freelas.com.br" + vaga.locator(".title a").get_attribute("href")
            
            if not db.projeto_visto(link) and any(t in titulo.lower() for t in TERMOS_INTERESSE):
                pagina.goto(link)
                time.sleep(2)
                desc = pagina.locator(".description-text").inner_text()
                texto_body = pagina.inner_text("body")
                
                m = re.search(r'(\d+)\s*Propostas', texto_body)
                p_int = int(m.group(1)) if m else 0
                
                score = calcular_score({"descricao": desc, "propostas_int": p_int})
                
                if score >= 50:
                    analise_ia = pensar_como_kelv(titulo, desc)
                    enviar_alerta(titulo, link, score, analise_ia)
                
                db.salvar_projeto(link, titulo, score)
                pagina.goto("https://www.99freelas.com.br/projects")
    except Exception as e:
        logging.error(f"Erro na caçada: {e}")