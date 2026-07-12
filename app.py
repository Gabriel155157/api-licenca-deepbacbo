import os
import psycopg2
from flask import Flask, request, jsonify, render_template_string, Response

app = Flask(__name__)

# --- CONFIGURAÇÃO ---
# Defina aqui a senha que você usará para acessar o painel
SENHA_ADMIN = "SUA_SENHA_AQUI"
DB_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    return psycopg2.connect(DB_URL)

# --- AUTENTICAÇÃO ---
def check_auth(password):
    return password == SENHA_ADMIN

def authenticate():
    return Response('Acesso Negado. Insira a senha de administrador.', 401, 
                    {'WWW-Authenticate': 'Basic realm="Login Requerido"'})

# --- TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Gestor V8 Pro</title>
    <style>
        body { background-color: #0f172a; color: #fff; font-family: sans-serif; padding: 40px; }
        .container { background-color: #1e293b; padding: 20px; border-radius: 10px; max-width: 500px; margin: auto; }
        input, button { padding: 10px; width: 100%; margin-top: 10px; }
        button { background: #38bdf8; border: none; cursor: pointer; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Painel V8 Pro</h1>
        <form action="/adicionar" method="POST">
            <input type="email" name="email" placeholder="E-mail do cliente" required>
            <button type="submit">Criar Licença</button>
        </form>
    </div>
</body>
</html>
"""

# --- ROTAS ---
@app.route('/', methods=['GET'])
def index():
    auth = request.authorization
    if not auth or not check_auth(auth.password):
        return authenticate()
    return render_template_string(HTML_TEMPLATE)

@app.route('/adicionar', methods=['POST'])
def adicionar():
    auth = request.authorization
    if not auth or not check_auth(auth.password):
        return authenticate()
        
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
        return f"Erro ao adicionar: {e}"

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
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
