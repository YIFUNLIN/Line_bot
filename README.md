# ﻿Financial Line_bot
歡迎使用投資理財小幫手😀
本系統提供三大功能:
1. 財報分析: 輸入股票代號與年份(eg. 2330 112)，即可自動爬找該公司年報並交由AI分析
2. 推薦系統: 每日進行標的更新，背後透過交易策略、技術指標(Markov chains、RSI等等)自動幫你篩選
3. 近況分析: 輸入股票代號(eg. 2330)，即可爬取該股的新聞

🌟 隱藏功能 🌟
聊天室中輸入: 推薦 or 推薦系統，即可透過LIFF去呼叫該網站 

![recommend system](https://github.com/YIFUNLIN/Line_bot/blob/main/images/rec_sysyem.png?raw=true)



## 系統架構圖:
(待更)

### 系統後台 :
1. 串接MongoDB Atlas
![image](https://hackmd.io/_uploads/S1hy_J941l.png)

### 串接股票推薦系統網站 :
![image](https://hackmd.io/_uploads/SyhO_1941g.png)

- 利用 LIFF 進行前後端串接此系統

https://yifunlin.github.io/stock/stock_report.html

- 此系統是基於 Github Action 自動每日進行排程更新

![image](https://hackmd.io/_uploads/SyI-tJqNyg.png)

程式碼: https://github.com/YIFUNLIN/stock/tree/main

