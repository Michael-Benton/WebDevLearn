from flask import Flask, render_template, url_for, redirect, request, abort, flash, json
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin, login_required, auth_token_required
from flask_mail import Mail
import sys
from flask_security.forms import RegisterForm, StringField, Required
from flask_login import current_user, LoginManager
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import exc

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://michaelbenton@localhost:5432/flaskmovie'
app.config['SECRET_KEY'] = 'super-secret'
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_PASSWORD_SALT'] = b"xxx"
app.config['SECURITY_PASSWORD_HASH'] = "sha512_crypt"
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'bill.haverty1234@gmail.com'
app.config['MAIL_PASSWORD'] = 'abcd1234!@'
app.config['SECURITY_EMAIL_SENDER'] = 'no-reply@localhost'
app.config['SECURITY_POST_LOGIN_VIEW'] = 'index'
app.config['SECURITY_POST_LOGOUT_VIEW'] = 'index'
app.config['SECURITY_POST_REGISTER_VIEW'] = 'index'
app.config['WTF_CSRF_ENABLED'] = False
mail = Mail(app)

db = SQLAlchemy(app)
login_manager = LoginManager()

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    email = db.Column(db.String(180), unique=True)
    password = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean(), default=False)
    active = db.Column(db.Boolean())
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))


class watchList(db.Model):
    __tablename__ = "watchList"

    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('Movie.movie_id'))
    tv_id = db.Column(db.Integer, db.ForeignKey('TV.tv_id'))
    title = db.Column(db.String(200))
    releaseDate = db.Column(db.DateTime())
    producer = db.Column(db.String(100))
    description = db.Column(db.String(300))
    genre = db.Column(db.String(50))
    image = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship("User", backref=db.backref('watchList'))



class Movie(db.Model):
    __tablename__ = 'Movie'

    movie_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    releaseDate = db.Column(db.Date)
    producer = db.Column(db.String(100))
    description = db.Column(db.String(300))
    genre = db.Column(db.String(50))
    image = db.Column(db.String(300))
    is_movie = db.Column(db.Boolean(), default=True)
    is_show = db.Column(db.Boolean(), default=False)


class TV(db.Model):
    __tablename__ = 'TV'

    tv_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200))
    releaseDate = db.Column(db.DateTime)
    producer = db.Column(db.String(100))
    description = db.Column(db.String(300))
    genre = db.Column(db.String(50))
    image = db.Column(db.String(300))
    is_movie = db.Column(db.Boolean(), default=False)
    is_show = db.Column(db.Boolean(), default=True)


class ExtendedRegisterForm(RegisterForm):
    first_name = StringField('First Name', [Required()])
    last_name = StringField('Last Name', [Required()])


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, register_form=ExtendedRegisterForm)


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


def require_admin():
    if not current_user.is_admin:
        abort(403)


@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    return render_template('index.html', error=error)


@app.route('/addMovie', methods=['GET', 'POST'])
@login_required
def addMovie():
    require_admin()
    error = None
    return render_template('addMovie.html', error=error)

@app.route('/addTV', methods=['GET', 'POST'])
@login_required
def addTV():
    require_admin()
    error = None
    return render_template('addTV.html', error=error)

@app.route('/search', methods=["GET"])
def search():
    error = None
    user_input = request.args.get("query")
    search_results_movie = Movie.query.all()
    search_results_tv = TV.query.all()
    i = 0
    j = 0
    listOfResults = []

    while j < len(search_results_movie):
        if (search_results_movie[i].title.lower()).find(user_input.lower()) is not -1:
            listOfResults.append(search_results_movie[i])

        i += 1
        j += 1

    i = 0
    j = 0

    while j < len(search_results_tv):
        if (search_results_tv[i].title.lower()).find(user_input.lower()) is not -1:
            listOfResults.append(search_results_tv[i])
        i += 1
        j += 1

    if len(listOfResults) is 0:
        error = 'No results found'
        return render_template("index.html", error=error)

    return render_template("index.html", results=listOfResults)


