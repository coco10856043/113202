#-----------------------
# 匯入模組
#-----------------------
from flask import Flask, render_template, request, Response, jsonify ,redirect,url_for
from utils import db
import requests, bcrypt
import os, time

#引入openai
from openai import OpenAI
import logging
import hashlib
import psycopg2
from psycopg2 import pool

# from collections import OrderedDict

#-----------------------
# 產生Flask app物件
#-----------------------
print (__name__)
app = Flask(__name__)

#-----------------------
# 設定路由
#-----------------------
#初入網頁
@app.route('/')
def first():
    return render_template('index.html')

#歷史創作按鈕
@app.route('/afterlogin_home', methods=['GET'])
def afterlogin_home():
    name = request.args.get('name')
    return render_template('home.html', name = name)

#進入登入畫面
@app.route('/login')
def login():
    return render_template('login.html')

#登入動作
@app.route('/home', methods=['POST'])
def home():
    try:
        # 取得參數
        title = request.form.get('title')
        password = request.form.get('password')

        # 取得資料庫連線
        conn = db.get_connection()

        # 查詢資料表
        cursor = conn.cursor()
        cursor.execute("select * from user_information where user_id = %s", (title,))
        user = cursor.fetchone()
        

        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            cursor.execute("select name from user_information where user_id = %s", (title,))
            name = cursor.fetchone()
            conn.close()
            # 渲染成功畫面
            return render_template('home.html', name = name[0])
        else:
            conn.close()
            # 渲染失敗畫面
            return render_template('login.html', error_message="登入失敗")
    except Exception as e:
        print(f"Error: {e}")
        conn.close()
        # 渲染失敗畫面
        return render_template('login.html', error_message="登入失敗")

#我要註冊按鈕
@app.route('/register')
def register():
    return render_template('register.html')

#註冊動作
@app.route('/do_register', methods=['POST'])
def do_register():
    try:
        #取得參數
        title = request.form.get('title')
        name = request.form.get('name')
        password = request.form.get('password')
        child_birth = request.form.get('child_birth')
        child_gender = request.form['age']
        
        #取得資料庫連線
        conn = db.get_connection()
        #將資料加入資料表
        cursor = conn.cursor()
        cursor.execute("select * from user_information where user_id = %s or name = %s", (title, name, ))
        user = cursor.fetchone()
        conn.close()
        try:
            child_birth = int(child_birth)
            if '@' in title and len(title) > 10:
                if user:
                    # 渲染失敗畫面
                    return render_template('register.html', error_message="註冊失敗，帳號或使用者名稱可能已被使用")
                elif title == name:
                    # 渲染失敗畫面
                    return render_template('register.html', error_message="註冊失敗，為了保護使用者，帳號與使用者名稱請不要使用同一個")
                elif int(child_birth) < 0 or int(child_birth) > 100:
                    # 渲染失敗畫面
                    return render_template('register.html', error_message="註冊失敗，孩子的年齡有誤")
                else:
                    hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    #取得資料庫連線
                    conn = db.get_connection()
                    #將資料加入資料表
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO user_information (user_id, name, password, child_gender, child_birth) VALUES (%s, %s, %s, %s, %s)", (title, name, hash_password, child_gender, child_birth))
                    conn.commit()
                    conn.close()

                    # 渲染成功畫面
                    return render_template('login.html', success_message ="註冊成功")
            else:
                return render_template('register.html', error_message="註冊失敗，帳號輸入格式有誤，可能缺少@符號或是長度不夠")
        except ValueError:
            # 渲染失敗畫面
            return render_template('register.html', error_message="註冊失敗，孩子的年齡有誤")
    except:
        # 渲染失敗畫面
        return render_template('register.html', error_message="註冊失敗")

# ============================================================================================
# 處理中
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "OPENAI_API_KEY"))

@app.route('/get-ai-json', methods=['POST'])
def get_ai_json():

    style = "校園風"
    text = "這是一個講述誠實的故事"
    question = f"故事風格為 {style}，故事大綱為 {text}"
    # theme = request.form.get('theme')

    thread = client.beta.threads.create()

    # Create a message to append to our thread
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question,
    )

    # Execute our run
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id='OPENAI_API_KEY',
    )

    def wait_on_run(run, thread):
        while run.status == "queued" or run.status == "in_progress":
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )
        return run
    
    run = wait_on_run(run, thread)

    # Retrieve all the messages added after our last user message
    messages = client.beta.threads.messages.list(
        thread_id = thread.id
    )

    for message in reversed(messages.data):
        data = message.content[0].text.value

    # 獲取回應內容
    # data = data.replace('"', "")

    data = data.replace("[", "")
    data = data.replace("]", "")

    # 將回應內容轉換為 JSON 格式，並按照指定格式進行分隔
    story_lines = data.split('\n')
    story_lines = [line for line in story_lines if line.strip()]

    lines = [line.replace("},", "}") for line in story_lines]
    print(lines)
    # 將回應以 JSON 格式返回
    return jsonify({"response": lines})

