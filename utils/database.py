# controle_gastos/utils/database.py

import sqlite3
from datetime import datetime
import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, '..', 'db', 'gastos.db')

# Garante que a pasta "db" exista
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def conectar():
    """Retorna uma conexão com o banco SQLite."""
    return sqlite3.connect(DB_PATH)

def criar_tabelas():
    """
    Cria as tabelas "usuarios" e "gastos" se ainda não existirem.
    - usuarios: id, username, senha (hash)
    - gastos: id, valor, categoria, descricao, data, usuario_id (FK)
    """
    try:
        with conectar() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    senha TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS gastos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    valor REAL NOT NULL,
                    categoria TEXT NOT NULL,
                    descricao TEXT,
                    data TEXT NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
                )
            """)
    except sqlite3.Error as e:
        print(f"❌ Erro ao criar tabelas: {e}")

def adicionar_gasto(valor, categoria, descricao, usuario_id):
    """
    Insere um novo gasto no banco:
    - valor (float)
    - categoria (string)
    - descricao (string)
    - data (horário atual)
    - usuario_id (inteiro)
    """
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with conectar() as conn:
            conn.execute("""
                INSERT INTO gastos (valor, categoria, descricao, data, usuario_id)
                VALUES (?, ?, ?, ?, ?)
            """, (valor, categoria, descricao, data, usuario_id))
    except sqlite3.Error as e:
        print(f"❌ Erro ao adicionar gasto: {e}")

def buscar_usuario_seguro(username):
    """
    Retorna um dicionário {"id": ..., "senha": <hash>} se o usuário existir,
    senão retorna None.
    """
    try:
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, senha FROM usuarios WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "senha": row[1]}
            return None
    except sqlite3.Error as e:
        print(f"❌ Erro ao buscar usuário: {e}")
        return None

def criar_usuario(username, senha_hash):
    """
    Insere um novo usuário no banco com senha criptografada (hash).
    Retorna True se criado com sucesso, False se já existir (ou erro).
    """
    try:
        with conectar() as conn:
            conn.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", (username, senha_hash))
            return True
    except sqlite3.IntegrityError:
        # Username já existe (constraint UNIQUE)
        return False
    except sqlite3.Error as e:
        print(f"❌ Erro ao criar usuário: {e}")
        return False

# Opção: se quiser buscar por ID, criar função a parte:
def buscar_usuario_por_id(user_id):
    """
    Retorna o username do usuário pelo ID, ou None se não existir.
    """
    try:
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM usuarios WHERE id = ?", (user_id,))
            resultado = cursor.fetchone()
            return resultado[0] if resultado else None
    except sqlite3.Error as e:
        print(f"❌ Erro ao buscar usuário por ID: {e}")
        return None
