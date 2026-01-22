import sqlite3
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

DB_NAME = "clientes_deepbacbo.db"

# --- INICIALIZA O BANCO ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Mantivemos a coluna 'key' para não dar erro se o banco já existir, 
    # mas vamos usar o email para validar.
    c.execute('''CREATE TABLE IF NOT EXISTS licencas
                 (email TEXT PRIMARY KEY, key TEXT, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- ROTA 1: KIWIFY AVISA QUE VENDEU ---
@app.route('/webhook/kiwify', methods=['POST'])
def kiwify_webhook():
    data = request.json
    
    if not data: return jsonify({"status": "ignored"}), 200

    email = data.get('customer', {}).get('email')
    status_pagamento = data.get('order_status') 
    status_assinatura = data.get('subscription_status')

    if not email: return jsonify({"error": "No email"}), 400

    # Normaliza o email para minúsculo
    email = email.lower().strip()

    print(f"🔄 Webhook: {email} | Status: {status_pagamento}")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Se pagou, libera o acesso
    if status_pagamento == 'paid' and (status_assinatura is None or status_assinatura == 'active'):
        # Salvamos o email como 'ativo'. A coluna key recebe um valor padrão.
        c.execute("INSERT OR REPLACE INTO licencas (email, key, status) VALUES (?, ?, 'ativo')", 
                  (email, "LOGIN_VIA_EMAIL"))
        print(f"✅ Acesso LIBERADO para: {email}")

    # Se cancelou/reembolsou, bloqueia
    elif status_assinatura in ['past_due', 'canceled', 'refunded']:
        c.execute("UPDATE licencas SET status = 'bloqueado' WHERE email = ?", (email,))
        print(f"🚫 Acesso BLOQUEADO para: {email}")

    conn.commit()
    conn.close()
    return jsonify({"status": "received"}), 200

# --- ROTA 2: O BOT PERGUNTA SE O EMAIL PAGOU ---
@app.route('/check_license', methods=['POST'])
def check_license():
    dados = request.json
    email_usuario = dados.get('email')
    
    if not email_usuario:
        return jsonify({"valid": False, "message": "E-mail obrigatório"}), 400
        
    email_usuario = email_usuario.lower().strip()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Verifica se o email existe e se o status é 'ativo'
    c.execute("SELECT status FROM licencas WHERE email = ?", (email_usuario,))
    resultado = c.fetchone()
    conn.close()
    
    if resultado and resultado[0] == 'ativo':
        return jsonify({"valid": True, "message": "Login Aprovado! Bem-vindo."}), 200
    else:
        return jsonify({"valid": False, "message": "E-mail não encontrado ou assinatura inativa."}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)