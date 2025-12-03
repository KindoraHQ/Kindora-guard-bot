import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatPermissions,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

# ====== READ BOT TOKEN FROM ENVIRONMENT VARIABLE ======
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Please set BOT_TOKEN environment variable in Render dashboard")

VERIFY_PREFIX = "verify_user"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simple /start command in private chat."""
    if update.effective_chat.type == "private":
        await update.message.reply_text(
            "Hi! I'm Kindora Guard Bot.\n"
            "Add me as admin to your group and I will protect it with a simple verify button."
        )


async def handle_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When a new user joins the group, restrict and send verify button."""
    message = update.message
    chat = message.chat

    for member in message.new_chat_members:
        user_id = member.id

        # 1) Restrict the user (no messages until verify)
        perms_blocked = ChatPermissions(
            can_send_messages=False,
            can_send_audios=False,
            can_send_documents=False,
            can_send_photos=False,
            can_send_videos=False,
            can_send_video_notes=False,
            can_send_voice_notes=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
        )

        try:
            await context.bot.restrict_chat_member(
                chat_id=chat.id,
                user_id=user_id,
                permissions=perms_blocked,
            )
        except Exception as e:
            print("Error restricting user:", e)

        # 2) Send verify button
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="✅ Verify (I'm human)",
                        callback_data=f"{VERIFY_PREFIX}:{user_id}",
                    )
                ]
            ]
        )

        text = (
            f"Welcome, {member.mention_html()}!\n\n"
            "Please press the button below to verify you are human.\n"
            "Until you verify, you cannot send messages."
        )

        try:
            await context.bot.send_message(
                chat_id=chat.id,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except Exception as e:
            print("Error sending verify message:", e)


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle verify button click."""
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    if not data.startswith(VERIFY_PREFIX + ":"):
        return

    try:
        _, user_id_str = data.split(":")
        target_user_id = int(user_id_str)
    except Exception:
        return

    # Only the correct user can verify themselves
    if query.from_user.id != target_user_id:
        await query.reply_text("This button is not for you.")
        return

    chat_id = query.message.chat.id

    # Give full permissions (normal member)
    perms_unlocked = ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_change_info=False,
        can_invite_users=True,
        can_pin_messages=False,
    )

    try:
        await context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user_id,
            permissions=perms_unlocked,
        )
    except Exception as e:
        print("Error un-restricting user:", e)

    # Edit the message to show success
    try:
        await query.edit_message_text(
            "✅ Verified! You can now chat.\nWelcome to Kindora community!"
        )
    except Exception as e:
        print("Error editing message:", e)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # /start in private chat
    app.add_handler(CommandHandler("start", start))

    # New members in groups
    app.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_members)
    )

    # Button clicks
    app.add_handler(CallbackQueryHandler(handle_button))

    print("Kindora Guard Bot started (polling)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
