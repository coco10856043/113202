#-----------------------
# 匯入模組
#-----------------------
from flask import Flask, render_template, request, Response, jsonify
from openai import OpenAI
from utils import db
import requests
import os, time

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

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "OPENAI_API_KEY"))
# 設置你的 OpenAI API 密鑰

# 定義 /get-ai-json route
@app.route('/get-ai-json')
def get_ai_json():
    thread = client.beta.threads.create()

    # Create a message to append to our thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="School",
    )

    # Execute our run
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id='assistant_id',
    )

    def wait_on_run(run, thread):
        while run.status == "queued" or run.status == "in_progress":
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )
            time.sleep(0.5)
        return run

    run = wait_on_run(run, thread)

    # Retrieve all the messages added after our last user message
    messages = client.beta.threads.messages.list(
        thread_id = 'thread_id'
    )

    for message in reversed(messages.data):
        data = message.content[0].text.value

    return data

# @app.route('/add')
# def add():
#     return render_template('index.html')

#-----------------------
# 執行app
#-----------------------
if __name__ == '__main__':
    app.run(port=5000, debug=True)