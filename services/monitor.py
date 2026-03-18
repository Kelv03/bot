import time
import logging
from core.database import DatabaseManager

class Monitor:
    def __init__(self, scraper):
        self.db = DatabaseManager()
        self.scraper = scraper

    def executar_rechecks(self, pagina):
        """Busca projetos abertos e verifica se o status mudou."""
        # Busca projetos que não foram finalizados no banco
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id, url, status FROM projetos WHERE status = 'aberto' LIMIT 5")
        projetos = cursor.fetchall()

        for pid, url, status_antigo in projetos:
            logging.info(f"🕰️ Rechecando status de: {url}")
            detalhes = self.scraper.extrair_detalhes(pagina, url)
            
            # Aqui você detectaria se o status mudou no HTML (ex: 'Trabalhando')
            # Por agora, vamos apenas atualizar o timestamp de check
            self.db.conn.execute("UPDATE projetos SET data_detectada = ? WHERE id = ?", 
                                (int(time.time()), pid))
            self.db.conn.commit()