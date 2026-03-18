import sqlite3
import time
import logging

class DatabaseManager:
    def __init__(self, db_path="sniper_v10.db"):
        self.conn = sqlite3.connect(db_path, timeout=30)
        self._configurar_performance()
        self._criar_tabelas()

    def _configurar_performance(self):
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")
        self.conn.execute("PRAGMA foreign_keys = ON")

    def _criar_tabelas(self):
        cursor = self.conn.cursor()
        # Clientes
        cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            perfil_url TEXT UNIQUE,
            nome TEXT,
            vagas_postadas INTEGER DEFAULT 0,
            contratacoes_estimadas INTEGER DEFAULT 0
        )''')
        # Projetos
        cursor.execute('''CREATE TABLE IF NOT EXISTS projetos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fonte TEXT,
            url TEXT UNIQUE,
            cliente_id INTEGER,
            titulo TEXT,
            descricao TEXT,
            score_sniper INTEGER,
            status TEXT DEFAULT 'aberto',
            data_detectada INTEGER,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        )''')
        # Índices para performance nível sênior
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON projetos(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_url ON projetos(url)")
        self.conn.commit()

    def projeto_existe(self, url):
        res = self.conn.execute("SELECT 1 FROM projetos WHERE url = ?", (url,)).fetchone()
        return bool(res)

    def salvar_projeto(self, dados):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT OR IGNORE INTO projetos 
            (fonte, url, titulo, descricao, score_sniper, data_detectada)
            VALUES (?, ?, ?, ?, ?, ?)''', 
            (dados['fonte'], dados['url'], dados['titulo'], dados['descricao'], dados['score'], int(time.time())))
        self.conn.commit()