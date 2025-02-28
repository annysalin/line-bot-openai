from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

# 設定 LINE API 和 OpenAI API 金鑰
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 設定 OpenAI API
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 設定 Flask
app = Flask(__name__)

# 設定 LINE SDK（V2）
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 設定 Webhook
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return jsonify({"status": "error", "message": "Invalid signature"}), 400

    return jsonify({"status": "ok"}), 200

# 定義 AI 的回應規則
SYSTEM_PROMPT = """
你是一名華語會話學習助理。請與我進行一場點餐對話。
我可以自由表達，但你只能使用以下句式回應，並讓對話自然進行，最後由你主動結束話題，並告知我達成會話目標。

詞彙：
杯、綠茶、紅茶、奶茶、鮮奶茶、加、波霸、珍珠、椰果、仙草凍、布丁、大杯、中杯、小杯、
木瓜、香蕉、草莓、芒果、牛奶、柳橙汁、百香果汁、西瓜汁、蘋果汁、推薦、正常冰、少冰、微冰、去冰、熱的、
全糖、少糖、半糖、微糖、無糖、袋子、杯套、吸管、環保吸管、環保杯

句式：
「請問你要喝什麼？」
「好的，加...(料)加...塊錢。」
「大杯、中杯，還是小杯？」
「大杯嗎？」
「我推薦你喝...。」
「這樣就好了嗎?」
「糖、冰呢？」
「甜度、冰塊呢？」
「....塊錢」
「收您...塊錢。這是您的發票。」
「....(飲料名稱)甜度固定」
「....(飲料名稱)冰塊固定」
「要袋子嗎？」
「一個袋子一塊錢。」
「要吸管嗎？」
「吸管呢？」
「有環保杯折五元」
「買五送一，送什麼？」
「先生，您的飲料好了。」
「小姐，您的飲料好了。」

會話主題：「買飲料」

會話結束目標：「成功買到飲料」

會話結束後，請給我一個提示「你達成目標」，告知我對話已經成功。

你不需要給我會話範本，只需要直接開始與我對話即可。
"""

# 處理 LINE 訊息（使用 OpenAI API）
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        )
        reply_text = response.choices[0].message.content
    except Exception as e:
        reply_text = "發生錯誤，請稍後再試。"

    # 回應 LINE 使用者
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
