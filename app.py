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
import traceback

load_dotenv()

# 串接 React 的前端框架
app = Flask(__name__, static_folder="build/static", template_folder="build") # static_folder: 靜態文件夾，template_folder: 模板文件夾

# CORS: 確保跨資源共享，允許所有來源對所有路徑的請求， 允許跨來源請求攜帶憑證（如 cookies）
# 開發所有路徑，額外開啟允許跨網域請求攜帶憑證的功能
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
API_BASE_URL = "https://d976-140-123-57-111.ngrok-free.app"

MONGO_URI = os.environ.get('mongodb_endpoint', '')
client = MongoClient(MONGO_URI)
db = client['mydatabase']
collection = db['Financial_report']
collection_profile = db['liff_user_data']

ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '') 
SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
LIFF_URL = os.environ.get('LINE_LIFF_URL', '')

line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(SECRET)



# 這兩支 recommend 相關的 API 都是去指向serve_react()這個函數: 去提供 React 的靜態頁面來供登入的畫面 (訪問推薦系統前)
@app.route('/recommend', defaults={'path': ''})  
@app.route('/recommend/<path:path>')
def serve_react(path):   # 定義 View function: 參數path: 來自 URL 的路徑
    if path and os.path.exists(os.path.join(app.template_folder, path)): 
        return send_from_directory(app.template_folder, path) 
    return send_from_directory(app.template_folder, 'index.html')  # 若沒抓到React 前端路徑，返回 React 應用的入口文件 build/index.html 確保正確顯示

# 定義註冊用戶資料的 API : 會由前端那邊的點擊觸發這支API (透過URL+API參數)
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
            
            existing_user = collection_profile.find_one({"userId": user_id, "loginType": "LINE"})
            if existing_user:
                print("LINE 用戶已存在:", existing_user)
                return jsonify({"message": "用戶已存在", "redirectUrl": "https://yifunlin.github.io/stock/stock_report.html"}), 200

        elif login_type == "EMAIL":
            email = user_data.get("email")
            password = user_data.get("password")
            if not email or not password:
                return jsonify({"error": "Email 註冊需提供 email 和 password"}), 400
            
            # 檢查 Email 用戶是否已存在: 用loginTye 和 email 來比對
            existing_user = collection_profile.find_one({"email": email, "loginType": "EMAIL"})
            if existing_user:
                print("Email 用戶已存在:", existing_user)
                return jsonify({"message": "用戶已存在"}), 200

        else:
            return jsonify({"error": "未知的 loginType"}), 400

        collection_profile.insert_one(user_data)
        print("用戶資料已成功儲存:", user_data)
        return jsonify({"message": "用戶資料已成功儲存！"}), 201

    except Exception as e:
        print("儲存資料時發生錯誤:", str(e))
        return jsonify({"error": str(e)}), 500

# 會由前端那邊的點擊觸發這支API (透過URL+API參數)
# 只提供 EMAIL 登入
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

        existing_user = collection_profile.find_one({"email": email, "password": password, "loginType": "EMAIL"})
        if existing_user:
            print("登入成功:", existing_user)
            return jsonify({"message": "登入成功", "redirectUrl": "https://yifunlin.github.io/stock/stock_report.html"}), 200   # 給前端接收
        else:
            return jsonify({"error": "帳號或密碼錯誤"}), 401

    except Exception as e:
        print("登入時發生錯誤:", str(e))
        return jsonify({"error": str(e)}), 500
    
