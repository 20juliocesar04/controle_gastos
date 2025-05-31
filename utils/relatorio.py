# controle_gastos/utils/relatorio.py

import sqlite3
from fpdf import FPDF
import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, '..', 'db', 'gastos.db')
RELATORIO_DIR = os.path.join(BASE_DIR, '..', 'reports')
STATIC_DIR = os.path.join(BASE_DIR, '..', 'static')

# Garante que as pastas existam
os.makedirs(RELATORIO_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

def gerar_relatorio_pdf(mes, usuario_id):
    """
    Gera um PDF com todos os registros de gastos do mês (mes: inteiro 1-12)
    para o usuário (usuario_id). Inclui valor, categoria, descrição e data.
    Adiciona também o gráfico se o arquivo estiver em static/.
    Salva como reports/relatorio_<mes>_u<usuario_id>.pdf.
    Retorna o caminho do arquivo ou None se der erro.
    """

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Seleciona os registros do mês e do usuário
        cursor.execute("""
            SELECT valor, categoria, descricao, data
            FROM gastos
            WHERE strftime('%m', data) = ? AND usuario_id = ?
            ORDER BY data DESC
        """, (f"{mes:02d}", usuario_id))
        registros = cursor.fetchall()

        # Soma total dos gastos do mês para exibir no relatório
        cursor.execute("""
            SELECT SUM(valor)
            FROM gastos
            WHERE strftime('%m', data) = ? AND usuario_id = ?
        """, (f"{mes:02d}", usuario_id))
        total = cursor.fetchone()[0] or 0

    except sqlite3.Error as e:
        print(f"❌ Erro no banco de dados: {e}")
        return None
    finally:
        conn.close()

    nome_arquivo = os.path.join(RELATORIO_DIR, f'relatorio_{mes:02d}_u{usuario_id}.pdf')
    img_path = os.path.join(STATIC_DIR, f'grafico_categoria_u{usuario_id}.png')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Relatório de Gastos - Mês {mes:02d}", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Total Gasto: R$ {total:.2f}", ln=True)
    pdf.ln(10)

    # Cabeçalhos da tabela
    pdf.set_font("Arial", "B", 12)
    pdf.cell(40, 10, "Valor", 1)
    pdf.cell(50, 10, "Categoria", 1)
    pdf.cell(60, 10, "Descrição", 1)
    pdf.cell(40, 10, "Data", 1)
    pdf.ln()

    # Conteúdo da tabela
    pdf.set_font("Arial", "", 10)
    for valor, categoria, descricao, data in registros:
        pdf.cell(40, 10, f"R$ {valor:.2f}", 1)
        pdf.cell(50, 10, categoria[:20], 1)
        pdf.cell(60, 10, (descricao or '---')[:30], 1)
        pdf.cell(40, 10, data.split(" ")[0], 1)
        pdf.ln()

    # Se o gráfico existir, adiciona uma segunda página com a imagem
    if os.path.exists(img_path):
        pdf.add_page()
        pdf.image(img_path, x=30, y=30, w=150)

    pdf.output(nome_arquivo)
    print(f"✅ Relatório PDF gerado: {nome_arquivo}")
    return nome_arquivo
