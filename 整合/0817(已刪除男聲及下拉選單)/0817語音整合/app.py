#-----------------------
# 匯入模組
#-----------------------
from flask import Flask, render_template, request, Response, jsonify, redirect, url_for, session, send_from_directory
from utils import db
import requests, bcrypt
import os, time, re, shutil

#引入openai
from openai import OpenAI
import logging
import hashlib

from werkzeug.utils import secure_filename

# from collections import OrderedDict

#-----------------------
# 產生Flask app物件
#-----------------------
print (__name__)
app = Flask(__name__)

#-----------------------
# 設定一個祕鑰
#-----------------------
app.config['SECRET_KEY'] = 'itismysecretkey'

#-----------------------
# 設定路由
#-----------------------

# 初入網頁
#-----------------------
@app.route('/')
def first():
    return render_template('index.html')

@app.route('/editt')
def editt():
    return render_template('edit.html')

# 登入後畫面轉換
#-----------------------
@app.route('/afterlogin_home')
def afterlogin_home():
    username = session['username']
    return render_template('home.html', username = username)

# 進入登入畫面
#-----------------------
@app.route('/login')
def login():
    return render_template('login.html')


# 登入動作
#-----------------------
@app.route('/home', methods=['POST'])
def home():
    try:
        # 取得參數
        title = request.form.get('title')
        password = request.form.get('password')

        # 取得資料庫連線
        conn = db.get_connection()

        # 验证电子邮件格式
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if (not re.match(email_regex, title)) or len(title) <= 10:
                return render_template('login.html', error_message="登入失敗，帳號輸入格式有誤")

        # 查詢資料表
        cursor = conn.cursor()
        cursor.execute("select * from user_information where user_id = %s", (title,))
        user = cursor.fetchone()
        

        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            cursor.execute("select * from user_information where user_id = %s", (title,))
            user_information = cursor.fetchone()
            conn.close()
            user_id = user_information[0]
            username = user_information[1]
            
            session['user_id'] = user_id
            session['username'] = username

            # 渲染成功畫面
            return render_template('home.html', username = username)
        else:
            conn.close()
            # 渲染失敗畫面
            return render_template('login.html', error_message="登入失敗")
    except Exception as e:
        print(f"Error: {e}")
        conn.close()
        # 渲染失敗畫面
        return render_template('login.html', error_message="登入失敗")
    
# 進入註冊畫面
#-----------------------
@app.route('/register')
def register():
    return render_template('register.html')

# 註冊動作
#-----------------------
# 設置文件上傳目錄和允許的文件類型
UPLOAD_FOLDER = 'static/avatar'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 檢查文件類型是否允許
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/do_register', methods=['POST'])
def do_register():
    try:
        # 取得參數
        title = request.form.get('title')
        name = request.form.get('name')
        password = request.form.get('password')
        child_birth = request.form.get('child_birth')
        child_gender = request.form.get('age')
        avatar = request.files.get('avatar')

        # 验证参数
        if not (title and name and password and child_birth and child_gender):
            return render_template('register.html', error_message="所有字段都是必填的")

        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_information WHERE user_id = %s OR name = %s", (title, name))
        user = cursor.fetchone()
        conn.close()
        
        # 驗證資料
        try:
            # 验证电子邮件格式
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

            child_birth = int(child_birth)
            if (not re.match(email_regex, title)) or len(title) <= 10:
                return render_template('register.html', error_message="註冊失敗，帳號輸入格式有誤")
            if user:
                return render_template('register.html', error_message="註冊失敗，帳號或使用者名稱可能已被使用")
            if title == name:
                return render_template('register.html', error_message="註冊失敗，為了保護使用者，帳號與使用者名稱請不要使用同一個")
            if child_birth < 0 or child_birth > 100:
                return render_template('register.html', error_message="註冊失敗，孩子的年齡有誤")

            # 處理上傳的頭像
            if avatar and allowed_file(avatar.filename):
                file_extension = avatar.filename.rsplit('.', 1)[1].lower()
                filename = f"{title}.{file_extension}"  # 使用user_id作為檔名
                avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                avatar.save(avatar_path)
                print(f"File saved as {filename}")

            else:
                filename = None
                return render_template('register.html', error_message="註冊失敗，頭像上傳有誤")

            # 加密密碼並將資料儲存到資料庫
            hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user_information (user_id, name, password, child_gender, child_birth, avatar) VALUES (%s, %s, %s, %s, %s, %s)", (title, name, hash_password, child_gender, child_birth, filename))
            conn.commit()
            conn.close()

            # 渲染成功畫面
            return render_template('login.html', success_message="註冊成功")

        except ValueError:
            return render_template('register.html', error_message="註冊失敗")

    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('register.html', error_message="註冊失敗")

