import os
import json
import datetime
from flask import Flask, request, abort
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient,
    MessagingApi, MessagingApiBlob,
    ReplyMessageRequest, PushMessageRequest,
    TextMessage, QuickReply, QuickReplyItem, MessageAction,
    RichMenuRequest, RichMenuArea, RichMenuBounds, RichMenuSize,
    URIAction
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# =====================
# Load environment
# =====================
load_dotenv()
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

# Flask app
app = Flask(__name__)

# LINE v3 setup
handler = WebhookHandler(CHANNEL_SECRET)
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
api_client = ApiClient(configuration)
messaging_api = MessagingApi(api_client)
messaging_blob = MessagingApiBlob(api_client)

# =====================
# Load messages.json
# =====================
with open("messages.json", "r", encoding="utf-8") as f:
    MESSAGES = json.load(f)

# =====================
# State
# =====================
user_joined = {}  # {user_id: datetime}
scheduler = BackgroundScheduler()
scheduler.start()

# =====================
# LINE Webhook
# =====================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# =====================
# Event Handler
# =====================
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text.strip()

    # Step 0: First-time user → Greeting
    if user_id not in user_joined:
        user_joined[user_id] = datetime.datetime.now()

        quick_reply = QuickReply(items=[
            QuickReplyItem(action=MessageAction(label="🎁 Gift", text="receive gift"))
        ])
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=MESSAGES["greeting"], quick_reply=quick_reply)]
            )
        )
        return

    # Step 1: Handle Gift
    if text.lower() in ["receive gift", "🎁", "gift"]:
        reply = MESSAGES["gift"]
        schedule_messages(user_id)
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )
        return

    # Step 2: Handle Activation
    if "⚡" in text or "activated" in text.lower():
        reply = MESSAGES["activated"]
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )
        return

    # Step 3: Handle Rose Path
    if "🌹" in text or "rose" in text.lower():
        reply = MESSAGES["rose_path"]
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )
        return

    # Default fallback
    messaging_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="🙏 โปรดทำตามคำแนะนำ / Please follow the instructions.")]
        )
    )

# =====================
# Scheduler
# =====================
def schedule_messages(user_id):
    now = datetime.datetime.now()

    # Day 1 after +24h
    scheduler.add_job(
        send_message,
        "date",
        # run_date=now + datetime.timedelta(hours=24),
        run_date=now + datetime.timedelta(seconds=30),
        args=[user_id, MESSAGES["day1_reminder"]]
    )

    # Day 2 after +48h
    scheduler.add_job(
        send_message,
        "date",
        # run_date=now + datetime.timedelta(hours=48),
        run_date=now + datetime.timedelta(seconds=60),  # change to hours=48 for real
        args=[user_id, MESSAGES["day2_invite"]]
    )
    scheduler.add_job(
        send_message,
        "date",
        # run_date=now + datetime.timedelta(hours=48, minutes=10),
        run_date=now + datetime.timedelta(seconds=70),  # blessing card
        args=[user_id, MESSAGES["day2_blessing"]]
    )

    # Day 3 after +72h
    scheduler.add_job(
        send_message,
        "date",
        # run_date=now + datetime.timedelta(hours=72),
        run_date=now + datetime.timedelta(seconds=90),  # change to hours=72 for real
        args=[user_id, MESSAGES["day3_teaser"]]
    )
    # Day 3 after +72h
    scheduler.add_job(
        send_message,
        "date",
        # run_date=now + datetime.timedelta(hours=72,minutes=10),
        run_date=now + datetime.timedelta(seconds=92),  # change to hours=72 for real
        args=[user_id, MESSAGES["rose_path"]]
    )

def send_message(user_id, message):
    messaging_api.push_message(
        PushMessageRequest(
            to=user_id,
            messages=[TextMessage(text=message)]
        )
    )

# =====================
# Rich Menu Setup
# =====================
def setup_rich_menu():
    # Delete existing menus
    for rm in messaging_api.get_rich_menu_list():
        messaging_api.delete_rich_menu(rm.rich_menu_id)

    # Create rich menu
    rich_menu_req = RichMenuRequest(
        size=RichMenuSize(width=2500, height=843),
        selected=True,
        name="AGAIA Menu",
        chat_bar_text="🌸 Menu",
        areas=[
            RichMenuArea(
                bounds=RichMenuBounds(x=0, y=0, width=833, height=843),
                action=MessageAction(label="📜 Archetype", text="archetype")
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=834, y=0, width=833, height=843),
                action=MessageAction(label="🎁 Gift", text="receive gift")
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=1667, y=0, width=833, height=421),
                action=MessageAction(label="🕊️ Journey", text="journey")
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=1667, y=422, width=833, height=421),
                action=URIAction(label="🛍️ Shop", uri="[SHOP_LINK]")
            ),
            RichMenuArea(
                bounds=RichMenuBounds(x=2500-833, y=0, width=833, height=843),
                action=MessageAction(label="💬 Oracle", text="oracle")
            )
        ]
    )

    rich_menu_id = messaging_api.create_rich_menu(rich_menu_req)

    # Upload image (must exist as rich_menu.png)
    with open("rich_menu.png", "rb") as f:
        messaging_blob.set_rich_menu_image(rich_menu_id, "image/png", f)

    # Set as default
    messaging_api.set_default_rich_menu(rich_menu_id)

# =====================
# Main
# =====================
if __name__ == "__main__":
    try:
        setup_rich_menu()
        print("✅ Rich menu created")
    except Exception as e:
        print(f"⚠️ Rich menu setup failed: {e}")

    app.run(port=5000, debug=True)
