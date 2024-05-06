#-----------------------
# 匯入模組
#-----------------------
from flask import Flask, render_template, request, Response
from utils import db

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
        cursor.execute("INSERT into User (user_id, name) values(1234, 'abcd')")
        conn.commit()
        conn.close()

        # 渲染成功畫面
        return Response('create_success.html')
    except:
        # 渲染失敗畫面
        return Response('create_fail.html')


# @app.route('/add')
# def add():
#     return render_template('index.html')

#-----------------------
# 執行app
#-----------------------
if __name__ == '__main__':
    app.run(port=5000, debug=True)