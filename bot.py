import asyncio
import json
import os
import sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "9051506952:AAH1xy03e64jIU4ynaMGIf-h2L1e7Zxmco4"
DATA_FILE = "tools_config.json"

DEFAULT_TOOLS = {
    "digikala": {"name": "🛒 ابزار دیجی‌کالا", "package": "digikala-mcp"}
}

def load_tools():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_TOOLS.copy()

def save_tools(tools):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(tools, f, ensure_ascii=False, indent=2)

MCP_TOOLS = load_tools()

async def get_keyboard():
    keyboard = []
    for key, tool in MCP_TOOLS.items():
        keyboard.append([InlineKeyboardButton(tool["name"], callback_data=f"exec_{key}")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = await get_keyboard()
    msg = (
        "سلام! ابزار MCP مورد نظر را انتخاب کنید.\n\n"
        "برای نصب ابزار جدید از این دستور استفاده کنید:\n"
        "`/install نام-پکیج نام_نمایشی_دکمه`\n\n"
        "مثال:\n`/install iran-crypto-mcp 🪙 ارز دیجیتال`"
    )
    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

async def install_tool(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ فرمت اشتباه!\nمثال: `/install iran-crypto-mcp 🪙 ارز دیجیتال`", parse_mode="Markdown")
        return
    
    package_name = args[0]
    display_name = " ".join(args[1:])
    key = package_name.replace("-mcp", "").replace("-", "_")

    await update.message.reply_text(f"⏳ در حال نصب پکیج `{package_name}`...")

    try:
        process = await asyncio.create_subprocess_exec(
            "uv", "pip", "install", package_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            MCP_TOOLS[key] = {
                "name": display_name,
                "package": package_name
            }
            save_tools(MCP_TOOLS)
            
            reply_markup = await get_keyboard()
            await update.message.reply_text(
                f"✅ ابزار **{display_name}** با موفقیت نصب شد و دکمه آن اضافه گردید!",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            error_msg = stderr.decode() if stderr else stdout.decode()
            await update.message.reply_text(f"❌ خطا در نصب:\n`{error_msg[:1500]}`", parse_mode="Markdown")
            
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در اجرا: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    tool_key = query.data.replace("exec_", "")
    if tool_key in MCP_TOOLS:
        tool_info = MCP_TOOLS[tool_key]
        await query.edit_message_text(f"⏳ در حال فراخوانی {tool_info['name']}...")
        
        try:
            process = await asyncio.create_subprocess_exec(
                "uvx", tool_info["package"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            result = stdout.decode() if stdout else stderr.decode()
            if not result.strip():
                result = "ابزار اجرا شد اما خروجی متنی بازنگرداند."
                
            await query.message.reply_text(f"خروجی ابزار:\n```\n{result[:3500]}\n```", parse_mode="Markdown")
        except Exception as e:
            await query.message.reply_text(f"خطا در اجرای ابزار: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("install", install_tool))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("🤖 ربات با موفقیت روی سیستم فعال شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