# 進入使用者更新資訊畫面
#-----------------------
@app.route('/user_profile')
def user_profile():
    return render_template('user-profile.html')

# 更新使用者資訊動作
#-----------------------
@app.route('/update_userinformation', methods=['POST'])
def update_userinformation():
    try:
        # 取得參數
        name = request.form.get('name')
        password = request.form.get('password')
        avatar = request.files.get('avatar')

        user_id = session['user_id']

        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_information WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        conn.close()

        user_name = user[1]
        user_password = user[2]
        user_avatar = user[5]

        try:
            if name:
                # 取得資料庫連線
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM user_information WHERE name = %s", (name,))
                user = cursor.fetchone()
                conn.close()

                if user and user[0] == user_id:
                    return render_template('user-profile.html', error_message="更新無效")
                elif user:
                    return render_template('user-profile.html', error_message="更新失敗，暱稱可能已被使用")
                else:
                    user_name = name

            if password:
                # 加密密碼並將資料儲存到資料庫
                hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                user_password = hash_password

            # 處理上傳的頭像
            if avatar and allowed_file(avatar.filename):
                file_extension = avatar.filename.rsplit('.', 1)[1].lower()
                filename = f"{user_id}.{file_extension}"  # 使用user_id作為檔名
                avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                avatar.save(avatar_path)
                print(f"File saved as {filename}")
                user_avatar = filename

            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE user_information SET name=%s, password=%s, avatar=%s where user_id=%s", (user_name, user_password, user_avatar, user_id))
            conn.commit()
            conn.close()
            session['username'] = user_name

            # 渲染成功畫面
            print("更新成功")
            return render_template('user-profile.html', success_message="更新成功")

        except ValueError as ve:
            print(f"ValueError occurred: {ve}")
            return render_template('user-profile.html', error_message="更新失敗")

    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('user-profile.html', error_message="更新失敗")
                    
# 進入追蹤者畫面
#-----------------------
@app.route('/follow')
def follow():
    user_id = session['user_id']
    username = session['username']
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT follow_user FROM follow WHERE user_id = %s", (user_id,))
    users = cursor.fetchall()  # 改为 fetchall()
    conn.close()

    users_information = []

    for user in users:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, avatar FROM user_information WHERE user_id = %s", (user,))
        user = cursor.fetchone()
        conn.close()

        users_information.append({
            'name': user[0],
            'avatar': user[1]
        })
    
    return render_template('follow.html', username = username, users_information = users_information)

# 搜尋追蹤者畫面
#-----------------------
@app.route('/searchuser', methods=['GET'])
def searchuser():
    
    search_user = request.args.get('search_user')

    user_id = session['user_id']
    username = session['username']
    
    users_information = []
    # 找被搜尋的使用者id
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM user_information WHERE name LIKE %s", (f"%{search_user}%",))
    follow_users_id = cursor.fetchall()
    conn.close()

    if follow_users_id:
        for follow_user in follow_users_id:
            # 確認是否有先追蹤
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT follow_user FROM follow WHERE user_id = %s and follow_user = %s", (user_id, follow_user[0]))
            follow_users = cursor.fetchall()
            conn.close()

            if follow_users:
                for follow_user_id in follow_users:
                    conn = db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT name, avatar FROM user_information WHERE user_id = %s", (follow_user_id[0],))
                    user = cursor.fetchall()
                    conn.close()

                    for follow_user_information in user:
                        print(user)
                        users_information.append({
                                'name': follow_user_information[0],
                                'avatar': follow_user_information[1]
                            })

    return render_template('follow.html', username = username, users_information = users_information)

