import time
import re
import logging
from scrapers.base_scraper import BaseScraper

class Scraper99(BaseScraper):
    def identificar_fonte(self):
        return "99freelas"

    def buscar_projetos(self, pagina):
        projetos_encontrados = []
        try:
            pagina.goto("https://www.99freelas.com.br/projects", timeout=60000)
            pagina.wait_for_selector("li.result-item")
            vagas = pagina.locator("li.result-item")

            for i in range(min(vagas.count(), 10)):
                vaga = vagas.nth(i)
                titulo = vaga.locator(".title").inner_text()
                link = "https://www.99freelas.com.br" + vaga.locator(".title a").get_attribute("href")
                
                # Coleta básica da lista
                projetos_encontrados.append({
                    "titulo": titulo,
                    "url": link,
                    "fonte": self.identificar_fonte()
                })
        except Exception as e:
            logging.error(f"Erro no Scraper 99: {e}")
        
        return projetos_encontrados

    def extrair_detalhes(self, pagina, url):
        """Entra na página da vaga para pegar a descrição real."""
        try:
            pagina.goto(url, timeout=40000)
            desc = pagina.locator(".description-text").first.inner_text()
            texto_full = pagina.inner_text("body")
            
            # Radar Duplo: Pega "Propostas: 15" ou "15 Propostas"
            m = re.search(r'[Pp]ropostas[\s:]*(\d+)|(\d+)\s*[Pp]ropostas', texto_full)
            if m:
                # O grupo 1 pega se o número vier depois, o grupo 2 pega se vier antes
                propostas_str = m.group(1) if m.group(1) else m.group(2)
                propostas = int(propostas_str)
            else:
                propostas = 0
            
            # Retorna 'propostas' pro motor de Score, e 'qtd_propostas' pro Telegram
            return {
                "descricao": desc, 
                "propostas": propostas, 
                "qtd_propostas": str(propostas)
            }
        except:
            return {"descricao": "", "propostas": 0, "qtd_propostas": "0"}