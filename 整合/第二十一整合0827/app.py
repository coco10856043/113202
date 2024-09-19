#-----------------------
# 匯入模組
#-----------------------
from flask import (Flask, render_template, request, Response, jsonify, redirect, url_for, session, send_from_directory)
from utils import db  # 自定義模組，處理資料庫相關功能
from datetime import datetime
import requests  # 用於處理 HTTP 請求
import bcrypt  # 用於密碼加密和驗證
import os  # 用於操作系統相關操作，例如路徑管理
import time  # 用於時間相關操作
import re  # 用於正則表達式處理
import shutil  # 用於文件和目錄操作
import logging  # 用於記錄日誌
import hashlib  # 用於雜湊函數處理
from werkzeug.utils import secure_filename  # 用於安全地處理文件名
from openai import OpenAI  # 用於與 OpenAI API 交互
import subprocess  # 用於執行外部命令

# from collections import OrderedDict

#-----------------------
# 產生Flask app物件
#-----------------------
print (__name__)
app = Flask(__name__)

#-----------------------
# 設定一個祕鑰
#-----------------------
app.config['SECRET_KEY'] = 'assistant_id'

#-----------------------
# 設定路由
#-----------------------

# 初入網頁
#-----------------------
@app.route('/')
def first():
    return render_template('index.html')

# 登入後畫面轉換
#-----------------------
@app.route('/afterlogin_home')
def afterlogin_home():
    username = session['username']
    user_id = session['user_id']
    
    try:
        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()

        # 批量查詢所有故事
        cursor.execute("SELECT * FROM story")
        stories = cursor.fetchall()

        # 取得所有kind資料並轉為字典以提高查找效率
        cursor.execute("SELECT kind_id, name FROM kind")
        kind_dict = {row[0]: row[1] for row in cursor.fetchall()}

        # 批量查詢所有使用者資料並轉為字典
        cursor.execute("SELECT user_id, name, avatar FROM user_information")
        user_dict = {str(row[0]): (row[1], row[2]) for row in cursor.fetchall()}

        # 批量查詢所有收藏資料
        cursor.execute("SELECT story_id, COUNT(*) FROM collect GROUP BY story_id")
        collect_dict = {str(row[0]): row[1] for row in cursor.fetchall()}

        # 批量查詢所有追蹤資料
        cursor.execute("SELECT follow_user FROM follow WHERE user_id = %s", (user_id,))
        follow_dict = {str(row[0]): '已追蹤' for row in cursor.fetchall()}

    except Exception as e:
        # 在發生錯誤時，確保資料庫連線關閉
        if conn:
            conn.close()
        # 返回錯誤頁面或訊息
        return jsonify({'success': False, 'error': str(e)}), 500
    
    # 構建故事列表
    stories_list = []
    for story in stories:
        if story[4] != user_id:  # 過濾掉自己的故事
            story_kind = kind_dict.get(story[2], "未知類型")  # 從字典中查詢類型名稱
            user = user_dict.get(str(story[4]), ("未知作者", "default_avatar.png"))  # 從字典中查詢作者信息
            story_detail = story[5][:40] + '...' if len(story[5]) > 40 else story[5]  # 縮短故事內容
            num_collects = collect_dict.get(str(story[0]), 0)  # 從字典中查詢收藏數量
            follow_state = follow_dict.get(str(story[4]), '未追蹤')  # 從字典中查詢追蹤狀態

            if story[3] == True:  # 確保故事狀態為有效
                stories_list.append({
                    "story_id": story[0],
                    "title": story[1],
                    "detail": story_detail,
                    "image": "static/image/story_cover/" + story[6],
                    "author_image": "static/avatar/" + user[1],
                    "author_name": user[0],
                    "style": story_kind,
                    "favorites": num_collects,
                    "follow": follow_state
                })

    conn.close()  # 結束資料庫連線
    return render_template('home.html', username=username, stories=stories_list)

