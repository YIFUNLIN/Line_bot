from dotenv import load_dotenv 
import os
import requests
from bs4 import BeautifulSoup
from langchain.document_loaders import PyPDFLoader
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from pymongo import MongoClient

load_dotenv()

ENDPOINT = os.environ.get('mongodb_endpoint', '')
client = MongoClient(ENDPOINT)
db = client['mydatabase']
collection = db['Financial_report']

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

def perform_financial_analysis(stock_id, year):
    pdf_path = f"./{stock_id}_{year}.pdf"  # 預設 PDF 路徑
    try:
        # 先去DB中查找是否有相同的 stock_id 和 year 的財報
        existing_document = collection.find_one({'stock_id': stock_id, 'year': year})
        if existing_document:
            print("已存在，直接從DB中提取")
            pdf_content = existing_document["content"]
            
            # 將DB中的pdf content 寫入成文件
            with open(pdf_path, "wb") as f:
                f.write(pdf_content)
        else:  # DB中找不到的話再去爬蟲
            url = "https://doc.twse.com.tw/server-java/t57sb01"

            # 年報爬蟲code
            # 第一個請求
            data = {
                'id': '',
                'key': '',
                'step': '1',
                'co_id': stock_id,
                'year': year,
                'seamon': '',
                'mtype': 'F',
                'dtype': 'F04'
            }

            response = requests.post(url, data=data) # 透過POST請求(傳入stockID、year)
            link = BeautifulSoup(response.text, 'html.parser')
            filename_tag = link.find('a')
            if not filename_tag:
                return "無法找到財報檔案，請確認輸入的股票代號與年份是否正確。"
            filename = filename_tag.text

            # 第二個請求
            data2 = {
                'step': '9',
                'kind': 'F',
                'co_id': stock_id,
                'filename': filename
            }

            response = requests.post(url, data=data2)
            link = BeautifulSoup(response.text, 'html.parser')
            href_tag = link.find('a')
            if not href_tag:
                return "無法找到財報下載連結"
            download_link = href_tag.get('href')  

            # 下載 PDF 並進行分析
            response = requests.get('https://doc.twse.com.tw' + download_link)
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            pdf_content = response.content
            
            # 將 結果 存入 MongoDB
            document = {
                "stock_id": stock_id,
                "year": year,   
                "content": pdf_content
            }
            collection.insert_one(document)
            print(f"成功儲存{stock_id}_{year}的年報")

        # 使用 LangChain 分析 PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY) # 生成向量嵌入
        vectorstore = FAISS.from_documents(documents, embeddings)  # 使用vectorDB:FAISS 主打高效檢索

        qa_chain = load_qa_chain(   # 問答鏈
            ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY),
            chain_type="stuff"  # 'stuff': 將所有檢索到的文檔串接一起再傳給LLM
        )

        questions = [
            "請精簡總結這份財報與整理出財務狀況、經營績效與未來股價的展望。"
        ]

        results = []
        for question in questions:
            result = qa_chain.run(input_documents=vectorstore.similarity_search(question), question=question) # VectorDB利用相似性檢索相關PDF段落
            results.append(f"{result}")

        return "\n\n".join(results)

    except Exception as e:
        return f"下載或分析財報失敗，錯誤原因：{e}"

def perform_recent_analysis(stock_id):
    url = f"https://ess.api.cnyes.com/ess/api/v1/news/keyword?q={stock_id}&limit=3&page=1"
    try:
        response = requests.get(url)
        response.raise_for_status()  # 確保請求成功
        json_data = response.json()

        # 確認資料格式並擷取前三筆新聞
        items = json_data.get('data', {}).get('items', [])
        if not items:
            return f"無法找到與 {stock_id} 相關的新聞資料。"

        news = []
        for item in items[:3]:
            title = item['title']
            news_id = item['newsId']
            link = f"https://news.cnyes.com/news/id/{news_id}"
            news.append(f"標題: {title}\n連結: {link}")

        news_list = "\n\n".join(news)
        return f"以下是與 {stock_id} 相關的最新新聞：\n\n{news_list}"

    except Exception as e:
        return f"無法取得或分析近況，錯誤原因：{e}"