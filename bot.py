#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Bot Key Manager ErZet - Manual GitHub Token Input
"""

import json
import os
import base64
import datetime
import requests
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackContext, 
    MessageHandler, 
    filters,
    ConversationHandler
)

# ==================== KONFIGURASI ====================
TOKEN = "8685035296:AAE63pWz3EFja5PEgWABtQaAaR41D21MUWE"
ADMIN_IDS = [1759242119]

# Conversation States
(
    ASK_GITHUB_TOKEN,
    ASK_GITHUB_REPO,
    CONFIRM_SETTINGS
) = range(3)

# ==================== STORAGE ====================
CONFIG_FILE = "github_config.json"

def load_github_config():
    """Load konfigurasi GitHub dari file"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {
        "github_token": "",
        "github_username": "RyzzXCODING",
        "github_repo": "erzet-key",
        "github_file": "keylist.json",
        "github_branch": "main"
    }

def save_github_config(config):
    """Save konfigurasi GitHub"""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except:
        return False

# Global config
github_config = load_github_config()

# ==================== FUNGSI GITHUB ====================
def github_api_url():
    return f"https://api.github.com/repos/{github_config['github_username']}/{github_config['github_repo']}/contents/{github_config['github_file']}"

def get_github_headers():
    return {
        "Authorization": f"token {github_config['github_token']}",
        "Accept": "application/vnd.github.v3+json"
    }

def get_raw_url():
    return f"https://raw.githubusercontent.com/{github_config['github_username']}/{github_config['github_repo']}/{github_config['github_branch']}/{github_config['github_file']}"

def test_github():
    """Test koneksi GitHub"""
    if not github_config["github_token"]:
        return False, "Token GitHub belum di-set!"
    
    try:
        # Cek repository
        response = requests.get(
            f"https://api.github.com/repos/{github_config['github_username']}/{github_config['github_repo']}",
            headers=get_github_headers()
        )
        
        if response.status_code == 401:
            return False, "Token GitHub TIDAK VALID!"
        elif response.status_code == 404:
            return False, f"Repository '{github_config['github_username']}/{github_config['github_repo']}' TIDAK ADA!"
        
        # Cek file
        response = requests.get(github_api_url(), headers=get_github_headers())
        
        if response.status_code == 404:
            return False, f"File '{github_config['github_file']}' TIDAK ADA di repository!"
        elif response.status_code == 200:
            return True, "Koneksi GitHub BERHASIL!"
        else:
            return False, f"Error: {response.status_code}"
            
    except Exception as e:
        return False, f"Error: {str(e)[:100]}"

def fetch_keys_from_github():
    """Ambil keys dari GitHub"""
    try:
        response = requests.get(github_api_url(), headers=get_github_headers())
        if response.status_code == 200:
            data = response.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            keys_data = json.loads(content)
            return keys_data.get("keys", {}), data["sha"]
        return {}, None
    except:
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
            "branch": github_config["github_branch"]
        }
        
        if sha:
            payload["sha"] = sha
        
        response = requests.put(github_api_url(), headers=get_github_headers(), json=payload)
        
        if response.status_code in [200, 201]:
            return True, "Berhasil push!"
        else:
            return False, f"Gagal push: {response.status_code}"
    except Exception as e:
        return False, f"Error: {str(e)[:100]}"

def generate_key(prefix="VIP-USER"):
    """Generate key"""
    keys, sha = fetch_keys_from_github()
    counter = len(keys) + 1
    key = f"{prefix}-{counter:03d}"
    return key, keys, sha

# ==================== HANDLERS ====================
async def start(update: Update, context: CallbackContext):
    """Handler /start"""
    user = update.effective_user
    
    if user.id in ADMIN_IDS:
        # Cek status GitHub
        token_status = "✅ SET" if github_config["github_token"] else "❌ BELUM SET"
        
        msg = (
            "👋 Ada yang bisa saya bantu tuan ErZet?\n\n"
            "🔐 KEY MANAGER BOT\n\n"
            f"📊 Status GitHub: {token_status}\n"
            f"📦 Repo: {github_config['github_username']}/{github_config['github_repo']}\n\n"
            "📋 PERINTAH:\n"
            "/setgithub - Set token GitHub\n"
            "/genkey <hari> - Generate key\n"
            "/listkeys - List keys\n"
            "/check <key> - Cek key\n"
            "/ban <key> - Ban key\n"
            "/unban <key> - Unban key\n"
            "/testgithub - Test koneksi\n"
            "/config - Lihat konfigurasi"
        )
    else:
        msg = f"👋 Halo {user.first_name}!\n\n/check <key> - Cek key"
    
    await update.message.reply_text(msg)

