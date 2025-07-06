import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = 262011432  # اینجا آیدی عددی خودت رو بذار

DATA_FILE = "data.json"

# اگر فایل دیتا وجود نداشت، یه دونه خالی می‌سازه
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"predictions": {}, "result": None, "scores": {}}, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! خوش اومدی به ربات پیش‌بینی بستقلات دات کام ⚽\n"
        "با دستور /predict پیش‌بینی کن.\n"
        "با /my_score امتیازت رو ببین.\n"
        "با /top کاربران برتر رو ببین."
    )

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if len(context.args) != 2:
        await update.message.reply_text("لطفا به صورت زیر بنویس:\n/predict گل_تیم_اول گل_تیم_دوم")
        return

    try:
        g1 = int(context.args[0])
        g2 = int(context.args[1])
    except ValueError:
        await update.message.reply_text("فقط عدد بنویس لطفا!")
        return

    with open(DATA_FILE) as f:
        data = json.load(f)

    data["predictions"][user_id] = [g1, g2]
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

    await update.message.reply_text(f"پیش‌بینی شما ذخیره شد: {g1}-{g2}")

async def set_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("فقط مدیر می‌تواند نتیجه را وارد کند.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("لطفا به صورت زیر بنویس:\n/set_result گل_تیم_اول گل_تیم_دوم")
        return

    try:
        rg1 = int(context.args[0])
        rg2 = int(context.args[1])
    except ValueError:
        await update.message.reply_text("فقط عدد بنویس لطفا!")
        return

    with open(DATA_FILE) as f:
        data = json.load(f)

    data["result"] = [rg1, rg2]

    # محاسبه امتیاز کاربران
    scores = {}
    for user_id, pred in data["predictions"].items():
        score = 1  # حداقل امتیاز برای پیش‌بینی کردن
        if pred == [rg1, rg2]:
            score = 3
        elif (rg1 - rg2)*(pred[0] - pred[1]) > 0:
            score = 2
        scores[user_id] = scores.get(user_id, 0) + score

    data["scores"] = scores
    data["predictions"] = {}  # پاک کردن پیش‌بینی‌ها برای بازی بعد

    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

    await update.message.reply_text("نتیجه ثبت شد و امتیاز کاربران به‌روزرسانی شد.")

async def my_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    with open(DATA_FILE) as f:
        data = json.load(f)
    score = data["scores"].get(user_id, 0)
    await update.message.reply_text(f"امتیاز شما: {score}")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(DATA_FILE) as f:
        data = json.load(f)
    scores = data["scores"]
    top_users = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]

    text = "🏆 کاربران برتر:\n"
    for idx, (uid, sc) in enumerate(top_users, 1):
        text += f"{idx}- کاربر {uid}: {sc} امتیاز\n"

    await update.message.reply_text(text)

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("predict", predict))
    app.add_handler(CommandHandler("set_result", set_result))
    app.add_handler(CommandHandler("my_score", my_score))
    app.add_handler(CommandHandler("top", top))
    app.run_polling()