@app.route('/addToWatchList', methods=["POST"])
@login_required
def addToWatchList():
    error=None
    movie_list = Movie.query.all()
    tv_list = TV.query.all()
    watch_list = watchList.query.all()
    movie = None
    show = None
    i = 0
    j = 0

    is_movie = request.form.get('is_movie')
    is_show = request.form.get('is_show')

    if is_movie == 'True':
        while j < len(movie_list):
            if int(movie_list[i].movie_id) == int(request.form.get('id')):
                movie = movie_list[i]

            i += 1
            j += 1

    i = 0
    j = 0

    if is_show == 'True':
        while j < len(tv_list):
            if int(tv_list[i].tv_id) == int(request.form.get('id')):
                show = tv_list[i]

            i += 1
            j += 1

    if show is None:
        if len(watch_list) != 0:
            if db.session.query(watchList).filter(watchList.movie_id == movie.movie_id,
                                                  watchList.user_id == current_user.id).first():
                error = 'Movie is already in your watchlist'
                return redirect(url_for('MovieDescription', title=movie.title, error=error))

        movieItem = watchList(user_id=current_user.id,movie_id=movie.movie_id, tv_id=None, title=movie.title,
                              releaseDate=movie.releaseDate, producer=movie.producer, description=movie.description,
                              genre=movie.genre, image=movie.image)
        db.session.add(movieItem)
        db.session.commit()

        flash("This Movie has been added to your watch list!")
        return redirect(url_for('profile', id=current_user.id, movies=watchList.query.all()))

    else:
        if len(watch_list) != 0:
            if db.session.query(watchList).filter(watchList.tv_id == show.tv_id,
                                                  watchList.user_id == current_user.id).first():
                error = 'TV Show is already in your watchlist'
                return redirect(url_for('TVShowDescription', title=show.title, error=error))

        showItem = watchList(user_id=current_user.id, movie_id=None, tv_id=show.tv_id,title=show.title,
                             releaseDate=show.releaseDate, producer=show.producer, description=show.description,
                             genre=show.genre, image=show.image)
        db.session.add(showItem)
        db.session.commit()

        flash("This TV Show has been added to your watch list!")
        return redirect(url_for('profile', id=current_user.id, movies=watchList.query.all()))


@app.route('/deleteFromWatchList', methods=['POST'])
def deleteFromWatchList():
    itemToBeDeleted = request.form.get('id')
    itemsInWatchList = watchList.query.all()
    i = 0

    while i < len(itemsInWatchList):
        if int(itemToBeDeleted) == int(itemsInWatchList[i].id):
            db.session.delete(itemsInWatchList[i])
            db.session.commit()
        i += 1

    return redirect(url_for('profile', id=current_user.id, movies=watchList.query.all()))


def getUserWatchList(id):
    watchList_results = watchList.query.all()
    listItems = []

    i = 0
    if len(watchList_results) != 0:
        while i < len(watchList_results):
            if int(watchList_results[i].user_id) == int(id):
                listItems.append(watchList_results[i])
            i += 1

    return listItems


def getReccomendations(wl):

    movie_list = []
    tv_show_list = []
    all_movies = Movie.query.all()
    all_shows = TV.query.all()

    i = 0
    while i < len(wl):
        j = 0
        while j < len(all_movies):
            if all_movies[j].movie_id == wl[i].movie_id:
                all_movies.remove(all_movies[j])
            j += 1
        i += 1

    i = 0
    while i < len(wl):
            j = 0
            while j < len(all_shows):
                if all_shows[j].tv_id == wl[i].tv_id:
                    all_shows.remove(all_shows[j])
                j += 1
            i += 1

    if len(wl) != 0:
        last_entry = wl[len(wl) - 1]
        last_entry_genre = last_entry.genre

        i = 0
        while i < len(all_movies):
            if all_movies[i].genre == last_entry_genre:
                movie_list.append(all_movies[i])
            if len(movie_list) == 5:
                break
            i += 1

        i = 0
        while i < len(all_shows):
            if all_shows[i].genre == last_entry_genre:
                tv_show_list.append(all_shows[i])
            if len(tv_show_list) == 5:
                break
            i += 1

    return tv_show_list + movie_list


