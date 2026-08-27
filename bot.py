#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Bot Key Manager ErZet - Auto Push ke GitHub
"""

import json
import os
import base64
import datetime
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# ==================== KONFIGURASI ====================
TOKEN = "8685035296:AAE63pWz3EFja5PEgWABtQaAaR41D21MUWE"
ADMIN_IDS = [1759242119]

# GitHub Configuration
GITHUB_TOKEN = "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"
GITHUB_REPO = "RyzzXCODING/erzet_key"
GITHUB_FILE = "keylist.json"
GITHUB_BRANCH = "main"

# Raw URL untuk sync
RAW_URL = "https://raw.githubusercontent.com/RyzzXCODING/erzet_key/refs/heads/main/keylist.json"

# ==================== FUNGSI GITHUB ====================
def github_api_url():
    return f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"

def get_github_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def fetch_keys_from_github():
    """AMBIL keys dari GitHub"""
    try:
        response = requests.get(github_api_url(), headers=get_github_headers())
        if response.status_code == 200:
            data = response.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            keys_data = json.loads(content)
            return keys_data.get("keys", {}), data["sha"]
        return {}, None
    except Exception as e:
        print(f"Error fetching: {e}")
        return {}, None

def push_keys_to_github(keys, sha=None):
    """PUSH keys ke GitHub"""
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
            print("✅ Keys berhasil di-push ke GitHub!")
            return True
        else:
            print(f"❌ Gagal push: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def generate_key(prefix="VIP-USER"):
    """GENERATE key baru"""
    keys, sha = fetch_keys_from_github()
    counter = len(keys) + 1
    key = f"{prefix}-{counter:03d}"
    return key, keys, sha

# ==================== HANDLERS ====================
async def start(update: Update, context: CallbackContext):
    """Handler /start"""
    user = update.effective_user
    
    if user.id in ADMIN_IDS:
        msg = (
            "👋 Ada yang bisa saya bantu tuan ErZet?\n\n"
            "🔐 KEY MANAGER BOT (Auto Sync GitHub)\n\n"
            "📋 PERINTAH:\n"
            "/genkey <hari> - Generate key + sync\n"
            "/delkey <key> - Hapus key + sync\n"
            "/listkeys - List keys dari GitHub\n"
            "/check <key> - Cek key\n"
            "/ban <key> - Ban key + sync\n"
            "/unban <key> - Unban key + sync\n"
            "/sync - Sync manual ke GitHub\n\n"
            "🔗 Server: " + RAW_URL
        )
    else:
        msg = (
            f"👋 Halo {user.first_name}!\n\n"
            "/check <key> - Cek status key"
        )
    
    await update.message.reply_text(msg)

async def genkey(update: Update, context: CallbackContext):
    """Generate key + auto push ke GitHub"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Anda bukan admin!")
        return
    
    args = context.args
    days = int(args[0]) if args else 7
    
    loading_msg = await update.message.reply_text("🔄 Generating key...")
    
    # Fetch keys dari GitHub
    await loading_msg.edit_text("📥 Fetching keys dari GitHub...")
    key, keys, sha = generate_key()
    
    # Buat expiry
    expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
    
    # Tambah key baru
    keys[key] = {
        "expiry": expiry,
        "active": True,
        "device": None,
        "created": datetime.datetime.now().isoformat()
    }
    
    # Push ke GitHub
    await loading_msg.edit_text("📤 Pushing ke GitHub...")
    success = push_keys_to_github(keys, sha)
    
    if success:
        await loading_msg.edit_text(
            f"✅ KEY DIGENERATE & ADDED TO SERVER!\n\n"
            f"🔑 Key: {key}\n"
            f"⏰ Expired: {expiry}\n"
            f"📅 Durasi: {days} hari\n"
            f"🌐 Server: GitHub\n"
            f"📊 Total keys: {len(keys)}\n\n"
            f"✅ Key sudah aktif dan bisa digunakan!"
        )
    else:
        await loading_msg.edit_text(
            f"⚠️ KEY DIGENERATE (LOKAL)\n\n"
            f"🔑 Key: {key}\n"
            f"❌ Gagal push ke GitHub!\n"
            f"Periksa GITHUB_TOKEN Anda."
        )

