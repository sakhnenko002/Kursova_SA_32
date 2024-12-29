


from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from datetime import timedelta


app = Flask(__name__)
app.secret_key = '\x17\xcf\xb5\x7fp\xd0eT\xf0B\xb1\xff\xba[\xd7z/\xfb\x91&\xd6DS\xd6'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


app.permanent_session_lifetime = timedelta(minutes=30)


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)


class User(db.Model):
    id_user = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)


class Route(db.Model):
    id_route = db.Column(db.Integer, primary_key=True)
    route_name = db.Column(db.String(100), nullable=False)
    departure = db.Column(db.String(50), nullable=False)
    arrival = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)


class Ticket(db.Model):
    id_ticket = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id_user'), nullable=False)
    id_route = db.Column(db.Integer, db.ForeignKey('route.id_route'), nullable=False)
    date_of_purchase = db.Column(db.String(50), nullable=False)
    payment_amount = db.Column(db.Float, nullable=True)  

 
    route = db.relationship('Route', backref='tickets', lazy=True)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    username = session.get('username')
    return render_template('index.html', username=username)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        repeat_password = request.form['repeat_password']

        
        if password != repeat_password:
            return "Паролі не співпадають!"

       
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)

        
        try:
            db.session.add(new_user)
            db.session.commit()
            return "Реєстрація успішна! <a href='/login'>Увійти</a>"
        except Exception as e:
            db.session.rollback() 
            return f"Помилка: {str(e)} <a href='/login'>Увійти</a>"

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

     
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session.permanent = True  
            session['user_id'] = user.id_user
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            return "Неправильний логін або пароль."

    return render_template('login.html')


@app.route('/select_route', methods=['GET', 'POST'])
def select_route():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    
    routes = Route.query.all()

    if request.method == 'POST':
        route_id = request.form['route_id']
        return redirect(url_for('select_ticket', route_id=route_id))

    return render_template('select_route.html', routes=routes)


@app.route('/select_ticket/<int:route_id>', methods=['GET', 'POST'])
def select_ticket(route_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    route = Route.query.get(route_id)
    if request.method == 'POST':
        date_of_purchase = request.form['date_of_purchase']
        payment_amount = float(request.form['payment_amount'])

        
        if payment_amount != route.price:
            return f"Помилка: введена сума не співпадає з ціною квитка ({route.price} грн)."

        
        ticket = Ticket(id_user=session['user_id'], id_route=route_id, date_of_purchase=date_of_purchase, payment_amount=payment_amount)
        db.session.add(ticket)
        db.session.commit()

        return "Квиток заброньовано успішно! <a href='/'>На Головну сторінку</a>"

    return render_template('select_ticket.html', route=route)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    
    user_tickets = Ticket.query.filter_by(id_user=session['user_id']).all()

    if request.method == 'POST':
        ticket_id = request.form['ticket_id']
        ticket = Ticket.query.get(ticket_id)
        if ticket:
            try:
               
                db.session.delete(ticket)
                db.session.commit()
                return "Квиток скасовано успішно! <a href='/profile'>Перейти до профілю</a>"
            except Exception as e:
                db.session.rollback()  
                return f"Помилка: {str(e)}"

    return render_template('profile.html', user_tickets=user_tickets)


@app.route('/logout')
def logout():
    session.clear()  
    return redirect(url_for('index'))  


if __name__ == '__main__':
    app.run(debug=True)