# 搜尋故事動作
#-----------------------
@app.route('/searchstory', methods=['GET'])
def searchstory():
    search_story = request.args.get('search_story')

    user_id = session['user_id']
    username = session['username']

    stories_list = []

    # 找到與搜尋條件匹配的故事
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM story WHERE title LIKE %s", (f"%{search_story}%",))
    stories_information = cursor.fetchall()

    # 取得所有kind資料並轉為字典以提高查找效率
    cursor.execute("SELECT kind_id, name FROM kind")
    kind_dict = {row[0]: row[1] for row in cursor.fetchall()}

    # 批量查詢所有使用者資料並轉為字典
    cursor.execute("SELECT user_id, name, avatar FROM user_information")
    user_dict = {str(row[0]): (row[1], row[2]) for row in cursor.fetchall()}

    # 批量查詢所有收藏資料
    cursor.execute("SELECT story_id, COUNT(*) FROM collect GROUP BY story_id")
    collect_dict = {str(row[0]): row[1] for row in cursor.fetchall()}

    # 批量查詢所有追蹤資料
    cursor.execute("SELECT follow_user FROM follow WHERE user_id = %s", (user_id,))
    follow_dict = {str(row[0]): '已追蹤' for row in cursor.fetchall()}

    conn.close()  # 結束資料庫連線

    for story in stories_information:
        if story[4] != user_id:  # 過濾掉自己的故事
            story_kind = kind_dict.get(story[2], "未知類型")  # 從字典中查詢類型名稱
            user = user_dict.get(str(story[4]), ("未知作者", "default_avatar.png"))  # 從字典中查詢作者信息
            story_detail = story[5][:40] + '...' if len(story[5]) > 40 else story[5]  # 縮短故事內容
            num_collects = collect_dict.get(str(story[0]), 0)  # 從字典中查詢收藏數量
            follow_state = follow_dict.get(str(story[4]), '未追蹤')  # 從字典中查詢追蹤狀態

            if story[3] == True:  # 確保故事狀態為有效
                stories_list.append({
                    "story_id": story[0],
                    "title": story[1],
                    "detail": story_detail,
                    "image": "static/image/story_cover/" + story[6],
                    "author_image": "static/avatar/" + user[1],
                    "author_name": user[0],
                    "style": story_kind,
                    "favorites": num_collects,
                    "follow": follow_state
                })

    return render_template('home.html', username=username, stories=stories_list)

# 新增追蹤動作
#-----------------------
@app.route('/add_follow', methods=['POST'])
def add_follow():
    user_id = session['user_id']
    data = request.get_json()  # 從請求中取得 author_name 參數
    author_name = data.get('author_name')

    try:
        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()

        # 查詢 user_information 表以取得對應的 user_id
        cursor.execute("SELECT user_id FROM user_information WHERE name = %s", (author_name,))
        follow_user_id = cursor.fetchone()

        if follow_user_id is None:
            return jsonify({'success': False, 'error': 'Author not found'}), 404  # 找不到作者

        # 插入追蹤記錄，避免重複追蹤
        cursor.execute(
            "INSERT INTO follow (user_id, follow_user) "
            "SELECT %s, %s WHERE NOT EXISTS (SELECT 1 FROM follow WHERE user_id = %s AND follow_user = %s)",
            (user_id, follow_user_id[0], user_id, follow_user_id[0])
        )
        conn.commit()  # 提交事務

        return jsonify({'success': True}), 200  # 返回成功狀態碼

    except Exception as e:
        conn.rollback()  # 發生錯誤時回滾事務
        return jsonify({'success': False, 'error': str(e)}), 500  # 返回錯誤訊息

    finally:
        conn.close()  # 確保無論是否發生錯誤，都會關閉資料庫連線

# 取消追蹤動作
#-----------------------
@app.route('/delete_follow', methods=['POST'])
def delete_follow():
    user_id = session['user_id']
    data = request.get_json()  # 從請求中取得 author_name 參數
    author_name = data.get('author_name')

    try:
        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()

        # 查詢 user_information 表以取得對應的 user_id
        cursor.execute("SELECT user_id FROM user_information WHERE name = %s", (author_name,))
        follow_user_id = cursor.fetchone()

        if follow_user_id is None:
            return jsonify({'success': False, 'error': 'Author not found'}), 404  # 找不到作者

        # 刪除追蹤記錄
        cursor.execute("DELETE FROM follow WHERE user_id = %s AND follow_user = %s", (user_id, follow_user_id[0]))
        conn.commit()  # 提交事務

        return jsonify({'success': True}), 200  # 返回成功狀態碼

    except Exception as e:
        conn.rollback()  # 發生錯誤時回滾事務
        return jsonify({'success': False, 'error': str(e)}), 500  # 返回錯誤訊息

    finally:
        conn.close()  # 確保無論是否發生錯誤，都會關閉資料庫連線

