# ﻿Financial Line_bot
歡迎使用投資理財小幫手😀

影片連結: https://www.youtube.com/watch?v=LrBWKAA-1_Q

本系統提供三大功能:
1. 財報分析: 輸入股票代號與年份(eg. 2330 112)，即可自動爬找該公司年報並交由AI分析
2. 推薦系統: 每日進行標的更新，背後透過交易策略、技術指標(Markov chains、RSI等等)自動幫你篩選
3. 近況分析: 輸入股票代號(eg. 2330)，即可爬取該股的新聞

🌟 驗證功能 🌟
使用推薦系統時，需要先進行註冊or Line 的 LIFF 驗證才可使用哦 !

![main](https://github.com/YIFUNLIN/Line_bot/blob/main/images/main.jpg)

## 系統架構圖:
(待更)

### 系統後台 :
1. 串接MongoDB Atlas 存放財報分析時所爬取的年報
若日後需要用到相同資料，則直接從DB拿取，以提升系統運作效率
![MongoDB](https://github.com/YIFUNLIN/Line_bot/blob/main/images/mongodb.png)

2. 存放使用者註冊資料，並於登錄時進行比對
<img width="684" alt="image" src="https://github.com/user-attachments/assets/9389948e-b2d9-4764-a9a7-b9c25d5dede6" />


### 串接股票推薦系統網站 :
利用 LIFF 進行與 Linebot 的前後端串接

![recommend system](https://github.com/YIFUNLIN/Line_bot/blob/main/images/rec_sysyem.png?raw=true)

🌟 特點:
1. 金融指標應用:
- 結合技術分析指標（MA、RSI、MACD）和數據標準化，優化模型輸入
- 引入 Sharpe Ratio 和 Maximum Drawdown，評估投資績效
2. 程式化交易策略
- 整合 LSTM 模型預測與 Markov Chain 趨勢分析，自動判斷買賣信號
- 考慮交易成本與滑點，模擬真實交易場景
3. 系統建置技術
- 採用 Keras Tuner 調整超參數，提升模型效能
- 使用 Jinja2 自動生成報告，結合批次處理支持多檔股票分析、連接 Goodinfo
- 整體系統架構具有靈活性與可擴展性，適用於不同投資需求
  
- 此系統是基於 Github Action 自動每日進行排程更新

![git](https://github.com/YIFUNLIN/Line_bot/blob/main/images/git.png)

程式碼: https://github.com/YIFUNLIN/stock/tree/main
