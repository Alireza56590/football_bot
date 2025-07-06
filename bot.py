from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
from datetime import datetime

# مدیر اصلی
SUPER_ADMIN = 262011432

# بقیه ادمین‌ها
ADMINS = set([SUPER_ADMIN])

# لیست بازی‌ها: [{'id':1, 'home':'TeamA', 'away':'TeamB', 'time':'2025-07-05 18:00', 'result':'2-1'}]
matches = []

# پیش‌بینی‌ها: {user_id: {match_id: '2-1'}}
predictions = {}

# امتیاز کاربران: {user_id: points}
scores = {}

# دستور استارت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 خوش آمدید به ربات پیش‌بینی فوتبال!")

# افزودن ادمین جدید (فقط سوپر ادمین)
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != SUPER_ADMIN:
        await update.message.reply_text("🚫 فقط سوپر ادمین می‌تواند ادمین اضافه کند.")
        return
    if not context.args:
        await update.message.reply_text("مثال: /add_admin 123456789")
        return
    new_admin = int(context.args[0])
    ADMINS.add(new_admin)
    await update.message.reply_text(f"✅ ادمین جدید اضافه شد: {new_admin}")

# افزودن بازی جدید توسط ادمین (مثال: /add_match TeamA TeamB 2025-07-05_18:00)
async def add_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("🚫 فقط ادمین می‌تواند بازی اضافه کند.")
        return
    if len(context.args) != 3:
        await update.message.reply_text("مثال: /add_match TeamA TeamB 2025-07-05_18:00")
        return
    home, away, time_str = context.args
    match_id = len(matches) + 1
    matches.append({'id': match_id, 'home': home, 'away': away, 'time': time_str, 'result': None})
    await update.message.reply_text(f"✅ بازی جدید اضافه شد: {home} vs {away} در {time_str}")

# دیدن لیست مسابقات امروز
async def today_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime('%Y-%m-%d')
    text = "🏟 مسابقات امروز:\n"
    found = False
    for m in matches:
        if m['time'].startswith(today):
            text += f"{m['id']}: {m['home']} vs {m['away']} ساعت {m['time'][11:]}\n"
            found = True
    if not found:
        text = "امروز مسابقه‌ای وجود ندارد."
    await update.message.reply_text(text)

# پیش‌بینی (مثال: /predict 1 2-1)
async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) != 2:
        await update.message.reply_text("مثال: /predict 1 2-1")
        return
    match_id = int(context.args[0])
    pred = context.args[1]

    # بررسی زمان بازی
    match = next((m for m in matches if m['id'] == match_id), None)
    if not match:
        await update.message.reply_text("بازی یافت نشد.")
        return
    match_time = datetime.strptime(match['time'], '%Y-%m-%d_%H:%M')
    if datetime.now() >= match_time:
        await update.message.reply_text("⏰ مهلت پیش‌بینی برای این بازی تمام شده است.")
        return

    if user_id not in predictions:
        predictions[user_id] = {}
    predictions[user_id][match_id] = pred
    await update.message.reply_text(f"✅ پیش‌بینی شما برای بازی {match['home']} vs {match['away']} ثبت شد: {pred}")

# وارد کردن نتیجه بازی توسط ادمین (مثال: /set_result 1 2-1)
async def set_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("🚫 فقط ادمین می‌تواند نتیجه وارد کند.")
        return
    if len(context.args) != 2:
        await update.message.reply_text("مثال: /set_result 1 2-1")
        return
    match_id = int(context.args[0])
    result = context.args[1]

    match = next((m for m in matches if m['id'] == match_id), None)
    if not match:
        await update.message.reply_text("بازی یافت نشد.")
        return

    match['result'] = result
    await update.message.reply_text(f"✅ نتیجه بازی {match['home']} vs {match['away']} ثبت شد: {result}")

    real_home, real_away = map(int, result.split('-'))

    # محاسبه امتیاز کاربران
    for uid, user_preds in predictions.items():
        pred = user_preds.get(match_id)
        if pred:
            pred_home, pred_away = map(int, pred.split('-'))
            if pred_home == real_home and pred_away == real_away:
                point = 3
            elif pred_home == real_home or pred_away == real_away:
                point = 2
            else:
                point = 1
            scores[uid] = scores.get(uid, 0) + point

# دیدن امتیاز کاربر
async def my_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    point = scores.get(user_id, 0)
    await update.message.reply_text(f"🏆 امتیاز شما: {point}")

# دیدن جدول برترین‌ها
async def top_scores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not scores:
        await update.message.reply_text("هنوز کسی امتیازی ندارد.")
        return
    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    text = "🏆 جدول برترین‌ها:\n"
    for uid, point in ranking:
        text += f"- کاربر {uid}: {point} امتیاز\n"
    await update.message.reply_text(text)

# راه‌اندازی
async def main():
    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_admin", add_admin))
    app.add_handler(CommandHandler("add_match", add_match))
    app.add_handler(CommandHandler("today_matches", today_matches))
    app.add_handler(CommandHandler("predict", predict))
    app.add_handler(CommandHandler("set_result", set_result))
    app.add_handler(CommandHandler("my_score", my_score))
    app.add_handler(CommandHandler("top_scores", top_scores))

    print("🤖 Bot is running...")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
