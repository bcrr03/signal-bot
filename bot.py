

@app.route("/send-update", methods=["POST"])
def handle_update():
    data = request.json
    init_data = data.get("initData", "")

    if not verify_telegram_data(init_data):
        return jsonify({"ok": False, "error": "Unauthorized"}), 403

    user_id = get_user_id_from_init_data(init_data)
    if user_id not in ADMIN_IDS:
        return jsonify({"ok": False, "error": "Not an admin"}), 403

    level = data.get("level", "")
    value = data.get("value", "")

    if not level or not value:
        return jsonify({"ok": False, "error": "Missing level or value"}), 400

    text = (
        f"✏️ <b>UPDATE</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"• {level}: <b>{value}</b>"
    )

    ok, tg_response = send_signal(text)
    return jsonify({"ok": ok, "tg": tg_response})
