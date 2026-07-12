from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_NAME = 'licencas_v2.db'

# ── INICIALIZA A BASE DE DADOS ──
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            status INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ── TEMPLATE VISUAL DO PAINEL (DARK NEON V8 PRO) ──
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestor de Licenças - V8 Pro</title>
    <style>
        body {
            background-color: #0f172a;
            color: #e2e8f0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 40px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            background-color: #1e293b;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            width: 100%;
            max-width: 600px;
            border: 1px solid #334155;
        }
        h1 {
            color: #38bdf8;
            text-align: center;
            font-size: 24px;
            margin-bottom: 5px;
        }
        p.subtitle {
            text-align: center;
            color: #94a3b8;
            font-size: 14px;
            margin-bottom: 25px;
        }
        .msg-sucesso { background: #22c55e20; color: #22c55e; padding: 10px; border-radius: 6px; text-align: center; margin-bottom: 15px; border: 1px solid #22c55e;}
        .msg-erro { background: #ef444420; color: #ef4444; padding: 10px; border-radius: 6px; text-align: center; margin-bottom: 15px; border: 1px solid #ef4444;}
        
        form { display: flex; gap: 10px; margin-bottom: 30px; }
        input[type="email"] {
            flex: 1;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #334155;
            background: #0b1120;
            color: white;
            outline: none;
        }
        input[type="email"]:focus { border-color: #38bdf8; }
        button.btn-add {
            padding: 12px 20px;
            background: #38bdf8;
            color: #0f172a;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s;
        }
        button.btn-add:hover { background: #0284c7; color: white;}
        
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #334155; }
        th { color: #94a3b8; font-size: 12px; text-transform: uppercase; }
        td { font-size: 14px; }
        .status-on { color: #22c55e; font-weight: bold; font-size: 12px; background: #22c55e20; padding: 4px 8px; border-radius: 4px;}
        .btn-del {
            background: #ef444420;
            color: #ef4444;
            border: 1px solid #ef4444;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: bold;
        }
        .btn-del:hover { background: #ef4444; color: white; }
    </style>
</head>
<body>

<div class="container">
    <h1>🚀 DEEPBACBO V8 PRO</h1>
    <p class="subtitle">Gestor Central de Licenças (Acessos)</p>

    {% if msg %}
        <div class="msg-sucesso">{{ msg }}</div>
    {% endif %}
    {% if erro %}
        <div class="msg-erro">{{ erro }}</div>
    {% endif %}

    <form action="/adicionar" method="POST">
        <input type="email" name="email" placeholder="E-mail do cliente (Ex: cliente@gmail.com)" required>
        <button type="submit" class="btn-add">+ Criar Licença</button>
    </form>

    <table>
        <thead>
            <tr>
                <th>E-mail Autorizado</th>
                <th>Status</th>
                <th style="text-align: right;">Ação</th>
            </tr>
        </thead>
        <tbody>
            {% for cliente in clientes %}
            <tr>
                <td>{{ cliente[0] }}</td>
                <td><span class="status-on">ATIVO</span></td>
                <td style="text-align: right;">
                    <form action="/deletar" method="POST" style="margin:0; display:inline;">
                        <input type="hidden" name="email" value="{{ cliente[0] }}">
                        <button type="submit" class="btn-del">REMOVER</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="3" style="text-align: center; color: #64748b; padding: 20px;">Nenhuma licença ativa no momento.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

</body>
</html>
"""

# ── ROTA PRINCIPAL (PAINEL VISUAL) ──
@app.route('/', methods=['GET'])
def index():
    msg = request.args.get('msg')
    erro = request.args.get('erro')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT email FROM clientes ORDER BY id DESC")
    clientes = c.fetchall()
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, clientes=clientes, msg=msg, erro=erro)

# ── ROTA PARA ADICIONAR LICENÇA NO PAINEL ──
@app.route('/adicionar', methods=['POST'])
def adicionar():
    email = request.form.get('email', '').strip().lower()
    if not email:
        return redirect(url_for('index', erro="E-mail inválido!"))
        
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO clientes (email, status) VALUES (?, 1)", (email,))
        conn.commit()
        conn.close()
        return redirect(url_for('index', msg=f"Licença gerada com sucesso para {email}"))
    except sqlite3.IntegrityError:
        return redirect(url_for('index', erro="Este e-mail já possui uma licença ativa!"))

# ── ROTA PARA DELETAR/CORTAR O ACESSO DO CLIENTE ──
@app.route('/deletar', methods=['POST'])
def deletar():
    email = request.form.get('email')
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM clientes WHERE email=?", (email,))
    conn.commit()
    conn.close()
    return redirect(url_for('index', erro=f"Acesso cortado para {email}"))

# ── API QUE A EXTENSÃO DO CHROME VAI LER (O CÉREBRO DA VERIFICAÇÃO) ──
@app.route('/validar', methods=['GET'])
def validar():
    email = request.args.get('email', '').strip().lower()
    
    if not email:
        return jsonify({"autorizado": False, "mensagem": "E-mail não fornecido"}), 400
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT status FROM clientes WHERE email=?", (email,))
    row = c.fetchone()
    conn.close()
    
    if row and row[0] == 1:
        return jsonify({"autorizado": True, "mensagem": "Licença Válida! Acesso Permitido."}), 200
    else:
        return jsonify({"autorizado": False, "mensagem": "Licença Inválida ou Expirada."}), 403

if __name__ == '__main__':
    # Usado apenas para testes locais. No Render, o Gunicorn assume o comando.
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
