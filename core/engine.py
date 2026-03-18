import re
from core.utils import limpar_texto

class SniperEngine:
    def __init__(self, termos_interesse):
        self.termos = termos_interesse 
        self.regex_stack = re.compile(r'\b(' + '|'.join(map(re.escape, self.termos)) + r')\b', re.IGNORECASE)

    def calcular_score(self, dados):
        # 0. KILL SWITCH - A LISTA NEGRA DO ESTÚDIO KELV
        # Junta título e descrição para procurar as palavras proibidas
        texto_completo = limpar_texto(dados.get('titulo', '') + " " + dados.get('descricao', '')).lower()
        
        proibidas = ["tradução", "inglês", "redator", "copywriter", "legenda", "tiktok", "reels", "vídeo", "edição", "canva", "tradutor"]
        
        if any(palavra in texto_completo for palavra in proibidas):
            return 0 # Mata a vaga na hora! Score zero.

        # 1. Lógica Base
        score = 50.0
        desc = limpar_texto(dados.get('descricao', '')).lower()

        # 2. Sinais Técnicos (O que a gente gosta)
        if self.regex_stack.search(desc): 
            score += 20
        if any(token in desc for token in ["api", "github", "documentação", "json", "python", "automação"]): 
            score += 15

        # 3. Penalidades por Tamanho
        tam = len(desc)
        if tam < 50: score *= 0.5
        elif tam < 150: score *= 0.8

        # 4. Competição (Lê o número de propostas com segurança)
        # Transforma o que vier em número inteiro
        p_str = str(dados.get('propostas', '0'))
        numeros = re.findall(r'\d+', p_str)
        p = int(numeros[0]) if numeros else 0

        if p > 30: score *= 0.5
        elif p <= 5: score *= 1.4

        return int(min(max(score, 0), 100))