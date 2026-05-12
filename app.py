from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from flask_socketio import SocketIO, send
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import pytz
import pymysql
pymysql.install_as_MySQLdb()

user = os.environ.get("DB_USER")
pwd = os.environ.get("DB_PASSWORD")
host = os.environ.get("DB_HOST")
name = os.environ.get("DB_NAME")



app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER')


db = SQLAlchemy(app)
socketio =  SocketIO(app, async_mode='eventlet')

# -------------------- Models --------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(80), nullable=False)
    receiver = db.Column(db.String(80), nullable=False)
    text = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    is_read = db.Column(db.Boolean, nullable=False, default=False)

# -------------------- Routes --------------------
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('chat'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username.capitalize()).first()
    if user and check_password_hash(user.password, password):
        session['username'] = username.capitalize()
        return redirect(url_for('chat'))
    return 'Invalid credentials'

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            return 'User already exists'
        user = User(username=username.capitalize(), password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('index'))

    current_user = session['username']
    users = User.query.filter(User.username != current_user).order_by(User.username).all()

    unread_counts = {}
    for user in users:
        count = Message.query.filter_by(sender=user.username, receiver=current_user, is_read=False).count()
        unread_counts[user.username] = count

    return render_template('chat.html', users=users, messages=[], username=current_user, unread_counts=unread_counts)


@app.route('/messages/<receiver_username>', methods=['GET'])
def get_messages(receiver_username):
    current_user = session.get('username')
    if not current_user:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    messages = Message.query.filter(
        ((Message.sender == current_user) & (Message.receiver == receiver_username)) |
        ((Message.sender == receiver_username) & (Message.receiver == current_user))
    ).order_by(Message.timestamp).all()

    message_list = [{
        "sender": m.sender,
        "receiver": m.receiver,
        "text": m.text,
        "time": m.timestamp.strftime('%d/%m/%Y - %I:%M %p'),
        "is_read": m.is_read
    } for m in messages]

    return jsonify({"status": "success", "messages": message_list})


@app.route('/mark_read', methods=['POST'])
def mark_read():
    data = request.get_json()
    sender = data.get('sender')
    receiver = session.get('username')

    if not sender or not receiver:
        return jsonify({"status": "error", "message": "Missing data"}), 400

    unread_msgs = Message.query.filter_by(sender=sender, receiver=receiver, is_read=False).all()
    for msg in unread_msgs:
        msg.is_read = True

    db.session.commit()
    return jsonify({"status": "success", "read_count": len(unread_msgs)})

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

# -------------------- SocketIO Events --------------------
@socketio.on('message')
def handle_message(msg):
    username = session.get('username', 'Unknown')
    receiver = msg.get('receiver')
    text = msg.get('text')

    if not text or not receiver:
        return  # don't process incomplete messages

    india_tz = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(india_tz)

    # Save to database
    message = Message(sender=username, receiver=receiver, text=text, timestamp=current_time, is_read=False)
    db.session.add(message)
    db.session.commit()

    formatted_time = current_time.strftime('%d/%m/%Y - %I:%M %p')

    # Send message to all connected clients
    send({
        'sender': username,
        'receiver': receiver,
        'text': text,
        'time': formatted_time,
        'is_read': False
    }, broadcast=True)
 
    
# -------------------- Main --------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=False)

