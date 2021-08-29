import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, jsonify, Markup
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import smtplib
from functools import wraps


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
# db = SQL(os.getenv("DATABASE_URL"))
db = SQL("sqlite:///volunteersNet.db")
# redirect user to homepage if they are not logged in


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


@app.route('/', methods=['POST', 'GET'])
def index():
    # subscribe to newsletter
    if request.method == 'POST':
        # get the user's email
        email = request.form.get('email')
        emails = [em['email']
                  for em in db.execute('SELECT email FROM subscribers')]
        if email:
            # check to see if the user is already subscribed before adding the email to database
            if email in emails:
                flash("You are already subscribed to our Mailing list " +
                      u'\U0001F525', "info")
            else:
                db.execute('INSERT INTO subscribers (email) VALUES (?)', email)
                flash("Thanks for Subscribing! " + u'\U0001F64C', 'info')
            return redirect('/')
    return render_template('index.html')


@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == 'POST':
        # get the user's info
        username = request.form.get("username")
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        mode = request.form.get("mode")
        if mode == 'recruiter':
            company = request.form.get("company")
        else:
            company = None

        # Validate inputs
        if db.execute("SELECT username FROM users WHERE username=?", username):
            flash("User name Is Taken", "danger")
            return redirect('/signup')
        if db.execute("SELECT email FROM users WHERE email=?", email):
            flash(
                Markup('An account has been registered with this Email, <a href="/login">Login</a>'), 'info')
            return redirect('/signup')
        if password1 != password2:
            flash("Passwords Don't Match", "danger")
            return redirect('/signup')

        # add the user's input to a database
        password = generate_password_hash(password1)
        db.execute("INSERT INTO users (username, email, password, mode, company) VALUES (?, ?, ?, ?, ?)",
                   username, email, password, mode, company)
        # Set session keys. 'user_id' is the id of the user in the db
        # and 'user_mode' tells if the user is signed up as a 'recruiter' or a 'volunteer'
        user_id = db.execute(
            "SELECT id FROM users WHERE username=?", username)[0]['id']
        session["user_id"] = user_id
        session["user_mode"] = db.execute(
            "SELECT mode FROM users WHERE username=?", username)[0]['mode']
        flash("You have successfully registered!", 'info')
        return redirect('/')
    else:
        return render_template('signup.html')


@app.route('/login', methods=["GET", "POST"])
def login():

    if request.method == 'POST':
        # get user info for login
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        # validate user input
        if not username or not email or not password:
            flash("Please fill out the boxes below", "danger")
            return redirect('/login')
        # query the row of the user
        row = db.execute(
            "SELECT * FROM users WHERE username=? AND email=?", username, email)

        # if a user is not found in the table with username, email and password or if the password is incorrect
        if len(row) != 1 or not check_password_hash(row[0]['password'], password):
            flash("incorrect Username and password combination", "danger")
            return redirect('/login')

        # clear any old session
        session.clear()

        # store the new user's id in session
        session['user_id'] = row[0]['id']
        session['user_mode'] = row[0]['mode']
        return redirect('/')
    else:
        return render_template('login.html')


@app.route('/logout')
def logout():
    # clear any old session
    session.clear()
    return redirect('/')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    '''contact us page'''
    if request.method == 'POST':
        # get sender's info
        email = request.form.get('email')
        password = request.form.get('password')
        subject = request.form.get('subject')
        message = request.form.get('message')
        message = 'Subject: {}\n\nYou have recieved a new email from.{}\n{}'.format(
            subject, email, message)

        # send the message to the admin as if it was sent from a single common email
        # THIS IS JUST A TEMPORARY EMAIL
        admin = "pasiki1202@enamelme.com"
        common_sender_email = "cyzajyfu@onekisspresave.com"
        common_sender_password = "1234"
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(common_sender_email, common_sender_password)
            server.sendmail(common_sender_email, admin, message)
            server.quit()
        except:
            flash("Couldn't send email, try again", "danger")
        return redirect('/contact')
    else:
        return render_template('contact.html')