# 搜尋追蹤者畫面
#-----------------------
@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html')

# 進入故事創作畫面
#-----------------------
@app.route('/creation_story')
def creation_story():
    username = session['username']
    return render_template('creation.html', username = username)


# openai_api_key
#-----------------------
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "OPENAI_API_KEY"))

# 建立故事並進入故事編輯頁
#-----------------------
@app.route('/creation', methods=['POST'])
def creation():

    title = request.form.get('title')
    kind = request.form.get('kind')
    story_detail = request.form.get('story_detail')
    question = f"這本故事名稱叫做 {title}，故事風格為 {kind}，故事大綱為 {story_detail}"
    # theme = request.form.get('theme')

    session['story_title'] = title
    session['story_kind'] = kind
    session['story_detail'] = story_detail

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
        assistant_id='assistant_id',
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
    
    lines = [line.replace("{'", "'") for line in story_lines]
    lines = [line.replace("'}", "'") for line in lines]
    
    array_story = []

    # 處理每個字串，轉換為子陣列並加入主陣列
    for line in lines:
        # 去除首尾的引號並分割為編號和描述
        parts = line.strip("'").split("','")
        # 去除描述部分的末尾逗號
        parts[-1] = parts[-1].rstrip(',')
        parts[-1] = parts[-1].rstrip("'")
        array_story.append(parts)
        
    print(array_story)
    # return array_story
    return render_template('edit.html', story_title = title, story_kind = kind, array_story = array_story)

# 生成圖片
#-----------------------
save_folder = 'static/image/story_select'
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
            size="1792x1024"
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
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"message": "未提供消息"}), 400
        
        message = data.get('message')

        story_kind = session['story_kind']
        
        # 更新 prompt，使风格更可爱
        prompt = "故事風格為" + story_kind + "故事段落為" + message
        total_images = 1  # 生成1张图片
        image_paths = []

        for i in range(total_images):
            image_path = generate_single_image(prompt, i)
            if image_path:
                # 返回相对静态文件夹的路径
                relative_path = os.path.relpath(image_path, start='static')
                image_paths.append(f'/static/{relative_path}')
            else:
                return jsonify({"message": f"生成第{i+1}张图片失败"}), 500

        return jsonify({"message": "success", "image_paths": image_paths})

    except Exception as e:
        logging.error(f"处理请求时出现错误: {str(e)}")
        return jsonify({"message": "内部错误"}), 500

@app.route('/static/image/story/<path:filename>')
def serve_image(filename):
    return send_from_directory(save_folder, filename)

