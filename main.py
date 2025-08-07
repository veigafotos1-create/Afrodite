# 📦 IMPORTAÇÕES E CONFIGURAÇÕES INICIAIS
import os
import json
import random
import re
import datetime
import pytz
import time
import threading
from flask import Flask, request
import telebot

# 🛡️ --- CONFIGURAÇÕES DO BOT ---
TOKEN = os.getenv("TOKEN_AFRODITE", "COLOQUE_SEU_TOKEN_AQUI")
ID_GRUPO = None  # Deixe None para qualquer grupo ou coloque um ID específico
ID_ZEUS = 1481389775  # Seu ID fixo

# 🌍 Fuso horário de Brasília
FUSO_BRT = pytz.timezone('America/Sao_Paulo')

# 🚀 Inicialização do bot e Flask
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# 📂 --- ARQUIVOS JSON (TODOS NA RAIZ) ---
ARQUIVOS_JSON = {
    "bem_vindo": "frases_bem_vindo_afrodite.json",
    "menção_homens": "menção_afrodite_homens.json",
    "menção_mulheres": "menção_afrodite_mulheres.json",
    "gatilho_amor": "gatilho_amor.json",
    "gatilho_sexo": "gatilho_sexo.json",
    "gatilho_coracao": "gatilho_coracao.json",
    "gatilho_relacionamento": "gatilho_relacionamento.json",
    "oraculo": "frases_oraculo_afrodite.json",
    "respeito_zeus": "frases_respeito_zeus.json",
    "homens": "homens.json",
    "mulheres": "mulheres.json"
}

# 📌 Controle de respostas (cooldown)
limite_respostas_dia = {}
ultimo_tempo_resposta = {}

MAX_RESPOSTAS_DIA = 3
INTERVALO_MINIMO_SEG = 3600  # 1 hora

# Base directory para carregar arquivos JSON da pasta do script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 📌 --- FUNÇÕES UTILITÁRIAS ---
def carregar_json(nome_arquivo):
    caminho_completo = os.path.join(BASE_DIR, nome_arquivo)
    try:
        with open(caminho_completo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar o arquivo {nome_arquivo}: {e}")
        return []

def escolher_frase(lista):
    return random.choice(lista) if lista else ""

def agora_brasilia():
    return datetime.datetime.now(FUSO_BRT)

def nome_usuario(user):
    return user.first_name or "Mortal"

def usuario_homem(user):
    homens = carregar_json(ARQUIVOS_JSON["homens"])
    return user.username and user.username.lower() in [h.lower() for h in homens]

def usuario_mulher(user):
    mulheres = carregar_json(ARQUIVOS_JSON["mulheres"])
    return user.username and user.username.lower() in [m.lower() for m in mulheres]

def pode_responder(user_id):
    agora = time.time()
    # Limite diário
    if limite_respostas_dia.get(user_id, 0) >= MAX_RESPOSTAS_DIA:
        return False
    # Intervalo mínimo
    if user_id in ultimo_tempo_resposta and agora - ultimo_tempo_resposta[user_id] < INTERVALO_MINIMO_SEG:
        return False
    return True

def registrar_resposta(user_id):
    limite_respostas_dia[user_id] = limite_respostas_dia.get(user_id, 0) + 1
    ultimo_tempo_resposta[user_id] = time.time()

# 📢 --- HANDLERS ---
@bot.message_handler(content_types=["new_chat_members"])
def boas_vindas(message):
    for membro in message.new_chat_members:
        frase = escolher_frase(carregar_json(ARQUIVOS_JSON["bem_vindo"]))
        bot.reply_to(message, frase.replace("{nome}", nome_usuario(membro)))

@bot.message_handler(func=lambda msg: True)
def mensagens(msg):
    user = msg.from_user

    # Resposta especial para Zeus
    if user.id == ID_ZEUS:
        frase = escolher_frase(carregar_json(ARQUIVOS_JSON["respeito_zeus"]))
        bot.reply_to(msg, frase)
        return

    # Cooldown
    if not pode_responder(user.id):
        return

    texto = (msg.text or "").lower()

    # Menção direta
    if re.search(r"\bafrodite\b", texto) or f"@{bot.get_me().username.lower()}" in texto:
        if usuario_homem(user):
            frases = carregar_json(ARQUIVOS_JSON["menção_homens"])
        elif usuario_mulher(user):
            frases = carregar_json(ARQUIVOS_JSON["menção_mulheres"])
        else:
            frases = carregar_json(ARQUIVOS_JSON["menção_homens"]) + carregar_json(ARQUIVOS_JSON["menção_mulheres"])
        bot.reply_to(msg, escolher_frase(frases).replace("{nome}", nome_usuario(user)))
        registrar_resposta(user.id)
        return

    # Gatilhos
    gatilhos = {
        "amor": "gatilho_amor",
        "sexo": "gatilho_sexo",
        "❤️": "gatilho_coracao",
        "💔": "gatilho_coracao",
        "😍": "gatilho_coracao",
        "relacionamento": "gatilho_relacionamento",
        "traição": "gatilho_relacionamento"
    }

    for palavra, arquivo in gatilhos.items():
        if palavra in texto:
            frase = escolher_frase(carregar_json(ARQUIVOS_JSON[arquivo]))
            bot.reply_to(msg, frase.replace("{nome}", nome_usuario(user)))
            registrar_resposta(user.id)
            return

# 🎯 --- MENSAGEM ORÁCULO DIÁRIA ---
def enviar_oraculo():
    frase = escolher_frase(carregar_json(ARQUIVOS_JSON["oraculo"]))
    if frase:
        if ID_GRUPO:
            bot.send_message(ID_GRUPO, frase)
        else:
            print("💬 Oráculo:", frase)

def agendador():
    while True:
        agora = agora_brasilia()
        if agora.strftime("%H:%M") == "12:00":
            enviar_oraculo()
        # Reset diário de limite de respostas
        if agora.strftime("%H:%M") == "00:00":
            limite_respostas_dia.clear()
        time.sleep(60)

threading.Thread(target=agendador, daemon=True).start()

# 🌐 --- FLASK WEBHOOK ---
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def home():
    return "💋 Afrodite está presente."

# ▶️ --- INICIAR APP ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
