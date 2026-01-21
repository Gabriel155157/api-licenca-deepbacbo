import sqlite3
import hashlib
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURAÇÃO ---
DB_NAME = "clientes_deepbacbo.db"

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabela: Email | Key | Status
    c.execute('''CREATE TABLE IF NOT EXISTS licencas
                 (email TEXT PRIMARY KEY, key TEXT, status TEXT)''')
    conn.commit()
    conn.close()

# Inicia o banco ao ligar o servidor
init_db()

# --- ROTA 1: RECEBER AVISO DA KIWIFY ---
@app.route('/webhook/kiwify', methods=['POST'])
def kiwify_webhook():
    data = request.json
    
    # Proteção simples: se não vier dados, ignora
    if not data: return jsonify({"status": "ignored"}), 200

    email = data.get('customer', {}).get('email')
    status_pagamento = data.get('order_status') # paid, refunded, chargedback
    status_assinatura = data.get('subscription_status') # active, past_due, canceled

    if not email: return jsonify({"error": "No email"}), 400

    print(f"🔄 Webhook: {email} | Pag: {status_pagamento} | Sub: {status_assinatura}")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Lógica: Aprovou o pagamento? Ativa. Cancelou? Bloqueia.
    if status_pagamento == 'paid' and (status_assinatura is None or status_assinatura == 'active'):
        # Gera uma key única baseada no e-mail
        raw_string = f"{email}DEEPBACBO_SECRET_2026"
        nova_key = hashlib.sha256(raw_string.encode()).hexdigest()[:16].upper()
        # Formata: AAAA-BBBB-CCCC-DDDD
        key_formatada = f"{nova_key[:4]}-{nova_key[4:8]}-{nova_key[8:12]}-{nova_key[12:16]}"
        
        c.execute("INSERT OR REPLACE INTO licencas (email, key, status) VALUES (?, ?, 'ativo')", (email, key_formatada))
        print(f"✅ Key Ativada: {key_formatada}")

    elif status_assinatura in ['past_due', 'canceled', 'refunded']:
        c.execute("UPDATE licencas SET status = 'bloqueado' WHERE email = ?", (email,))
        print(f"🚫 Bloqueado: {email}")

    conn.commit()
    conn.close()
    return jsonify({"status": "received"}), 200

# --- ROTA 2: O SEU BOT CHAMA AQUI ---
@app.route('/check_license', methods=['POST'])
def check_license():
    dados = request.json
    key_usuario = dados.get('key')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT status FROM licencas WHERE key = ?", (key_usuario,))
    resultado = c.fetchone()
    conn.close()
    
    if resultado and resultado[0] == 'ativo':
        return jsonify({"valid": True, "message": "Acesso Autorizado"}), 200
    else:
        return jsonify({"valid": False, "message": "Licença Inválida ou Bloqueada"}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)