@app.route('/volunteer-form', methods=['GET', 'POST'])
@login_required
def vform():
    '''volunteer form'''
    user_id = session['user_id']
    if request.method == 'POST':
        # get data from the volunteers form
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        age = request.form.get('age')
        phone = request.form.get('phone')
        country = request.form.get('country')
        city = request.form.get('city')
        street1 = request.form.get('street1')
        street2 = request.form.get('street2')
        days = request.form.getlist('days')
        activities = request.form.getlist('activities')
        other = request.form.get('other-text')

        # check to see if the user has already submitted the form
        exists = db.execute(
            "SELECT * FROM applications WHERE applicant_id=?", user_id)
        if any(exists) and exists[0]:
            flash(Markup(
                "You have already submitted this form, wait till you get <a href='/offers'>Offers</a>" + u'\U0001f609'), "info")
            return redirect('/')

        # validate input
        if not days:
            flash("You have to select at least 1 day", "info")
            return redirect('/volunteer-form')
        if not activities:
            flash("You have to select at least 1 activity", "info")
            return redirect('/volunteer-form')
        if other:
            activities.append(other)
        activities = [a for a in activities if a != 'other']
        # add the info to applications table
        # I converted 'days' and 'activities' to string so that I can store a list of values in a single cell
        db.execute(
            "INSERT INTO applications (applicant_id, fname, lname, age, phone, country, city, street1, street2, days, activities) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            user_id, fname, lname, age, phone, country, city, street1, street2, str(days), str(activities))

        return redirect('/')
    else:
        current_row = db.execute(
            'SELECT mode FROM users WHERE id = ?', session['user_id'])
        if current_row[0]['mode'] == 'recruiter':
            return redirect('/')
        return render_template('vform.html')


@app.route('/search')
@login_required
def search():
    '''Filter and search volunteers data'''
    # if the user is signed in as a volunteer, redirect them to the homepage because only a recruiter can access this page
    current_row = db.execute(
        'SELECT mode FROM users WHERE id = ?', session['user_id'])
    if current_row[0]['mode'] == 'volunteer':
        return redirect('/')
    # get the provided parameters
    country = request.args.get("country")
    city = request.args.get("city")
    age = request.args.get("age")
    if age and age == '40+':
        age = ['40', '200']
    elif age:
        age = age.split('-')
    days = request.args.getlist("days")
    activities = request.args.getlist("activities")
    other = request.args.get("other-text")
    if other:
        activities.append(other.lower())

    if country and city and age and days and activities:
        # search the database with the given inputs
        search_results = db.execute("SELECT * FROM applications WHERE country = ? AND city = ? AND age BETWEEN ? AND ? AND days = ? AND activities = ?",
                                    country, city, age[0], age[1], str(days), str(activities))

        if not any(search_results):
            search_results.append({"found": None})
            no_results = "No results found"
            return render_template('search.html', no_results=no_results)
        for applicant in search_results:
            applicant['activities'] = activities
            applicant['days'] = days
        return render_template('search.html', search_results=search_results)
    elif country and city and not (age or days or activities):
        flash("Please fill out the form below", "warning")
    return render_template('search.html')


@app.route('/request_volunteer', methods=['POST'])
def request_volunteer():
    '''Send a request to a volunteer'''
    # get the id and username of the volunteer to whom the request is being sent
    applicant_id = request.get_json()[0]['applicant_id']
    volunteer_name = db.execute(
        "SELECT username FROM users WHERE id=?", applicant_id)[0]['username']
    recruiter_name = db.execute(
        "SELECT username FROM users WHERE id=?", session['user_id'])[0]['username']
    try:
        # append the requester(the recruiter), the 'volunteer' and the status i.e. pending, accepted, rejected
        db.execute(
            "INSERT INTO offers (user_id, recruiter, volunteer, status) VALUES (?, ?, ?, ?)", applicant_id, recruiter_name, volunteer_name, "pending")
        results = {'processed': 'true'}
    except:
        results = {'processed': 'false'}
    return jsonify(results)


@login_required
@app.route('/offers', methods=['POST', 'GET'])
def offers():
    '''Displays all the offers that the volunteer has received'''
    username = db.execute(
        "SELECT username FROM users WHERE id=?", session['user_id'])[0]['username']
    if request.method == "POST":
        # update the status of 'offers' table based on the data sent from AJAX
        recruiter = request.get_json()[0]['recruiter']
        response_id = request.get_json()[1]['response_id']
        db.execute("UPDATE offers SET status=? WHERE volunteer=? AND recruiter=?",
                   response_id, username, recruiter)
        return jsonify({'status': response_id})
    else:
        # get all the offers that the volunteer received
        offers_for_volunteer = db.execute(
            "SELECT recruiter, status FROM offers WHERE volunteer=?", username)
        if not any(offers_for_volunteer):
            msg = f"You haven't received any offers yet."
            return render_template('offers.html', msg=msg)
        for offer in offers_for_volunteer:
            # add the recruiter's email and company name to 'offers_for_volunteer'
            email = db.execute(
                'SELECT email FROM users WHERE username=?', offer['recruiter'])[0]['email']
            company = db.execute(
                'SELECT company FROM users WHERE username=?', offer['recruiter'])[0]['company']
            offer['email'] = email
            offer['company'] = company
        return render_template('offers.html', offers_for_volunteer=offers_for_volunteer)


@login_required
@app.route('/requests')
def requests():
    '''Displays all the requests made by the recruiter'''
    recruiter = db.execute(
        "SELECT username FROM users WHERE id=?", session['user_id'])[0]['username']
    requested_offers = db.execute(
        "SELECT user_id, volunteer, status FROM offers WHERE recruiter=?", recruiter)
    if not any(requested_offers):
        msg = "You haven't made any requests yet"
        return render_template("requested.html", msg=msg)
    # get the whole info about each volunteers that the recruiter sent requests to
    for offer in requested_offers:
        vol_info = db.execute(
            "SELECT applicant_id, fname, lname, age, phone, country, city, street1, days, activities FROM applications WHERE applicant_id=?", offer['user_id'])[0]
        offer['name'] = vol_info['fname'] + ' ' + vol_info['lname']
        offer['location'] = f"{vol_info['street1'].capitalize()}, {vol_info['city'].capitalize()}, {vol_info['country'].capitalize()}"
        offer['days'] = vol_info['days'][1:-1].replace(" ", "").split(',')
        offer['days'] = [d[1:-1] for d in offer['days']]
        offer['activities'] = vol_info['activities'][1:-
                                                     1].replace(" ", "").split(',')
        offer['activities'] = [a[1:-1] for a in offer['activities']]
        offer['age'] = vol_info['age']
        offer['phone'] = vol_info['phone']
        offer['email'] = db.execute(
            'SELECT email FROM users WHERE id=?', vol_info['applicant_id'])[0]['email']

    return render_template('requested.html', requested_offers=requested_offers)


if __name__ == '__main__':
    app.run()