async def config_cmd(update: Update, context: CallbackContext):
    """Tampilkan konfigurasi"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    token = github_config["github_token"]
    token_display = f"{token[:10]}...{token[-5:]}" if token else "BELUM SET"
    
    msg = (
        "⚙️ KONFIGURASI GITHUB\n\n"
        f"🔑 Token: {token_display}\n"
        f"👤 Username: {github_config['github_username']}\n"
        f"📦 Repo: {github_config['github_repo']}\n"
        f"📄 File: {github_config['github_file']}\n"
        f"🌿 Branch: {github_config['github_branch']}\n\n"
        f"🌐 Raw URL: {get_raw_url()}\n\n"
        "Gunakan /setgithub untuk mengubah"
    )
    await update.message.reply_text(msg)

async def set_github_start(update: Update, context: CallbackContext):
    """Mulai proses set token GitHub"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Anda bukan admin!")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "🔑 SET GITHUB TOKEN\n\n"
        "Kirim token GitHub Anda.\n"
        "Token bisa didapat dari:\n"
        "https://github.com/settings/tokens\n\n"
        "Atau kirim /cancel untuk batal"
    )
    return ASK_GITHUB_TOKEN

async def receive_github_token(update: Update, context: CallbackContext):
    """Terima token GitHub"""
    token = update.message.text.strip()
    
    if token.lower() == "/cancel":
        await update.message.reply_text("❌ Dibatalkan!")
        return ConversationHandler.END
    
    if not token.startswith(("ghp_", "github_pat_")):
        await update.message.reply_text(
            "❌ Token tidak valid!\n"
            "Token harus diawali 'ghp_' atau 'github_pat_'\n\n"
            "Kirim ulang atau /cancel"
        )
        return ASK_GITHUB_TOKEN
    
    # Simpan sementara
    context.user_data["github_token"] = token
    
    await update.message.reply_text(
        "✅ Token diterima!\n\n"
        "Sekarang kirim nama repository.\n"
        "Format: username/nama-repo\n"
        "Contoh: RyzzXCODING/erzet-key\n\n"
        "Atau kirim /skip untuk gunakan default"
    )
    return ASK_GITHUB_REPO

async def receive_github_repo(update: Update, context: CallbackContext):
    """Terima nama repo"""
    repo = update.message.text.strip()
    
    if repo.lower() == "/cancel":
        await update.message.reply_text("❌ Dibatalkan!")
        return ConversationHandler.END
    
    if repo.lower() == "/skip":
        # Gunakan default
        await update.message.reply_text("✅ Menggunakan repo default!")
        repo = f"{github_config['github_username']}/{github_config['github_repo']}"
    else:
        if "/" not in repo:
            await update.message.reply_text(
                "❌ Format salah!\n"
                "Gunakan: username/nama-repo\n\n"
                "Kirim ulang atau /cancel"
            )
            return ASK_GITHUB_REPO
    
    # Simpan config
    username, repo_name = repo.split("/", 1)
    
    github_config["github_token"] = context.user_data.get("github_token", "")
    github_config["github_username"] = username
    github_config["github_repo"] = repo_name
    
    save_github_config(github_config)
    
    # Test koneksi
    await update.message.reply_text("🔍 Testing koneksi GitHub...")
    success, message = test_github()
    
    if success:
        await update.message.reply_text(
            f"✅ KONFIGURASI BERHASIL!\n\n"
            f"{message}\n\n"
            f"📦 Repo: {username}/{repo_name}\n"
            f"🌐 URL: {get_raw_url()}\n\n"
            "Sekarang bot sudah terhubung ke GitHub!\n"
            "Gunakan /genkey untuk generate key."
        )
    else:
        await update.message.reply_text(
            f"⚠️ KONFIGURASI TERSIMPAN TAPI GAGAL!\n\n"
            f"{message}\n\n"
            "Periksa:\n"
            "1. Token GitHub valid\n"
            "2. Repository sudah dibuat\n"
            "3. keylist.json sudah diupload\n\n"
            "Gunakan /setgithub untuk mencoba lagi"
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: CallbackContext):
    """Cancel"""
    await update.message.reply_text("❌ Dibatalkan!")
    return ConversationHandler.END

