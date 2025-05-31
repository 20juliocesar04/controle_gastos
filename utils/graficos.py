# controle_gastos/utils/graficos.py

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, '..', 'db', 'gastos.db')
STATIC_DIR = os.path.join(BASE_DIR, '..', 'static')

def gerar_grafico_categoria(mes, usuario_id):
    """
    Gera um gráfico de pizza (pie chart) que mostra a porcentagem de gastos por categoria
    de um dado mês (mes: inteiro 1-12) para um usuário específico (usuario_id).
    Salva a imagem em static/grafico_categoria_u<usuario_id>.png e retorna o caminho.
    """

    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
            SELECT categoria, SUM(valor) as total
            FROM gastos
            WHERE strftime('%m', data) = ? AND usuario_id = ?
            GROUP BY categoria
        """
        df = pd.read_sql_query(query, conn, params=(f"{mes:02d}", usuario_id))
    except sqlite3.Error as e:
        print(f"❌ Erro ao acessar o banco: {e}")
        return None
    finally:
        conn.close()

    if df.empty:
        # Se não houver dados, retorna None sem gerar gráfico
        print(f"⚠️ Nenhum gasto encontrado para o mês {mes:02d} e usuário {usuario_id}.")
        return None

    # Garante que a pasta "static" exista
    os.makedirs(STATIC_DIR, exist_ok=True)

    nome_arquivo = f'grafico_categoria_u{usuario_id}.png'
    caminho_img = os.path.join(STATIC_DIR, nome_arquivo)

    # Geração do gráfico de pizza
    plt.figure(figsize=(6, 6))
    plt.pie(
        df['total'],
        labels=df['categoria'],
        autopct='%1.1f%%',
        startangle=90
    )
    plt.title(f"Gastos por Categoria - Mês {mes:02d}")
    plt.tight_layout()
    plt.savefig(caminho_img)
    plt.close()

    return caminho_img
