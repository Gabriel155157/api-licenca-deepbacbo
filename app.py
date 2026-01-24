import sqlite3
import requests
import json
import base64
import os
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
DB_NAME = "licencas_v5.db"  
SENHA_ADMIN = "1234"

# --- CONFIGURAÇÕES DO GITHUB (Pega do Render) ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO") 
ARQUIVO_BACKUP = "backup_clientes.json"

# --- FUNÇÃO 1: SALVAR/ATUALIZAR NA NUVEM ---
def salvar_no_github(email, dias):
    if not GITHUB_TOKEN or not GITHUB_REPO: return

    print(f"☁️ Atualizando {email} no GitHub...")
    url_api = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{ARQUIVO_BACKUP}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

    try:
        # 1. Baixa lista atual
        resp = requests.get(url_api, headers=headers)
        if resp.status_code == 200:
            dados = resp.json()
            sha = dados['sha']
            conteudo = json.loads(base64.b64decode(dados['content']).decode('utf-8'))
        else:
            conteudo = []
            sha = None

        # 2. Atualiza ou Adiciona (Logica de Alterar)
        encontrado = False
        for user in conteudo:
            if user['email'] == email:
                user['dias'] = dias # Atualiza os dias se já existir
                encontrado = True
                break
        
        if not encontrado:
            conteudo.append({"email": email, "dias": dias})

        # 3. Envia de volta
        novo_json = json.dumps(conteudo, indent=2)
        novo_b64 = base64.b64encode(novo_json.encode('utf-8')).decode('utf-8')
        
        payload = {"message": f"Update: {email}", "content": novo_b64}
        if sha: payload["sha"] = sha
        
        requests.put(url_api, headers=headers, json=payload)
        print("✅ GitHub Atualizado!")

    except Exception as e:
        print(f"❌ Erro GitHub Save: {e}")

# --- FUNÇÃO 2: REMOVER DA NUVEM (NOVA!) ---
def remover_do_github(email_para_deletar):
    if not GITHUB_TOKEN or not GITHUB_REPO: return

    print(f"🔥 Removendo {email_para_deletar} do GitHub...")
    url_api = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{ARQUIVO_BACKUP}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

    try:
        # 1. Baixa lista atual
        resp = requests.get(url_api, headers=headers)
        if resp.status_code != 200: return # Se não tem arquivo, não tem o que deletar

        dados = resp.json()
        sha = dados['sha']
        conteudo = json.loads(base64.b64decode(dados['content']).decode('utf-8'))

        # 2. Filtra a lista (Mantém todos QUE NÃO SÃO o email deletado)
        nova_lista = [u for u in conteudo if u['email'] != email_para_deletar]

        # Se o tamanho não mudou, é porque o email não estava lá
        if len(nova_lista) == len(conteudo): return 

        # 3. Envia a lista nova (sem o usuário)
        novo_json = json.dumps(nova_lista, indent=2)
        novo_b64 = base64.b64encode(novo_json.encode('utf-8')).decode('utf-8')
        
        payload = {"message": f"Delete: {email_para_deletar}", "content": novo_b64, "sha": sha}
        
        requests.put(url_api, headers=headers, json=payload)
        print("🗑️ Usuário removido do GitHub com sucesso!")

    except Exception as e:
        print(f"❌ Erro GitHub Delete: {e}")

# --- HTML E CSS (VISUAL) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepBacbo | Cloud Admin</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root { --bg: #050505; --card: #111; --accent: #00ff41; --danger: #ff003c; --text: #e0e0e0; }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'JetBrains Mono', monospace; }
        body { background-color: var(--bg); color: var(--text); padding: 20px; }
        .header { display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding-bottom: 15px; margin-bottom: 30px; }
        .brand { color: var(--accent); font-size: 1.5rem; }
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
        .btn-del { background: transparent; border: 1px solid var(--danger); color: var(--danger); padding: 5px 10px; cursor: pointer; border-radius: 4px; }
        .btn-del:hover { background: var(--danger); color: white; }
        .status-ok { color: var(--accent); font-weight: bold; }
        .status-end { color: var(--danger); font-weight: bold; }
        #lock-screen { position: fixed; top:0; left:0; width:100%; height:100%; background: #000; z-index: 999; display: flex; align-items: center; justify-content: center; flex-direction: column; }
    </style>