#歷史創作按鈕
#-----------------------
@app.route('/myStory')
def myStory():
    username = session['username']
    user_id = session['user_id']

    # 取得資料庫連線
    conn = db.get_connection()
    cursor = conn.cursor()

    # 查詢該使用者的所有故事
    cursor.execute("SELECT * FROM story WHERE user_id = %s", (user_id,))
    stories = cursor.fetchall()

    conn.close()  # 結束資料庫連線

    stories_list = []
    for story in stories:
        # 縮短故事內容
        story_detail = story[5][:40] + '...' if len(story[5]) > 40 else story[5]

        stories_list.append({
            "image": "static/image/story_cover/" + story[6],
            "title": story[1],
            "user": username,
            "description": story_detail,
            "link": '/story_details?story_id=' + str(story[0])
        })
        htmltitle = '我的創作'

    return render_template('myStory.html', username=username, htmltitle = htmltitle, stories=stories_list)

# 搜尋故事動作
#-----------------------
@app.route('/searchmystory', methods=['GET'])
def searchmystory():
    search_mystory = request.args.get('search_mystory')

    user_id = session['user_id']
    username = session['username']

    # 取得資料庫連線
    conn = db.get_connection()
    cursor = conn.cursor()

    # 查詢資料表：找出符合搜尋條件的故事
    cursor.execute("SELECT story_id, title, story_detail, story_picture FROM story WHERE user_id = %s AND title LIKE %s", (user_id, f"%{search_mystory}%"))
    stories = cursor.fetchall()

    conn.close()  # 結束資料庫連線

    stories_list = []
    for story in stories:
        # 縮短故事內容
        story_detail = story[2][:40] + '...' if len(story[2]) > 40 else story[2]

        stories_list.append({
            "image": "static/image/story_cover/" + story[3],
            "title": story[1],
            "user": username,
            "description": story_detail,
            "link": '/story_details?story_id=' + str(story[0])
        })

        htmltitle = '我的創作'

    return render_template('myStory.html', username=username, htmltitle = htmltitle, stories=stories_list)

# 故事收藏按鈕
#-----------------------
@app.route('/collection')
def collection():
    username = session['username']
    user_id = session['user_id']

    # 取得資料庫連線
    conn = db.get_connection()
    cursor = conn.cursor()

    # 合併查詢，獲取收藏的故事以及相關的故事資訊和用戶名稱
    query = "SELECT c.story_id, c.collect_time, s.title, s.story_detail, s.story_picture, u.name AS user_name FROM collect c JOIN story s ON c.story_id = s.story_id JOIN user_information u ON s.user_id = u.user_id WHERE c.user_id = %s"
    cursor.execute(query, (user_id,))
    stories = cursor.fetchall()

    stories_list = []
    for story in stories:
        story_id = str(story[0])
        summary = story[3]
        if len(summary) > 40:
            summary = summary[:40] + '...'

        stories_list.append({
            "image": "static/image/story_cover/" + story[4],
            "title": story[2],
            "date": story[1],
            "user": story[5],
            "summary": summary,
            "link": '/story_details?story_id=' + story_id
        })

    return render_template('collection.html', username=username, stories=stories_list)

# 搜尋收藏故事動作
#-----------------------
@app.route('/searchmycollection', methods=['GET'])
def searchmycollection():
    search_mycollection = request.args.get('search_mycollection')
    user_id = session['user_id']
    username = session['username']

    # 取得資料庫連線
    conn = db.get_connection()
    cursor = conn.cursor()

    # 合併查詢，過濾收藏的故事並在資料庫層面進行搜索
    query = "SELECT c.story_id, c.collect_time, s.title, s.story_detail, s.story_picture, u.name AS user_name FROM collect c JOIN story s ON c.story_id = s.story_id JOIN user_information u ON s.user_id = u.user_id WHERE c.user_id = %s AND s.title LIKE %s"
    cursor.execute(query, (user_id, '%' + search_mycollection + '%'))
    stories = cursor.fetchall()

    stories_list = []
    for story in stories:
        story_id = str(story[0])
        summary = story[3]
        if len(summary) > 40:
            summary = summary[:40] + '...'

        stories_list.append({
            "image": "static/image/story_cover/" + story[4],
            "title": story[2],
            "date": story[1],
            "user": story[5],
            "summary": summary,
            "link": '/story_details?story_id=' + story_id
        })

    return render_template('collection.html', username=username, stories=stories_list)

