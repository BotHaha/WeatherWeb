import sqlite3
from datetime import datetime

DB_FILE = "users.db"

#建立資料庫
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    
    # 一次建立所有需要的表格
    # 1. 使用者表
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    
    # 2. 登入紀錄表
    c.execute('''CREATE TABLE IF NOT EXISTS login_log 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, timestamp TEXT)''')
    
    # 3. 天氣查詢紀錄表
    c.execute('''CREATE TABLE IF NOT EXISTS query_history 
                 (username TEXT, city TEXT, ip TEXT, timestamp TEXT)''')
    
    # 加入預設測試帳號 (如果表是空的)
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?)", ("admin", "1234"))
    
    conn.commit()
    conn.close()

def record_login(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO login_log (username) VALUES (?)", (username,))
    conn.commit()
    conn.close()

def get_login_history(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT timestamp FROM login_log WHERE username=? ORDER BY timestamp DESC", (username,))
    records = c.fetchall()
    conn.close()
    return [r[0] for r in records]



def record_query(username, city, ip_address):
    if not username:
        return
        
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    # 確保欄位包含 ip
    c.execute("INSERT INTO query_history (username, city, ip, timestamp) VALUES (?, ?, ?, ?)", 
              (username, city, ip_address, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()