async def ban(update: Update, context: CallbackContext):
    """Ban key + auto push"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Anda bukan admin!")
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
    else:
        await loading_msg.edit_text(f"🚫 Key {key} diblokir (lokal)!")

async def unban(update: Update, context: CallbackContext):
    """Unban key + auto push"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    args = context.args
    if not args:
        await update.message.reply_text("❌ Gunakan: /unban <KEY>")
        return
    
    key = args[0].upper()
    loading_msg = await update.message.reply_text("🔄 Unbanning key...")
    
    keys, sha = fetch_keys_from_github()
    
    if key not in keys:
        await loading_msg.edit_text(f"❌ Key {key} tidak ditemukan!")
        return
    
    keys[key]["active"] = True
    keys[key]["unbanned_at"] = datetime.datetime.now().isoformat()
    
    success = push_keys_to_github(keys, sha)
    
    if success:
        await loading_msg.edit_text(f"✅ Key {key} diaktifkan! Synced to GitHub!")
    else:
        await loading_msg.edit_text(f"✅ Key {key} diaktifkan (lokal)!")

async def delkey(update: Update, context: CallbackContext):
    """Hapus key + auto push"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    args = context.args
    if not args:
        await update.message.reply_text("❌ Gunakan: /delkey <KEY>")
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
    else:
        await loading_msg.edit_text(f"✅ Key {key} dihapus (lokal)!")

async def listkeys(update: Update, context: CallbackContext):
    """List keys dari GitHub"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    loading_msg = await update.message.reply_text("🔄 Fetching keys dari GitHub...")
    
    keys, sha = fetch_keys_from_github()
    
    if not keys:
        await loading_msg.edit_text("📭 Belum ada key di server GitHub.")
        return
    
    msg = f"📋 KEYS DI SERVER GITHUB\n📊 Total: {len(keys)}\n\n"
    for k, v in keys.items():
        status = "✅" if v.get("active", True) else "🚫"
        expiry = v.get("expiry", "N/A")
        msg += f"{status} {k}\n  ⏰ {expiry}\n\n"
    
    await loading_msg.edit_text(msg)

async def check(update: Update, context: CallbackContext):
    """Cek key dari GitHub"""
    args = context.args
    if not args:
        await update.message.reply_text("❌ Gunakan: /check <KEY>")
        return
    
    key = args[0].upper()
    loading_msg = await update.message.reply_text("🔄 Checking key...")
    
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
        await loading_msg.edit_text(
            f"✅ VALID!\n"
            f"🔑 {key}\n"
            f"⏰ Expired: {key_data['expiry']}\n"
            f"⏳ Sisa: {days} hari {hours} jam"
        )
    else:
        await loading_msg.edit_text(f"❌ EXPIRED!\n🔑 {key}")

async def sync_cmd(update: Update, context: CallbackContext):
    """Sync manual"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    loading_msg = await update.message.reply_text("🔄 Syncing...")
    
    keys, sha = fetch_keys_from_github()
    
    if sha:
        await loading_msg.edit_text(f"✅ Sync berhasil! Total: {len(keys)} keys")
    else:
        await loading_msg.edit_text("❌ Gagal sync!")

# ==================== MAIN ====================
def main():
    print("=" * 50)
    print("🤖 BOT KEY MANAGER ERZET")
    print("=" * 50)
    print(f"🔗 Server: {RAW_URL}")
    
    # Test koneksi GitHub
    print("\nTesting koneksi GitHub...")
    keys, sha = fetch_keys_from_github()
    if sha:
        print(f"✅ Terhubung ke GitHub!")
        print(f"📊 Total keys: {len(keys)}")
    else:
        print("⚠️ Gagal terhubung ke GitHub!")
        print("Periksa GITHUB_TOKEN dan nama repo!")
    
    print()
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("delkey", delkey))
    app.add_handler(CommandHandler("listkeys", listkeys))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("sync", sync_cmd))
    
    print("✅ Bot berjalan...")
    print("Tekan Ctrl+C untuk berhenti")
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