async def test_github_cmd(update: Update, context: CallbackContext):
    """Test koneksi GitHub"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    loading_msg = await update.message.reply_text("🔍 Testing...")
    success, message = test_github()
    
    if success:
        await loading_msg.edit_text(f"✅ {message}")
    else:
        await loading_msg.edit_text(
            f"❌ {message}\n\n"
            "Gunakan /setgithub untuk mengatur token"
        )

async def genkey(update: Update, context: CallbackContext):
    """Generate key"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Anda bukan admin!")
        return
    
    if not github_config["github_token"]:
        await update.message.reply_text(
            "❌ Token GitHub belum di-set!\n"
            "Gunakan /setgithub dulu"
        )
        return
    
    args = context.args
    days = int(args[0]) if args else 7
    
    loading_msg = await update.message.reply_text("🔄 Generating...")
    
    key, keys, sha = generate_key()
    
    if not sha:
        await loading_msg.edit_text(
            "❌ Gagal terhubung ke GitHub!\n"
            "Gunakan /testgithub untuk cek"
        )
        return
    
    expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
    
    keys[key] = {
        "expiry": expiry,
        "active": True,
        "device": None,
        "created": datetime.datetime.now().isoformat()
    }
    
    success, message = push_keys_to_github(keys, sha)
    
    if success:
        await loading_msg.edit_text(
            f"✅ KEY DIGENERATE!\n\n"
            f"🔑 Key: {key}\n"
            f"⏰ Expired: {expiry}\n"
            f"📅 Durasi: {days} hari"
        )
    else:
        await loading_msg.edit_text(
            f"❌ GAGAL!\n{message}\n\n"
            f"🔑 Key: {key}\n"
            "Gunakan /setgithub untuk perbaiki token"
        )

async def listkeys(update: Update, context: CallbackContext):
    """List keys"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    keys, sha = fetch_keys_from_github()
    
    if not sha:
        await update.message.reply_text("❌ Gagal terhubung!\nGunakan /setgithub")
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
    """Cek key"""
    args = context.args
    if not args:
        return
    
    key = args[0].upper()
    keys, sha = fetch_keys_from_github()
    
    if not sha:
        await update.message.reply_text("❌ Gagal terhubung ke server!")
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
    """Ban key"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    args = context.args
    if not args:
        return
    
    key = args[0].upper()
    keys, sha = fetch_keys_from_github()
    
    if not sha:
        await update.message.reply_text("❌ Gagal terhubung!")
        return
    
    if key not in keys:
        await update.message.reply_text(f"❌ {key} tidak ditemukan!")
        return
    
    keys[key]["active"] = False
    success, message = push_keys_to_github(keys, sha)
    
    if success:
        await update.message.reply_text(f"🚫 {key} DIBLOKIR! Synced!")
    else:
        await update.message.reply_text(f"❌ Gagal: {message}")

async def unban(update: Update, context: CallbackContext):
    """Unban key"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    args = context.args
    if not args:
        return
    
    key = args[0].upper()
    keys, sha = fetch_keys_from_github()
    
    if not sha:
        await update.message.reply_text("❌ Gagal terhubung!")
        return
    
    if key not in keys:
        await update.message.reply_text(f"❌ {key} tidak ditemukan!")
        return
    
    keys[key]["active"] = True
    success, message = push_keys_to_github(keys, sha)
    
    if success:
        await update.message.reply_text(f"✅ {key} diaktifkan! Synced!")

def main():
    print("=" * 50)
    print("🤖 BOT KEY MANAGER ERZET")
    print("=" * 50)
    
    # Tampilkan status
    if github_config["github_token"]:
        print(f"✅ GitHub Token: SET")
        print(f"📦 Repo: {github_config['github_username']}/{github_config['github_repo']}")
    else:
        print("⚠️ GitHub Token: BELUM SET")
        print("Gunakan /setgithub di Telegram")
    
    print()
    
    app = Application.builder().token(TOKEN).build()
    
    # Conversation handler untuk set GitHub
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("setgithub", set_github_start)],
        states={
            ASK_GITHUB_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_github_token)],
            ASK_GITHUB_REPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_github_repo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("config", config_cmd))
    app.add_handler(CommandHandler("testgithub", test_github_cmd))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("listkeys", listkeys))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    
    print("✅ Bot berjalan...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
