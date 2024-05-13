#-----------------------
# 匯入模組
#-----------------------
from flask import Flask, render_template, request, Response, jsonify
from utils import db
import requests

#-----------------------
# 產生Flask app物件
#-----------------------
print (__name__)
app = Flask(__name__)

#-----------------------
# 設定路由
#-----------------------
@app.route('/')
def index():
    return render_template('index.html')


#客戶新增表單
# @app.route('/customer/create/form')
# def customer_create_form():
#     return render_template('customer_create_form.html') 

#客戶新增
@app.route('/create', methods=['POST'])
def customer_create():
    try:
        #取得參數
        print("*****")
        title = request.form.get('title')
        print(title)

        #取得資料庫連線
        conn = db.get_connection()

        #將資料加入customer表
        cursor = conn.cursor()
        cursor.execute("INSERT INTO kind (name) VALUES (%s)", (title, ))
        print('test')
        conn.commit()
        conn.close()

        # 渲染成功畫面
        return render_template('create_success.html')
    except:
        # 渲染失敗畫面
        return render_template('create_fail.html')


@app.route('/get-json')
def get_json():
    # 这里你可以定义想要返回的数据
    data = {
        'title': '123',
        'name': 'ABC',
        'context': '123465ABC'
    }
    return jsonify(data)

@app.route('/add-story')
def add_story():
    # 调用 /get-json 路由获取 JSON 数据
    response = app.test_client().get('/get-json')
    # 将响应数据转换为 JSON 格式
    json_data = response.get_json()

    # 将获取到的数据传递给 HTML 模板
    return render_template('index.html', story=json_data)

@app.route('/get-ai-json', methods=['GET'])
def get_ai_json():
    # 从请求URL参数中获取问题
    question = request.args.get('question', 'create a story')  # 如果没有提供问题，默认问题是 "What is AI?"
    openai_api_key = "openai_api_key"  # 替换为你的OpenAI API密钥

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}'
    }

    # 替换为文档中指定的当前可用模型
    data = {
        "model": "gpt-3.5-turbo",  # 替换为最新的可用模型
        "messages": [{"role": "system", "content": "You are a helpful assistant."}, 
                     {"role": "user", "content": question}]
    }

    # 发送请求到 OpenAI API 的聊天型模型端点
    response = requests.post('https://api.openai.com/v1/chat/completions', json=data, headers=headers)
    response_json = response.json()
    if response.status_code == 200:
        answer = response_json.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        return jsonify({'question': question, 'answer': answer})
    else:
        # 如果发生错误，返回错误信息
        return jsonify({'error': response_json.get('error', 'Unknown error')})



# @app.route('/add')
# def add():
#     return render_template('index.html')

#-----------------------
# 執行app
#-----------------------
if __name__ == '__main__':
    app.run(port=5000, debug=True)