</head>
<body>
    <div id="lock-screen">
        <h1 style="color: var(--accent); margin-bottom: 20px;">🔒 CLOUD SYNC</h1>
        <input type="password" id="pass-input" placeholder="Senha..." style="width: 200px; text-align: center;">
        <br><br>
        <button onclick="checkPass()" style="padding: 10px 30px; background: var(--accent); border: none; cursor:pointer;">ACESSAR</button>
    </div>

    <div id="dashboard" style="display: none;">
        <div class="header">
            <div class="brand"><i class="fas fa-cloud"></i> DEEPBACBO ADMIN</div>
            <div>SYNC: <span style="color: var(--accent);">ON</span></div>
        </div>

        <div class="stats-grid">
            <div class="stat-card"><h3>Clientes</h3><div class="val">{{ total }}</div></div>
            <div class="stat-card"><h3>Ativos</h3><div class="val" style="color: var(--accent);">{{ ativos }}</div></div>
        </div>

        <div class="add-panel">
            <h3 style="margin-bottom: 15px; color: white;">+ Adicionar / Alterar (Salva na Nuvem)</h3>
            <form action="/manual_add" method="POST" class="form-row">
                <input type="hidden" name="senha_admin" id="hidden-pass-add">
                <input type="email" name="email" placeholder="E-mail" required>
                <input type="number" name="dias" placeholder="Dias" required>
                <button type="submit" class="btn-add">SALVAR</button>
            </form>
        </div>

        <table>
            <thead><tr><th>Cliente</th><th>Validade</th><th>Status</th><th>Ação</th></tr></thead>
            <tbody>
                {% for u in users %}
                <tr>
                    <td style="color: white;">{{ u.email }}</td>
                    <td>{{ u.validade }}</td>
                    <td><span class="{{ u.cor_status }}">{{ u.msg_status }}</span></td>
                    <td>
                        <form action="/delete_user" method="POST" onsubmit="return confirm('Apagar {{ u.email }} da Nuvem e Local?');">
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
                document.getElementById('hidden-pass-add').value = pass;
                var dels = document.getElementsByClassName('hidden-pass-del');
                for(var i=0; i<dels.length; i++) { dels[i].value = pass; }
            } else { alert("Senha Incorreta!"); }
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

# --- ROTAS ---
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
        msg = "Ativo"
        cor = "status-ok"
        val_fmt = "Vitalício"
        if val:
            try:
                dt_val = datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
                val_fmt = dt_val.strftime("%d/%m/%Y")
                if now > dt_val:
                    msg = "Expirado"
                    cor = "status-end"
                else:
                    ativos_count += 1
            except: pass
        else: ativos_count += 1

        users.append({"email": email, "validade": val_fmt, "msg_status": msg, "cor_status": cor})

    return render_template_string(HTML_TEMPLATE, users=users, total=len(users), ativos=ativos_count, senha_real=SENHA_ADMIN)

@app.route('/manual_add', methods=['POST'])
def manual_add():
    if request.form.get('senha_admin') != SENHA_ADMIN: return "Senha errada", 403
    
    email = request.form.get('email').lower().strip()
    dias = int(request.form.get('dias'))
    data_exp = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")

    # 1. Salva no Banco Local
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO licencas (email, key, status, data_validade) VALUES (?, ?, 'ativo', ?)", 
              (email, "MANUAL", data_exp))
    conn.commit()
    conn.close()

    # 2. Salva na Nuvem GitHub (BACKUP)
    salvar_no_github(email, dias)

    return redirect('/admin')

@app.route('/delete_user', methods=['POST'])
def delete_user():
    if request.form.get('senha_admin') != SENHA_ADMIN: return "Senha errada", 403
    
    email = request.form.get('email')
    
    # 1. Deleta do Banco Local
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM licencas WHERE email = ?", (email,))
    conn.commit()
    conn.close()

    # 2. Deleta da Nuvem GitHub (BACKUP)
    remover_do_github(email)
    
    return redirect('/admin')

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
