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
    Cria as tabelas principais do sistema se ainda não existirem.
    - usuarios: credenciais básicas do usuário
    - gastos: lançamentos de gastos variáveis
    - categorias: limites mensais de cada categoria
    - gastos_fixos: gastos que se repetem mensalmente
    """
    try:
        with conectar() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    senha TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gastos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    valor REAL NOT NULL,
                    categoria TEXT NOT NULL,
                    descricao TEXT,
                    data TEXT NOT NULL,
                    forma_pagamento TEXT NOT NULL DEFAULT 'Cartão de Crédito',
                    usuario_id INTEGER NOT NULL,
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    limite REAL NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    UNIQUE(nome, usuario_id),
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gastos_fixos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    valor REAL NOT NULL,
                    dia_vencimento INTEGER NOT NULL,
                    forma_pagamento TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    ativo INTEGER NOT NULL DEFAULT 1,
                    usuario_id INTEGER NOT NULL,
                    UNIQUE(nome, usuario_id),
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
                )
                """
            )
    except sqlite3.Error as e:
        print(f"❌ Erro ao criar tabelas: {e}")

def adicionar_gasto(valor, categoria, descricao, usuario_id, forma_pagamento="Cartão de Crédito"):
    """
    Insere um novo gasto no banco:
    - valor (float)
    - categoria (string)
    - descricao (string)
    - data (horário atual)
    - forma_pagamento (string)
    - usuario_id (inteiro)
    """
    data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with conectar() as conn:
            conn.execute(
                """
                INSERT INTO gastos (valor, categoria, descricao, data, forma_pagamento, usuario_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (valor, categoria, descricao, data, forma_pagamento, usuario_id),
            )
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


# ==== Funções de categorias e limites ====

def definir_limite_categoria(nome, limite, usuario_id):
    """Cria ou atualiza o limite mensal de uma categoria."""
    try:
        with conectar() as conn:
            conn.execute(
                """
                INSERT INTO categorias (nome, limite, usuario_id)
                VALUES (?, ?, ?)
                ON CONFLICT(nome, usuario_id) DO UPDATE SET limite=excluded.limite
                """,
                (nome, limite, usuario_id),
            )
    except sqlite3.Error as e:
        print(f"❌ Erro ao definir limite: {e}")


def obter_limite_categoria(nome, usuario_id):
    try:
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT limite FROM categorias WHERE nome=? AND usuario_id=?",
                (nome, usuario_id),
            )
            row = cursor.fetchone()
            return row[0] if row else None
    except sqlite3.Error as e:
        print(f"❌ Erro ao obter limite: {e}")
        return None


def calcular_gasto_categoria_mes(categoria, usuario_id, mes=None, ano=None):
    agora = datetime.now()
    mes = mes or agora.month
    ano = ano or agora.year
    try:
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT SUM(valor) FROM gastos
                WHERE categoria LIKE ? AND usuario_id = ?
                  AND strftime('%m', data) = ?
                  AND strftime('%Y', data) = ?
                """,
                (categoria if categoria != '%' else '%', usuario_id, f"{mes:02d}", str(ano)),
            )
            total = cursor.fetchone()[0]
            return total or 0
    except sqlite3.Error as e:
        print(f"❌ Erro ao calcular gasto: {e}")
        return 0


def saldo_categoria(nome, usuario_id, mes=None, ano=None):
    limite = obter_limite_categoria(nome, usuario_id)
    if limite is None:
        return None
    gasto = calcular_gasto_categoria_mes(nome, usuario_id, mes, ano)
    return limite - gasto


def excede_limite_categoria(nome, valor, usuario_id, mes=None, ano=None):
    saldo = saldo_categoria(nome, usuario_id, mes, ano)
    if saldo is None:
        return False
    return valor > saldo


def total_gasto_mes(usuario_id, mes=None, ano=None):
    agora = datetime.now()
    mes = mes or agora.month
    ano = ano or agora.year
    try:
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT SUM(valor) FROM gastos
                WHERE usuario_id = ?
                  AND strftime('%m', data) = ?
                  AND strftime('%Y', data) = ?
                """,
                (usuario_id, f"{mes:02d}", str(ano)),
            )
            total = cursor.fetchone()[0]
            return total or 0
    except sqlite3.Error as e:
        print(f"❌ Erro ao calcular total: {e}")
        return 0


# ==== Funções de gastos fixos ====

def adicionar_gasto_fixo(nome, valor, dia_vencimento, forma_pagamento, categoria, usuario_id):
    try:
        with conectar() as conn:
            conn.execute(
                """
                INSERT INTO gastos_fixos
                    (nome, valor, dia_vencimento, forma_pagamento, categoria, usuario_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (nome, valor, dia_vencimento, forma_pagamento, categoria, usuario_id),
            )
    except sqlite3.Error as e:
        print(f"❌ Erro ao adicionar gasto fixo: {e}")


def listar_gastos_fixos(usuario_id):
    try:
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT nome, valor, dia_vencimento, forma_pagamento, categoria, ativo FROM gastos_fixos WHERE usuario_id=?",
                (usuario_id,),
            )
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"❌ Erro ao listar gastos fixos: {e}")
        return []


def remover_gasto_fixo(nome, usuario_id):
    try:
        with conectar() as conn:
            conn.execute(
                "DELETE FROM gastos_fixos WHERE nome=? AND usuario_id=?",
                (nome, usuario_id),
            )
    except sqlite3.Error as e:
        print(f"❌ Erro ao remover gasto fixo: {e}")


def editar_gasto_fixo(nome, usuario_id, **dados):
    if not dados:
        return
    campos = ", ".join(f"{k}=?" for k in dados.keys())
    valores = list(dados.values()) + [nome, usuario_id]
    try:
        with conectar() as conn:
            conn.execute(
                f"UPDATE gastos_fixos SET {campos} WHERE nome=? AND usuario_id=?",
                valores,
            )
    except sqlite3.Error as e:
        print(f"❌ Erro ao editar gasto fixo: {e}")


def registrar_gastos_fixos_mes(usuario_id, mes=None, ano=None):
    """Insere no histórico os gastos fixos ativos que ainda não foram registrados no mês."""
    agora = datetime.now()
    mes = mes or agora.month
    ano = ano or agora.year
    try:
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT nome, valor, forma_pagamento, categoria FROM gastos_fixos WHERE ativo=1 AND usuario_id=?",
                (usuario_id,),
            )
            fixos = cursor.fetchall()
            for nome, valor, forma_pagamento, categoria in fixos:
                cursor.execute(
                    """
                    SELECT 1 FROM gastos
                    WHERE descricao = ? AND usuario_id=?
                      AND strftime('%m', data)=? AND strftime('%Y', data)=?
                    """,
                    (f"[FIXO] {nome}", usuario_id, f"{mes:02d}", str(ano)),
                )
                if cursor.fetchone():
                    continue
                data = datetime(ano, mes, 1).strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    """
                    INSERT INTO gastos (valor, categoria, descricao, data, forma_pagamento, usuario_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (valor, categoria, f"[FIXO] {nome}", data, forma_pagamento, usuario_id),
                )
            conn.commit()
    except sqlite3.Error as e:
        print(f"❌ Erro ao registrar gastos fixos: {e}")

