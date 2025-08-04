# controle_gastos/main.py

import os
from flask import Flask, render_template, request, send_file, url_for, redirect, session, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from utils import database, relatorio, graficos
from whatsapp_bot import processar_mensagem
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)
# Em produção, substitua "segredo123" por uma variável de ambiente segura
app.secret_key = os.environ.get("SECRET_KEY", "segredo123")


# === ROTA /login ===
@app.route("/login", methods=["GET", "POST"])
def login():
    username_cookie = request.cookies.get("username", "")

    if request.method == "POST":
        username = request.form["username"]
        senha = request.form["senha"]
        lembrar = request.form.get("lembrar")

        # Busca usuário (id e senha hasheada) no banco
        user = database.buscar_usuario_seguro(username)
        if user and check_password_hash(user["senha"], senha):
            session["usuario_id"] = user["id"]
            session["usuario_nome"] = username

            resposta = make_response(redirect("/"))
            if lembrar:
                # Gravar cookie por 30 dias
                resposta.set_cookie("username", username, max_age=30*24*60*60)
            else:
                resposta.delete_cookie("username")
            return resposta
        else:
            # Se credenciais inválidas, exibe erro
            return render_template("login.html",
                                   erro="Usuário ou senha inválidos.",
                                   username=username)

    return render_template("login.html", username=username_cookie)


# === ROTA /cadastro ===
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        username = request.form["username"]
        senha = request.form["senha"]
        confirmar = request.form.get("confirmar_senha")

        # Validações:
        if len(username) < 3:
            return render_template("cadastro.html",
                                   erro="Nome de usuário muito curto.",
                                   username=username)
        if len(senha) < 6:
            return render_template("cadastro.html",
                                   erro="A senha deve ter pelo menos 6 caracteres.",
                                   username=username)
        if senha != confirmar:
            return render_template("cadastro.html",
                                   erro="As senhas não coincidem.",
                                   username=username)

        # Cria hash da senha e insere usuário
        senha_hash = generate_password_hash(senha)
        if database.criar_usuario(username, senha_hash):
            return render_template("cadastro.html",
                                   sucesso="✅ Cadastro realizado com sucesso!")
        else:
            return render_template("cadastro.html",
                                   erro="❌ Nome de usuário já existe.",
                                   username=username)

    return render_template("cadastro.html")


# === ROTA /logout ===
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# === ROTA / ===
@app.route("/", methods=["GET"])
def index():
    if "usuario_id" not in session:
        return redirect("/login")

    mes = request.args.get("mes", default=None, type=int)
    imagem = None
    caminho_pdf = None
    total_gasto = None

    if mes:
        usuario_id = session["usuario_id"]
        # Gera gráfico e PDF (se houver dados)
        imagem = graficos.gerar_grafico_categoria(mes, usuario_id)
        caminho_pdf = relatorio.gerar_relatorio_pdf(mes, usuario_id)

        # Busca total de gastos do mês para exibir
        try:
            conn = database.conectar()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT SUM(valor) FROM gastos WHERE strftime('%m', data) = ? AND usuario_id = ?",
                (f"{mes:02d}", usuario_id)
            )
            total_gasto = cursor.fetchone()[0] or 0
        except Exception:
            total_gasto = 0
        finally:
            conn.close()

    nome_img = f"grafico_categoria_u{session['usuario_id']}.png"
    return render_template("index.html",
                           mes=mes,
                           imagem=url_for('static', filename=nome_img) if imagem else None,
                           relatorio=f"/baixar?mes={mes}" if caminho_pdf else None,
                           usuario=session.get("usuario_nome"),
                           total_gasto=total_gasto)


# === ROTA /baixar ===
@app.route("/baixar")
def baixar_pdf():
    if "usuario_id" not in session:
        return redirect("/login")

    mes = request.args.get("mes", type=int)
    caminho = os.path.join("reports", f"relatorio_{mes:02d}_u{session['usuario_id']}.pdf")
    if os.path.exists(caminho):
        return send_file(caminho, as_attachment=True)
    return "Arquivo não encontrado", 404


