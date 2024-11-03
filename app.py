import os
from flask import Flask, redirect, url_for, render_template, request
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

tasks = [
    {
        "name": "sample", 
        "done": True
    },
    {
        "name": "sample 2", 
        "done": False
    }
]

@app.route("/")
@login_required
def index():
    return render_template("index.html", tasks=tasks, user=current_user)

# Auth routes
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        form_data = request.form
        user = User.query.filter_by(username=form_data['username']).first()
        if user and bcrypt.check_password_hash(user.password_hash, form_data['password']):
            login_user(user, form_data['remember'])
            return redirect(url_for('index'))
        
        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

@app.route("/logout", methods=['POST'])
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
            form_data = request.form

            if User.query.where(User.username == form_data['username']).first():
                return render_template("signup.html", error=f"User with username {form_data['username']} already exists.")

            hashed_password = bcrypt.generate_password_hash(form_data['password'], 5).decode('utf-8')
            user = User(form_data['username'], hashed_password)

            db.session.add(user)
            db.session.commit()

            return redirect(url_for('login'))

    return render_template("signup.html")

# Task routes
@app.route("/add-task", methods=['POST'])
@login_required
def add_task():
    form_data = request.form

    task = Task(form_data['name'], datetime.strptime(form_data['due_date'], '%Y-%m-%d'), current_user.id)

    db.session.add(task)
    db.session.commit()

    return redirect(url_for('index'))

@app.route("/update-task")
def update_task():
    return ""

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
