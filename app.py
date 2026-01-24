import sqlite3
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime, timedelta

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
DB_NAME = "licencas_v3.db"  # Mantendo o nome atual para não perder dados
SENHA_ADMIN = "1234"        # SENHA DO PAINEL

# --- HTML E CSS PROFISSIONAL (DASHBOARD) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepBacbo | Admin Command Center</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <style>
        :root {
            --bg-color: #050505;
            --card-bg: #111111;
            --accent: #00ff41; /* Verde Matrix */
            --danger: #ff003c;
            --text: #e0e0e0;
            --gray: #333;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'JetBrains Mono', monospace; }
        
        body { background-color: var(--bg-color); color: var(--text); padding: 20px; }

        /* HEADER */
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 1px solid var(--gray); padding-bottom: 15px; }
        .brand { font-size: 1.5rem; color: var(--accent); text-shadow: 0 0 10px rgba(0, 255, 65, 0.5); }
        .brand i { margin-right: 10px; }

        /* CARDS DE ESTATÍSTICA */
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: var(--card-bg); padding: 20px; border: 1px solid var(--gray); border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .stat-card h3 { font-size: 0.9rem; color: #888; margin-bottom: 10px; }
        .stat-card .value { font-size: 2rem; font-weight: bold; color: white; }
        .stat-card.green-glow { border-color: var(--accent); }

        /* FORMULÁRIO */
        .add-panel { background: var(--card-bg); padding: 25px; border-radius: 8px; border: 1px solid var(--gray); margin-bottom: 30px; }
        .add-panel h2 { margin-bottom: 20px; color: white; border-left: 4px solid var(--accent); padding-left: 10px; }
        
        .form-row { display: flex; gap: 15px; flex-wrap: wrap; }
        input { flex: 1; padding: 12px; background: #000; border: 1px solid var(--gray); color: var(--accent); border-radius: 4px; outline: none; }
        input:focus { border-color: var(--accent); box-shadow: 0 0 8px rgba(0, 255, 65, 0.2); }
        
        button { padding: 12px 30px; background: var(--accent); color: black; font-weight: bold; border: none; border-radius: 4px; cursor: pointer; transition: 0.3s; text-transform: uppercase; letter-spacing: 1px; }
        button:hover { background: #00cc33; box-shadow: 0 0 15px var(--accent); transform: translateY(-2px); }

        /* TABELA */
        .table-container { overflow-x: auto; background: var(--card-bg); border-radius: 8px; border: 1px solid var(--gray); }
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; padding: 15px; background: #1a1a1a; color: #888; font-size: 0.8rem; text-transform: uppercase; }
        td { padding: 15px; border-bottom: 1px solid #222; vertical-align: middle; }
        tr:hover { background: #1a1a1a; }
        
        .status-badge { padding: 5px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
        .status-active { background: rgba(0, 255, 65, 0.1); color: var(--accent); border: 1px solid var(--accent); }
        .status-expired { background: rgba(255, 0, 60, 0.1); color: var(--danger); border: 1px solid var(--danger); }
        
        .days-left { font-weight: bold; }
        .days-ok { color: var(--accent); }
        .days-low { color: orange; }
        .days-end { color: var(--danger); }

        /* LOCK SCREEN */
        #lock-screen { position: fixed; top:0; left:0; width:100%; height:100%; background: #000; z-index: 999; display: flex; flex-direction: column; justify-content: center; align-items: center; }
        .lock-box { text-align: center; width: 300px; }
        .lock-box input { margin-bottom: 15px; width: 100%; text-align: center; font-size: 1.2rem; }

    </style>
</head>
<body>

    <div id="lock-screen">
        <div class="lock-box">
            <h1 style="color: var(--accent); margin-bottom: 20px;">🔒 ACESSO RESTRITO</h1>
            <input type="password" id="pass-input" placeholder="Senha do Admin">
            <button onclick="checkPass()">Desbloquear Sistema</button>
            <p id="error-msg" style="color: red; margin-top: 10px; display: none;">Acesso Negado</p>
        </div>
    </div>

    <div id="dashboard" style="display: none;">
        
        <div class="header">
            <div class="brand"><i class="fas fa-robot"></i> DEEPBACBO <span style="font-size: 0.8rem; color: #666;">// v3.0</span></div>
            <div>
                <span style="color: #666;">Status Servidor:</span> <span style="color: var(--accent);">ONLINE ●</span>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card green-glow">
                <h3>👥 Total de Clientes</h3>
                <div class="value">{{ total_clientes }}</div>
            </div>
            <div class="stat-card">
                <h3>✅ Licenças Ativas</h3>
                <div class="value" style="color: var(--accent);">{{ ativos }}</div>
            </div>
            <div class="stat-card">
                <h3>🚫 Expiradas/Bloqueadas</h3>
                <div class="value" style="color: var(--danger);">{{ expirados }}</div>
            </div>
        </div>

        <div class="add-panel">
            <h2><i class="fas fa-plus-circle"></i> Gerar Nova Licença</h2>
            <form action="/manual_add" method="POST" style="display: flex; gap: 10px; align-items: center;">
                <input type="hidden" name="senha_admin" id="hidden-pass">
                
                <input type="email" name="email" placeholder="E-mail do Cliente" required style="flex: 2;">
                <input type="number" name="dias" placeholder="Dias (Ex: 30)" required style="flex: 1;">
                <button type="submit">ATIVAR AGORA</button>
            </form>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Cliente</th>
                        <th>Origem</th>
                        <th>Validade (Data)</th>
                        <th>Tempo Restante</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for u in users %}
                    <tr>
                        <td style="color: white; font-weight: bold;">{{ u.email }}</td>
                        <td>{{ u.key }}</td>
                        <td>{{ u.data_formatada }}</td>
                        <td>
                            <span class="days-left {{ u.classe_cor }}">{{ u.dias_restantes }}</span>
                        </td>
                        <td>
                            {% if u.ativo %}
                                <span class="status-badge status-active">ATIVO</span>
                            {% else %}
                                <span class="status-badge status-expired">INATIVO</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // Sistema simples de proteção visual
        function checkPass() {
            var pass = document.getElementById('pass-input').value;
            // A senha é verificada no back-end também, aqui é só visual
            if(pass === "{{ senha_real }}") {
                document.getElementById('lock-screen').style.display = 'none';
                document.getElementById('dashboard').style.display = 'block';
                document.getElementById('hidden-pass').value = pass; // Preenche pro form funcionar
            } else {
                document.getElementById('error-msg').style.display = 'block';
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

# --- ROTA: PAINEL DE ADMINISTRAÇÃO ---
@app.route('/admin')
def admin_panel():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT email, key, status, data_validade FROM licencas")
    rows = c.fetchall()
    conn.close()

    users_processed = []
    total = 0
    ativos = 0
    expirados = 0

    agora = datetime.now()

    for row in rows:
        email, key, status, data_val = row
        total += 1
        
        # Lógica de cálculo de dias
        dias_restantes_str = "Infinito"
        classe_cor = "days-ok"
        is_active = (status == 'ativo')
        data_fmt = "Vitalício"

        if data_val:
            try:
                dt_validade = datetime.strptime(data_val, "%Y-%m-%d %H:%M:%S")
                data_fmt = dt_validade.strftime("%d/%m/%Y")
                
                delta = dt_validade - agora
                
                if delta.days < 0:
                    dias_restantes_str = "Expirou"
                    classe_cor = "days-end"
                    is_active = False # Força inativo visualmente
                else:
                    dias_restantes_str = f"{delta.days} dias"
                    if delta.days < 5:
                        classe_cor = "days-low"
            except:
                data_fmt = "Erro Data"

        if not is_active:
            expirados += 1
        else:
            ativos += 1

        users_processed.append({
            "email": email,
            "key": key,
            "data_formatada": data_fmt,
            "dias_restantes": dias_restantes_str,
            "classe_cor": classe_cor,
            "ativo": is_active
        })

    return render_template_string(HTML_TEMPLATE, 
                                  users=users_processed, 
                                  total_clientes=total, 
                                  ativos=ativos, 
                                  expirados=expirados,
                                  senha_real=SENHA_ADMIN)

# --- ROTA: ADICIONAR MANUALMENTE ---
@app.route('/manual_add', methods=['POST'])
def manual_add():
    data = request.form
    email = data.get('email')
    dias = data.get('dias')
    senha = data.get('senha_admin')

    if senha != SENHA_ADMIN:
        return "<h1>SENHA ERRADA! ACESSO NEGADO.</h1>", 403

    if not email or not dias:
        return "Faltou dados", 400

    email = email.lower().strip()
    
    # Calcula validade
    data_hoje = datetime.now()
    data_exp = data_hoje + timedelta(days=int(dias))
    data_str = data_exp.strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO licencas (email, key, status, data_validade) VALUES (?, ?, 'ativo', ?)", 
              (email, "MANUAL", data_str))
    conn.commit()
    conn.close()

    # Redireciona de volta para o admin para ficar fluido
    return '<script>alert("Licença Criada com Sucesso!"); window.location.href="/admin";</script>'

# --- ROTAS DA API (MANTIDAS IGUAIS) ---
@app.route('/webhook/kiwify', methods=['POST'])
def kiwify_webhook():
    # ... (Sua lógica do Kiwify permanece aqui, pode manter a do código anterior) ...
    return jsonify({"status": "received"}), 200

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
        if status != 'ativo':
            return jsonify({"valid": False, "message": "Licença Bloqueada"}), 403
        
        if validade:
            dt_val = datetime.strptime(validade, "%Y-%m-%d %H:%M:%S")
            if datetime.now() > dt_val:
                return jsonify({"valid": False, "message": "Licença Expirada"}), 403
        
        return jsonify({"valid": True, "message": "Acesso Permitido"}), 200
    
    return jsonify({"valid": False, "message": "E-mail não encontrado"}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
