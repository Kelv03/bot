import requests

TOKEN = "8741826033:AAGWC0cjLQDq5DU1hxgg4V_7-fGXMdOQvK0"
CHAT_ID = "5464508366"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {"chat_id": CHAT_ID, "text": "🚀 TESTE: Se você recebeu isso, o robô está configurado!"}

try:
    response = requests.post(url, json=payload)
    print(f"Status do Telegram: {response.status_code}")
    print(f"Resposta: {response.json()}")
except Exception as e:
    print(f"Erro ao conectar: {e}")