# 進入細節畫面
#-----------------------
@app.route('/story_details', methods=['GET'])
def story_details():
    user_id = session['user_id']
    username = session['username']
    story_id = request.args.get('story_id')

    conn = db.get_connection()
    cursor = conn.cursor()

    query = "SELECT s.story_id, s.title, s.story_detail, s.story_picture, s.user_id AS author_id, k.name AS kind_name, p.picture AS page_picture FROM story s JOIN kind k ON s.kind_id = k.kind_id LEFT JOIN pages p ON s.story_id = p.story_id WHERE s.story_id = %s"
    cursor.execute(query, (story_id,))
    story_info = cursor.fetchall()

    if not story_info:
        return "Story not found", 404

    story_info = story_info[0]

    cursor.execute("SELECT name FROM user_information WHERE user_id = %s", (story_info[4],))
    author_name = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM collect WHERE story_id = %s", (story_id,))
    total_collections = cursor.fetchone()[0]

    follow_state = '未追蹤'
    cursor.execute("SELECT 1 FROM follow WHERE user_id = %s AND follow_user = %s", (user_id, story_info[4]))
    if cursor.fetchone():
        follow_state = '已追蹤'

    cursor.execute("SELECT COUNT(*) FROM story WHERE user_id = %s", (story_info[4],))
    total_stories = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM follow WHERE follow_user = %s", (story_info[4],))
    total_follow_users = cursor.fetchone()[0]

    cursor.execute("SELECT picture FROM pages WHERE story_id = %s ORDER BY page", (story_id,))
    page_pictures = cursor.fetchall()

    page_pictures = ["static/image/page/" + pic[0] for pic in page_pictures]

    collected_state = '未收藏'
    cursor.execute("SELECT 1 FROM collect WHERE user_id = %s and story_id = %s", (user_id, story_id,))
    if cursor.fetchone():
        collected_state = '已收藏'

    detail_list = [{
        "story_id": story_id,
        "title": story_info[1],
        "detail": story_info[2],
        "kind": story_info[5],
        "user": author_name,
        "follow": follow_state,
        "tot_follow": total_follow_users,
        "tot_stories": total_stories,
        "collect": total_collections,
        "picture_cover": "static/image/story_cover/" + story_info[3],
        "pictures": page_pictures,
        "link":'/test2?story_id=' + story_id,
        "collected": collected_state
    }]

    return render_template('story-details.html', username=username, details=detail_list[0])

# 進入登入畫面
#-----------------------
@app.route('/login')
def login():
    return render_template('login.html')