# 儲存故事動作
#-----------------------
@app.route('/save-story', methods=['POST'])
def save_story():
    try:
        # 取得參數
        openstate = request.form.get('isPublic') 
        if openstate is None:
            openstate = 'false'
        else:
            openstate = 'true'

        message1 = request.form.get('message1')
        image_filename1 = request.form.get('image-filenames1')
        message2 = request.form.get('message2')
        image_filename2 = request.form.get('image-filenames2')
        message3 = request.form.get('message3')
        image_filename3 = request.form.get('image-filenames3')
        message4 = request.form.get('message4')
        image_filename4 = request.form.get('image-filenames4')
        message5 = request.form.get('message5')
        image_filename5 = request.form.get('image-filenames5')

        story_title = session['story_title']
        story_kind = session['story_kind']
        user_id = session['user_id']
        story_detail = session['story_detail']
        # # 检查是否有任何值为空
        if not all([message1, image_filename1, message2, image_filename2,
                    message3, image_filename3, message4, image_filename4,
                    message5, image_filename5]):
            array_story = ['1', message1],['2', message2],['3', message3],['4', message4],['5', message5]
            return render_template('edit.html', error_message="儲存失敗，請檢查所有故事內容是否填寫完整或圖片是否皆生成完成。", array_story = array_story)
        
        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT kind_id FROM kind where name = %s", (story_kind, ))
        kind_id = cursor.fetchone()
        kind_id = kind_id[0]
        conn.close()

        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO story (title, kind_id, state, user_id, story_detail) VALUES (%s, %s, %s, %s, %s) RETURNING story_id", (story_title, kind_id, openstate, user_id, story_detail, ))
        # 获取生成的 story_id
        story_id = str(cursor.fetchone()[0])
        conn.commit()
        conn.close()

        # 获取文件名并定义源路径和目标路径
        source = "static/image/story_select"
        destination = "static/image/story"

        filename1 = os.path.basename(image_filename1)
        source_path1 = os.path.join(source, filename1)
        destination_path1 = os.path.join(destination, filename1)
        # 确保目标目录存在
        os.makedirs(os.path.dirname(destination_path1), exist_ok=True)
        # 移动文件
        shutil.move(source_path1, destination_path1)
        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pages (story_id, page, content, picture) VALUES (%s, %s, %s, %s)", (int(story_id), 1, message1, filename1, ))
        conn.commit()
        conn.close()

        filename2 = os.path.basename(image_filename2)
        source_path2 = os.path.join(source, filename2)
        destination_path2 = os.path.join(destination, filename2)
        # 确保目标目录存在
        os.makedirs(os.path.dirname(destination_path2), exist_ok=True)
        # 移动文件
        shutil.move(source_path2, destination_path2)
        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pages (story_id, page, content, picture) VALUES (%s, %s, %s, %s)", (int(story_id), 2, message2, filename2, ))
        conn.commit()
        conn.close()

        filename3 = os.path.basename(image_filename3)
        source_path3 = os.path.join(source, filename3)
        destination_path3 = os.path.join(destination, filename3)
        # 确保目标目录存在
        os.makedirs(os.path.dirname(destination_path3), exist_ok=True)
        # 移动文件
        shutil.move(source_path3, destination_path3)
        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pages (story_id, page, content, picture) VALUES (%s, %s, %s, %s)", (int(story_id), 3, message3, filename3, ))
        conn.commit()
        conn.close()

        filename4 = os.path.basename(image_filename4)
        source_path4 = os.path.join(source, filename4)
        destination_path4 = os.path.join(destination, filename4)
        # 确保目标目录存在
        os.makedirs(os.path.dirname(destination_path4), exist_ok=True)
        # 移动文件
        shutil.move(source_path4, destination_path4)
        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pages (story_id, page, content, picture) VALUES (%s, %s, %s, %s)", (int(story_id), 4, message4, filename4, ))
        conn.commit()
        conn.close()

        filename5 = os.path.basename(image_filename5)
        source_path5 = os.path.join(source, filename5)
        destination_path5 = os.path.join(destination, filename5)
        # 确保目标目录存在
        os.makedirs(os.path.dirname(destination_path5), exist_ok=True)
        # 移动文件
        shutil.move(source_path5, destination_path5)
        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pages (story_id, page, content, picture) VALUES (%s, %s, %s, %s)", (int(story_id), 5, message5, filename5, ))
        conn.commit()
        conn.close()

        # 输出移动后的文件路径
        return render_template('creation.html')

    except Exception as e:
        print(f"Error: {e}")
        # 渲染失敗畫面
        return render_template('edit.html', error_message="儲存失敗，請檢查所有故事內容是否填寫完整或圖片是否皆生成完成。", array_story = array_story)

# ============================================================================================
## 待處理

#歷史創作按鈕
@app.route('/myStory')
def myStory():
    username = session['username']
    return render_template('myStory.html', username = username)

#歷史創作按鈕
@app.route('/collection')
def collection():
    username = session['username']
    return render_template('collection.html', username = username)

#故事瀏覽按鈕
@app.route('/story_details')
def story_details():
    username = session['username']
    return render_template('story-details.html', username = username)

#test2按鈕
@app.route('/test2')
def test2():
    username = session['username']
    return render_template('test2.html', username = username)

#creation按鈕
@app.route('/edit')
def edit():
    username = session['username']
    return render_template('edit.html', username = username)

