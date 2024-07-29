# 匯入連結資料庫模組
import psycopg2


# PostgreSQL連線資訊
DB_HOST = "hattie.db.elephantsql.com"
DB_NAME = "zjthptvz"
DB_USER = "zjthptvz"
DB_PASSWORD = "wFC04bEPVsG31QbU8T3KG_aRHeiQl9ay"


# 建立資料庫連線
def get_connection():
    connection = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return connection