# 登入動作
#-----------------------
@app.route('/home', methods=['POST'])
def home():
    conn = None
    try:
        # 取得參數
        title = request.form.get('title')
        password = request.form.get('password')

        # 验证电子邮件格式
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if (not re.match(email_regex, title)) or len(title) <= 10:
            return render_template('login.html', error_message="登入失敗，帳號輸入格式有誤")

        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 查詢資料表
        cursor.execute("SELECT * FROM user_information WHERE user_id = %s", (title,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            user_id = user[0]
            username = user[1]
            
            session['user_id'] = user_id
            session['username'] = username

            # 渲染成功畫面
            return redirect(url_for('afterlogin_home'))
        else:
            # 渲染失敗畫面
            return render_template('login.html', error_message="登入失敗")
    except Exception as e:
        print(f"Error: {e}")
        # 渲染失敗畫面
        return render_template('login.html', error_message="登入失敗")
    finally:
        if conn:
            conn.close()
    
# 進入註冊畫面
#-----------------------
@app.route('/register')
def register():
    return render_template('register.html')

# 進入忘記密碼畫面
#-----------------------
@app.route('/forget')
def forget():
    return render_template('forget.html')

# 變更密碼動作
#-----------------------
@app.route('/change', methods=['POST'])
def change():
    title = request.form.get('title')
    name = request.form.get('name')
    password_new = request.form.get('password1')
    password_check = request.form.get('password2')

    # 使用正則表達式檢查 email 格式
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, title) or len(title) <= 10:
        return render_template('forget.html', error_message="更新失敗，帳號輸入格式有誤")

    try:
        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()

        # 查詢資料表
        cursor.execute("SELECT * FROM user_information WHERE user_id = %s AND name = %s", (title, name))
        user = cursor.fetchone()

        if user:
            if password_new == password_check:
                hash_password = bcrypt.hashpw(password_new.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                # 更新密碼
                cursor.execute("UPDATE user_information SET password=%s WHERE user_id=%s", (hash_password, title))
                conn.commit()
                return render_template('login.html', success_message="密碼已修改，請登入")
            else:
                return render_template('forget.html', error_message="密碼修改失敗，請確認新密碼是否輸入正確")
        else:
            return render_template('forget.html', error_message="密碼修改失敗，查無此使用者")

    except Exception as e:
        # 紀錄異常
        print(f"An error occurred: {e}")
        return render_template('forget.html', error_message="密碼修改失敗，請稍後再試")
    
    finally:
        # 確保資料庫連線被關閉
        conn.close()
    
# 註冊動作
#-----------------------
UPLOAD_FOLDER = 'static/avatar'  # 設定文件上傳目錄
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}  # 允許上傳的文件類型
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # 配置 Flask 的文件上傳目錄

def allowed_file(filename):
    # 檢查文件是否為允許的類型
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/do_register', methods=['POST'])
def do_register():
    # 處理註冊請求
    try:
        # 取得表單參數
        title = request.form.get('title')
        name = request.form.get('name')
        password = request.form.get('password')
        child_birth = request.form.get('child_birth')
        child_gender = request.form.get('age')
        avatar = request.files.get('avatar')  # 取得上傳的頭像文件

        # 驗證表單參數是否齊全
        if not (title and name and password and child_birth and child_gender):
            return render_template('register.html', error_message="所有字段都是必填的")

        # 檢查電子郵件格式
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        try:
            child_birth = int(child_birth)  # 將孩子出生年齡轉換為整數
            if not re.match(email_regex, title) or len(title) <= 10:
                return render_template('register.html', error_message="註冊失敗，帳號輸入格式有誤")
            if title == name:
                return render_template('register.html', error_message="註冊失敗，帳號與使用者名稱請不要使用同一個")
            if child_birth < 0 or child_birth > 100:
                return render_template('register.html', error_message="註冊失敗，孩子的年齡有誤")

            # 檢查和處理上傳的頭像文件
            if avatar and allowed_file(avatar.filename):
                file_extension = avatar.filename.rsplit('.', 1)[1].lower()  # 獲取文件擴展名
                filename = f"{title}.{file_extension}"  # 使用帳號作為文件名
                avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # 構建文件存儲路徑
                
                # 確保上傳目錄存在
                os.makedirs(os.path.dirname(avatar_path), exist_ok=True)
                
                avatar.save(avatar_path)  # 保存文件到指定路徑
                print(f"File saved as {filename}")
            else:
                filename = None
                return render_template('register.html', error_message="註冊失敗，頭像上傳有誤")

            # 加密密碼
            hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # 將用戶資料插入資料庫
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_information (user_id, name, password, child_gender, child_birth, avatar) VALUES (%s, %s, %s, %s, %s, %s)",
                (title, name, hash_password, child_gender, child_birth, filename)
            )
            conn.commit()
            conn.close()

            # 渲染註冊成功頁面
            return render_template('login.html', success_message="註冊成功")

        except ValueError:
            return render_template('register.html', error_message="註冊失敗")

    except Exception as e:
        logging.error(f"An error occurred: {e}")  # 記錄錯誤信息
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
        avatar = request.files.get('avatar')
        user_id = session.get('user_id')

        if not user_id:
            return render_template('user-profile.html', error_message="用戶未登入")

        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()

        # 取得用戶資訊
        cursor.execute("SELECT * FROM user_information WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return render_template('user-profile.html', error_message="用戶不存在")

        user_name = user[1]
        user_avatar = user[5]

        if name:
            cursor.execute("SELECT * FROM user_information WHERE name = %s", (name,))
            existing_user = cursor.fetchone()

            if existing_user and existing_user[0] != user_id:
                conn.close()
                return render_template('user-profile.html', error_message="更新失敗，暱稱可能已被使用")
            user_name = name

        if avatar and allowed_file(avatar.filename):
            file_extension = avatar.filename.rsplit('.', 1)[1].lower()
            filename = f"{user_id}.{file_extension}"
            avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            avatar.save(avatar_path)
            user_avatar = filename

        cursor.execute("UPDATE user_information SET name=%s, avatar=%s WHERE user_id=%s", (user_name, user_avatar, user_id))
        conn.commit()
        conn.close()

        session['username'] = user_name

        return render_template('user-profile.html', success_message="更新成功")

    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('user-profile.html', error_message="更新失敗")
                    
# 進入追蹤者畫面
#-----------------------
@app.route('/follow')
def follow():
    user_id = session['user_id']
    username = session['username']

    # 建立資料庫連接
    conn = db.get_connection()
    cursor = conn.cursor()

    # 查詢用戶的 follow_user
    cursor.execute("SELECT follow_user FROM follow WHERE user_id = %s", (user_id,))
    follow_users = cursor.fetchall()
    
    # 提取所有 follow_user 的 user_id
    follow_user_ids = [user[0] for user in follow_users]
    
    # 查詢所有跟隨用戶的信息
    if follow_user_ids:
        format_strings = ','.join(['%s'] * len(follow_user_ids))
        query = f"SELECT user_id, name, avatar FROM user_information WHERE user_id IN ({format_strings})"
        cursor.execute(query, tuple(follow_user_ids))
        users_information = cursor.fetchall()
    else:
        users_information = []

    # 關閉資料庫連接
    conn.close()

    # 整理用戶信息
    users_info_list = [{'name': user[1], 'avatar': user[2], 'link': '/user_detail?follow_user_name=' + user[1] }for user in users_information]
    
    return render_template('follow.html', username=username, users_information=users_info_list)

# 搜尋追蹤者畫面
#-----------------------
@app.route('/searchuser', methods=['GET'])
def searchuser():
    search_user = request.args.get('search_user')
    user_id = session['user_id']
    username = session['username']
    
    users_information = []

    # 打開資料庫連接
    conn = db.get_connection()
    cursor = conn.cursor()

    # 查找被搜尋的使用者 id
    cursor.execute("SELECT user_id FROM user_information WHERE name LIKE %s", (f"%{search_user}%",))
    follow_users_id = cursor.fetchall()

    if follow_users_id:
        # 獲取所有的用戶 id
        follow_user_ids = tuple(user[0] for user in follow_users_id)

        # 查找用戶是否已經追蹤
        cursor.execute("SELECT follow_user FROM follow WHERE user_id = %s AND follow_user IN %s", (user_id, follow_user_ids))
        followed_users = cursor.fetchall()

        # 獲取已追蹤用戶的 id
        followed_user_ids = {user[0] for user in followed_users}

        # 獲取所有用戶資訊
        cursor.execute("SELECT user_id, name, avatar FROM user_information WHERE user_id IN %s", (follow_user_ids,))
        all_users = cursor.fetchall()

        for user in all_users:
            if user[0] in followed_user_ids:
                users_information.append({
                    'name': user[1],
                    'avatar': user[2],
                    'link': '/user_detail?follow_user_name=' + user[1]
                })

    # 關閉資料庫連接
    conn.close()

    # 渲染模板
    return render_template('follow.html', username=username, users_information=users_information)

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

    session['story_title'] = title
    session['story_kind'] = kind
    session['story_detail'] = story_detail

    # Create a thread and send a message
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question,
    )

    # Execute the run
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id='assistant_id', # 助理名稱：story
    )

    # Efficiently wait for the run to complete
    def wait_on_run(run):
        while run.status in ["queued", "in_progress"]:
            time.sleep(1)  # Sleep to avoid hitting API rate limits
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )
        return run

    run = wait_on_run(run)

    # Retrieve and process messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    response_text = ""
    for message in reversed(messages.data):
        response_text += message.content[0].text.value

    # Clean up and format the response text
    response_text = response_text.replace("[", "").replace("]", "")
    story_lines = [line.strip().replace("{'", "'").replace("'}", "'") for line in response_text.split('\n') if line.strip()]

    array_story = []
    for line in story_lines:
        parts = line.strip("'").split("','")
        parts[-1] = parts[-1].rstrip(',').rstrip("'")
        array_story.append(parts)

    print(array_story)
    # Check if any story part contains '第' and '段'
    needs_retry = any("第" in i[1] and "段" in i[1] for i in array_story)
    
    if needs_retry:
        # Redirect with the same form data
        return redirect(url_for('creation', title=title, kind=kind, story_detail=story_detail))

    return render_template('edit.html', story_title=title, story_kind=kind, story_detail=story_detail, array_story=array_story)

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

            # Return relative URL
            relative_path = os.path.relpath(image_path, start='static')
            return relative_path
        else:
            logging.error(f"下載第{i+1}張圖片失敗: {image_response.status_code}")
            return None
    except Exception as e:
        logging.error(f"生成第{i+1}張圖片時出現錯誤: {str(e)}", exc_info=True)
        return None