#生圖測試1(成功用OPENAI函數)
save_folder = r"C:\Users\VTGHOKJUQASWQ\Desktop\0710整合\static\image\story"
os.makedirs(save_folder, exist_ok=True)

# 設定日誌記錄
logging.basicConfig(level=logging.INFO)

def hash_image_content(content):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content)
    return sha256_hash.hexdigest()

def generate_single_image(prompt, i):
    try:
        response = client.images.generate(
            prompt=prompt,
            model="dall-e-3",
            n=1,
            size="1024x1024"
        )

        image_url = response.data[0].url
        image_response = requests.get(image_url)

        if image_response.status_code == 200:
            content = image_response.content
            hashed_name = hash_image_content(content)
            image_path = os.path.join(save_folder, f"{hashed_name}.png")
            with open(image_path, 'wb') as f:
                f.write(content)
            logging.info(f"第{i+1}張圖片已保存至 {image_path}")
            return image_path
        else:
            logging.error(f"下載第{i+1}張圖片失敗: {image_response.status_code}")
            return None
    except Exception as e:
        logging.error(f"生成第{i+1}張圖片時出現錯誤: {str(e)}")
        return None

@app.route('/ai-image', methods=['POST'])
def generate_images():
    picture = request.form.get('picture')
    prompt = "純圖片，藝術風格：柔和、飽和的顏色" + picture
    total_images = 3  # 生成5張圖片
    image_paths = []

    for i in range(total_images):
        image_path = generate_single_image(prompt, i)
        if image_path:
            image_paths.append(image_path)
        else:
            return jsonify({"message": f"生成第{i+1}張圖片失敗"}), 500

    return jsonify({"message": "success! Check your folder", "image_paths": image_paths})


# ============================================================================================
## 待處理

#歷史創作按鈕
@app.route('/myStory', methods=['GET'])
def myStory():
    name = request.args.get('name')
    return render_template('myStory.html', name = name)

#歷史創作按鈕
@app.route('/collection', methods=['GET'])
def collection():
    name = request.args.get('name')
    return render_template('collection.html', name = name)


#歷史創作按鈕
# @app.route('/follow', methods=['GET'])
# def follow():
#     name = request.args.get('name')
#     return render_template('follow.html', name = name)


#顯示追蹤作者
@app.route('/follow', methods=['GET'])
def follow():
    name = request.args.get('name')
    user_id = f"@aa{name}" 
    # user_id  =request.args.get('user_id ')
    if user_id :
        conn = db.get_connection()
        cur = conn.cursor()       
        # 使用參數化查詢來防止 SQL 注入
        cur.execute("SELECT follow_user FROM follow WHERE user_id = %s", (user_id ,))      
        # 獲取所有結果
        follow_data = cur.fetchall()
        cur.close()
        conn.close()
        followed_users = [row[0] for row in follow_data]
    return render_template('follow.html', user_id =user_id , followed_users=followed_users)
#顯示追蹤作者



#上傳圖片到資料庫_開始
# @app.route('/add_avatar', methods=['POST'])
# def upload_file():
#     if 'file' not in request.files:
#         return redirect(request.url)
#     file = request.files['file']
#     if file.filename == '':
#         return redirect(request.url)
#     if file:
#         filename = file.filename
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         file.save(filepath)
        
#         # 將圖片路徑儲存到資料庫
#         conn = db.get_connection()
#         cursor = conn.cursor()
#         user_id = request.form['user_id']
#         cursor.execute("UPDATE user_information SET avatar_id = %s WHERE user_id = %s", (filename, user_id))
#         conn.commit()
#         cursor.close()
#         conn.close()

#         return redirect(url_for('add_avatar', user_id=user_id))



# 顯示用戶頭像
# @app.route('/user_profile?name=')
# def display_avatar(name):
#     name = request.args.get('name')
#     user_id = f"@aa{name}"
#     conn = db.get_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT avatar_id FROM user_information WHERE user_id = %s", (user_id,))
#     avatar = cursor.fetchone()
#     cursor.close()
#     conn.close()
#     if avatar:
#         avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], avatar[0])
#         return render_template('/user_profile.html', avatar_path=avatar_path)
#     else:
#         return "Avatar not found", 404



