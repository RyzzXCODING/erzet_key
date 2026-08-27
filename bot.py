#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Bot Key Manager ErZet - Auto Sync ke GitHub
"""

import json
import os
import base64
import datetime
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# ==================== KONFIGURASI ====================
TOKEN = "8932986825:AAFRi7x72nGw1XF326jgwCouT9VmBjoAbIw"
ADMIN_IDS = [1759242119]

# GitHub Configuration
GITHUB_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxxxxxx"  # GANTI dengan token GitHub Anda
GITHUB_REPO = "RyzzXCODING/erzet_key"  # GANTI dengan username/repo Anda
GITHUB_FILE = "keylist.json"
GITHUB_BRANCH = "main"

# ==================== FUNGSI GITHUB ====================
def github_api_url():
    return f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"

def get_github_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def fetch_keys_from_github():
    """Fetch keys dari GitHub"""
    try:
        response = requests.get(github_api_url(), headers=get_github_headers())
        if response.status_code == 200:
            content = base64.b64decode(response.json()["content"]).decode("utf-8")
            data = json.loads(content)
            return data.get("keys", {}), response.json()["sha"]
        return {}, None
    except Exception as e:
        print(f"Error fetching: {e}")
        return {}, None

def push_keys_to_github(keys, sha=None):
    """Push keys ke GitHub"""
    try:
        data = {
            "version": "1.0.0",
            "bot_name": "ErZet Key Manager",
            "owner": "ErZet",
            "keys": keys
        }
        
        content = json.dumps(data, indent=2, ensure_ascii=False)
        content_base64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": f"Update keys: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": content_base64,
            "branch": GITHUB_BRANCH
        }
        
        if sha:
            payload["sha"] = sha
        
        response = requests.put(github_api_url(), headers=get_github_headers(), json=payload)
        
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"Error pushing: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def generate_key(prefix="VIP-USER"):
    """Generate key"""
    keys, sha = fetch_keys_from_github()
    counter = len(keys) + 1
    return f"{prefix}-{counter:03d}", keys, sha

# ==================== HANDLERS ====================
async def start(update: Update, context: CallbackContext):
    """Handler /start"""
    user = update.effective_user
    if user.id in ADMIN_IDS:
        msg = (
            "👋 Ada yang bisa saya bantu tuan ErZet?\n\n"
            "🔐 KEY MANAGER BOT (Auto Sync GitHub)\n\n"
            "/genkey <hari> - Generate key + sync\n"
            "/delkey <key> - Hapus key + sync\n"
            "/listkeys - List keys dari GitHub\n"
            "/check <key> - Cek key\n"
            "/ban <key> - Ban key + sync\n"
            "/unban <key> - Unban key + sync"
        )
    else:
        msg = f"👋 Halo {user.first_name}!\n\n/check <key> - Cek key"
    await update.message.reply_text(msg)

async def genkey(update: Update, context: CallbackContext):
    """Generate key dan auto push ke GitHub"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Anda bukan admin!")
        return
    
    args = context.args
    days = int(args[0]) if args else 7
    
    loading_msg = await update.message.reply_text("🔄 Generating key...")
    
    key, keys, sha = generate_key()
    expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
    
    keys[key] = {
        "expiry": expiry,
        "active": True,
        "device": None,
        "created": datetime.datetime.now().isoformat()
    }
    
    await loading_msg.edit_text("📤 Syncing ke GitHub...")
    success = push_keys_to_github(keys, sha)
    
    if success:
        await loading_msg.edit_text(
            f"✅ KEY DIGENERATE & SYNCED!\n\n"
            f"🔑 Key: {key}\n"
            f"⏰ Expired: {expiry}\n"
            f"📅 Durasi: {days} hari\n"
            f"🌐 Status: Synced to GitHub"
        )
    else:
        await loading_msg.edit_text(
            f"✅ KEY DIGENERATE!\n"
            f"🔑 Key: {key}\n"
            f"❌ Gagal sync ke GitHub!"
        )