@app.route('/ai-image', methods=['POST'])
def generate_images():
    try:
        data = request.get_json()
        # 確保請求包含消息
        if not data or 'message' not in data:
            return jsonify({"message": "未提供消息"}), 400
        
        message = data.get('message')
        story_kind = session.get('story_kind', 'default')
        print(message)
        # 更新 prompt，調整為可愛的風格
        prompt = "故事風格為" + story_kind + "故事段落為" + message + "，重要的是圖片中不可以有任何的文字元素(包含英文和中文)，而且一定要保證符合圖片風格，盡量風格統一，需要小孩看得懂"
        total_images = 1  # 生成1張圖片
        image_paths = []

        for i in range(total_images):
            image_path = generate_single_image(prompt, i)
            if image_path:
                # 只返回圖片檔案名稱，不再加上靜態文件夾的前綴
                image_paths.append(f'static/image/story_select/{os.path.basename(image_path)}')
            else:
                return jsonify({"message": f"生成第{i+1}張圖片失敗"}), 500

        return jsonify({"message": "success", "image_paths": image_paths})

    except Exception as e:
        logging.error(f"處理請求時出現錯誤: {str(e)}")
        return jsonify({"message": "內部錯誤"}), 500
    
# 儲存故事動作
#-----------------------
@app.route('/save-story', methods=['POST'])
def save_story():
    try:
        # 取得參數
        openstate = request.form.get('isPublic', 'false')
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
        image_filename_cover = request.form.get('image-filenames0')
        
        # 檢查是否有任何值為空
        if not all([message1, image_filename1, message2, image_filename2,
                    message3, image_filename3, message4, image_filename4,
                    message5, image_filename5, image_filename_cover]):
            return render_template('edit.html', 
                                   error_message="儲存失敗，請檢查所有故事內容是否填寫完整或圖片是否皆生成完成。",
                                   story_title=session.get('story_title'),
                                   story_kind=session.get('story_kind'),
                                   story_detail=session.get('story_detail'),
                                   array_story=[['1', message1], ['2', message2], ['3', message3], ['4', message4], ['5', message5]])
        
        # 取得資料庫連線
        conn = db.get_connection()
        cursor = conn.cursor()

        # 獲取 kind_id
        cursor.execute("SELECT kind_id FROM kind WHERE name = %s", (session['story_kind'],))
        kind_id = cursor.fetchone()[0]
        
        # 移動封面圖片
        source = "static/image/story_select"
        destination_cover = "static/image/story_cover"
        destination_page = "static/image/page"
        os.makedirs(destination_cover, exist_ok=True)
        os.makedirs(destination_page, exist_ok=True)

        # 移動封面圖片到 story_cover 資料夾
        if image_filename_cover:
            source_path_cover = os.path.join(source, image_filename_cover)
            destination_path_cover = os.path.join(destination_cover, image_filename_cover)
            shutil.move(source_path_cover, destination_path_cover)

        # 移動其他圖片到 page 資料夾
        files = {
            '1': image_filename1,
            '2': image_filename2,
            '3': image_filename3,
            '4': image_filename4,
            '5': image_filename5
        }

        for page, filename in files.items():
            if filename:
                source_path = os.path.join(source, filename)
                destination_path = os.path.join(destination_page, filename)
                shutil.move(source_path, destination_path)

        # 插入故事
        cursor.execute("INSERT INTO story (title, kind_id, state, user_id, story_detail, story_picture) VALUES (%s, %s, %s, %s, %s, %s) RETURNING story_id", 
                       (session['story_title'], kind_id, openstate, session['user_id'], session['story_detail'], image_filename_cover))
        story_id = str(cursor.fetchone()[0])

        # 插入每頁的內容
        pages = [
            (1, message1, image_filename1),
            (2, message2, image_filename2),
            (3, message3, image_filename3),
            (4, message4, image_filename4),
            (5, message5, image_filename5)
        ]

        cursor.executemany("INSERT INTO pages (story_id, page, content, picture) VALUES (%s, %s, %s, %s)", 
                           [(int(story_id), page, message, filename) for page, message, filename in pages])

        # 提交所有資料庫操作
        conn.commit()
        conn.close()

        return render_template('creation.html')

    except Exception as e:
        print(f"Error: {e}")
        return render_template('edit.html',
                               error_message="儲存失敗，請檢查所有故事內容是否填寫完整或圖片是否皆生成完成。",
                               array_story=[['1', message1], ['2', message2], ['3', message3], ['4', message4], ['5', message5]])

