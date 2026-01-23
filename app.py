import sqlite3
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta

app = Flask(__name__)

DB_NAME = "licencas_v3.db"
SENHA_ADMIN = "1234"  # <--- TROQUE ESSA SENHA PARA NINGUÉM ACESSAR SEU PAINEL

# --- INICIALIZA O BANCO ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Adicionamos a coluna 'data_validade'
    c.execute('''CREATE TABLE IF NOT EXISTS licencas
                 (email TEXT PRIMARY KEY, key TEXT, status TEXT, data_validade TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- ROTA: PAINEL VISUAL PARA ADICIONAR MANUALMENTE (NOVO) ---
@app.route('/admin')
def admin_panel():
    # Um HTML simples para você usar pelo navegador
    html = f'''
    <html>
        <head><title>Painel DeepBacbo</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h2>Gerenciar Licenças Manuais</h2>
            <form action="/manual_add" method="POST">
                <label>Senha Admin:</label><br>
                <input type="password" name="senha_admin" required><br><br>
                
                <label>E-mail do Cliente:</label><br>
                <input type="email" name="email" required><br><br>
                
                <label>Dias de Acesso (Ex: 30):</label><br>
                <input type="number" name="dias" required><br><br>
                
                <button type="submit" style="padding: 10px; background: green; color: white;">Gerar Licença</button>
            </form>
        </body>
    </html>
    '''
    return html

# --- ROTA: PROCESSA A ADIÇÃO MANUAL (NOVO) ---
@app.route('/manual_add', methods=['POST'])
def manual_add():
    # Pega dados do formulário ou do JSON
    data = request.form if request.form else request.json
    
    email = data.get('email')
    dias = data.get('dias')
    senha = data.get('senha_admin')

    if senha != SENHA_ADMIN:
        return "Senha de administrador incorreta!", 403

    if not email or not dias:
        return "Preencha e-mail e dias.", 400

    email = email.lower().strip()
    
    # Calcula a data de expiração (Hoje + Dias escolhidos)
    data_hoje = datetime.now()
    data_expiracao = data_hoje + timedelta(days=int(dias))
    data_expiracao_str = data_expiracao.strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Insere ou Atualiza
    c.execute("INSERT OR REPLACE INTO licencas (email, key, status, data_validade) VALUES (?, ?, ?, ?)", 
              (email, "MANUAL", "ativo", data_expiracao_str))
    
    conn.commit()
    conn.close()

    return f"<h1>Sucesso!</h1><p>Cliente: <b>{email}</b></p><p>Válido até: <b>{data_expiracao_str}</b></p><br><a href='/admin'>Voltar</a>", 200

# --- ROTA 1: KIWIFY (MANTIDA IGUAL) ---
@app.route('/webhook/kiwify', methods=['POST'])
def kiwify_webhook():
    data = request.json
    if not data: return jsonify({"status": "ignored"}), 200

    email = data.get('customer', {}).get('email')
    status_pagamento = data.get('order_status') 
    status_assinatura = data.get('subscription_status')

    if not email: return jsonify({"error": "No email"}), 400

    email = email.lower().strip()
    print(f"🔄 Webhook: {email} | Status: {status_pagamento}")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if status_pagamento == 'paid' and (status_assinatura is None or status_assinatura == 'active'):
        # Kiwify entra como 'LIFETIME' (sem data de expiração, ou validade infinita)
        # Se quiser limitar kiwify também, teria que alterar aqui. Por enquanto, deixei NULL na data.
        c.execute("INSERT OR REPLACE INTO licencas (email, key, status, data_validade) VALUES (?, ?, 'ativo', NULL)", 
                  (email, "KIWIFY"))
        print(f"✅ Acesso LIBERADO para: {email}")

    elif status_assinatura in ['past_due', 'canceled', 'refunded']:
        c.execute("UPDATE licencas SET status = 'bloqueado' WHERE email = ?", (email,))
        print(f"🚫 Acesso BLOQUEADO para: {email}")

    conn.commit()
    conn.close()
    return jsonify({"status": "received"}), 200

# --- ROTA 2: O ROBÔ VERIFICA (ATUALIZADA) ---
@app.route('/check_license', methods=['POST'])
def check_license():
    dados = request.json
    email_usuario = dados.get('email')
    
    if not email_usuario:
        return jsonify({"valid": False, "message": "E-mail obrigatório"}), 400
        
    email_usuario = email_usuario.lower().strip()

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Pegamos status E data de validade
    c.execute("SELECT status, data_validade FROM licencas WHERE email = ?", (email_usuario,))
    resultado = c.fetchone()
    conn.close()
    
    if resultado:
        status_db = resultado[0]
        validade_db = resultado[1]

        # 1. Se estiver marcado como bloqueado manualmente ou pelo Kiwify
        if status_db != 'ativo':
             return jsonify({"valid": False, "message": "Licença inativa ou bloqueada."}), 403

        # 2. Se tiver data de validade, verifica se já venceu
        if validade_db:
            data_exp = datetime.strptime(validade_db, "%Y-%m-%d %H:%M:%S")
            if datetime.now() > data_exp:
                # Opcional: Atualizar status no banco para 'expirado' para organizar
                return jsonify({"valid": False, "message": f"Sua licença expirou em {validade_db}."}), 403

        # Se passou por tudo, está aprovado
        return jsonify({"valid": True, "message": "Login Aprovado! Bem-vindo."}), 200

    else:
        return jsonify({"valid": False, "message": "E-mail não encontrado."}), 403

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000)