async def ban(update: Update, context: CallbackContext):
    """Ban key dan auto push ke GitHub"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    args = context.args
    if not args:
        await update.message.reply_text("❌ Gunakan: /ban <KEY>")
        return
    
    key = args[0].upper()
    loading_msg = await update.message.reply_text("🔄 Banning key...")
    
    keys, sha = fetch_keys_from_github()
    
    if key not in keys:
        await loading_msg.edit_text(f"❌ Key {key} tidak ditemukan!")
        return
    
    keys[key]["active"] = False
    keys[key]["banned_at"] = datetime.datetime.now().isoformat()
    
    success = push_keys_to_github(keys, sha)
    
    if success:
        await loading_msg.edit_text(
            f"🚫 KEY DIBLOKIR!\n\n"
            f"🔑 Key: {key}\n"
            f"🌐 Status: Synced to GitHub\n"
            f"❌ Key tidak akan berfungsi lagi!"
        )

async def unban(update: Update, context: CallbackContext):
    """Unban key"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    args = context.args
    if not args:
        return
    
    key = args[0].upper()
    loading_msg = await update.message.reply_text("🔄 Unbanning key...")
    
    keys, sha = fetch_keys_from_github()
    
    if key not in keys:
        await loading_msg.edit_text(f"❌ Key {key} tidak ditemukan!")
        return
    
    keys[key]["active"] = True
    success = push_keys_to_github(keys, sha)
    
    if success:
        await loading_msg.edit_text(f"✅ Key {key} diaktifkan! Synced to GitHub!")

async def delkey(update: Update, context: CallbackContext):
    """Hapus key"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    args = context.args
    if not args:
        return
    
    key = args[0].upper()
    loading_msg = await update.message.reply_text("🔄 Deleting key...")
    
    keys, sha = fetch_keys_from_github()
    
    if key not in keys:
        await loading_msg.edit_text(f"❌ Key {key} tidak ditemukan!")
        return
    
    del keys[key]
    success = push_keys_to_github(keys, sha)
    
    if success:
        await loading_msg.edit_text(f"✅ Key {key} dihapus dari GitHub!")

async def listkeys(update: Update, context: CallbackContext):
    """List keys dari GitHub"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    loading_msg = await update.message.reply_text("🔄 Fetching keys...")
    
    keys, sha = fetch_keys_from_github()
    
    if not keys:
        await loading_msg.edit_text("📭 Belum ada key di GitHub.")
        return
    
    msg = "📋 KEYS (GitHub)\n\n"
    for k, v in keys.items():
        status = "✅" if v.get("active", True) else "🚫"
        msg += f"{status} {k}\n"
    
    await loading_msg.edit_text(msg)

async def check(update: Update, context: CallbackContext):
    """Cek key"""
    args = context.args
    if not args:
        return
    
    key = args[0].upper()
    loading_msg = await update.message.reply_text("🔄 Checking...")
    
    keys, sha = fetch_keys_from_github()
    
    if key not in keys:
        await loading_msg.edit_text(f"❌ {key} TIDAK TERDAFTAR!")
        return
    
    key_data = keys[key]
    
    if not key_data.get("active", True):
        await loading_msg.edit_text(f"🚫 {key} DIBLOKIR!")
        return
    
    expiry = datetime.datetime.fromisoformat(key_data["expiry"])
    now = datetime.datetime.now()
    remaining = expiry - now
    
    if remaining.total_seconds() > 0:
        days = remaining.days
        hours = remaining.seconds // 3600
        await loading_msg.edit_text(f"✅ VALID!\n🔑 {key}\n⏳ Sisa: {days} hari {hours} jam")
    else:
        await loading_msg.edit_text(f"❌ EXPIRED!\n🔑 {key}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("delkey", delkey))
    app.add_handler(CommandHandler("listkeys", listkeys))
    app.add_handler(CommandHandler("check", check))
    print("🤖 Bot berjalan...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()