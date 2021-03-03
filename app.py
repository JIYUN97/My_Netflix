from pymongo import MongoClient
import hashlib
import jwt
import datetime
from flask import Flask, render_template, jsonify, request, redirect,url_for
from datetime import datetime, timedelta
from flask_login import login_required

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
SECRET_KEY = 'hanghae_16'
client = MongoClient('localhost', 27017)
db = client.my_netflix

## HTML을 주는 부분
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/register', methods=['GET'])
def sign_up_page():
    return render_template('register.html')

    
@app.route('/main', methods=['GET'])
def main_page():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive,SECRET_KEY,algorithms=['HS256'])
        member_info = db.member.find_one({"mem_id":payload['id']})
        nick = member_info['mem_nick']
        # 1. DB에서 리뷰 정보 모두 가져오기
        all_netflixs = list(db.netflix.find({}, {'_id': False}))
        # 2. 성공 여부 & 리뷰 목록 반환하기
        return render_template("main.html", netflixs=all_netflixs,nick=nick)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login_page", msg ="로그인 시간 만료!"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login_page",msg = "로그인 정보 없음!"))

## 회원 가입 관련 - 닉네임 중복 체크 
@app.route('/nick_dup_check', methods=['POST'])
def nick_dup_check():
    nick = request.form['nick']
    dup_check = bool(db.member.find_one({'mem_nick':nick}))
    return jsonify({'msg':dup_check})

## 회원 가입 관련 - 아이디 중복 체크 
@app.route('/id_dup_check', methods=['POST'])
def id_dup_check():
    id = request.form['id']
    dup_check = bool(db.member.find_one({'mem_id':id}))
    return jsonify({'msg':dup_check})

## 회원 가입 관련 - 회원 가입
@app.route('/register',methods=['POST'])
def sign_up():
    nick = request.form['nick']
    id = request.form['id']
    pwd = request.form['pwd']
    pwd_hash = hashlib.sha256(pwd.encode('utf-8')).hexdigest()
    person = {
        'mem_nick':nick,
        'mem_id':id,
        'mem_pwd':pwd_hash
    }
    db.member.insert_one(person)
    return jsonify({"msg":nick})

## 로그인 관련 - 로그인 페이지
@app.route('/login', methods=['GET'])
def login_page():
    msg = request.args.get("msg")
    return render_template('login.html',msg = msg)

## 로그인 관련 - 로그인 버튼 클릭 시
@app.route('/login', methods=['POST'])
def login():
    id = request.form['id']
    pwd = request.form['pwd']
    pwd_hash = hashlib.sha256(pwd.encode('utf-8')).hexdigest()

    result = db.member.find_one({'mem_id': id, 'mem_pwd': pwd_hash})

    if result is not None:
        payload = {
         'id': id,
         'nick':result['mem_nick'],
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)