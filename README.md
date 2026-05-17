# ✈️ Radar de Passagens Aéreas → Telegram

Monitora o Google Flights automaticamente e manda alertas no Telegram quando encontrar passagens baratas saindo de GRU.

## 🚀 Como configurar (passo a passo)

### 1. Criar o Bot do Telegram

1. Abra o Telegram e busque por **@BotFather**
2. Mande `/newbot`
3. Escolha um nome (ex: `Radar Passagens`)
4. Escolha um username (ex: `meu_radar_passagens_bot`)
5. O BotFather vai te dar um **token** — guarde esse token! Parece assim:
   ```
   7123456789:AAHdqTcvCHhvQEKHEKJEJE123456789abcde
   ```

### 2. Pegar seu Chat ID

1. Mande qualquer mensagem para o bot que você criou
2. Acesse no navegador (troque pelo seu token):
   ```
   https://api.telegram.org/bot<SEU_TOKEN>/getUpdates
   ```
3. Procure por `"chat":{"id":` — esse número é seu **Chat ID**
   - Se for negativo (ex: `-123456789`) é um grupo
   - Se for positivo (ex: `123456789`) é você mesmo

### 3. Criar repositório no GitHub

1. Crie uma conta em [github.com](https://github.com) se não tiver
2. Clique em **New repository** → nomeie como `radar-passagens`
3. Marque como **Private** (para proteger seus tokens)
4. Faça upload de todos os arquivos deste projeto

### 4. Configurar os Secrets no GitHub

No seu repositório → **Settings** → **Secrets and variables** → **Actions**:

#### Secrets (informações sensíveis):
| Nome | Valor |
|------|-------|
| `TELEGRAM_BOT_TOKEN` | Token do BotFather (ex: `7123...abcde`) |
| `TELEGRAM_CHAT_ID` | Seu Chat ID (ex: `123456789`) |

#### Variables (configurações):
| Nome | Valor padrão | Descrição |
|------|-------------|-----------|
| `PRECO_LIMITE` | `800` | Preço máximo em R$ para alertar |
| `ORIGEM` | `GRU` | Código IATA do aeroporto de origem |
| `DIAS_ANTECEDENCIA` | `30` | Quantos dias à frente buscar |

### 5. Ativar o GitHub Actions

1. Vá em **Actions** no seu repositório
2. Se pedir para ativar, clique em **I understand my workflows, go ahead and enable them**
3. O radar vai rodar automaticamente 4x por dia (00h, 6h, 12h, 18h — horário de Brasília)

### 6. Testar manualmente

Em **Actions** → **✈️ Radar de Passagens** → **Run workflow** → **Run workflow**

---

## 🛠️ Personalizar

### Mudar destinos monitorados

Edite o arquivo `radar.py` e altere as listas:
```python
DESTINOS_NACIONAIS = [
    ("FOR", "Fortaleza"),
    ("REC", "Recife"),
    # Adicione ou remova destinos aqui
]
```

### Mudar frequência de verificação

Edite `.github/workflows/radar.yml`:
```yaml
- cron: "0 3,9,15,21 * * *"  # UTC (= BRT + 3h)
```

Para rodar a cada 2 horas: `0 */2 * * *`

### Rodar localmente

```bash
pip install -r requirements.txt

export TELEGRAM_BOT_TOKEN="seu_token"
export TELEGRAM_CHAT_ID="seu_chat_id"
export PRECO_LIMITE="600"

python radar.py
```

---

## 📱 Exemplo de alerta no Telegram

```
✈️ PASSAGEM BARATA ENCONTRADA!

🌴 GRU → Fortaleza (FOR)
💰 R$ 349
📅 Data: 2025-08-15
⏱ Duração: 3h 20min
✈️ Companhia: LATAM

🔗 Ver no Google Flights
```

---

## ⚠️ Avisos

- O script usa a biblioteca `fast-flights` que faz scraping do Google Flights — pode parar de funcionar se o Google mudar o layout
- O GitHub Actions gratuito tem 2.000 minutos/mês — 4 execuções por dia × ~5 min = ~600 min/mês (dentro do limite)
- Histórico de alertas é salvo via cache do GitHub Actions para evitar spam

---

## 🆓 Custo total: R$ 0,00

| Serviço | Custo |
|---------|-------|
| GitHub Actions | Gratuito (até 2.000 min/mês) |
| Telegram Bot | Gratuito |
| Google Flights (scraping) | Gratuito |