#第二版
# @app.route('/add_avatar', methods=['POST'])
# def upload_file():
#     if 'file' not in request.files:
#         return jsonify({'error': '沒有檔案部分'}), 400
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({'error': '沒有選擇檔案'}), 400
    
#     # 讀取文件內容
#     file_content = file.read()
    
#     # 使用 SHA-256 生成圖片的雜湊值
#     hash_object = hashlib.sha256(file_content)
#     hash_value = hash_object.hexdigest()
    
#     # 將文件內容轉換為 base64 編碼
#     file_content_b64 = base64.b64encode(file_content).decode('utf-8')
    
#     # 將圖片內容和雜湊值儲存到資料庫
#     conn = db.get_connection()
#     cursor = conn.cursor()
#     user_id = request.form.get('user_id')
    
#     try:
#         # 假設 avatar 表有 user_id, hash_value, image_data 欄位
#         cursor.execute("""
#             INSERT INTO user_information (user_id, hash_value, image_data) 
#             VALUES (%s, %s, %s) 
#             ON CONFLICT (user_id) DO UPDATE 
#             SET hash_value = EXCLUDED.hash_value, 
#                 image_data = EXCLUDED.image_data
#         """, (user_id, hash_value, file_content_b64))
        
#         # 更新 user_information 表中的 avatar_id
#         cursor.execute("""
#             UPDATE user_information 
#             SET avatar_id = %s 
#             WHERE user_id = %s
#         """, (hash_value, user_id))
        
#         conn.commit()
#         return jsonify({'success': True, 'hash_value': hash_value}), 200
#     except Exception as e:
#         conn.rollback()
#         return jsonify({'error': str(e)}), 500
#     finally:
#         cursor.close()
#         conn.close()

# @app.route('/user_profile', methods=['GET'])
# def get_avatar():
#     name = request.args.get('name')
#     user_id = f"@aa{name}" 
#     conn = db.get_connection()
#     cursor = conn.cursor() 
#     try:
#         cursor.execute("SELECT avatar_id FROM user_imforment WHERE user_id = %s", (user_id,))
#         result = cursor.fetchone()
#         if result:
#             return jsonify({'image_data': result[0]}), 200
#         else:
#             return jsonify({'error': '找不到頭像'}), 404
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
#     finally:
#         cursor.close()
#         conn.close()
#         return render_template('user-profile.html', user_id =user_id )
# #第二版




# #第三版
# def upload_avatar(user_id, file_path):
#     try:
#         # 讀取圖片檔案
#         with open(file_path, "rb") as file:
#             file_content = file.read()
        
#         # 計算 hash 值
#         hash_object = hashlib.sha256(file_content)
#         hash_value = hash_object.hexdigest()
        
#         # 將圖片轉換為 base64 字串
#         # file_content_b64 = base64.b64encode(file_content).decode('utf-8')

#         # 假設 avatar 表有 user_id, hash_value, image_data 欄位
#         conn = db.get_connection()
#         cursor = conn.cursor()
#         cursor.execute("""
#             INSERT INTO  user_information (user_id, avatar_id) 
#             VALUES (%s, %s) 
#             ON CONFLICT (user_id) DO UPDATE 
#             SET avatar_id = EXCLUDED.hash_value, 
#         """, (user_id, hash_value))
        
#         # 更新 user_information 表中的 avatar_id
#         cursor.execute("""
#             UPDATE user_information 
#             SET avatar_id = %s 
#             WHERE user_id = %s
#         """, (hash_value, user_id))
        
#         conn.commit()
#         return jsonify({'success': True, 'hash_value': hash_value}), 200
#     except Exception as e:
#         conn.rollback()
#         return jsonify({'error': str(e)}), 500
#     finally:
#         cursor.close()
#         conn.close()


#第三版
# name = request.args.get('name')
# user_id = f"@aa{name}" 
# conn = db.get_connection()
# 第四版
# db_pool = psycopg2.pool.SimpleConnectionPool(1, 20,)
# DB_HOST = "hattie.db.elephantsql.com"
# DB_NAME = "zjthptvz"
# DB_USER = "zjthptvz"
# DB_PASSWORD = "wFC04bEPVsG31QbU8T3KG_aRHeiQl9ay"


# def get_db_connection():
#     try:
#         conn = db.get_connection()
#         if conn:
#             return conn
#     except Exception as e:
#         print(f"Error: {e}")
#     return None