@app.route("/", methods=['GET', 'POST']) # Root API
def index():
    if request.method == 'GET':   # 先用 GET 測試，測試後端運作
        return "success" 
    elif request.method == 'POST':  # LINE Webhook 的 request 是通過POST方法傳遞(會攜帶用戶的事件數據)
        body = request.get_data(as_text=True)  # 獲取 HTTP 請求的主體（body）-> 字串
        try:         
            # 先驗證
            signature = request.headers['X-Line-Signature'] # 從 HTTP 請求的標頭中提取 X-Line-Signature，X-Line-Signature 是 LINE 平台用來驗證 Webhook 請求合法性的標籤。LINE 平台在發送 Webhook 請求時，會用密鑰簽署請求並附上這個簽名
            handler.handle(body, signature)  # 提取簽名後，用 handler.handle 驗證這個請求是否來自 LINE，而非偽造
            
            json_data = json.loads(body)  #  將request的body從字串 -> JSON 
            events = json_data.get('events', []) # 提取 events，
            if not events:
                return 'OK'

            event = events[0] # 取出 events 中的第一個事件(由很多key-value組成的字典)
            reply_token = event['replyToken'] # 從事件中提取 replyToken: replyToken 是 LINE 提供的一個令牌，用於回應用戶訊息。

            # 處理用戶在聊天室中的訊息
            if event['type'] == 'message' and event['message']['type'] == 'text': 
                user_message = event['message']['text']  # 抓取使用者的query
                print('userMessage:', user_message)

                # 使用者若點擊圖文選單的功能，會回傳對應的 message 文字形式
                if user_message == '推薦系統' or user_message == '推薦':
                    react_url = f"{API_BASE_URL}/recommend"

                    # 設定點選進入登入畫面前的訊息，使用 LINE 的 Flex Message 來設計
                    flex_message = FlexSendMessage(  
                        alt_text="點擊查看網頁",   # 當用戶裝置不支援 Flex Message 時顯示「點擊查看網頁」(不支援 Web 版的 LINE)
                        contents={
                            "type": "bubble",
                            "hero": {
                                "type": "image",
                                "size": "full",
                                "aspectRatio": "20:13",
                                "aspectMode": "cover",
                                "action": {
                                "type": "uri",
                                "uri": "https://line.me/"
                                },
                                "url": "https://raw.githubusercontent.com/YIFUNLIN/Line_bot/refs/heads/main/images/rec_sysyem.png"
                            },
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                {
                                    "type": "text",
                                    "text": "股票買賣推薦系統",
                                    "weight": "bold",
                                    "size": "xl"
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "margin": "lg",
                                    "spacing": "sm",
                                    "contents": [
                                    {
                                        "type": "box",
                                        "layout": "baseline",
                                        "spacing": "sm",
                                        "contents": [
                                        {
                                            "type": "text",
                                            "text": "說明",
                                            "color": "#aaaaaa",
                                            "size": "sm",
                                            "flex": 1
                                        },
                                        {
                                            "type": "text",
                                            "text": "使用前需要先登入",
                                            "wrap": True,
                                            "color": "#666666",
                                            "size": "sm",
                                            "flex": 5
                                        }
                                        ]
                                    }
                                    ]
                                }
                                ]
                            },
                            "footer": {
                                "type": "box",
                                "layout": "vertical",
                                "spacing": "sm",
                                "contents": [
                                {
                                    "type": "button",
                                    "style": "link",
                                    "height": "sm",
                                    "action": {
                                    "type": "uri",
                                    "label": "Login",
                                    "uri": react_url
                                    }
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [],
                                    "margin": "sm"
                                }
                                ],
                                "flex": 0
                            }
                            })
                    line_bot_api.reply_message(reply_token, flex_message) # 後端透過 LINE Messaging API 與 LINE 平台通訊，成功發送訊息後，LINE 平台將該訊息推送到用戶的 LINE App => 點擊後跳轉到指定 URL

                # 財報分析功能
                elif user_message.startswith("財報分析"): 
                    line_bot_api.reply_message(  
                        reply_token,
                        TextSendMessage(text="請輸入股票代號與年份，格式：[股票代號] [年份] eg. 2330 112") # 回覆訊息
                    )

                # 財報分析 - 處理股票代號與年份
                elif len(user_message.split()) == 2: 
                    stock_id, year = user_message.split() 
                    if stock_id.isdigit() and year.isdigit():
                        analysis_result = perform_financial_analysis(stock_id, year) # 進行財報蒐集&分析，處理完會回傳結果
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
                elif user_message.isdigit():  # 檢查 input
                    stock_id = user_message
                    analysis_result = perform_recent_analysis(stock_id)  # 爬新聞
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text=analysis_result)
                    )


                else:
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text=f"沒錯，{user_message}")
                    )
            return 'OK' 
        
        except InvalidSignatureError: # 如果伺服器收到的 X-Line-Signature 與計算出的簽名不匹配時，會觸發此錯誤
            return 'Invalid signature. Please check your channel access token/channel secret.'
        
        except Exception as e: 
            print("發生錯誤：")
            print(traceback.format_exc())  #
            return 'Internal Server Error', 500

if __name__ == "__main__":  
    app.run(host="0.0.0.0", port=5000)  