# 閱讀故事
#-----------------------
@app.route('/test2')
def test2():
    story_id = request.args.get('story_id')
    
    # 取得資料庫連線，使用連線池來提高效能
    with db.get_connection() as conn:
        with conn.cursor() as cursor:
            # 使用JOIN合併兩個查詢，減少多次查詢的開銷
            cursor.execute("SELECT s.title, s.story_picture, p.content, p.picture FROM story s JOIN pages p ON s.story_id = p.story_id WHERE s.story_id = %s ORDER BY p.page", (story_id,))
            # 抓取所有結果
            results = cursor.fetchall()

    if results:
        # 從查詢結果中提取標題和封面
        title = results[0][0]
        cover = results[0][1]

        # 拆分成配對列表
        paired_list = [(row[2], row[3]) for row in results]

        story_list = [{
            "title": title,
            "cover": cover,
            "pages": paired_list,  # 這裡使用配對的列表
        }]
    else:
        story_list = []

    return render_template('test2.html', story_list=story_list)

# 收藏故事動作
#-----------------------
@app.route('/collect_story', methods=['POST'])
def collect_story():
    data = request.get_json()  # 從請求中取得 author_name 參數
    story_id = data.get('story_id')
    user_id = session["user_id"]

    # 取得資料庫連線
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO collect (user_id, story_id, collect_time) VALUES (%s, %s, %s)", (user_id, str(story_id), datetime.now()))

    # 提交所有資料庫操作
    conn.commit()
    conn.close()
    return jsonify(success=True)

