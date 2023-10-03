from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

#Database configuration
db = SQLAlchemy()
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('URI_STRING')
db.init_app(app)

#Loading Bootstrap
bootstrap = Bootstrap5(app)

#Flask_login Setup
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Databases
class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(1000))
    day = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    note = db.relationship('Notes')

    def __repr__(self):
        return f'<User {self.username}>'

#Forms
class SignupForm(FlaskForm):
    username= StringField('Username', validators=[DataRequired()], render_kw={'placeholder': 'wayne1212'})
    email= StringField('Email', validators=[DataRequired(), Email()], render_kw={'placeholder': 'john@email.com'})
    password= PasswordField('Password', validators=[DataRequired(), Length(min=8, max=12)])
    confirm = PasswordField('Confirm Password', [DataRequired(), EqualTo('password')])
    submit= SubmitField('SignUp')

class LoginForm(FlaskForm):
    email= StringField('Email', validators=[DataRequired()])
    password= PasswordField('Password', validators=[DataRequired()])
    submit= SubmitField('Login')


with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("home.html", user=current_user)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                flash("LogIn Successfully.", category='success')
                return redirect(url_for('home'))
            else:
                flash("Incorrect Password.", category='error')
        else:
            flash("This email does not exists. Please Sign Up first.", category='error')
            return redirect(url_for('sign_up'))
    return render_template("login.html", form=form, user=current_user)

@app.route("/sign_up", methods=['GET', 'POST'])
def sign_up():
    form = SignupForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data
            user = User.query.filter_by(email=email).first()
            hashed_password = generate_password_hash(
                form.password.data,
                method="pbkdf2",
                salt_length=8
            )
            new_user = User(
                username=form.username.data,
                email=form.email.data,
                password=hashed_password
            )
            if user:
                flash("Email already exists. Login instead!", category='error')
                return redirect(url_for('login'))
            else:
                db.session.add(new_user)
                db.session.commit()
                flash("Account Created Successfully. Redirected to Home Page!", category='info')
            return redirect(url_for('home'))
    return render_template("sign_up.html", form=form, user=current_user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/notes", methods=['GET', 'POST'])
@login_required
def notes():
    if request.method == 'POST':
        note = request.form.get("note")
        new_note = Notes(data=note, user_id=current_user.id)
        db.session.add(new_note)
        db.session.commit()
        flash("Note Added!", category='success')

    return render_template('notes.html', user=current_user)

@app.route("/delete/<int:note_id>")
def delete_note(note_id):
    note = db.get_or_404(Notes, note_id)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('notes'))

if __name__ == "__main__":
    app.run(debug=True)

