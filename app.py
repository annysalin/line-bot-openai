from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

# 設定 LINE 與 OpenAI API 金鑰
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 設定 OpenAI API
openai.api_key = OPENAI_API_KEY

# 定義 AI 的回應規則
SYSTEM_PROMPT = """
你是一個華語學習助理，請只使用以下句式與使用者對話：
- 「請問你要喝什麼？」
- 「好的，加...(料)加...塊錢。」
- 「大杯、中杯，還是小杯？」
- 「大杯嗎？」
- 「我推薦你喝...。」
- 「這樣就好了嗎?」
- 「糖、冰呢？」
- 「甜度、冰塊呢？」
- 「....塊錢」
- 「收您...塊錢。這是您的發票。」
- 「....(飲料名稱)甜度固定」
- 「....(飲料名稱)冰塊固定」
- 「要袋子嗎？」
- 「一個袋子一塊錢。」
- 「要吸管嗎？」
- 「吸管呢？」
- 「有環保杯折五元」
- 「買五送一，送什麼？」
- 「先生，您的飲料好了。」
- 「小姐，您的飲料好了。」
不一定要用上所有對話，請讓對話自然進行，並在適當時機結束話題。
"""

# 初始化 Flask
app = Flask(__name__)

# 初始化 LINE SDK
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 設定 Webhook
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400
    return "OK"

# LINE 訊息處理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # 發送用戶訊息給 OpenAI API
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    )

    reply_text = response["choices"][0]["message"]["content"]
    
    # 回覆使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