@app.route('/add_avatar', methods=['POST'])
def add_avatar():
    conn = None
    cursor = None
    try:
        user_id = request.form['user_id']
        file = request.files['file']
        file_content = file.read()

        # 計算 hash 值
        hash_object = hashlib.sha256(file_content)
        hash_value = hash_object.hexdigest()

        conn = db.get_connection()
        if conn is None:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = conn.cursor()

        # 將 hash 值插入或忽略到 avatar 表，不指定 avatar_id
        cursor.execute("""
            INSERT INTO avatar (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
        """, (hash_value,))

        # 獲取剛插入的 avatar_id
        cursor.execute("""
            SELECT avatar_id FROM avatar WHERE name = %s
        """, (hash_value,))
        avatar_id = cursor.fetchone()[0]

        # 更新 user_information 表中的 avatar_id
        cursor.execute("""
            UPDATE user_information 
            SET avatar_id = %s 
            WHERE user_id = %s
        """, (avatar_id, user_id))

        conn.commit()
        return jsonify({'success': True, 'hash_value': hash_value}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()

@app.route('/user_profile', methods=['GET'])
def get_user_profile():
    conn = None
    cursor = None
    name = request.args.get('name')
    user_id = f"@aa{name}" 
    try:
        conn = db.get_connection()
        if conn is None:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.name AS avatar_name
            FROM user_information u
            JOIN avatar a ON u.avatar_id = a.avatar_id
            WHERE u.user_id = %s
        """, (user_id,))
        result = cursor.fetchone()
        if result:
            return jsonify({'image_hash': result[0]}), 200
        else:
            return jsonify({'error': 'User or avatar not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
            return render_template('user-profile.html', user_id =user_id )

#第四版
    
#上傳圖片到資料庫_結束










# @api_view()
# # @user_login_required
# def all_review(request):
#     data = request.query_params
#     account = data.get('account')

#     account = str(account).strip()
#     restaurant_msgs = RestaurantMsg.objects.all()

#     return Response({
#         'success': True,
#         'data': [
#             {
#                 'restaurant_msg_id': restaurant_msg.restaurant_msg_id,
#                 'restaurant_id': restaurant_msg.restaurant_id,
#                 'account': restaurant_msg.account,
#                 'content': restaurant_msg.content,
#                 'time': restaurant_msg.time,
#             }
#             for restaurant_msg in restaurant_msgs
#         ]
#     })


# @api_view()
# def get_restaurant_comment(request):
#     data = request.data

#     restaurant_id = data.get('restaurant_id')
#     restaurants = RestaurantMsg.objects.filter(restaurant_id=restaurant_id)
#     if not restaurants.exists():
#         return Response({'success': False, 'message': '此餐廳沒有留言'}, status=status.HTTP_404_NOT_FOUND)
#     return Response({
#         'success': True,
#         'data': [
#             {

#                 'account': restaurant.account,
#                 'content': restaurant.content,
#                 'time': restaurant.time,
#             }
#             for restaurant in restaurants
#         ]
#     })

#follow設計1








#歷史創作按鈕
@app.route('/creation_story', methods=['GET'])
def creation_story():
    name = request.args.get('name')
    return render_template('creation.html', name = name)

#歷史創作按鈕
@app.route('/user_profile', methods=['GET'])
def user_profile():
    name = request.args.get('name')
    return render_template('user-profile.html', name = name)

#故事瀏覽按鈕
@app.route('/story_details', methods=['GET'])
def story_details():
    name = request.args.get('name')
    return render_template('story-details.html', name = name)

#test2按鈕
@app.route('/test2', methods=['GET'])
def test2():
    name = request.args.get('name')
    return render_template('test2.html', name = name)

#-----------------------
# 生成圖片與故事
#-----------------------

# # 設定OpenAI API Key
# openai.api_key = os.getenv("OPENAI_API_KEY")

# # 创建保存图像的文件夹
# save_folder = r"C:\Users\User\Desktop\311test\第六整合0627()\static\image\story"
# os.makedirs(save_folder, exist_ok=True)

# # 设置日志记录
# logging.basicConfig(level=logging.INFO)

# def hash_image_content(content):
#     sha256_hash = hashlib.sha256()
#     sha256_hash.update(content)
#     return sha256_hash.hexdigest()

# def generate_single_image(prompt, i):
#     try:
#         response = openai.Completion.create(
#             engine="dall-e-3",
#             prompt=prompt,
#             max_tokens=100,
#             n=1
#         )

#         image_url = response['choices'][0]['model']['url']
#         image_response = requests.get(image_url)

#         if image_response.status_code == 200:
#             content = image_response.content
#             hashed_name = hash_image_content(content)
#             image_path = os.path.join(save_folder, f"{hashed_name}.png")
#             with open(image_path, 'wb') as f:
#                 f.write(content)
#             logging.info(f"第{i+1}张图片已保存至 {image_path}")
#             return image_path
#         else:
#             logging.error(f"下载第{i+1}张图片失败: {image_response.status_code}")
#             return None
#     except Exception as e:
#         logging.error(f"生成第{i+1}张图片时出现错误: {str(e)}")
#         return None

# @app.route('/ai-image', methods=['POST'])
# def generate_images():
#     picture = request.form.get('picture')
#     prompt = "纯图片，艺术风格：柔和的圆滑线条，高度饱和的颜色" + picture
#     total_images = 5  # 生成5张图像
#     image_paths = []

#     for i in range(total_images):
#         image_path = generate_single_image(prompt, i)
#         if image_path:
#             image_paths.append(image_path)
#         else:
#             return jsonify({"message": f"生成第{i+1}张图片失败"}), 500

#     return jsonify({"message": "success! Check your folder", "image_paths": image_paths})

# @app.route('/get-ai-json', methods=['POST'])
# def get_ai_json():

#     theme = request.form.get('theme')

#     # 創建一個對話並發送消息
#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": "你是一個會生成兒童繪本故事的助理，請幫忙生成10句(不能少於10句)的故事，故事要完整詳細，並每句話用\n分割，請不要用從前開頭"},
#             {"role": "user", "content": theme}
#         ]
#     )

#     # 獲取回應內容
#     ai_response = response.choices[0].message["content"].replace("|", " ")

#     # 將回應內容轉換為 JSON 格式，並按照指定格式進行分隔
#     story_lines = ai_response.split('\n')
#     story_lines = [line for line in story_lines if line.strip()]

#     # 使用有序字典確保順序
#     story_json = OrderedDict((str(index + 1), line) for index, line in enumerate(story_lines))

#     # 將回應以 JSON 格式返回
#     return jsonify({"response": story_json})
#===============================================================================
# #我要註冊按鈕
# @app.route('/logout')
# def logout():
#     return render_template('login.html')

#客戶新增表單
# @app.route('/customer/create/form')
# def customer_create_form():
#     return render_template('customer_create_form.html') 

#客戶新增
# @app.route('/create', methods=['POST'])
# def customer_create():
#     try:
#         #取得參數
#         print("*****")
#         title = request.form.get('title')
#         print(title)

#         #取得資料庫連線
#         conn = db.get_connection()

#         #將資料加入customer表
#         cursor = conn.cursor()
#         cursor.execute("INSERT INTO kind (name) VALUES (%s)", (title, ))
#         print('test')
#         conn.commit()
#         conn.close()

#         # 渲染成功畫面
#         return render_template('create_success.html')
#     except:
#         # 渲染失敗畫面
#         return render_template('create_fail.html')


# @app.route('/get-json')
# def get_json():
#     # 这里你可以定义想要返回的数据
#     data = {
#         'title': '123',
#         'name': 'ABC',
#         'context': '123465ABC'
#     }
#     return jsonify(data)

# @app.route('/add-story')
# def add_story():
#     # 调用 /get-json 路由获取 JSON 数据
#     response = app.test_client().get('/get-json')
#     # 将响应数据转换为 JSON 格式
#     json_data = response.get_json()

#     # 将获取到的数据传递给 HTML 模板
#     return render_template('index.html', story=json_data)

# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "OPENAI_API_KEY"))
# # 設置你的 OpenAI API 密鑰
# #openai.api_key = "OPENAI_API_KEY"

# # 定義 /get-ai-json route
# @app.route('/get-ai-json')
# def get_ai_json():
#     thread = client.beta.threads.create()

#     # Create a message to append to our thread
#     message = client.beta.threads.messages.create(
#         thread_id=thread.id,
#         role="user",
#         content="學校",
#     )

#     # Execute our run
#     response = OpenAI.AssistantRun.create(
#         thread_id=thread.id,
#         assistant_id='OPENAI_API_KEY',
#     )

#     def wait_on_run(run, thread):
#         while run.status == "queued" or run.status == "in_progress":
#             run = client.beta.threads.runs.retrieve(
#                 thread_id=thread.id,
#                 run_id=run.id,
#             )
#             time.sleep(0.5)
#         return run

#     run = wait_on_run(run, thread)

#     # Retrieve all the messages added after our last user message
#     messages = client.beta.threads.messages.list(
#         thread_id = thread.id
#     )

#     for message in reversed(messages.data):
#         data = message.content[0].text.value
    
#     return data

# @app.route('/add')
# def add():
#     return render_template('index.html')

#-----------------------
# 執行app
#-----------------------
if __name__ == '__main__':
    app.run(port=5000, debug=True)