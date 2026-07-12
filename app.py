import os
import psycopg2
from flask import Flask, request, jsonify, render_template_string, redirect, url_for

app = Flask(__name__)

# O Render lerá a variável DATABASE_URL configurada no painel
DB_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DB_URL)

# ── TEMPLATE HTML (Painel Visual) ──
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Gestor de Licenças - V8 Pro</title>
    <style>
        body { background-color: #0f172a; color: #e2e8f0; font-family: sans-serif; padding: 40px; display: flex; flex-direction: column; align-items: center; }
        .container { background-color: #1e293b; padding: 30px; border-radius: 12px; width: 100%; max-width: 600px; }
        h1 { color: #38bdf8; text-align: center; }
        form { display: flex; gap: 10px; margin-bottom: 30px; }
        input { flex: 1; padding: 12px; border-radius: 6px; border: 1px solid #334155; background: #0b1120; color: white; }
        button { padding: 12px 20px; background: #38bdf8; color: #0f172a; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 DEEPBACBO V8 PRO</h1>
        <form action="/adicionar" method="POST">
            <input type="email" name="email" placeholder="E-mail do cliente" required>
            <button type="submit">+ Criar Licença</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/adicionar', methods=['POST'])
def adicionar():
    email = request.form.get('email', '').strip().lower()
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO clientes (email, status) VALUES (%s, 1)", (email,))
        conn.commit()
        c.close()
        conn.close()
        return "Licença gerada com sucesso!"
    except Exception as e:
        return f"Erro: {e}"

@app.route('/validar', methods=['GET'])
def validar():
    email = request.args.get('email', '').strip().lower()
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT status FROM clientes WHERE email=%s", (email,))
        row = c.fetchone()
        c.close()
        conn.close()
        if row and row[0] == 1:
            return jsonify({"autorizado": True}), 200
        return jsonify({"autorizado": False}), 403
    except Exception:
        return jsonify({"autorizado": False}), 500

if __name__ == '__main__':
    # O Render injeta a porta correta na variável de ambiente PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
