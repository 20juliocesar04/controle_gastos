# controle_gastos/whatsapp_bot.py

"""Módulo com regras de negócio para o bot do WhatsApp.
Ele interpreta mensagens de texto recebidas e registra gastos
no banco de dados utilizando as funções do módulo `utils.database`.
"""

import re

from utils import database

# Mapeamento simples de palavras-chave para categorias
CATEGORY_KEYWORDS = {
    "gasolina": "Combustível",
    "pão": "Alimentação",
    "pao": "Alimentação",
}

DEFAULT_PAYMENT = "Cartão de Crédito"


def _extrair_valor(texto: str) -> float | None:
    """Extrai o primeiro número encontrado no texto."""
    match = re.search(r"(\d+(?:[.,]\d+)?)", texto)
    if match:
        return float(match.group(1).replace(",", "."))
    return None


def _identificar_categoria(texto: str) -> str:
    texto_lower = texto.lower()
    for palavra, categoria in CATEGORY_KEYWORDS.items():
        if palavra in texto_lower:
            return categoria
    return "Outros"


def _processar_gasto(texto: str, usuario_id: int) -> str:
    valor = _extrair_valor(texto)
    if valor is None:
        return "Não entendi o valor do gasto."
    categoria = _identificar_categoria(texto)

    if database.excede_limite_categoria(categoria, valor, usuario_id):
        # Registra mesmo excedendo o limite, mas avisa o usuário
        database.adicionar_gasto(valor, categoria, texto, usuario_id)
        return f"⚠️ Gasto registrado, mas excede o limite da categoria {categoria}."

    database.adicionar_gasto(valor, categoria, texto, usuario_id)
    return f"✅ Gasto de R$ {valor:.2f} em {categoria} registrado!"


def _comando_saldo_categoria(texto: str, usuario_id: int) -> str:
    categoria = texto.split("saldo categoria", 1)[1].strip()
    saldo = database.saldo_categoria(categoria, usuario_id)
    if saldo is None:
        return f"Categoria {categoria} sem limite cadastrado."
    return f"Você ainda pode gastar R$ {saldo:.2f} em {categoria} este mês."


def _comando_relatorio_mes(usuario_id: int) -> str:
    total = database.total_gasto_mes(usuario_id)
    return f"Total gasto no mês: R$ {total:.2f}"


def _comando_listar_fixos(usuario_id: int) -> str:
    fixos = database.listar_gastos_fixos(usuario_id)
    if not fixos:
        return "Nenhum gasto fixo cadastrado."
    linhas = []
    for nome, valor, dia, forma, categoria, ativo in fixos:
        status = "ativo" if ativo else "pausado"
        linhas.append(f"{nome} - R$ {valor:.2f} dia {dia} ({categoria}) {status}")
    return "Gastos fixos:\n" + "\n".join(linhas)


def _comando_add_fixo(texto: str, usuario_id: int) -> str:
    """Adiciona um gasto fixo.
    Formato esperado: fixo <nome> <valor> <dia> <forma_pagamento> <categoria>
    """
    partes = texto.split()
    if len(partes) < 6:
        return "Formato inválido. Use: fixo <nome> <valor> <dia> <forma_pagamento> <categoria>"
    nome = partes[1]
    try:
        valor = float(partes[2].replace(",", "."))
        dia = int(partes[3])
    except ValueError:
        return "Valor ou dia inválido."
    forma = partes[4]
    categoria = " ".join(partes[5:])
    database.adicionar_gasto_fixo(nome, valor, dia, forma, categoria, usuario_id)
    return f"Gasto fixo {nome} cadastrado."


def _comando_remover_fixo(texto: str, usuario_id: int) -> str:
    nome = texto.split("remover", 1)[1].strip()
    database.remover_gasto_fixo(nome, usuario_id)
    return f"Gasto fixo {nome} removido."


def processar_mensagem(mensagem: str, usuario_id: int) -> str:
    """Processa o texto recebido no WhatsApp e retorna a resposta."""
    texto = mensagem.strip().lower()

    if texto.startswith("saldo categoria"):
        return _comando_saldo_categoria(texto, usuario_id)
    if texto == "relatorio do mes":
        return _comando_relatorio_mes(usuario_id)
    if texto == "listar fixos":
        return _comando_listar_fixos(usuario_id)
    if texto.startswith("fixo "):
        return _comando_add_fixo(texto, usuario_id)
    if texto.startswith("remover "):
        return _comando_remover_fixo(texto, usuario_id)

    # Antes de registrar gastos variáveis, garante que os fixos do mês estejam lançados
    database.registrar_gastos_fixos_mes(usuario_id)
    return _processar_gasto(mensagem, usuario_id)

