from datetime import datetime, timedelta
import os
from flask import Flask, redirect, url_for, render_template, request
from flask.json import jsonify
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from sqlalchemy import inspect
from models import db, User, Task

# Flask
app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = '\x14B~^\x07\xe1\x197\xda\x18\xa6[[\x05\x03QVg\xce%\xb2<\x80\xa4\x00'
app.config['DEBUG'] = True

# Database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'book.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
db.init_app(app)

# Flask Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

bcrypt = Bcrypt(app)

@app.route("/")
@login_required
def index():
  user_tasks = Task.query.where(Task.user_id == current_user.id).order_by(Task.due_date)
  return render_template("index.html", user=current_user, tasks=user_tasks)

# Auth routes
@app.route("/login", methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
    return redirect(url_for('index'))
  
  if request.method == 'POST':
    form_data = request.form

    user = User.query.where(User.username == form_data['username']).first()
    if user and bcrypt.check_password_hash(user.password_hash, form_data['password']):
      login_user(user, True if form_data.get('remember') is not None else False, timedelta(0, 1, 0, 0, 0))
      return redirect(url_for('index'))
    
    return render_template("login.html", error="Invalid username or password")

  return render_template("login.html")

@app.route("/logout", methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/signup", methods=['GET', 'POST'])
def signup():
  error = None
  
  if request.method == 'POST':
    form_data = request.form  
    try:
      if not form_data.get('username'):
        error = "Please insert a username."
      elif not form_data.get('password'):
        error = "Please insert a password."
      elif User.query.filter_by(username=form_data['username'].strip()).first():
        error = f"User with username {form_data['username']} already exists."

      if not error:
        hashed_password = bcrypt.generate_password_hash(
            form_data['password'], 
            5
        ).decode('utf-8')
        
        user = User(
            username=form_data['username'].strip(),
            password_hash=hashed_password
        )

        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('login'))
              
    except Exception as e:
      db.session.rollback()
      app.logger.error(f"Error during signup: {str(e)}")
      error = "An unexpected error occurred. Please try again."
      
  return render_template("signup.html", error=error)

# Task routes
@app.route("/add-task", methods=['POST'])
@login_required
def add_task():
  form_data = request.form

  task = Task(form_data['name'], datetime.strptime(form_data['due_date'], '%Y-%m-%d'), current_user.id)

  db.session.add(task)
  db.session.commit()

  return redirect(url_for('index'))

@app.route("/update-task/<int:task_id>", methods=['PUT'])
def update_task(task_id):
  data = request.json
  task = Task.query.where(Task.id == task_id).first()

  if task:
    task.name = data.get('name', task.name)
    task.due_date = datetime.strptime(data.get('due_date'), '%Y-%m-%d')
    db.session.commit()
    return jsonify({'success': True}), 200
  else:
    return jsonify({'error': 'Task not found'}), 404

@app.route("/update-task-status/<int:task_id>", methods=['PUT'])
def update_task_status(task_id):
  data = request.json
  task = Task.query.where(Task.id == task_id).first()

  if task:
    task.is_done = data.get('is_done', task.is_done)
    db.session.commit()
    return jsonify({'success': True}), 200
  else:
    return jsonify({'error': 'Task not found'}), 404
  
@app.route("/delete-task/<int:task_id>", methods=['DELETE'])
def delete_task(task_id):
  task = Task.query.where(Task.id == task_id).first()

  try:
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True}), 200
  except:
    return jsonify({'error': 'Unable to delete task'}), 404

@app.route('/tasks', methods=['GET'])
def get_tasks():
  sort_by = request.args.get('sort_by')
  order = request.args.get('order', 'asc')

  order_by_field = {
    'name': Task.name,
    'due_date': Task.due_date,
    'is_done': Task.is_done
  }.get(sort_by, Task.due_date)

  query = Task.query.filter(Task.user_id == current_user.id)
  
  if order == 'desc':
    query = query.order_by(order_by_field.desc())
  else:
    query = query.order_by(order_by_field.asc())
  
  tasks = query.all()

  if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
    return jsonify([{
      'id': task.id,
      'name': task.name,
      'due_date': task.due_date.strftime('%Y-%m-%d'),
      'is_done': task.is_done
    } for task in tasks])
  
  return render_template("index.html", user=current_user, tasks=tasks)


def init_db():
  """Initialize the database."""
  try:
    with app.app_context():
      # Create database directory if it doesn't exist
      db_path = os.path.join(basedir, 'book.sqlite')
      db_dir = os.path.dirname(db_path)
      os.makedirs(db_dir, exist_ok=True)

      # Create all tables
      db.create_all()
      print("~🚀 Database initialized")
          
      # Check if tables were created
      inspector = inspect(db.engine)
      tables = inspector.get_table_names()
      print(f"Created tables: {tables}")
                  
  except Exception as e:
    print(f"Error initializing database: {e}")
    raise

if __name__ == "__main__":
  init_db()  # This will recreate the database and tables

  app.run(port=3000)
