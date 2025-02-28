from flask import Flask, request, render_template
from datetime import datetime

app = Flask (__name__) 
app.secret_key='your_secret_key_here' #設定session安全密鑰

#模擬身分驗證資料庫
users={
    "David Chou": "A123456789", 
    "Vivian Kuo": "B223348910", 
    "Angela Tsai": "C221159139"
    }

@app.route('/')
def home():
    return redirect(url_for('verification')) #預設導向驗證頁面

@app.route('/verification', methods=['GET', 'POST'])
def verification():
    if request.method == 'POST':
        username = request.form.get['username']
        password = request.form.get['password']
    
        if username in users and users[username]==password:
            session['username']=username  #設定session，表示登入成功
            return redirect(url_for('mainpage'))
        else:
            return render_template('verification.html', error="帳號或密碼錯誤，請重新輸入！")

    return render_template('verification.html')


@app.route('/mainpage')
def mainpage():
    if 'username' not in session:  #如果未登入，導回驗證頁面
        return redirect(url_for('verification))
    
    now=datetime.now()
    return render_template('chatbot_mainpage.html, username=session['username], now=now)


@app.route('/logout')
def logout():
    session.pop('username, None)  #清除session
    return redirect(url_for('verification))  #登出後導回驗證頁面

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False)