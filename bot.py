#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Bot Key Manager ErZet - Auto Sync
"""

import json
import os
import base64
import datetime
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# ==================== KONFIGURASI ====================
TOKEN = os.environ.get("BOT_TOKEN", "8685035296:AAE63pWz3EFja5PEgWABtQaAaR41D21MUWE")
ADMIN_IDS = [1759242119]

# Gunakan SERVER_TOKEN (bukan GITHUB_TOKEN)
SERVER_TOKEN = os.environ.get("SERVER_TOKEN", "")  # Akan diisi dari GitHub Secrets

# GitHub Configuration
GITHUB_USERNAME = "RyzzXCODING"
GITHUB_REPO = "erzet-key"
GITHUB_FILE = "keylist.json"
GITHUB_BRANCH = "main"

RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{GITHUB_BRANCH}/{GITHUB_FILE}"

# ==================== FUNGSI ====================
def github_api_url():
    return f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{GITHUB_FILE}"

def get_headers():
    return {
        "Authorization": f"token {SERVER_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def fetch_keys():
    """Fetch keys dari server"""
    try:
        if not SERVER_TOKEN:
            # Coba baca dari file lokal
            if os.path.exists("keylist.json"):
                with open("keylist.json", "r") as f:
                    data = json.load(f)
                    return data.get("keys", {}), "local"
            return {}, None
        
        response = requests.get(github_api_url(), headers=get_headers())
        if response.status_code == 200:
            data = response.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            keys_data = json.loads(content)
            return keys_data.get("keys", {}), data["sha"]
        return {}, None
    except Exception as e:
        print(f"Error: {e}")
        return {}, None

def push_keys(keys, sha=None):
    """Push keys ke server"""
    try:
        if not SERVER_TOKEN:
            # Simpan ke file lokal
            data = {"keys": keys}
            with open("keylist.json", "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        
        data = {
            "version": "1.0.0",
            "bot_name": "ErZet Key Manager",
            "owner": "ErZet",
            "keys": keys
        }
        
        content = json.dumps(data, indent=2, ensure_ascii=False)
        content_base64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": f"Update: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": content_base64,
            "branch": GITHUB_BRANCH
        }
        
        if sha and sha != "local":
            payload["sha"] = sha
        
        response = requests.put(github_api_url(), headers=get_headers(), json=payload)
        
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"Push failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def generate_key(prefix="VIP-USER"):
    """Generate key"""
    keys, sha = fetch_keys()
    counter = len(keys) + 1
    key = f"{prefix}-{counter:03d}"
    return key, keys, sha

# ==================== HANDLERS ====================
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    
    if user.id in ADMIN_IDS:
        token_status = "✅ SET" if SERVER_TOKEN else "⚠️ LOKAL"
        msg = (
            "👋 Ada yang bisa saya bantu tuan ErZet?\n\n"
            "🔐 KEY MANAGER BOT\n"
            f"📊 Server Token: {token_status}\n\n"
            "/genkey <hari> - Generate key\n"
            "/listkeys - List keys\n"
            "/check <key> - Cek key\n"
            "/ban <key> - Ban key\n"
            "/unban <key> - Unban key\n"
            "/delkey <key> - Hapus key"
        )
    else:
        msg = f"👋 Halo {user.first_name}!\n\n/check <key> - Cek key"
    
    await update.message.reply_text(msg)

async def genkey(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Anda bukan admin!")
        return
    
    args = context.args
    days = int(args[0]) if args else 7
    
    loading_msg = await update.message.reply_text("🔄 Generating...")
    
    key, keys, sha = generate_key()
    
    if not sha:
        await loading_msg.edit_text("❌ Gagal fetch keys!")
        return
    
    expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
    
    keys[key] = {
        "expiry": expiry,
        "active": True,
        "device": None,
        "created": datetime.datetime.now().isoformat()
    }
    
    success = push_keys(keys, sha)
    
    if success:
        await loading_msg.edit_text(
            f"✅ KEY DIGENERATE!\n\n"
            f"🔑 Key: {key}\n"
            f"⏰ Expired: {expiry}\n"
            f"📅 Durasi: {days} hari"
        )
    else:
        await loading_msg.edit_text(f"❌ GAGAL PUSH!\n🔑 Key: {key}")

async def listkeys(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    keys, sha = fetch_keys()
    
    if not sha:
        await update.message.reply_text("❌ Gagal terhubung!")
        return
    
    if not keys:
        await update.message.reply_text("📭 Belum ada key.")
        return
    
    msg = "📋 KEYS\n\n"
    for k, v in keys.items():
        status = "✅" if v.get("active", True) else "🚫"
        msg += f"{status} {k}\n"
    
    await update.message.reply_text(msg)

async def check(update: Update, context: CallbackContext):
    args = context.args
    if not args:
        return
    
    key = args[0].upper()
    keys, sha = fetch_keys()
    
    if not sha:
        await update.message.reply_text("❌ Gagal terhubung!")
        return
    
    if key not in keys:
        await update.message.reply_text(f"❌ {key} TIDAK TERDAFTAR!")
        return
    
    key_data = keys[key]
    
    if not key_data.get("active", True):
        await update.message.reply_text(f"🚫 {key} DIBLOKIR!")
        return
    
    expiry = datetime.datetime.fromisoformat(key_data["expiry"])
    now = datetime.datetime.now()
    remaining = expiry - now
    
    if remaining.total_seconds() > 0:
        days = remaining.days
        hours = remaining.seconds // 3600
        await update.message.reply_text(f"✅ VALID!\n🔑 {key}\n⏳ {days} hari {hours} jam")
    else:
        await update.message.reply_text(f"❌ EXPIRED!\n🔑 {key}")

async def ban(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    args = context.args
    if not args:
        return
    
    key = args[0].upper()
    keys, sha = fetch_keys()
    
    if not sha:
        await update.message.reply_text("❌ Gagal terhubung!")
        return
    
    if key in keys:
        keys[key]["active"] = False
        if push_keys(keys, sha):
            await update.message.reply_text(f"🚫 {key} DIBLOKIR! Synced!")
        else:
            await update.message.reply_text(f"🚫 {key} DIBLOKIR!")

async def unban(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    args = context.args
    if not args:
        return
    
    key = args[0].upper()
    keys, sha = fetch_keys()
    
    if not sha:
        await update.message.reply_text("❌ Gagal terhubung!")
        return
    
    if key in keys:
        keys[key]["active"] = True
        if push_keys(keys, sha):
            await update.message.reply_text(f"✅ {key} diaktifkan! Synced!")
        else:
            await update.message.reply_text(f"✅ {key} diaktifkan!")

async def delkey(update: Update, context: CallbackContext):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    args = context.args
    if not args:
        return
    
    key = args[0].upper()
    keys, sha = fetch_keys()
    
    if not sha:
        await update.message.reply_text("❌ Gagal terhubung!")
        return
    
    if key in keys:
        del keys[key]
        if push_keys(keys, sha):
            await update.message.reply_text(f"✅ {key} dihapus! Synced!")
        else:
            await update.message.reply_text(f"✅ {key} dihapus!")

def main():
    print("=" * 50)
    print("🤖 BOT KEY MANAGER ERZET")
    print("=" * 50)
    print(f"🌐 Server: {RAW_URL}")
    print(f"🔑 Token: {'SET' if SERVER_TOKEN else 'LOKAL MODE'}")
    print()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("listkeys", listkeys))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("delkey", delkey))
    
    print("✅ Bot berjalan...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
