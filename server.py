"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import Flask, jsonify, render_template, redirect, request, flash, session
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""
  
    return render_template('homepage.html')


@app.route('/users')
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template('user_list.html', users=users)

@app.route('/register')
def register_user():
    """Allow user to make an account."""

    return render_template('registration_form.html')

@app.route('/registration_confirm', methods=["POST"])
def redirect_to_users():

    email = request.form.get("email")
    password = request.form.get("password")

    test = len(User.query.filter(User.email == email).all())
    if test >= 1:
        flash('This user already exists')
    else:
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.user_id

    return redirect("/users")

@app.route('/log_in')
def log_in():
    """Renders log in form."""

    return render_template('log_in_form.html')


@app.route('/log_out')
def log_out():
    """Logs out user and removes from session."""

    flash('Successfully logged out')
    del session['user_id']
    return redirect('/')

@app.route('/log_confirm', methods=["POST"])
def log_confirm():
    """Check whether email and password input matches database."""

    new_email = request.form.get("email")
    password = request.form.get("password")
    check = User.query.filter(User.email == new_email).first()

    if check:

        if check.password == password:
            session['user_id'] = check.user_id
            flash('Logged In')
            return redirect('/')
        else:
            flash('Incorrect password')
            return redirect('/log_in')
    else:
        flash('Incorrect login information')
        return redirect('/log_in')

@app.route('/users/<user_id>')
def display_user_details(user_id):

    user = User.query.get(user_id)
    age = user.age
    zipcode = user.zipcode
    ratings = user.ratings

    return render_template('user_details.html', user=user, age=age, 
                                                zipcode=zipcode, ratings=ratings)


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)


    
    app.run(port=5000, host='0.0.0.0')
