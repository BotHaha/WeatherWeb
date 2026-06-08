from flask import Flask, session, request, render_template, redirect, url_for, jsonify
from db_utils import init_db, record_login, record_query
import sqlite3
import requests
from datetime import datetime

# 在檔案上方定義全台縣市鄉鎮字典
CITIES = [
    "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市", 
    "基隆市", "新竹市", "新竹縣", "苗栗縣", "彰化縣", "南投縣", 
    "雲林縣", "嘉義市", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣", 
    "臺東縣", "澎湖縣", "金門縣", "連江縣"
]

init_db()
app = Flask(__name__)

@app.context_processor
def inject_city_towns():
    return dict(CITIES=CITIES)

#Session 密鑰
app.secret_key = 'super_secret_key_12345' 

#中央氣象局 API 金鑰
API_KEY = "CWA-257DB651-5678-452F-BC08-6ADF9CFB0BFB"

# 1. 在檔案最上方設定變數
API_KEY = "CWA-257DB651-5678-452F-BC08-6ADF9CFB0BFB"

def fetch_weather_api(county_name):
    import urllib.parse
    # 使用一般天氣預報 API
    encoded_county = urllib.parse.quote(county_name)
    url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={API_KEY}&locationName={encoded_county}&format=JSON"
    
    try:
        response = requests.get(url, verify=False).json()
        
        # 取得縣市列表
        location_list = response['records']['location']
        # 找到目標縣市 (直接從列表第一筆拿)
        target = location_list[0]
        
        # 整理氣象因子
        elements = {item['elementName']: item['time'][0]['parameter'] for item in target['weatherElement']}
        
        # 回傳你需要的所有資料
        return {
            "max_t": elements.get('MaxT', {}).get('parameterName'),  # 最高溫
            "min_t": elements.get('MinT', {}).get('parameterName'),  # 最低溫
            "ci": elements.get('CI', {}).get('parameterName'),       # 舒適度
            "wx": elements.get('Wx', {}).get('parameterName'),       # 天氣現象
            "pop": elements.get('PoP', {}).get('parameterName')      # 降雨機率
        }
    except Exception as e:
        print(f"DEBUG: 解析錯誤: {e}")
        return None

@app.route("/")
def index():
    # 改從 session 讀取，保持登入狀態
    username = session.get('username')
    return render_template("dashboard.html", username=username, history=[], weather_data=None, city=None)


@app.route("/dashboard")
def dashboard():
    username = session.get('username')
    county = request.args.get("county") 
    town = request.args.get("town")
    
    weather_data = None
    history = []
    
    # 1. 如果有收到查詢，先處理天氣資料
    if county:
            weather_data = fetch_weather_api(county)
            if username:
                record_query(username, county, request.remote_addr)
    
    # 2. 如果使用者有登入，撈取歷史紀錄 (不管有沒有查天氣，這段都要跑)
    if username:
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT city, timestamp FROM query_history WHERE username = ? ORDER BY timestamp DESC LIMIT 20", (username,))
        history = c.fetchall()
        conn.close()
    
    # 3. 最後再一次性回傳給網頁
    return render_template("dashboard.html", username=username, weather_data=weather_data, city=county)

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    next_page = request.form.get("next")
    
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['username'] = username  # 【關鍵】將登入者存入 Session
        record_login(username)
        if next_page == 'history':
            return redirect(url_for("history_page"))
        return redirect(url_for("dashboard"))
        
    return "帳號或密碼錯誤。 <a href='/'>回首頁</a>"

@app.route("/login_page")
def login_page():
    return render_template("Web.html", next_page=None)

@app.route("/logout")
def logout():
    session.clear()  # 清除 Session 中所有的資料
    return redirect(url_for("index")) # 登出後導回首頁



@app.route("/history")
def history_page():
    username = session.get('username')
    if not username:
        return redirect(url_for("login_page"))
    
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT city, timestamp FROM query_history WHERE username = ? ORDER BY timestamp DESC LIMIT 20", (username,))
    rows = c.fetchall()
    conn.close()
    
    return render_template("history.html", username=username, history=rows)



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)