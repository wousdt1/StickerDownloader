import os
import json
import asyncio
from http.server import BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application
import requests
from PIL import Image
import io

# 核心修改：直接写死你的 Token 钥匙，防止 Vercel 系统环境变量读取失败
TOKEN = "8910208885:AAH8MVJ4HR63zQ_7CHmF28ZpWo9nczmLtqA"
app = Application.builder().token(TOKEN).build()

async def process_update(update_dict):
    async with app:
        update = Update.de_json(update_dict, app.bot)
        
        # 1. 响应 /start 命令
        if update.message and update.message.text == "/start":
            await app.bot.send_message(
                chat_id=update.message.chat_id, 
                text="👋 你好！我是专属表情包下载机器人。请直接发给我任意【单个静态贴纸】。"
            )
            return

        # 2. 处理贴纸
        if update.message and update.message.sticker:
            sticker = update.message.sticker
            if sticker.is_animated or sticker.is_video:
                await app.bot.send_message(chat_id=update.message.chat_id, text="❌ 暂不支持动态或视频贴纸，请发送静态贴纸。")
                return
            
            await app.bot.send_message(chat_id=update.message.chat_id, text="⏳ 正在为你下载并转换格式，请稍候...")
            
            # 获取贴纸网络路径
            file = await app.bot.get_file(sticker.file_id)
            file_url = file.file_path
            
            # 下载、转换并打包发回
            res = requests.get(file_url)
            img = Image.open(io.BytesIO(res.content)).convert("RGBA")
            
            out_img = io.BytesIO()
            img.save(out_img, format="PNG")
            out_img.seek(0)
            
            await app.bot.send_document(
                chat_id=update.message.chat_id, 
                document=out_img, 
                filename="sticker.png", 
                caption="✅ 转换成功！您可以直接保存此 PNG 图片并上传至微信。"
            )

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        update_dict = json.loads(post_data.decode('utf-8'))
        
        # 异步执行机器人逻辑
        asyncio.run(process_update(update_dict))
        
        # 必须给 Telegram 服务器返回 200 OK，否则 Telegram 会重复发送
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
