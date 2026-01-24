import sqlite3
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
# Dica: Se mudar de hospedagem (VPS), esse arquivo nunca sumirá.
DB_NAME = "licencas_v4.db"  
SENHA_ADMIN = "1234"        

# --- HTML E CSS PROFISSIONAL (COM BOTÃO DELETAR) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepBacbo | Admin Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <style>
        :root { --bg: #050505; --card: #111; --accent: #00ff41; --danger: #ff003c; --text: #e0e0e0; }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'JetBrains Mono', monospace; }
        body { background-color: var(--bg); color: var(--text); padding: 20px; }

        .header { display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding-bottom: 15px; margin-bottom: 30px; }
        .brand { color: var(--accent); font-size: 1.5rem; text-shadow: 0 0 10px rgba(0,255,65,0.4); }

        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: var(--card); padding: 20px; border: 1px solid #333; border-radius: 8px; }
        .stat-card .val { font-size: 2rem; font-weight: bold; color: white; }

        .add-panel { background: var(--card); padding: 20px; border-radius: 8px; border: 1px solid #333; margin-bottom: 30px; }
        .form-row { display: flex; gap: 10px; }
        input { flex: 1; padding: 12px; background: #000; border: 1px solid #333; color: var(--accent); border-radius: 4px; }
        button.btn-add { padding: 12px 30px; background: var(--accent); border: none; font-weight: bold; cursor: pointer; }

        table { width: 100%; border-collapse: collapse; background: var(--card); border-radius: 8px; overflow: hidden; }
        th { text-align: left; padding: 15px; background: #1a1a1a; color: #888; text-transform: uppercase; font-size: 0.8rem; }
        td { padding: 15px; border-bottom: 1px solid #222; }
        
        .btn-del { background: transparent; border: 1px solid var(--danger); color: var(--danger); padding: 5px 10px; cursor: pointer; border-radius: 4px; transition: 0.2s; }
        .btn-del:hover { background: var(--danger); color: white; }

        .status-ok { color: var(--accent); font-weight: bold; }
        .status-end { color: var(--danger); font-weight: bold; }

        #lock-screen { position: fixed; top:0; left:0; width:100%; height:100%; background: #000; z-index: 999; display: flex; align-items: center; justify-content: center; flex-direction: column; }
    </style>
</head>
<body>

    <div id="lock-screen">
        <h1 style="color: var(--accent); margin-bottom: 20px;">🔒 ACESSO RESTRITO</h1>
        <input type="password" id="pass-input" placeholder="Senha..." style="width: 200px; text-align: center;">
        <br><br>
        <button onclick="checkPass()" style="padding: 10px 30px; background: var(--accent); border: none; cursor:pointer;">ENTRAR</button>
    </div>

    <div id="dashboard" style="display: none;">
        <div class="header">
            <div class="brand"><i class="fas fa-robot"></i> DEEPBACBO V4</div>
            <div>STATUS: <span style="color: var(--accent);">ONLINE</span></div>
        </div>

        <div class="stats-grid">
            <div class="stat-card"><h3>Clientes</h3><div class="val">{{ total }}</div></div>
            <div class="stat-card"><h3>Ativos</h3><div class="val" style="color: var(--accent);">{{ ativos }}</div></div>
        </div>

        <div class="add-panel">
            <h3 style="margin-bottom: 15px; color: white;">+ Adicionar Licença</h3>
            <form action="/manual_add" method="POST" class="form-row">
                <input type="hidden" name="senha_admin" id="hidden-pass-add">
                <input type="email" name="email" placeholder="E-mail do Cliente" required>
                <input type="number" name="dias" placeholder="Dias" required>
                <button type="submit" class="btn-add">SALVAR</button>
            </form>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Cliente</th>
                    <th>Validade</th>
                    <th>Status</th>
                    <th>Ação</th>
                </tr>
            </thead>
            <tbody>
                {% for u in users %}
                <tr>
                    <td style="color: white;">{{ u.email }}</td>
                    <td>{{ u.validade }}</td>
                    <td>
                        <span class="{{ u.cor_status }}">{{ u.msg_status }}</span>
                    </td>
                    <td>
                        <form action="/delete_user" method="POST" onsubmit="return confirm('Tem certeza que quer apagar {{ u.email }}?');">
                            <input type="hidden" name="senha_admin" class="hidden-pass-del">
                            <input type="hidden" name="email" value="{{ u.email }}">
                            <button type="submit" class="btn-del"><i class="fas fa-trash"></i></button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <script>
        function checkPass() {
            var pass = document.getElementById('pass-input').value;
            if(pass === "{{ senha_real }}") {
                document.getElementById('lock-screen').style.display = 'none';
                document.getElementById('dashboard').style.display = 'block';
                
                // Preenche a senha nos formulários ocultos para funcionar as ações
                document.getElementById('hidden-pass-add').value = pass;
                var dels = document.getElementsByClassName('hidden-pass-del');
                for(var i=0; i<dels.length; i++) { dels[i].value = pass; }
            } else {
                alert("Senha Incorreta!");
            }
        }
    </script>
</body>
</html>
"""

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS licencas
                 (email TEXT PRIMARY KEY, key TEXT, status TEXT, data_validade TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- ROTA ADMIN ---
@app.route('/admin')
def admin_panel():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT email, data_validade FROM licencas")
    rows = c.fetchall()
    conn.close()

    users = []
    ativos_count = 0
    now = datetime.now()

    for email, val in rows:
        msg_status = "Ativo"
        cor_status = "status-ok"
        val_fmt = "Vitalício"

        if val:
            try:
                dt_val = datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
                val_fmt = dt_val.strftime("%d/%m/%Y")
                if now > dt_val:
                    msg_status = "Expirado"
                    cor_status = "status-end"
                else:
                    ativos_count += 1
            except:
                pass
        else:
            ativos_count += 1 # Considera vitalicio como ativo

        users.append({
            "email": email,
            "validade": val_fmt,
            "msg_status": msg_status,
            "cor_status": cor_status
        })

    return render_template_string(HTML_TEMPLATE, users=users, total=len(users), ativos=ativos_count, senha_real=SENHA_ADMIN)

# --- ROTA ADICIONAR ---
@app.route('/manual_add', methods=['POST'])
def manual_add():
    if request.form.get('senha_admin') != SENHA_ADMIN: return "Senha errada", 403
    
    email = request.form.get('email').lower().strip()
    dias = int(request.form.get('dias'))
    
    data_exp = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO licencas (email, key, status, data_validade) VALUES (?, ?, 'ativo', ?)", 
              (email, "MANUAL", data_exp))
    conn.commit()
    conn.close()
    return redirect('/admin')

# --- ROTA DELETAR (NOVA) ---
@app.route('/delete_user', methods=['POST'])
def delete_user():
    if request.form.get('senha_admin') != SENHA_ADMIN: return "Senha errada", 403
    
    email = request.form.get('email')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM licencas WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    
    return redirect('/admin')

# --- API CHECK ---
@app.route('/check_license', methods=['POST'])
def check_license():
    data = request.json
    email = data.get('email', '').lower().strip()
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT status, data_validade FROM licencas WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()

    if row:
        status, validade = row
        if status != 'ativo': return jsonify({"valid": False, "message": "Bloqueado"}), 403
        
        if validade:
            if datetime.now() > datetime.strptime(validade, "%Y-%m-%d %H:%M:%S"):
                return jsonify({"valid": False, "message": "Licença Expirada"}), 403
        
        return jsonify({"valid": True, "message": "Acesso Permitido"}), 200
    
    return jsonify({"valid": False, "message": "E-mail não encontrado"}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