# === ROTA /adicionar (WEB) ===
@app.route("/adicionar", methods=["GET", "POST"])
def adicionar_web():
    """
    GET: exibe o formulário de cadastro de um novo gasto.
    POST: recebe dados do formulário, grava no banco, exibe mensagem de sucesso/erro.
    """
    if "usuario_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        # Tenta converter valor para float e ler os campos
        try:
            valor = float(request.form["valor"])
            categoria = request.form["categoria"].strip()
            descricao = request.form["descricao"].strip()
        except ValueError:
            return render_template("adicionar.html",
                                   erro="Informe um valor numérico válido.",
                                   valor=request.form.get("valor", ""),
                                   categoria=request.form.get("categoria", ""),
                                   descricao=request.form.get("descricao", ""))

        usuario_id = session["usuario_id"]
        database.adicionar_gasto(valor, categoria, descricao, usuario_id)
        return render_template("adicionar.html", sucesso="✅ Gasto cadastrado com sucesso!")

    # Se for GET, renderiza o formulário vazio
    return render_template("adicionar.html")


# === ROTA /webhook (WhatsApp) ===
@app.route("/webhook", methods=["POST"])
def whatsapp_webhook():
    """Recebe mensagens do WhatsApp e responde."""
    corpo = request.form.get("Body", "")
    # Neste exemplo simples, usamos o primeiro usuário.
    usuario_id = session.get("usuario_id", 1)
    texto = processar_mensagem(corpo, usuario_id)
    resposta = MessagingResponse()
    resposta.message(texto)
    return str(resposta)


# === TERMINAL MENU INTERFACE (opcional) ===
def menu():
    print("==== CONTROLE DE GASTOS ====")
    print("1. Adicionar gasto")
    print("2. Gerar relatório mensal (PDF + gráfico)")
    print("3. Sair")
    return input("Escolha uma opção: ")


def adicionar():
    try:
        valor = float(input("Valor do gasto: R$ "))
        categoria = input("Categoria (ex: alimentação, transporte): ")
        descricao = input("Descrição (opcional): ")
        usuario_id = int(input("ID do usuário: "))
        database.adicionar_gasto(valor, categoria, descricao, usuario_id)
        print("✅ Gasto adicionado com sucesso!\n")
    except ValueError:
        print("❌ Valor inválido. Tente novamente.\n")


def gerar_relatorio():
    try:
        mes = int(input("Digite o número do mês (ex: 5 para maio): "))
        usuario_id = int(input("ID do usuário: "))
        graficos.gerar_grafico_categoria(mes, usuario_id)
        caminho_pdf = relatorio.gerar_relatorio_pdf(mes, usuario_id)
        print(f"✅ Relatório gerado com sucesso: {caminho_pdf}\n")
    except Exception as e:
        print(f"❌ Erro ao gerar relatório: {e}")


# === INÍCIO DO PROGRAMA ===
if __name__ == "__main__":
    database.criar_tabelas()

    # Quando estiver no reloader do Flask (modo debug), a variável WERKZEUG_RUN_MAIN existe,
    # então apenas executa app.run(debug=True) sem reexibir o menu interativo.
    if os.environ.get("WERKZEUG_RUN_MAIN"):
        app.run(debug=True)
    else:
        # Exibe prompt Terminal x Web apenas na primeira execução
        try:
            modo = input("Modo de uso:\n1. Terminal\n2. Servidor Web\nEscolha (1 ou 2): ")
            if modo == "1":
                while True:
                    opcao = menu()
                    if opcao == "1":
                        adicionar()
                    elif opcao == "2":
                        gerar_relatorio()
                    elif opcao == "3":
                        print("Encerrando...")
                        break
                    else:
                        print("Opção inválida.\n")
            elif modo == "2":
                app.run(debug=True)
            else:
                print("Opção inválida. Encerrando.")
        except KeyboardInterrupt:
            print("\nEncerrado pelo usuário.")
