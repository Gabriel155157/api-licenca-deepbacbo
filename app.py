from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
ARQUIVO_BANCO = "licencas.json"

# Defina a senha secreta do seu painel de admin aqui:
SENHA_ADMIN = "8507"

def carregar_banco():
    if not os.path.exists(ARQUIVO_BANCO):
        return {}
    try:
        with open(ARQUIVO_BANCO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def salvar_banco(dados):
    with open(ARQUIVO_BANCO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# Rota principal (Home)
@app.route("/", methods=["GET"])
def home():
    return "<h1>🚀 Servidor de Licenças DeepBacBo.IA Ativo e Operando!</h1>"

# Rota de validação que o robô acessa automaticamente
@app.route("/check_license", methods=["POST"])
def check_license():
    dados_requisicao = request.get_json() or {}
    email = dados_requisicao.get("email", "").strip().lower()

    if not email:
        return jsonify({"valid": False, "message": "E-mail não informado."}), 400

    banco = carregar_banco()
    agora = datetime.now()

    # Se o e-mail não existe no sistema, cria automaticamente o teste de 1 dia grátis
    if email not in banco:
        data_expiracao = agora + timedelta(days=1)
        banco[email] = {
            "expira_em": data_expiracao.strftime("%Y-%m-%d %H:%M:%S"),
            "tipo": "teste_gratis"
        }
        salvar_banco(banco)
        return jsonify({
            "valid": True, 
            "message": "Teste grátis de 1 dia ativado com sucesso!"
        })

    # Valida a data de expiração
    info_cliente = banco[email]
    data_expiracao = datetime.strptime(info_cliente["expira_em"], "%Y-%m-%d %H:%M:%S")

    if agora <= data_expiracao:
        return jsonify({
            "valid": True,
            "message": "Licença ativa.",
            "expira_em": info_cliente["expira_em"]
        })
    else:
        return jsonify({
            "valid": False,
            "message": "Sua licença ou período de teste expirou."
        })

# --- PAINEL ADMINISTRADOR VISUAL ---
@app.route("/admin", methods=["GET", "POST"])
def admin():
    banco = carregar_banco()
    mensagem = ""

    if request.method == "POST":
        senha = request.form.get("senha", "")
        if senha != SENHA_ADMIN:
            mensagem = "❌ Senha de Administrador incorreta!"
        else:
            acao = request.form.get("acao")
            email = request.form.get("email", "").strip().lower()

            if acao == "adicionar":
                dias = int(request.form.get("dias", 30))
                tipo = request.form.get("tipo", "pago")
                
                # Se o cliente já existe, soma os dias a partir de hoje (ou da expiração atual)
                agora = datetime.now()
                if email in banco:
                    exp_atual = datetime.strptime(banco[email]["expira_em"], "%Y-%m-%d %H:%M:%S")
                    base_tempo = exp_atual if exp_atual > agora else agora
                else:
                    base_tempo = agora

                nova_expiracao = base_tempo + timedelta(days=dias)
                banco[email] = {
                    "expira_em": nova_expiracao.strftime("%Y-%m-%d %H:%M:%S"),
                    "tipo": tipo
                }
                salvar_banco(banco)
                mensagem = f"✅ Sucesso! E-mail {email} liberado por {dias} dias."

            elif acao == "remover":
                if email in banco:
                    del banco[email]
                    salvar_banco(banco)
                    mensagem = f"🗑️ E-mail {email} removido com sucesso."
                else:
                    mensagem = "⚠️ E-mail não encontrado no banco de dados."

    # HTML simples e direto para gerenciar tudo pelo navegador
    html_painel = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Painel Admin - DeepBacBo.IA</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 20px; color: #333; }
            .container { max-width: 800px; margin: auto; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
            h2, h3 { color: #007bff; }
            input, select, button { padding: 10px; margin: 8px 0; width: 100%; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; }
            button { background: #28a745; color: white; font-weight: bold; cursor: pointer; border: none; }
            button:hover { background: #218838; }
            .btn-danger { background: #dc3545; }
            .btn-danger:hover { background: #c82333; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 14px; }
            th { background: #007bff; color: white; }
            .msg { padding: 10px; margin-bottom: 15px; background: #e2f0d9; border: 1px solid #c3e6cb; color: #155724; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔐 Painel Administrativo - DeepBacBo.IA</h2>
            {% if mensagem %}
                <div class="msg">{{ mensagem }}</div>
            {% endif %}
            
            <form method="POST">
                <label><b>Senha de Admin:</b></label>
                <input type="password" name="senha" placeholder="Digite a senha de admin" required>

                <label><b>Ação:</b></label>
                <select name="acao">
                    <option value="adicionar">Adicionar / Renovar Cliente</option>
                    <option value="remover">Remover Cliente</option>
                </select>

                <label><b>E-mail do Cliente:</b></label>
                <input type="email" name="email" placeholder="cliente@email.com" required>

                <label><b>Quantidade de Dias (apenas para Adicionar):</b></label>
                <input type="number" name="dias" value="30">

                <label><b>Tipo de Conta:</b></label>
                <select name="tipo">
                    <option value="pago_mensal">Pago Mensal</option>
                    <option value="vip_vitalicio">VIP / Vitalício</option>
                    <option value="teste_gratis">Teste Grátis</option>
                </select>

                <button type="submit">Executar Ação</button>
            </form>

            <hr style="margin: 30px 0;">

            <h3>📋 Clientes Cadastrados Atualmente</h3>
            <table>
                <tr>
                    <th>E-mail</th>
                    <th>Expira Em</th>
                    <th>Tipo</th>
                </tr>
                {% for email, info in banco.items() %}
                <tr>
                    <td>{{ email }}</td>
                    <td>{{ info.expira_em }}</td>
                    <td>{{ info.tipo }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_painel, banco=banco, mensagem=mensagem)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
