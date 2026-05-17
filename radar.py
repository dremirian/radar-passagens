#!/usr/bin/env python3
"""
✈️ Radar de Passagens Aéreas - GRU → Qualquer Lugar
Monitora Google Flights e manda alerta no Telegram quando achar passagem barata.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional
import requests
from fast_flights import FlightData, Passengers, Result, create_filter, get_flights

# ─── Configurações ────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
PRECO_LIMITE       = int(os.environ.get("PRECO_LIMITE", "800"))   # R$ máximo
ORIGEM             = os.environ.get("ORIGEM", "GRU")
DIAS_ANTECEDENCIA  = int(os.environ.get("DIAS_ANTECEDENCIA", "30"))  # quantos dias à frente buscar
HISTORICO_FILE     = "historico_alertas.json"

# Destinos nacionais populares para monitorar
DESTINOS_NACIONAIS = [
    ("FOR", "Fortaleza"),
    ("REC", "Recife"),
    ("SSA", "Salvador"),
    ("MCZ", "Maceió"),
    ("NAT", "Natal"),
    ("MAO", "Manaus"),
    ("BEL", "Belém"),
    ("FLN", "Florianópolis"),
    ("POA", "Porto Alegre"),
    ("CWB", "Curitiba"),
    ("BSB", "Brasília"),
    ("VIX", "Vitória"),
    ("SDU", "Rio de Janeiro"),
]

# Destinos internacionais (para voos mais baratos às vezes)
DESTINOS_INTERNACIONAIS = [
    ("EZE", "Buenos Aires"),
    ("SCL", "Santiago"),
    ("BOG", "Bogotá"),
    ("LIM", "Lima"),
    ("MVD", "Montevidéu"),
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ─── Tipos ────────────────────────────────────────────────────────────────────
@dataclass
class Passagem:
    origem: str
    destino_code: str
    destino_nome: str
    preco: int
    data_ida: str
    duracao: str
    companhia: str
    link: str


# ─── Histórico (evita spam de alertas repetidos) ──────────────────────────────
def carregar_historico() -> dict:
    if os.path.exists(HISTORICO_FILE):
        with open(HISTORICO_FILE) as f:
            return json.load(f)
    return {}


def salvar_historico(hist: dict):
    with open(HISTORICO_FILE, "w") as f:
        json.dump(hist, f, indent=2)


def ja_alertou(hist: dict, chave: str) -> bool:
    """Retorna True se já mandou alerta para essa passagem hoje."""
    hoje = datetime.now().strftime("%Y-%m-%d")
    return hist.get(chave, {}).get("data") == hoje


def marcar_alerta(hist: dict, chave: str):
    hist[chave] = {"data": datetime.now().strftime("%Y-%m-%d")}


# ─── Telegram ─────────────────────────────────────────────────────────────────
def enviar_telegram(mensagem: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log.warning("⚠️  Token ou Chat ID do Telegram não configurados!")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        log.info("✅ Mensagem enviada no Telegram!")
        return True
    except Exception as e:
        log.error(f"❌ Erro ao enviar Telegram: {e}")
        return False


def montar_mensagem(p: Passagem) -> str:
    emoji_destino = "🌴" if p.destino_code in [d[0] for d in DESTINOS_NACIONAIS] else "🌎"
    return (
        f"✈️ <b>PASSAGEM BARATA ENCONTRADA!</b>\n\n"
        f"{emoji_destino} <b>{p.origem} → {p.destino_nome} ({p.destino_code})</b>\n"
        f"💰 <b>R$ {p.preco:,.0f}</b>\n"
        f"📅 Data: {p.data_ida}\n"
        f"⏱ Duração: {p.duracao}\n"
        f"✈️ Companhia: {p.companhia}\n\n"
        f"🔗 <a href='{p.link}'>Ver no Google Flights</a>\n\n"
        f"<i>Radar rodando desde GRU | Limite: R$ {PRECO_LIMITE}</i>"
    )


# ─── Google Flights via fast-flights ──────────────────────────────────────────
def buscar_passagens(destino_code: str, destino_nome: str, data: str) -> Optional[Passagem]:
    """Busca voo de ida GRU → destino em uma data específica."""
    try:
        filter_ = create_filter(
            flight_data=[
                FlightData(date=data, from_airport=ORIGEM, to_airport=destino_code),
            ],
            trip="one-way",
            seat="economy",
            passengers=Passengers(adults=1),
        )
        result: Result = get_flights(filter_, currency="BRL")

        if not result or not result.flights:
            return None

        # Pega o voo mais barato
        voos = sorted(result.flights, key=lambda f: f.price if f.price else 99999)
        melhor = voos[0]

        if not melhor.price:
            return None

        preco_int = int(melhor.price)
        if preco_int > PRECO_LIMITE:
            return None

        # Monta link do Google Flights
        data_fmt = data.replace("-", "")
        link = (
            f"https://www.google.com/travel/flights?q=Voos+de+"
            f"{ORIGEM}+para+{destino_code}+em+{data}&hl=pt-BR&curr=BRL"
        )

        return Passagem(
            origem=ORIGEM,
            destino_code=destino_code,
            destino_nome=destino_nome,
            preco=preco_int,
            data_ida=data,
            duracao=melhor.duration or "N/A",
            companhia=melhor.name or "N/A",
            link=link,
        )

    except Exception as e:
        log.warning(f"⚠️  Erro ao buscar {ORIGEM}→{destino_code} em {data}: {e}")
        return None


# ─── Main ─────────────────────────────────────────────────────────────────────
def rodar_radar():
    log.info(f"🔍 Iniciando radar | Origem: {ORIGEM} | Limite: R$ {PRECO_LIMITE}")
    hist = carregar_historico()
    encontradas = []

    # Gera datas para buscar (próximos N dias, fins de semana + feriados)
    hoje = datetime.now()
    datas_busca = []
    for i in range(7, DIAS_ANTECEDENCIA + 1):  # começa em 7 dias à frente
        d = hoje + timedelta(days=i)
        # Prioriza sextas, sábados e domingos
        if d.weekday() in (4, 5, 6) or i % 10 == 0:
            datas_busca.append(d.strftime("%Y-%m-%d"))

    destinos = DESTINOS_NACIONAIS + DESTINOS_INTERNACIONAIS
    total = len(destinos) * len(datas_busca)
    log.info(f"📊 Verificando {len(destinos)} destinos × {len(datas_busca)} datas = {total} combinações")

    for idx, (code, nome) in enumerate(destinos):
        for data in datas_busca:
            chave = f"{ORIGEM}-{code}-{data}"
            passagem = buscar_passagens(code, nome, data)

            if passagem:
                log.info(f"🎯 ACHEI! {ORIGEM}→{code} em {data}: R$ {passagem.preco}")
                encontradas.append(passagem)

                if not ja_alertou(hist, chave):
                    msg = montar_mensagem(passagem)
                    if enviar_telegram(msg):
                        marcar_alerta(hist, chave)
                        salvar_historico(hist)
                else:
                    log.info(f"   (já alertado hoje, pulando)")
            else:
                log.debug(f"   {ORIGEM}→{code} em {data}: acima do limite ou sem resultado")

            # Pequena pausa para não sobrecarregar
            time.sleep(1.5)

        # Pausa maior entre destinos
        time.sleep(2)

    # Resumo
    log.info(f"\n{'='*50}")
    log.info(f"✅ Radar finalizado! {len(encontradas)} passagens abaixo de R$ {PRECO_LIMITE}")
    if not encontradas:
        log.info("   Nenhuma passagem barata encontrada agora. Tente novamente mais tarde.")

    # Manda resumo no Telegram (mesmo sem passagens baratas, 1x por dia)
    hoje_str = hoje.strftime("%Y-%m-%d")
    chave_resumo = f"resumo-{hoje_str}"
    if not ja_alertou(hist, chave_resumo) and TELEGRAM_BOT_TOKEN:
        if encontradas:
            resumo = f"📊 <b>Resumo do Radar</b> — {hoje_str}\n\nEncontrei {len(encontradas)} passagens abaixo de R$ {PRECO_LIMITE}! ✈️\nOs alertas individuais já foram enviados acima."
        else:
            resumo = f"📊 <b>Resumo do Radar</b> — {hoje_str}\n\nNenhuma passagem abaixo de R$ {PRECO_LIMITE} encontrada hoje. 😕\nContinuarei monitorando!"
        enviar_telegram(resumo)
        marcar_alerta(hist, chave_resumo)
        salvar_historico(hist)


if __name__ == "__main__":
    rodar_radar()
