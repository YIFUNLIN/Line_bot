from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
from flask_cors import CORS
import os
import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextSendMessage, FlexSendMessage
from function import perform_financial_analysis, perform_recent_analysis

# 載入環境變數
load_dotenv()

# 初始化 Flask
app = Flask(__name__, static_folder="build/static", template_folder="build")
# 確保允許所有來源
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# MongoDB Atlas 配置
MONGO_URI = os.environ.get('mongodb_endpoint', '')
client = MongoClient(MONGO_URI)
db = client['mydatabase']
collection = db['Financial_report']
collection_profile = db['liff_user_data']


# LINE Messaging API 配置
ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
LIFF_URL = os.environ.get('LINE_LIFF_URL', '')

line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(SECRET)

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

@app.route('/api/save_user', methods=['POST'])
def save_user():
    """
    註冊用戶（EMAIL或LINE）
    """
    try:
        user_data = request.json
        print("接收到的使用者資料:", user_data)

        login_type = user_data.get("loginType")
        if not login_type:
            return jsonify({"error": "缺少必要的欄位 (loginType)"}), 400

        if login_type == "LINE":
            # 必須有 userId
            user_id = user_data.get("userId")
            if not user_id:
                return jsonify({"error": "LINE 註冊需提供 userId"}), 400
            
            # 檢查 LINE 用戶是否已存在
            existing_user = collection_profile.find_one({"userId": user_id, "loginType": "LINE"})
            if existing_user:
                print("LINE 用戶已存在:", existing_user)
                return jsonify({"message": "用戶已存在"}), 200

        elif login_type == "EMAIL":
            # 必須有 email, password
            email = user_data.get("email")
            password = user_data.get("password")
            if not email or not password:
                return jsonify({"error": "Email 註冊需提供 email 和 password"}), 400
            
            # 檢查 Email 用戶是否已存在
            existing_user = collection_profile.find_one({"email": email, "loginType": "EMAIL"})
            if existing_user:
                print("Email 用戶已存在:", existing_user)
                return jsonify({"message": "用戶已存在"}), 200

        else:
            return jsonify({"error": "未知的 loginType"}), 400

        # 插入資料到 MongoDB
        collection_profile.insert_one(user_data)
        print("用戶資料已成功儲存:", user_data)
        return jsonify({"message": "用戶資料已成功儲存！"}), 201

    except Exception as e:
        print("儲存資料時發生錯誤:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login_user():
    """
    使用 Email 登入，檢查用戶是否存在
    """
    try:
        user_data = request.json
        print("接收到的登入資料:", user_data)

        login_type = user_data.get("loginType")
        if login_type != "EMAIL":
            return jsonify({"error": "僅支援 EMAIL 登入"}), 400

        email = user_data.get("email")
        password = user_data.get("password")

        if not email or not password:
            return jsonify({"error": "請提供 email 和 password"}), 400

        # 在資料庫中尋找匹配的用戶
        existing_user = collection_profile.find_one({"email": email, "password": password, "loginType": "EMAIL"})
        if existing_user:
            print("登入成功:", existing_user)
            return jsonify({"message": "登入成功"}), 200
        else:
            return jsonify({"error": "帳號或密碼錯誤"}), 401

    except Exception as e:
        print("登入時發生錯誤:", str(e))
        return jsonify({"error": str(e)}), 500
    
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
                    react_url = f"https://3a76-2401-e180-8c60-2501-7cae-12fa-2f97-a32e.ngrok-free.app/recommend"

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
