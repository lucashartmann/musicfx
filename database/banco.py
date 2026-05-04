import sqlite3

class Banco:
    def __init__(self, nome_banco="data/musicfx.db"):
        self.nome_banco = nome_banco
        self.conexao = None
        self.cursor = None

    def conectar(self):
        self.conexao = sqlite3.connect(self.nome_banco)
        self.cursor = self.conexao.cursor()

    def criar_tabelas(self):
        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS pedais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                intensidade REAL NOT NULL
            );''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS dispositivos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL
            );
        ''')
        self.conexao.commit()
        
    def listar_dispositivos(self):
        self.cursor.execute('SELECT * FROM dispositivos')
        return self.cursor.fetchall()
    
    def adicionar_dispositivo(self, nome, tipo):
        self.cursor.execute('''
            INSERT INTO dispositivos (nome, tipo) VALUES (?, ?)
        ''', (nome, tipo))
        self.conexao.commit()
        
    def remover_dispositivo(self, nome):
        self.cursor.execute('''
            DELETE FROM dispositivos WHERE nome = ?
        ''', (nome,))
        self.conexao.commit()

    def adicionar_pedal(self, tipo, intensidade):
        self.cursor.execute('''
            INSERT INTO pedais (tipo, intensidade) VALUES (?, ?)
        ''', (tipo, intensidade))
        self.conexao.commit()

    def listar_pedais(self):
        self.cursor.execute('SELECT * FROM pedais')
        return self.cursor.fetchall()

    def fechar_conexao(self):
        if self.conexao:
            self.conexao.close()