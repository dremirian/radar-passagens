#!/usr/bin/env python3
"""
Teste rápido para verificar se o Telegram está configurado corretamente.
Execute: python testar_telegram.py
"""
import os
import requests

TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

if not TOKEN or not CHAT_ID:
    print("❌ Configure as variáveis de ambiente:")
    print("   export TELEGRAM_BOT_TOKEN='seu_token'")
    print("   export TELEGRAM_CHAT_ID='seu_chat_id'")
    exit(1)

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT_ID,
    "text": (
        "✅ <b>Radar de Passagens configurado com sucesso!</b>\n\n"
        "Vou te avisar assim que encontrar passagens baratas saindo de GRU. ✈️"
    ),
    "parse_mode": "HTML",
}

r = requests.post(url, json=payload, timeout=10)
if r.status_code == 200:
    print("✅ Mensagem enviada com sucesso! Verifique seu Telegram.")
else:
    print(f"❌ Erro: {r.status_code} — {r.text}")
