import os
import json
import hmac
import hashlib
import requests
from urllib.parse import unquote, parse_qsl
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
SIGNAL_GROUP_ID = os.environ.get("SIGNAL_GROUP_ID")
ADMIN_IDS = set(os.environ.get("ADMIN_IDS", "").split(","))


def verify_telegram_data(init_data: str) -> bool:
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop("hash", None)
        if not received_hash:
            return False
        data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        computed = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, received_hash)
    except Exception:
        return False


def get_user_id_from_init_data(init_data: str) -> str | None:
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        user = json.loads(unquote(parsed.get("user", "{}")))
        return str(user.get("id"))
    except Exception:
        return None


def send_signal(text: str) -> bool:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": SIGNAL_GROUP_ID,
        "text": text,
        "parse_mode": "HTML"
    })
    return resp.ok


@app.route("/send-signal", methods=["POST"])
def handle_signal():
    data = request.json
    init_data = data.get("initData", "")

    if not verify_telegram_data(init_data):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    user_id = get_user_id_from_init_data(init_data)
    if user_id not in ADMIN_IDS:
        return jsonify({"ok": False, "error": "Not an admin"}), 403

    signal_type = data.get("type")
    pair = data.get("pair", "XAUUSD")

    if signal_type in ("BUY NOW", "SELL NOW"):
        tp1 = data.get("tp1", "")
        tp2 = data.get("tp2", "")
        tp3 = data.get("tp3", "")
        sl  = data.get("sl", "")
        emoji = "🟢" if signal_type == "BUY NOW" else "🔴"
        text = (
            f"{emoji} <b>{signal_type} {pair}</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"• TP1: <b>{tp1}</b>\n"
            f"• TP2: <b>{tp2}</b>\n"
            f"• TP3: <b>{tp3}</b>\n"
            f"• SL:  <b>{sl}</b>"
        )

    elif signal_type in ("BUY ZONE", "SELL ZONE"):
        zone_low  = data.get("zone_low", "")
        zone_high = data.get("zone_high", "")
        tp1 = data.get("tp1", "")
        tp2 = data.get("tp2", "")
        tp3 = data.get("tp3", "")
        sl  = data.get("sl", "")
        emoji = "🟢" if signal_type == "BUY ZONE" else "🔴"
        text = (
            f"{emoji} <b>{signal_type} {pair}</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"• Zone: <b>{zone_low} – {zone_high}</b>\n"
            f"• TP1: <b>{tp1}</b>\n"
            f"• TP2: <b>{tp2}</b>\n"
            f"• TP3: <b>{tp3}</b>\n"
            f"• SL:  <b>{sl}</b>"
        )
    else:
        return jsonify({"ok": False, "error": "Unknown signal type"}), 400

    ok = send_signal(text)
    return jsonify({"ok": ok})


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