#creation按鈕
@app.route('/user-details')
def user_details():
    username = session['username']
    return render_template('user-details.html', username = username)


# # ============================================================================================
# # 處理中
# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "OPENAI_API_KEY"))

# @app.route('/get-ai-json', methods=['POST'])
# def get_ai_json():

#     style = "校園風"
#     text = "這是一個講述誠實的故事"
#     question = f"故事風格為 {style}，故事大綱為 {text}"
#     # theme = request.form.get('theme')

#     thread = client.beta.threads.create()

#     # Create a message to append to our thread
#     message = client.beta.threads.messages.create(
#         thread_id=thread.id,
#         role="user",
#         content=question,
#     )

#     # Execute our run
#     run = client.beta.threads.runs.create(
#         thread_id=thread.id,
#         assistant_id='assistant_id',
#     )

#     def wait_on_run(run, thread):
#         while run.status == "queued" or run.status == "in_progress":
#             run = client.beta.threads.runs.retrieve(
#                 thread_id=thread.id,
#                 run_id=run.id,
#             )
#         return run
    
#     run = wait_on_run(run, thread)

#     # Retrieve all the messages added after our last user message
#     messages = client.beta.threads.messages.list(
#         thread_id = thread.id
#     )

#     for message in reversed(messages.data):
#         data = message.content[0].text.value

#     # 獲取回應內容
#     # data = data.replace('"', "")

#     data = data.replace("[", "")
#     data = data.replace("]", "")

#     # 將回應內容轉換為 JSON 格式，並按照指定格式進行分隔
#     story_lines = data.split('\n')
#     story_lines = [line for line in story_lines if line.strip()]

#     lines = [line.replace("},", "}") for line in story_lines]
#     print(lines)
#     # 將回應以 JSON 格式返回
#     return jsonify({"response": lines})

# #生圖測試1(成功用OPENAI函數)
# save_folder = 'static/image/story'
# os.makedirs(save_folder, exist_ok=True)

# # 設定日誌記錄
# logging.basicConfig(level=logging.INFO)

# def hash_image_content(content):
#     sha256_hash = hashlib.sha256()
#     sha256_hash.update(content)
#     return sha256_hash.hexdigest()

# def generate_single_image(prompt, i):
#     try:
#         response = client.images.generate(
#             prompt=prompt,
#             model="dall-e-3",
#             n=1,
#             size="1024x1024"
#         )

#         image_url = response.data[0].url
#         image_response = requests.get(image_url)

#         if image_response.status_code == 200:
#             content = image_response.content
#             hashed_name = hash_image_content(content)
#             image_path = os.path.join(save_folder, f"{hashed_name}.png")
#             with open(image_path, 'wb') as f:
#                 f.write(content)
#             logging.info(f"第{i+1}張圖片已保存至 {image_path}")
#             return image_path
#         else:
#             logging.error(f"下載第{i+1}張圖片失敗: {image_response.status_code}")
#             return None
#     except Exception as e:
#         logging.error(f"生成第{i+1}張圖片時出現錯誤: {str(e)}")
#         return None

# @app.route('/ai-image', methods=['POST'])
# def generate_images():
#     picture = request.form.get('picture')
#     prompt = "純圖片，藝術風格：柔和、飽和的顏色" + picture
#     total_images = 3  # 生成5張圖片
#     image_paths = []

#     for i in range(total_images):
#         image_path = generate_single_image(prompt, i)
#         if image_path:
#             image_paths.append(image_path)
#         else:
#             return jsonify({"message": f"生成第{i+1}張圖片失敗"}), 500

#     return jsonify({"message": "success! Check your folder", "image_paths": image_paths})


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

# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "sk-proj-RmZpsV6UyStRaqrVD6x2T3BlbkFJ3b47K7Oo7YCKm8X4zrMr"))
# # 設置你的 OpenAI API 密鑰
# #openai.api_key = "sk-proj-RmZpsV6UyStRaqrVD6x2T3BlbkFJ3b47K7Oo7YCKm8X4zrMr"

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
#         assistant_id='assistant_id',
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