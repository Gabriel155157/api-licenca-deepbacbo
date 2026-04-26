from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# Substitua pelas suas outras bibliotecas do servidor antigo (ex: pymongo, sqlite, datetime)
# import sqlite3 
# import datetime

app = Flask(__name__)
CORS(app) # Imprescindível para o robô conectar sem erros!

# ==========================================
# 🔐 ROTA 1: O SEU CÓDIGO ANTIGO DE LICENÇAS
# ==========================================
@app.route('/check_license', methods=['POST', 'OPTIONS'])
def check_license():
    # O navegador manda sempre um OPTIONS antes por segurança
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        dados = request.json
        email = dados.get("email", "")
        
        # ⚠️ AQUI ENTRA O SEU CÓDIGO ANTIGO QUE VALIDA O E-MAIL!
        # Exemplo simulado de como devia estar:
        # usuario = db.clientes.find_one({"email": email})
        # se usuario_valido:
        #    return jsonify({"valid": True, "message": "Aprovado"})
        
        # Como não tenho o seu código de BD, mantenha o que estava no seu ficheiro app.py antigo aqui!
        return jsonify({"valid": True, "message": "Simulação de licença aprovada"})
        
    except Exception as e:
        return jsonify({"valid": False, "message": "Erro interno do servidor"})


# ==========================================
# 🧠 ROTA 2: MOTOR DE MACHINE LEARNING
# ==========================================
@app.route('/prever_numeros', methods=['POST', 'OPTIONS'])
def prever_numeros():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    try:
        dados = request.json
        historico = dados.get('historico', [])
        limite = int(dados.get('limite', 5))

        if len(historico) < 50:
            return jsonify({"numeros": [], "confianca": 0.0})

        hist_cronologico = historico[::-1]

        X = []
        y = []
        passos = 3 
        
        for i in range(len(hist_cronologico) - passos):
            X.append(hist_cronologico[i : i + passos])
            y.append(hist_cronologico[i + passos])
            
        modelo = RandomForestClassifier(n_estimators=100, random_state=42)
        modelo.fit(X, y)
        
        ultimo_padrao = [hist_cronologico[-passos:]]
        probabilidades = modelo.predict_proba(ultimo_padrao)[0]
        classes = modelo.classes_
        
        indices_top = np.argsort(probabilidades)[-limite:][::-1]
        numeros_sugeridos = [int(classes[i]) for i in indices_top]
        
        confianca_total = sum([probabilidades[i] for i in indices_top]) * 100
        
        return jsonify({
            "numeros": numeros_sugeridos,
            "confianca": round(confianca_total, 1)
        })
    except Exception as e:
        print("Erro na IA:", e)
        return jsonify({"numeros": [], "confianca": 0.0})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)