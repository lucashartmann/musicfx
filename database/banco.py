import sqlite3
from model.pedals import pedal
from model.amps import amplificador


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
                nome TEXT NOT NULL UNIQUE,
                intensidade REAL NOT NULL
            );''')
        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS amplificadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                gain REAL NOT NULL,
                bass REAL NOT NULL,
                mid REAL NOT NULL,
                treble REAL NOT NULL
            );''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS dispositivos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL UNIQUE
            );
        ''')
        self.conexao.commit()

    def atualizar_pedal(self, pedal):
        try:
            self.cursor.execute('''
                UPDATE pedais SET intensidade = ? WHERE nome = ?
            ''', (pedal.get_intensidade(), pedal.get_nome()))
            self.conexao.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao atualizar pedal: {e}")
            return False

    def listar_dispositivos(self):
        try:
            self.cursor.execute('SELECT * FROM dispositivos')
            lista = []
            for row in self.cursor.fetchall():
                dict = {}
                dict["id"] = row[0]
                dict["nome"] = row[1]
                dict["tipo"] = row[2]
                lista.append(dict)
            return lista
        except sqlite3.Error as e:
            print(f"Erro ao listar dispositivos: {e}")
            return []

    def tipo_is_cadastrado(self, tipo):
        try:
            self.cursor.execute(
                'SELECT 1 FROM dispositivos WHERE tipo = ? LIMIT 1', (tipo,))
            return self.cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"Erro ao verificar tipo: {e}")
            return False

    def atualizar_dispositivo(self, nome, tipo):
        try:
            self.cursor.execute('''
                UPDATE dispositivos SET nome = ? WHERE tipo = ?
            ''', (nome, tipo))
            self.conexao.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao atualizar dispositivo: {e}")
            return False

    def adicionar_dispositivo(self, nome, tipo):
        if self.tipo_is_cadastrado(tipo):
            return self.atualizar_dispositivo(nome, tipo)
        try:
            self.cursor.execute('''
                INSERT INTO dispositivos (nome, tipo) VALUES (?, ?)
            ''', (nome, tipo))
            self.conexao.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao adicionar dispositivo: {e}")
            return False

    def remover_dispositivo(self, nome):
        try:
            self.cursor.execute('''
                DELETE FROM dispositivos WHERE nome = ?
            ''', (nome,))
            self.conexao.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao remover dispositivo: {e}")
            return False

    def adicionar_amp(self, amp):
        try:
            nome = amp.get_nome() if hasattr(amp, 'get_nome') else getattr(amp, 'nome', None)
            gain = getattr(amp, 'gain', 0.5)
            bass = getattr(amp, 'bass', 0.5)
            mid = getattr(amp, 'mid', 0.5)
            treble = getattr(amp, 'treble', 0.5)
            self.cursor.execute('''
                INSERT INTO amplificadores (nome, gain, bass, mid, treble) VALUES (?, ?, ?, ?, ?)
            ''', (nome, gain, bass, mid, treble))
            self.conexao.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao adicionar amplificador: {e}")
            return False

    def adicionar_pedal(self, pedal):
        try:
            self.cursor.execute('''
                INSERT INTO pedais (tipo, nome, intensidade) VALUES (?, ?, ?)
            ''', (pedal.get_tipo(), pedal.get_nome(), pedal.get_intensidade()))
            self.conexao.commit()
            return True
        except sqlite3.Error as e:
            print(f"Erro ao adicionar pedal: {e}")
            return False

    def listar_pedais(self):
        try:
            self.cursor.execute('SELECT * FROM pedais')
            lista = []
            for row in self.cursor.fetchall():
                pedal_obj = pedal.Pedal(row[2])
                pedal_obj.set_intensidade(row[3])
                try:
                    tipo_str = row[1]
                    tipo_enum = next((t for t in pedal.TipoPedal if t.value == tipo_str), None)
                    if tipo_enum is not None:
                        pedal_obj.set_tipo(tipo_enum)
                except Exception:
                    pass
                lista.append(pedal_obj)
            return lista
        except sqlite3.Error as e:
            print(f"Erro ao listar pedais: {e}")
            return []

    def pedal_nome_existe(self, nome):
        try:
            self.cursor.execute('SELECT 1 FROM pedais WHERE nome = ? LIMIT 1', (nome,))
            return self.cursor.fetchone() is not None
        except sqlite3.Error as e:
            print(f"Erro ao verificar existencia de pedal por nome: {e}")
            return False

    def listar_amps(self):
        try:
            self.cursor.execute('SELECT * FROM amplificadores')
            lista = []
            for row in self.cursor.fetchall():
                amp = amplificador.Amplificador(row[1], sample_rate=48000)
                amp.set_bass(row[3])
                amp.set_mid(row[4])
                amp.set_treble(row[5])
                amp.set_gain(row[2])
                lista.append(amp)
            return lista
        except sqlite3.Error as e:
            print(f"Erro ao listar amps: {e}")
            return []

    def fechar_conexao(self):
        if self.conexao:
            self.conexao.close()
