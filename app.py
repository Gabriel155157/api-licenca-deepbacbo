from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
ARQUIVO_BANCO = "licencas.json"

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

@app.route("/check_license", methods=["POST"])
def check_license():
    dados_requisicao = request.get_json() or {}
    email = dados_requisicao.get("email", "").strip().lower()

    if not email:
        return jsonify({"valid": False, "message": "E-mail não informado."}), 400

    banco = carregar_banco()
    agora = datetime.now()

    # Se o e-mail não existe, criamos automaticamente o TESTE GRÁTIS de 1 dia
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

    # Se o e-mail já existe, verificamos a validade
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
