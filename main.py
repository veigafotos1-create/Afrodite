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
from unidecode import unidecode
import itertools

# 🛡️ --- CONFIGURAÇÕES DO BOT ---
TOKEN = os.getenv("TOKEN_AFRODITE", "8307889841:AAHswZzH-lx6zKCYmY-g8VBLrJOClM3_U0Q")
ID_GRUPO = None
ID_ZEUS = 1481389775

FUSO_BRT = pytz.timezone('America/Sao_Paulo')

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

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
    "mulheres": "mulheres.json",
    "gatilho_insulto": "gatilho_insulto.json",
    "procura_dono": "frases_procura_dono.json"
}

limite_respostas_dia = {}
ultimo_tempo_resposta = {}
MAX_RESPOSTAS_DIA = 3
INTERVALO_MINIMO_SEG = 3600

insultos_ultimo = {}
INTERVALO_INSULTO_SEG = 3600

def pode_responder_insulto(user_id):
    agora = time.time()
    last = insultos_ultimo.get(user_id)
    if last and agora - last < INTERVALO_INSULTO_SEG:
        return False
    return True

def registrar_insulto(user_id):
    insultos_ultimo[user_id] = time.time()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
    mulheres_normalizadas = [unidecode(m.lower()) for m in mulheres]
    nome = unidecode((user.first_name or "").lower())
    username = unidecode((user.username or "").lower())
    return nome in mulheres_normalizadas or username in mulheres_normalizadas

def pode_responder(user_id):
    agora = time.time()
    if limite_respostas_dia.get(user_id, 0) >= MAX_RESPOSTAS_DIA:
        return False
    if user_id in ultimo_tempo_resposta and agora - ultimo_tempo_resposta[user_id] < INTERVALO_MINIMO_SEG:
        return False
    return True

def registrar_resposta(user_id):
    limite_respostas_dia[user_id] = limite_respostas_dia.get(user_id, 0) + 1
    ultimo_tempo_resposta[user_id] = time.time()

def salvar_json(nome_arquivo, lista):
    caminho_completo = os.path.join(BASE_DIR, nome_arquivo)
    try:
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            json.dump(lista, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar o arquivo {nome_arquivo}: {e}")

def escolher_par_aleatorio_sem_repetir():
    homens = carregar_json(ARQUIVOS_JSON["homens"])
    mulheres = carregar_json(ARQUIVOS_JSON["mulheres"])
    usados_homens = carregar_json("pares_usados_homens.json")
    usados_mulheres = carregar_json("pares_usados_mulheres.json")
    disponiveis_homens = [h for h in homens if h not in usados_homens]
    disponiveis_mulheres = [m for m in mulheres if m not in usados_mulheres]
    if not disponiveis_homens:
        usados_homens = []
        salvar_json("pares_usados_homens.json", usados_homens)
        disponiveis_homens = homens.copy()
    if not disponiveis_mulheres:
        usados_mulheres = []
        salvar_json("pares_usados_mulheres.json", usados_mulheres)
        disponiveis_mulheres = mulheres.copy()
    escolhido_homem = random.choice(disponiveis_homens)
    escolhido_mulher = random.choice(disponiveis_mulheres)
    usados_homens.append(escolhido_homem)
    usados_mulheres.append(escolhido_mulher)
    salvar_json("pares_usados_homens.json", usados_homens)
    salvar_json("pares_usados_mulheres.json", usados_mulheres)
    return escolhido_homem, escolhido_mulher

#@bot.message_handler(content_types=["new_chat_members"])
#def boas_vindas(message):
#    for membro in message.new_chat_members:
#        frase = escolher_frase(carregar_json(ARQUIVOS_JSON["bem_vindo"]))
#        bot.reply_to(message, frase.replace("{nome}", nome_usuario(membro)))

@bot.message_handler(func=lambda msg: True)
def mensagens(msg):
    user = msg.from_user
    texto = (msg.text or "").lower()

    if user.id == ID_ZEUS and (re.search(r"\bafrodite\b", texto) or f"@{bot.get_me().username.lower()}" in texto):
        frase = escolher_frase(carregar_json(ARQUIVOS_JSON["respeito_zeus"]))
        bot.reply_to(msg, frase)
        return

    padroes_zeus = [
        r"\bzeus\b",
        r"\bsamuel\b",
        r"\bsamu\b",
        r"\bsamuka\b",
        r"\bsamuca\b",
        r"dono.*grupo",
        r"cad[eê]\s+o\s+(zeus|samuel|samu(?:ka|ca)?)",
        r"algu[eé]m\s+(viu|chamou|falou)\s+(zeus|samuel|samu(?:ka|ca)?)"
    ]
    if user.id != ID_ZEUS and any(re.search(p, texto) for p in padroes_zeus):
        frases = carregar_json(ARQUIVOS_JSON["procura_dono"])
        bot.reply_to(msg, escolher_frase(frases).replace("{nome}", nome_usuario(user)))
        return

    gatilho_insultos = [
        "burra","bot burro","afrodite burra","dono burro",
        "chata","chato","xata",
        "aff","afff","affff",
        "brinquedo","robô","robo","jumenta","imoral","pervertida","sai fora"
    ]
    if any(p in texto for p in gatilho_insultos):
        if pode_responder_insulto(user.id):
            stickers = carregar_json(ARQUIVOS_JSON.get("gatilho_insulto", "gatilho_insulto.json"))
            if stickers:
                bot.send_sticker(msg.chat.id, random.choice(stickers))
                registrar_insulto(user.id)
        return

    if not pode_responder(user.id):
        return

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
            stickers = carregar_json(ARQUIVOS_JSON[arquivo])
            if stickers:
                bot.send_sticker(msg.chat.id, random.choice(stickers))
                registrar_resposta(user.id)
            return

def enviar_oraculo():
    frase = escolher_frase(carregar_json(ARQUIVOS_JSON["oraculo"]))
    if frase:
        homem, mulher = escolher_par_aleatorio_sem_repetir()
        mensagem = f"{frase}\n\nHoje o oráculo escolheu: @{homem} e @{mulher} 💫"
        if ID_GRUPO:
            bot.send_message(ID_GRUPO, mensagem)
        else:
            print("💬 Oráculo:", mensagem)

def agendador():
    while True:
        agora = agora_brasilia()
        if agora.strftime("%H:%M") == "09:00":
            enviar_oraculo()
            limite_respostas_dia.clear()
        time.sleep(60)

threading.Thread(target=agendador, daemon=True).start()

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def home():
    return "💋 Afrodite está presente."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
