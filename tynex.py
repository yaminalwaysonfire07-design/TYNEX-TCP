# ═══════════════════════════════════════════════════════════════
# app.py — ENTRY POINT (Render/Heroku ready)
# Dev: @YaminOnFire07 | TG: https://t.me/MrTripleR_YT0
# ═══════════════════════════════════════════════════════════════

import os
import threading
import asyncio
import base64
import zlib

from flask import Flask
from cfonts import render

import login_engine
import bot_core
from bot_core import (
    TcPOnLine,
    TcPChaT,
    build_ob55_online_auth,
    create_auth_token_chat,
)

# ─── Config ───
PORT = int(os.environ.get("PORT", 10000))

# Render/Heroku-তে environment variable দিয়ে দিন।
# Local test-এর জন্য ডিফল্ট fallback আছে (কিন্তু production-এ env var ব্যবহার করুন)।
UID        = os.environ.get("GUEST_UID", "7974957713")
PW         = os.environ.get(
    "GUEST_PW",
    "30E3665C6ED59B64AEB25E520C02CA2B842FE91F00C86A8F6F02487FDE6517A5",
)
REGION_PREF = os.environ.get("REGION", "BD")

app = Flask(__name__)

_ENCRYPTED_BANNER = "eJwVzMEJwjAQRNFe9jzF9wQJ2YDeQdJeQhJnY4ySXn8S5vBg3sx8Zw/P5R6Vx2xT29lr6CzVrZZMXKOlGUdsxAXVlLqQWadKccyt0u4ibZaVf/CyEKVZpOnU2NoQOxA8RjW7n9E6hSJz0kl1XKvvK0TdMj/HUmsZMOaMzCkU+1oWWaDzhS3fXlO5NpG3b/Fz7R8=" 
def _get_banner():
    try:
        # Decode kore original text ber kora hocche
        return zlib.decompress(base64.b64decode(_ENCRYPTED_BANNER)).decode('utf-8')
    except:
        return "TYNEX TCP" # Fallback jodi decode fail kore

# ───────────────────────────────────────────────────────────────
# Bot Core
# ───────────────────────────────────────────────────────────────
async def MaiiiinE():
    """Login + TCP start (একবার চলবে, শেষে return করবে)"""
    print("[*] Starting login...")
    result = await login_engine.do_login(UID, PW, REGION_PREF)
    if not result:
        print("[-] Login failed, retry in 10s...")
        await asyncio.sleep(10)
        return

    # bot_core-এর globals set করো
    bot_core.bot_uid = result["bot_uid"]
    bot_core.ToKen   = result["token"]
    bot_core.region  = result["region"]

    key       = result["key"]
    iv        = result["iv"]
    timestamp = result["timestamp"]
    online_ip = result["online_ip"]
    online_port = result["online_port"]
    chat_ip   = result["chat_ip"]
    chat_port = result["chat_port"]
    acc_name  = result["account_name"]

    print(f"[+] UID: {result['bot_uid']} | Region: {result['region']} | Name: {acc_name}")

    # Auth tokens
    ChatAutH = create_auth_token_chat(
        int(result["bot_uid"]), result["token"], int(timestamp), key, iv
    )
    OnlineAutH, _ = build_ob55_online_auth(
        int(result["bot_uid"]), result["token"], int(timestamp), key, iv
    )

    # TCP tasks start
    ready_event = asyncio.Event()
    t1 = asyncio.create_task(
        TcPChaT(chat_ip, chat_port, ChatAutH, key, iv, ready_event, result["region"])
    )
    await ready_event.wait()
    await asyncio.sleep(1)
    t2 = asyncio.create_task(
        TcPOnLine(online_ip, online_port, key, iv, OnlineAutH)
    )

    # Banner print
    print("\n")
    try:
        banner_text = _get_banner() # Hidden text theke ber korche
        print(render(banner_text, colors=['red', 'yellow'], align='center'))
    except Exception:
        print("====== TYNEX TCP ======")

    print(f" - Region => {result['region']}")
    print(f" - Bot Online! UID: {result['bot_uid']} | Name: {acc_name}")
    print(f" - Dev: @YaminOnFire07 | TG: https://t.me/MrTripleR_YT0\n")

    # Forever run until any task dies / timeout / error
    await asyncio.gather(t1, t2)


async def StarTinG():
    """Auto-restart loop (প্রতি ৭ ঘণ্টায় token refresh)"""
    while True:
        try:
            await asyncio.wait_for(MaiiiinE(), timeout=7 * 60 * 60)
        except asyncio.TimeoutError:
            print("[!] Token expired, restarting...")
        except asyncio.CancelledError:
            # graceful shutdown
            print("[!] Bot loop cancelled, exiting...")
            raise
        except Exception as e:
            print(f"[!] Error: {e} -> Restarting in 5s...")
            await asyncio.sleep(5)


# ───────────────────────────────────────────────────────────────
# Flask (Render health-check এর জন্য)
# ───────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return "Bot is active and running successfully!"


@app.route("/healthz")
def healthz():
    return {"status": "ok"}, 200


def run_web():
    print(f"[*] Flask listening on 0.0.0.0:{PORT}")
    app.run(
        host="0.0.0.0",
        port=PORT,
        use_reloader=False,   # duplicate process এড়াতে
        threaded=True,
    )


# ───────────────────────────────────────────────────────────────
# Entry
# ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # 1) Flask কে daemon thread-এ চালাও → PORT bind হবে → Render happy
    threading.Thread(target=run_web, daemon=True).start()

    # 2) asyncio bot loop main thread-এ (এটাই আসল কাজ)
    try:
        asyncio.run(StarTinG())
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user. Bot Stopped.")