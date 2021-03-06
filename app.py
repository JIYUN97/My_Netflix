from pymongo import MongoClient
import hashlib
import jwt
import datetime
from flask import Flask, render_template, jsonify, request, redirect,url_for
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
SECRET_KEY = 'hanghae_16'
client = MongoClient('localhost', 27017)
db = client.my_netflix

## HTML을 주는 부분
@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive,SECRET_KEY,algorithms=['HS256'])
        member_info = db.member.find_one({"mem_id":payload['id']})
        return redirect(url_for("main_page"))
    except:
        return render_template('login.html')

@app.route('/register', methods=['GET'])
def sign_up_page():
    return render_template('register.html')

    
@app.route('/main', methods=['GET'])
def main_page():
    token_receive = request.cookies.get('mytoken')
    search_title = request.args.get('search_title')
    try:
        payload = jwt.decode(token_receive,SECRET_KEY,algorithms=['HS256'])
        member_info = db.member.find_one({"mem_id":payload['id']})
        nick = member_info['mem_nick']

        if search_title is None:
            # DB에서 Netflix 정보 모두 가져오기 (리뷰 개수 내림차순 정렬 후 제목 오름차순 정렬)
            all_netflixs = list(db.netflix.find({}, {'_id': False}).sort([("net_rv_count", -1),("net_title", 1)]))

            # 닉네임 & Netflix 목록 반환하기
            return render_template("main.html", netflixs=all_netflixs,nick=nick)
        else:
            search_netflixs = list(db.netflix.find({"net_title":{"$regex":search_title}},{"id_":False}).sort([("net_rv_count", -1),("net_title", 1)]))
            return render_template("search_main.html", netflixs=search_netflixs,nick=nick)

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
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive,SECRET_KEY,algorithms=['HS256'])
        member_info = db.member.find_one({"mem_id":payload['id']})
        return redirect(url_for("main_page"))
    except:
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

@app.route('/review/write/<title>', methods=['GET'])
def review_write_page(title):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive,SECRET_KEY,algorithms=['HS256'])
        member_info = db.member.find_one({"mem_id":payload['id']})
        nick = member_info['mem_nick']
        # DB에서 해당 Netflix 정보 가져오기
        netflix = db.netflix.find_one({'net_title': title}, {'_id': False})
        return render_template('review_write.html', netflix=netflix, nick = nick)
    
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login_page", msg ="로그인 시간 만료!"))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login_page",msg = "로그인 정보 없음!"))

@app.route('/review/writeOk/<title>', methods=['POST'])
def review_write(title):
  token_receive = request.cookies.get('mytoken')

  try:
      payload = jwt.decode(token_receive,SECRET_KEY,algorithms=['HS256'])
      member_info = db.member.find_one({"mem_id":payload['id']})
      nick = member_info['mem_nick']
  
      # 리뷰 정보 받아오기
      hashtag = request.form['hashtag']
      visuals = request.form.getlist('visual')
      story = request.form.getlist('story')
      funny = request.form.getlist('funny')
      watch_again = request.form.getlist('wa')
      review_text = request.form['review_text']

      # 해당 netflix의 리뷰 개수를 받아와서 추가할 리뷰의 번호를 지정
      netflix = db.netflix.find_one({'net_title': title}, {'_id': False})

      num = netflix['net_rv_count'] + 1

      review = {
          'rv_num': num,
          'rv_nick':nick,
          'rv_hashtag':hashtag,
          'rv_visual': len(visuals), 
          'rv_story': len(story), 
          'rv_funny': len(funny), 
          'rv_watch_again': len(watch_again), 
          'rv_review': review_text, 
          'rv_net_title': title
      }

      # DB에 리뷰 정보 업데이트
      db.review.insert_one(review)

      # 해당 netflix의 리뷰 개수를 업데이트해서 DB에 적용
      db.netflix.update_one({ "net_title": title }, { "$inc": { "net_rv_count": 1 } })

      return redirect(url_for('review_list', title=title, nick=nick))

  except jwt.ExpiredSignatureError:
      return redirect(url_for("login_page", msg ="로그인 시간 만료!"))
  except jwt.exceptions.DecodeError:
      return redirect(url_for("login_page",msg = "로그인 정보 없음!"))

@app.route('/review/list/<title>', methods=['GET'])
def review_list(title):

    # 1. DB에서 해당 Netflix 정보 모두 가져오기
    netflix = db.netflix.find_one({"net_title": title}, {"_id": False})

    # 2. DB에서 해당 Netflix 리뷰 목록 반환하기
    reviews = list(db.review.find({"rv_net_title": title}, {'_id': False}))

    # 3. Netflix 정보 & 리뷰 목록 반환하기
    return render_template("review_list.html", netflix=netflix, reviews=reviews)
        
if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)