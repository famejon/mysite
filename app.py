from flask import Flask, render_template, request, redirect, url_for, session
import csv
import os
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'famejon'

VOTES_FILE = 'votes.csv'
CANDIDATES_FILE = 'candidates.csv'
VOTERS_FILE = 'voter_ids.csv'
CANDIDATES_INFO_FILE = 'nomzodlar_malumot.csv'
IP_LOG_FILE = 'ip_log.csv'
NEWS_FILE = 'news.csv'
ADMIN_PASSWORD = 'fameadmin'

# Fayllar mavjud bo‘lmasa, yaratish
for file_path, header in [
    (VOTES_FILE, ['id', 'candidate']),
    (CANDIDATES_FILE, ['name']),
    (VOTERS_FILE, ['id']),
    (IP_LOG_FILE, ['timestamp', 'ip_address', 'path']),
    (NEWS_FILE, ['title', 'content', 'image'])
]:
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)

class CandidateInfo:
    def __init__(self, name, age, clas, goal, photo):
        self.name = name
        self.age = age
        self.class_ = clas
        self.goal = goal
        self.photo = photo

@app.route('/home')
def home():
    candidates = []
    if os.path.exists(CANDIDATES_INFO_FILE):
        with open(CANDIDATES_INFO_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                candidates.append({
                    'name': row.get('name', ''),
                    'age': row.get('age', ''),
                    'class': row.get('class', ''),
                    'goal': row.get('goal', ''),
                    'photo': row.get('photo', '')
                })

    school_info = {
        'name': "Quvasoy shahar ixtisoslashtirilgan maktabi",
        'founded': "2022-yil",
        'director': "Akbarova Muattarxon Baxadirovna",
        'area': "4.5 gektar",
        'teachers': 45,
        'students': 450,
        'specialization': "Aniq va tabiy yo'nalishlar",
        'language': "Barcha darslar o'zbek tilida olib boriladi."
    }

    news = []
    news_dir = 'static/news'
    if not os.path.exists(news_dir):
        os.makedirs(news_dir)

    if os.path.exists(NEWS_FILE):
        with open(NEWS_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                image_filename = row.get('image', 'default.jpg')
                image_path = f'static/news/{image_filename}'

                if not os.path.exists(image_path) or image_filename == '':
                    image_filename = 'default.jpg'
                    # Create default.jpg if it doesn't exist
                    default_path = 'static/news/default.png'
                    if not os.path.exists(default_path):
                        # Create a placeholder default image path
                        image_filename = 'default.jpg'

                news.append({
                    'title': row.get('title', 'Yangilik'),
                    'content': row.get('content', 'Yangilik mazmuni'),
                    'image': image_filename
                })

    if not news:
        news = [
            {
                'title': 'Maktab yangiliklari',
                'content': 'Maktabimizda sodir bo\'layotgan eng so\'nggi yangiliklar va e\'lonlar.',
                'image': 'default.jpg'
            }
        ]

    return render_template('home.html', candidates=candidates, school_info=school_info, news=news)

@app.route("/faxirlarimiz")
def faxirlarimiz():
    data = []
    if os.path.exists("faxirlar.csv"):
        with open("faxirlar.csv", newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append({
                    'name': row.get('name', ''),
                    'success': row.get('success', ''),
                    'year': row.get('year', ''),
                    'level': row.get('level', ''),
                    'comment': row.get('comment', '')
                })
    return render_template("faxirlarimiz.html", data=data)


@app.route('/', methods=['GET', 'POST'])
def vote():
    message = ''
    candidates_info = []
    if os.path.exists(CANDIDATES_INFO_FILE):
        with open(CANDIDATES_INFO_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                candidates_info.append(CandidateInfo(
                    row['name'], row['age'], row['class'], row['goal'], row['photo']
                ))

    if request.method == 'GET':
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(IP_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, ip, '/vote'])

    if request.method == 'POST':
        voter_id = request.form['voter_id'].strip()
        candidate = request.form['candidate']

        with open(VOTERS_FILE, 'r', encoding='utf-8') as f:
            valid_ids = [row['id'] for row in csv.DictReader(f)]
        if voter_id not in valid_ids:
            message = "ID noto‘g‘ri yoki ro‘yxatda yo‘q!"
            return render_template('vote.html', candidates_info=candidates_info, message=message)

        with open(VOTES_FILE, 'r', encoding='utf-8') as f:
            if any(row['id'] == voter_id for row in csv.DictReader(f)):
                message = "Bu ID orqali allaqachon ovoz berilgan!"
                return render_template('vote.html', candidates_info=candidates_info, message=message)

        with open(VOTES_FILE, 'a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow([voter_id, candidate])
        message = "✅ Ovoz muvaffaqiyatli berildi!"

    return render_template('vote.html', candidates_info=candidates_info, message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Noto'g'ri parol!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    message = ''
    with open(CANDIDATES_FILE, 'r', encoding='utf-8') as f:
        candidates = [row['name'] for row in csv.DictReader(f)]

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            name = request.form['name'].strip()
            if name and name not in candidates:
                with open(CANDIDATES_FILE, 'a', newline='', encoding='utf-8') as f:
                    csv.writer(f).writerow([name])
                message = f"{name} qo‘shildi."
            else:
                message = "Nomzod mavjud yoki noto‘g‘ri."

        elif action == 'delete':
            name = request.form['name']
            candidates = [c for c in candidates if c != name]
            with open(CANDIDATES_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['name'])
                for c in candidates:
                    writer.writerow([c])
            message = f"{name} o‘chirildi."

        elif action == 'edit':
            old_name = request.form['old_name']
            new_name = request.form['name'].strip()
            candidates = [new_name if c == old_name else c for c in candidates]
            with open(CANDIDATES_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['name'])
                for c in candidates:
                    writer.writerow([c])
            message = f"{old_name} o‘rniga {new_name} yozildi."

        elif action == 'clear_votes':
            with open(VOTES_FILE, 'w', newline='', encoding='utf-8') as f:
                csv.writer(f).writerow(['id', 'candidate'])
            message = "Barcha ovozlar o‘chirildi."

    with open(CANDIDATES_FILE, 'r', encoding='utf-8') as f:
        candidates = [row['name'] for row in csv.DictReader(f)]

    return render_template('admin.html', message=message, candidates=candidates)

@app.route('/results')
def results():
    vote_counts = defaultdict(int)
    with open(VOTES_FILE, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            vote_counts[row['candidate']] += 1

    winner = max(vote_counts, key=vote_counts.get) if vote_counts else None
    return render_template('results.html', vote_counts=vote_counts, winner=winner)

if __name__ == '__main__':
    app.run(debug=True)
