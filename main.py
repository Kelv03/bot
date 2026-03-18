import os
import time
import random
import logging
from playwright.sync_api import sync_playwright
from bot_freelas import rodar_sniper, verificar_mensagens_novas

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

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
            contexto = p.chromium.launch_persistent_context(
                user_data_dir=user_path,
                channel="chrome", 
                headless=modo_fantasma,
                args=["--disable-blink-features=AutomationControlled"]
            )
            pagina = contexto.pages[0] if contexto.pages else contexto.new_page()
            
            if modo_fantasma:
                logging.info("⚠️ Modo Nuvem: Certifique-se de que fez login na primeira execução!")

            while True:
                logging.info("📩 Checando mensagens de clientes...")
                verificar_mensagens_novas(pagina)
                
                logging.info("🔎 Analisando o mercado...")
                rodar_sniper(pagina)
                
                delay = random.randint(200, 400)
                logging.info(f"😴 Pausa estratégica de {delay//60} min...")
                time.sleep(delay)
                
        except Exception as e:
            logging.error(f"❌ Falha crítica: {e}")
            if eh_windows: print("💡 DICA: Feche o Chrome normal antes de rodar!")

if __name__ == "__main__":
    iniciar_estudio_kelv()