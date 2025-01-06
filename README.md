# ﻿Financial Line_bot
歡迎使用投資理財小幫手😀

- 影片連結(12/31更新版): https://www.youtube.com/watch?v=dRLWFH17-NM
- 前端React程式碼: https://github.com/YIFUNLIN/React_Line_bot_project
- 推薦系統程式碼: https://github.com/YIFUNLIN/stock
  
本系統提供三大功能:
1. 財報分析: 輸入股票代號與年份(eg. 2330 112)，即可自動爬找該公司年報並交由AI分析
2. 推薦系統: 每日進行標的更新，背後透過交易策略、技術指標(Markov chains、RSI等等)自動幫你篩選
3. 近況分析: 輸入股票代號(eg. 2330)，即可爬取該股的新聞

### 🌟 驗證功能 🌟
使用推薦系統時，需要先進行註冊or Line 的 LIFF 驗證才可使用哦 !

### 🌟 技術 🌟
1. 前端: React
2. 後端: Flask
3. 驗證機制: LIFF (LINE Front-end Framework)
4. 資料庫: MongoDB Atlas
5. RAG技術: LangChain
6. API: gpt-4o-mini

<img width="300" alt="image" src="https://github.com/YIFUNLIN/Line_bot/blob/main/images/main.jpg" />



## 系統架構圖:

![system](https://github.com/YIFUNLIN/Line_bot/blob/main/images/system_architecture.png)

### 系統後台 :
1. 串接MongoDB Atlas 存放財報分析時所爬取的年報
若日後需要用到相同資料，則直接從DB拿取，以提升系統運作效率
![MongoDB](https://github.com/YIFUNLIN/Line_bot/blob/main/images/mongodb.png)

2. 存放使用者註冊資料，並於登錄時進行比對
<img width="684" alt="image" src="https://github.com/user-attachments/assets/9389948e-b2d9-4764-a9a7-b9c25d5dede6" />

3. 若使用者透過LINE 進行登入，會觸發liff.getProfile()，將資料回傳到後端
![LIFF_DB](https://github.com/YIFUNLIN/Line_bot/blob/main/images/LIFF_DB_store.png)

### 串接股票推薦系統網站 :
#### 1. 前端: 
- 使用 React 框架構建會員登入系統，實現動態渲染與狀態管理
- 使用 Axios 與後端 API 進行交互，完成資料傳遞與操作
#### 2. 後端: 
- 使用 Flask 框架實現後端 API，負責處理前端傳來的請求
- 完成用戶資料驗證、登入與註冊邏輯，並與資料庫進行交互
#### 3. LIFF:  
- 利用 LIFF API，實現與 LINE 平台的整合：
    - 獲取用戶在選擇 LINE Login 時的資料（如用戶名稱、照片URL、LINE User ID）
    - 獲取用戶的 Access Token，用於後端進行身份驗證
- 在 LINE 的內建瀏覽器（WebView） 中運行應用，無需離開 LINE 即可完成登入與操作

---
- 使用 Flex message 客製化 UI 提供點擊介面
<img width="300" alt="image" src="https://github.com/YIFUNLIN/Line_bot/blob/main/images/flex_message.jpg" />


- 先進入會員登入系統
<img width="300" alt="image" src="https://github.com/YIFUNLIN/Line_bot/blob/main/images/root_dir.jpg" />


- 可選擇 LINE Login 或 Email 註冊登入

<img width="300" alt="image" src="https://github.com/YIFUNLIN/Line_bot/blob/main/images/Line_login.jpg" />

<img width="300" alt="image" src="https://github.com/YIFUNLIN/Line_bot/blob/main/images/email_register.jpg" />


- 登入後即可進入推薦系統
![recommend system](https://github.com/YIFUNLIN/Line_bot/blob/main/images/rec_sysyem.png?raw=true)

🌟 系統簡介:
利用每日的股價資訊，搭配技術指標（如 MA、RSI、MACD）公式計算出訊號以豐富 Dataframe 欄位特徵，並利用這些資料訓練與構建出 LSTM 模型，並基於過去的價格與技術指標預測未來收盤價格。
根據預測價格與當前價格進行比較，同時搭配 Sharpe Ratio、Markov Chain 進行判斷以觸發買入或賣出信號，最後利用 Jinja2 將後端執行邏輯結果渲染至前端模板，並利用 Github Actions 每日自動排程。

🌟 特點:
1. 技術指標與 AI 結合應用 :
    - 結合技術分析指標（MA、RSI、MACD )、Max drawdown、Sharpe Ratio 和 Maximum Drawdown
    - 訓練 LSTM 模型 

2. 程式化交易策略
    - 整合 LSTM 模型進行預測，並搭配Sharpe Ratio、Markov Chain 趨勢分析，自動判斷作為買賣訊號來源
    - 考慮交易成本與滑點，模擬真實交易場景

3. 系統建置技術
    - 使用 Jinja2 自動生成報告，結合 Github Actions 每日進行排程實現自動更新


![git](https://github.com/YIFUNLIN/Line_bot/blob/main/images/git.png)


### 🌟 Functional Testing:
使用 Postman 針對這 4 支 API 進行 Functional Testing (功能測試) 
- GET : `/` 、`/recommend/` 、`/recommend/<path>`
- POST: `/api/save_user` 、`/api/login` 

1. 先對 `GET` method 進行 Testing :

`/`
![testing](https://github.com/YIFUNLIN/Line_bot/blob/main/images/image.png)


`/recommend/`

![testing](https://github.com/YIFUNLIN/Line_bot/blob/main/images/image-1.png)

`/recommend/<path>`

![testing](https://github.com/YIFUNLIN/Line_bot/blob/main/images/image-2.png)


2. 針對 `POST`method 進行 Testing :

`/api/save_user` (用來註冊)
- 利用 POST進行使用 Email 註冊的測試，並成功註冊

![testing](https://github.com/YIFUNLIN/Line_bot/blob/main/images/image-3.png)


資料也自動寫入至 MongoDB

![testing](https://github.com/YIFUNLIN/Line_bot/blob/main/images/image-4.png)


`/api/login` 會去MongoDB 比對有無此筆資料

![testing](https://github.com/YIFUNLIN/Line_bot/blob/main/images/image-5.png)


![testing](https://github.com/YIFUNLIN/Line_bot/blob/main/images/image-6.png)