@app.route('/profile/<id>')
@login_required
def profile(id):

    wl = getUserWatchList(int(id))
    recommendationList = getReccomendations(wl)

    return render_template('profile.html', movies=wl,
                           recommendations=recommendationList)


@app.route('/post_user', methods=['POST'])
def post_user():
    user = User(request.form['first_name'], request.form['last_name'], request.form['email'], request.form['password'])
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('login'))


@app.route('/TVShowDescription/<string:title>')
def TVShowDescription(title):
    tvItems = TV.query.all()
    i = 0
    j = 0

    while j < len(tvItems):
        if tvItems[i].title == title:
            return render_template("TVShowDescription.html", result=tvItems[i])
        i += 1
        j += 1

    return redirect(url_for('index'))


@app.route('/MovieDescription/<string:title>')
def MovieDescription(title):
    movieItems = Movie.query.all()
    i = 0
    j = 0

    while j < len(movieItems):
        if movieItems[i].title == title:
            return render_template("MovieDescription.html", result=movieItems[i])
        i += 1
        j += 1

    return redirect(url_for('index'))


@app.route('/post_Movie', methods=['POST'])
def post_Movie():
    newItem = Movie(title=(request.form['title']).upper(), releaseDate=request.form['releaseDate'],
                      producer=request.form['producer'], description=request.form['description'],
                      genre=request.form['genre'], image=request.form['image'])
    movies = Movie.query.all()
    i = 0
    while i < len(movies):
        if movies[i].title == newItem.title:
            return redirect(url_for('movieDuplicate'))
        i += 1

    db.session.add(newItem)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/post_TVShow', methods=['POST'])
def post_TVShow():
    newItem = TV(title=request.form['title'], releaseDate=request.form['releaseDate'],
                      producer=request.form['producer'], description=request.form['description'],
                      genre=request.form['genre'], image=request.form['image'])

    shows = TV.query.all()
    i = 0
    while i < len(shows):
        if shows[i].title == newItem.title:
            return redirect(url_for('showDuplicate'))
        i += 1

    db.session.add(newItem)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/getAppWatchlist/<id>', methods=['GET'])
@auth_token_required
def getAppWatchlist(id):
    return json.dumps(getUserWatchList(int(id)), cls=AlchemyEncoder)

@app.route('/movieDuplicateFound')
def movieDuplicate():
    return render_template("movieDuplicateFound.html")


@app.route('/showDuplicateFound')
def showDuplicate():
    return render_template("showDuplicateFound.html")


class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                if field == "releaseDate":
                    data = data.isoformat()
                try:
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)


def test_new_user():
    try:
        user = User(first_name='firstName', last_name='lastName', email='teergergmail@tester.com', password='abc123',
                is_admin=True)
        db.session.add(user)
        db.session.commit()
        return 200
    except exc.SQLAlchemyError:
        sys.exit("Could not add user to Database")


def test_add_movie():
    try:
        movie = Movie(title=('Star Wars: A New Hope').upper(),
                      releaseDate='11/16/2017',
                      producer='producer name',
                      description="Luke Skywalker joins forces with a Jedi "
                      "Knight, a cocky pilot, a Wookiee and two droids to "
                      "save the galaxy from the Empire's world-destroying "
                      "battle-station while also attempting to rescue "
                      "Princess Leia from the evil Darth Vader.",
                      genre='Scifi',
                      image='https://image.ibb.co/gBPcv6/51gl8_QQETFL_SY445.jpg')
        db.session.add(movie)
        db.session.commit()
        return 200
    except exc.SQLAlchemyError:
        sys.exit("Could not add movie to Database")


def test_add_tv_show():
    try:
        show = TV(title='Rick and Morty', releaseDate='11/17/2018,09:00 PM',
                  producer='Dan Harmon',
                  description="An animated series that follows the exploits"
                               "of a super scientist and his not-so-bright "
                               "grandson.",
                  genre='Scifi',
                  image='https://image.ibb.co/gBPcv6/51gl8_QQETFL_SY445.jpg')
        db.session.add(show)
        db.session.commit()
        return 200
    except exc.SQLAlchemyError:
        sys.exit("Could not add tv show to Database")


if __name__ == '__main__':
    app.run()
