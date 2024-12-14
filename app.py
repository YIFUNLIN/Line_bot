from dotenv import load_dotenv  
from flask import Flask, request, jsonify, send_from_directory
import os
import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextSendMessage, FlexSendMessage
from flask_cors import CORS
from function import perform_financial_analysis, perform_recent_analysis

# 載入環境變數
load_dotenv()

app = Flask(__name__, static_folder="frontend_build/static", template_folder="frontend_build")
CORS(app)  # 適用於開發階段，允許跨域訪問

# LINE Messaging API 配置
ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
LIFF_URL = os.environ.get('LINE_LIFF_URL', '')

line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(SECRET)

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return "success"
    elif request.method == 'POST':
        body = request.get_data(as_text=True)
        try:
            json_data = json.loads(body)
            signature = request.headers['X-Line-Signature']
            handler.handle(body, signature)

            events = json_data.get('events', [])
            if not events:
                return 'OK'

            event = events[0]
            reply_token = event['replyToken']

            # 處理用戶訊息
            if event['type'] == 'message' and event['message']['type'] == 'text':
                user_message = event['message']['text']
                print('userMessage:', user_message)

                # 推薦系統功能
                if user_message == '推薦系統' or user_message == '推薦':
                    # 動態生成 React 網頁 URL
                    react_url = f"https://128b-2401-e180-8c60-97dc-dd63-4f75-6024-a873.ngrok-free.app/recommend"

                    flex_message = FlexSendMessage(
                        alt_text="點擊查看網頁",
                        contents={
                            "type": "bubble",
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {"type": "text", "text": "推薦系統", "weight": "bold", "align": "center"}
                                ]
                            },
                            "footer": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {"type": "uri", "label": "前往網頁", "uri": react_url},
                                        "style": "primary"
                                    }
                                ]
                            }
                        }
                    )
                    line_bot_api.reply_message(reply_token, flex_message)


                # 財報分析功能
                elif user_message.startswith("財報分析"):
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text="請輸入股票代號與年份，格式：[股票代號] [年份] eg. 2330 112")
                    )

                # 財報分析 - 處理股票代號與年份
                elif len(user_message.split()) == 2:
                    stock_id, year = user_message.split()
                    if stock_id.isdigit() and year.isdigit():
                        analysis_result = perform_financial_analysis(stock_id, year)
                        line_bot_api.reply_message(
                            reply_token,
                            TextSendMessage(text=analysis_result)
                        )
                    else:
                        line_bot_api.reply_message(
                            reply_token,
                            TextSendMessage(text="輸入格式錯誤，請輸入正確的股票代號與年份！")
                        )

                # 近況分析功能
                elif user_message == "近況分析":
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text="請輸入股票代號，eg. 2330")
                    )

                # 近況分析 - 處理股票代號輸入
                elif user_message.isdigit():
                    stock_id = user_message
                    analysis_result = perform_recent_analysis(stock_id)
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text=analysis_result)
                    )

                # 處理其他訊息
                else:
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text=f"沒錯，{user_message}")
                    )
            return 'OK'
        except InvalidSignatureError:
            return 'Invalid signature. Please check your channel access token/channel secret.'
        except Exception as e:
            import traceback
            print("發生錯誤：")
            print(traceback.format_exc())
            return 'Internal Server Error', 500

# 提供 React 的靜態頁面
@app.route('/recommend', defaults={'path': ''})
@app.route('/recommend/<path:path>')
def serve_react(path):
    """
    提供 React 靜態文件，讓用戶訪問推薦系統頁面
    """
    if path and os.path.exists(os.path.join(app.template_folder, path)):
        return send_from_directory(app.template_folder, path)
    return send_from_directory(app.template_folder, 'index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
