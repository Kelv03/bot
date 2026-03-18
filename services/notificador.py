def enviar_alerta_ia(dados):
    # O .get() é a nossa blindagem. Se a IA esquecer de gerar algum dado, o bot não trava.
    score = dados.get('score', 0)
    preco = dados.get('preco_sugerido', 'A definir')
    proposta_pronta = dados.get('proposta_kelv', 'Proposta não gerada.')
    probabilidade = dados.get('probabilidade', 'Análise Pendente')
    estrategia = dados.get('dica_estrategia', 'Análise Pendente')
    titulo = dados.get('titulo', 'Vaga Sem Título')
    link = dados.get('url', 'https://www.99freelas.com.br/projects')

    msg = (
        f"🎯 *VAGA DE ELITE DETECTADA* (Score: {score})\n"
        f"🔥 *{titulo}*\n\n"
        f"🤖 *ANÁLISE DO CÉREBRO KELV:*\n"
        f"📊 *Probabilidade de Fechar:* {probabilidade}\n"
        f"💡 *Estratégia:* {estrategia}\n"
        f"💰 *Valor Sugerido:* {preco}\n\n"
        f"📋 *PROPOSTA GERADA PELA IA:*\n"
        f"```text\n{proposta_pronta}\n```\n\n"
        f"🔗 [Acessar Projeto]({link})"
    )
    
    # Certifique-se de que TELEGRAM_TOKEN e TELEGRAM_CHAT_ID estão importados/definidos no arquivo
    url_api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    try:
        # Tenta enviar lindão com Markdown
        resposta = requests.post(url_api, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        
        # O TRUQUE MESTRE: Se o Telegram barrar por causa de caractere especial, envia sem formatação!
        if resposta.status_code != 200:
            logging.warning(f"⚠️ Telegram rejeitou a formatação. Enviando em texto puro... Erro: {resposta.text}")
            requests.post(url_api, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        else:
            logging.info("✅ Alerta da IA enviado com sucesso pro celular!")
            
    except Exception as e:
        logging.error(f"❌ O Telegram caiu ou sem internet: {e}")