# 取消收藏故事動作
#-----------------------
@app.route('/uncollect_story', methods=['POST'])
def uncollect_story():
    data = request.get_json()  # 從請求中取得 author_name 參數
    story_id = data.get('story_id')
    user_id = session["user_id"]

    # 取得資料庫連線
    conn = db.get_connection()
    cursor = conn.cursor()

    # 刪除追蹤記錄
    cursor.execute("DELETE FROM collect WHERE user_id = %s AND story_id = %s", (user_id, str(story_id),))
    conn.commit()  # 提交事務
    conn.close()
    return jsonify(success=True)

# 追蹤者的歷史創作瀏覽
#-----------------------
@app.route('/user_detail', methods=['GET'])
def user_detail():
    follow_user_name = request.args.get('follow_user_name')
    username = session.get('username', '未知用户')  # 获取会话中的用户名，默认值为'未知用户'

    # 初始化 htmltitle 以确保它在函数的所有路径中都被赋值
    htmltitle = f"{follow_user_name}的創作" if follow_user_name else "用户的創作"

    try:
        # 取得資料庫連線
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                # 查询用户ID
                cursor.execute("SELECT user_id FROM user_information WHERE name = %s", (follow_user_name,))
                follow_user_id = cursor.fetchone()

                if follow_user_id:
                    follow_user_id = follow_user_id[0]
                    # 查询该用户的所有故事
                    cursor.execute("SELECT * FROM story WHERE user_id = %s AND state = true", (follow_user_id,))
                    stories = cursor.fetchall()

                    stories_list = []
                    for story in stories:
                        # 短缩故事内容
                        story_detail = story[5][:40] + '...' if len(story[5]) > 40 else story[5]

                        stories_list.append({
                            "image": "static/image/story_cover/" + story[6],
                            "title": story[1],
                            "user": follow_user_name,
                            "description": story_detail,
                            "link": '/story_details?story_id=' + str(story[0])
                        })
                else:
                    stories_list = []  # 如果没有找到用户ID，返回空故事列表
    except Exception as e:
        print(f"发生错误: {e}")
        stories_list = []  # 出现错误时返回空故事列表

    return render_template('myStory.html', username=username, htmltitle=htmltitle, stories=stories_list)



#-----------------------
# 執行app
#-----------------------
if __name__ == '__main__':
    # 先執行 node server.js
    subprocess.Popen(['node', 'server.js'])

    # 然後啟動 Flask 應用
    app.run(port=5000, debug=True)