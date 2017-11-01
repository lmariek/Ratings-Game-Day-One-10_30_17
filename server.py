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
    """Check account registration information for user."""

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
            return redirect('/users/{user_id}'.format(user_id=check.user_id))
        else:
            flash('Incorrect password')
            return redirect('/log_in')
    else:
        flash('Incorrect login information')
        return redirect('/log_in')


@app.route('/users/<user_id>')
def display_user_details(user_id):
    """Display information about each user."""

    user = User.query.get(user_id)
    age = user.age
    zipcode = user.zipcode
    ratings = user.ratings

    return render_template('user_details.html', user=user, age=age, 
                                                zipcode=zipcode, ratings=ratings)


@app.route('/movies')
def movie_list():
    """Show list of movies."""

    movies = Movie.query.order_by(Movie.title).all()
    return render_template('movies_list.html', movies=movies)


@app.route('/movies/<movie_id>')
def display_movie_details(movie_id):
    """Display information about each movie."""

    movie = Movie.query.get(movie_id)
    movie_id = movie.movie_id
    title = movie.title
    released_at = movie.released_at
    imdb_url = movie.imdb_url

    user_id = session.get("user_id")

    if user_id:
        user_rating = Rating.query.filter_by(
            movie_id=movie_id, user_id=user_id).first()

    else:
        user_rating = None

    #pull out scores for movie
    ratings = movie.ratings

    total_scores = 0
    count = 0
    #calculate average rating for each movie
    for rating in ratings:
        num_rating = rating.score
        total_scores += rating.score
        count += 1

    avg = total_scores/float(count)

    prediction = None
    # prediction code
    if (not user_rating) and user_id:
        user = User.query.get(user_id)
        if user:
            prediction = user.predict_rating(movie)

    # Either use the prediction or their real rating

    if prediction:
        # User hasn't scored; use our prediction if we made one
        effective_rating = prediction

    elif user_rating:
        # User has already scored for real; use that
        effective_rating = user_rating.score

    else:
        # User hasn't scored, and we couldn't get a prediction
        effective_rating = None

    # Get the eye's rating, either by predicting or using real rating

    the_eye = (User.query.filter_by(email="the_eye@of_judgment.com").one())
    eye_rating = Rating.query.filter_by(
        user_id=the_eye.user_id, movie_id=movie.movie_id).first()

    if eye_rating is None:
        eye_rating = the_eye.predict_rating(movie)

    else:
        eye_rating = eye_rating.score

    if eye_rating and effective_rating:
        difference = abs(eye_rating - effective_rating)

    else:
        # We couldn't get an eye rating, so we'll skip difference
        difference = None

    BERATEMENT_MESSAGES = [
        "I suppose you don't have such bad taste after all.",
        "I regret every decision that I've ever made that has " +
            "brought me to listen to your opinion.",
        "Words fail me, as your taste in movies has clearly " +
            "failed you.",
        "That movie is great. For a clown to watch. Idiot.",
        "Words cannot express the awfulness of your taste."
    ]

    if difference is not None:
        beratement = BERATEMENT_MESSAGES[int(difference)]

    else:
        beratement = None


    return render_template('movie_details.html', movie=movie, title=title,
                                                released_at=released_at,
                                                imdb_url=imdb_url, avg=avg,
                                                ratings=ratings,
                                                movie_id=movie_id,
                                                user_rating=user_rating,
                                                prediction=prediction,
                                                beratement=beratement)


@app.route('/rate_movie/<movie_id>', methods=['POST'])
def add_rating_to_db(movie_id):
    """Update rating display to include new user input."""

    rating = request.form.get('rating')

    temp_user_id = session['user_id']
    check = Rating.query.filter(Rating.user_id == temp_user_id,
                         Rating.movie_id == movie_id).first()

    if check:
        check.score = rating
        db.session.commit()
    else:
        new_rating = Rating(score=rating,
                            user_id=temp_user_id,
                            movie_id=movie_id)
        db.session.add(new_rating)
        db.session.commit()

    return redirect('/movies/{movie_id}'.format(movie_id=movie_id))


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)



    app.run(port=5000, host='0.0.0.0')
