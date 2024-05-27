#-----------------------
# 匯入模組
#-----------------------
from flask import Flask, render_template, request, Response, jsonify
# from openai import OpenAI
import json
import openai
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


# 定義 /get-ai-json route
@app.route('/get-ai-json')
def get_ai_json():
    thread = openai.beta.threads.create()

    # Create a message to append to our thread
    message = openai.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="宇宙與少女",
    )

    # Execute our run
    run = openai.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id='asst_ID',
    )

    def wait_on_run(run, thread):
        while run.status == "queued" or run.status == "in_progress":
            run = openai.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )
            time.sleep(0.5)
        return run

    run = wait_on_run(run, thread)

    # Retrieve all the messages added after our last user message
    messages = openai.beta.threads.messages.list(
        thread_id = 'thread_ID'
    )

    for message in reversed(messages.data):
        data = message.content[0].text.value

    return data





# test生成圖片

# desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
# save_folder = os.path.join(desktop_path, "generated_images")

# # 確保資料夾存在
# os.makedirs(save_folder, exist_ok=True)
# openai.api_key = os.environ.get("OPENAI_API_KEY", "")
# @app.route('/ai-image', methods=['GET'])
# def generate_image():
#     # 硬編碼的生成指令
#     prompt = " 藝術風格：柔和的圓滑線條，高度飽和的顏色，以及迷人的童話般氛圍 '小紅，你為什麼每天都這麼努力工作呢？”小白好奇地問。小紅微笑著回答：“因為我們需要食物和一個乾淨、安全的家，這樣我們才能在冬天不餓肚子"

#     # 使用OpenAI的DALL-E 3模型生成圖片
#     response = openai.Image.create(
#         prompt=prompt,
#         model="dall-e-3" ,
#         n=1,  # 生成1張圖片
#         size="1024x1024"  # 圖片尺寸
#     )

#     # 獲取生成的圖片URL
#     image_url = response['data'][0]['url']

#     # 下載圖片並保存到指定資料夾
#     image_response = requests.get(image_url)
#     if image_response.status_code == 200:
#         timestamp = int(time.time())  # 使用時間戳來確保文件名唯一
#         image_path = os.path.join(save_folder, f"{prompt}_{timestamp}.png")
#         with open(image_path, 'wb') as f:
#             f.write(image_response.content)
#         return jsonify({"message": "success!!check you folder"})
#     else:
#         return jsonify({"message": "fail"}), 500
# test生成故事


# 流水號版
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
save_folder = os.path.join(desktop_path, "generated_images")
os.makedirs(save_folder, exist_ok=True)

# 設定OpenAI API Key
openai.api_key = os.environ.get("OPENAI_API_KEY", "KEY")

# 初始化批次和圖片號
current_batch = 1
current_number = 0

def get_next_serial():
    global current_batch, current_number
    
    # 增加圖片號
    current_number += 1

    # 每批次最多10張圖片，超過後進入下一批次
    if current_number > 10:
        current_batch += 1
        current_number = 1

    return f'{current_batch}_{current_number}'

@app.route('/ai-image', methods=['GET'])
def generate_image():
    prompt = "純圖片，藝術風格：柔和的圓滑線條，高度飽和的顏色，以及迷人的童話般氛圍 '一天，村莊附近的森林中出現了一隻神秘的野狼，村民們都非常擔心。阿明決定和小紅一起去探查這隻野狼的真相。他們準備了一些食物和水，踏上了冒險之旅。"

    response = openai.Image.create(
        prompt=prompt,
        model="dall-e-3",
        n=1,
        size="1024x1024"
    )

    image_url = response['data'][0]['url']
    image_response = requests.get(image_url)
    if image_response.status_code == 200:
        serial_number = get_next_serial()
        image_path = os.path.join(save_folder, f"{serial_number}.png")
        with open(image_path, 'wb') as f:
            f.write(image_response.content)
        return jsonify({"message": "success! Check your folder"})#傳送圖片雜奏名稱
    else:
        return jsonify({"message": "fail"}), 500



#-----------------------
# 執行app
#-----------------------
if __name__ == '__main__':
    app.run(port=5000, debug=True)