# from cs50 import SQL
from flask import Flask, jsonify, flash, redirect, render_template, request, session, url_for
from flask_session import Session
#from flask_Jglue import JSGlue
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir

from helpers import *

import os
import sqlalchemy
import urlparse
import psycopg2

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])
# url2 = urlparse.urlparse(os.environ["DATABASE_2_URL"])

conn = psycopg2.connect(
   database=url.path[1:],
   user=url.username,
   password=url.password,
   host=url.hostname,
   port=url.port
)

# conn2 = psycopg2.connect(
#    database=url2.path[1:],
#    user=url2.username,
#    password=url2.password,
#    host=url2.hostname,
#    port=url2.port
# )

class SQL(object):
    def __init__(self, url):
        try:
            self.engine = sqlalchemy.create_engine(url)
        except Exception as e:
            raise RuntimeError(e)
    def execute(self, text, *multiparams, **params):
        try:
            statement = sqlalchemy.text(text).bindparams(*multiparams, **params)
            result = self.engine.execute(str(statement.compile(compile_kwargs={"literal_binds": True})))
            # SELECT
            if result.returns_rows:
                rows = result.fetchall()
                return [dict(row) for row in rows]
            # INSERT
            elif result.lastrowid is not None:
                return result.lastrowid
            # DELETE, UPDATE
            else:
                return result.rowcount
        except sqlalchemy.exc.IntegrityError:
            return None
        except Exception as e:
            raise RuntimeError(e)

# configure application
app = Flask(__name__)
#JSGlue(app)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use database
db = SQL(os.environ["DATABASE_URL"])
# db2 = SQL(os.environ["DATABASE_2_URL"])

@app.route("/")
@login_required
def index():
    # Home page: Explore the backstory of success stories, and see how you can reach your career goals!
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("Must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("Must provide password")

        # query database for username
        rows = db.execute("SELECT id,hash FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("Invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""

    # forget any user_id
    session.clear()

    # if user reached route via GET (as by clicking a link)
    if request.method == "GET":
        return render_template("register.html")

    # if user reached route via POST (as by submitting a form via POST)
    else:
        # ensure username was submitted
        if not request.form.get("username"):
            return apology("Must provide username")
        # ensure passwords submitted and match
        elif not request.form.get("password"):
            return apology("Must provide password")
        elif not request.form.get("confirm_password"):
            return apology("Must confirm password")
        elif request.form.get("password") != request.form.get("confirm_password"):
            return apology("Passwords don't match")

        # Search database and check to see if username taken
        rows = db.execute("SELECT id FROM users WHERE username = :username", username=request.form.get("username"))
        if len(rows) == 1:
            return apology("Username is already taken. Please select another")

        # Add new user to users database, with hashed password
        db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=request.form.get("username"), hash=pwd_context.encrypt(request.form.get("password")))

        # Query database for user data just inputted
        updated_rows = db.execute("SELECT id FROM users WHERE username = :username", username=request.form.get("username"))

        # remember which user has logged in
        session["user_id"] = updated_rows[0]["id"]

        # Create row in Users database with id
        db.execute("INSERT INTO users (id) VALUES(:id)", id=session["user_id"])

        # redirect user to survey
        return redirect(url_for("survey"))

@app.route("/survey", methods=["GET", "POST"])
@login_required
def survey():
    """ Surveys user for relevant career info """

    # if user reached route via GET (as by clicking a link)
    if request.method == "GET":
        return render_template("survey.html")

     # if user reached route via POST (as by submitting a form via POST)
    else:
        # save survey data in Users database, dependent on if user inputs info for each field
        if request.form.get("first_name"):
            db.execute("UPDATE users SET first_name = :first_name WHERE id = :id", first_name=request.form.get("first_name"), id=session["user_id"])
        if request.form.get("last_name"):
            db.execute("UPDATE users SET last_name = :last_name WHERE id = :id", last_name=request.form.get("last_name"), id=session["user_id"])
        if request.form.get("first_name") and request.form.get("last_name"):
            db.execute("UPDATE users SET full_name = :full_name WHERE id = :id", full_name=request.form.get("first_name") + " " + request.form.get("last_name"), id=session["user_id"])
        if request.form.get("current_company"):
            db.execute("UPDATE users SET current_company = :current_company WHERE id = :id", current_company=request.form.get("current_company"), id=session["user_id"])
        if request.form.get("second_company"):
            db.execute("UPDATE users SET second_company = :second_company WHERE id = :id", second_company=request.form.get("second_company"), id=session["user_id"])
        if request.form.get("third_company"):
            db.execute("UPDATE users SET third_company = :third_company WHERE id = :id", third_company=request.form.get("third_company"), id=session["user_id"])
        if request.form.get("current_title_1"):
            db.execute("UPDATE users SET current_title_1 = :current_title_1 WHERE id = :id", current_title_1=request.form.get("current_title_1"), id=session["user_id"])
        if request.form.get("alternate_title_1"):
            db.execute("UPDATE users SET alternate_title_1 = :alternate_title_1 WHERE id = :id", alternate_title_1=request.form.get("alternate_title_1"), id=session["user_id"])
        if request.form.get("current_title_2"):
            db.execute("UPDATE users SET current_title_2 = :current_title_2 WHERE id = :id", current_title_2=request.form.get("current_title_2"), id=session["user_id"])
        if request.form.get("alternate_title_2"):
            db.execute("UPDATE users SET alternate_title_2 = :alternate_title_2 WHERE id = :id", alternate_title_2=request.form.get("alternate_title_2"), id=session["user_id"])
        if request.form.get("current_title_3"):
            db.execute("UPDATE users SET current_title_3 = :current_title_3 WHERE id = :id", current_title_3=request.form.get("current_title_3"), id=session["user_id"])
        if request.form.get("alternate_title_3"):
            db.execute("UPDATE users SET alternate_title_3 = :alternate_title_3 WHERE id = :id", alternate_title_3=request.form.get("alternate_title_3"), id=session["user_id"])
        if request.form.get("current_industry_1"):
            db.execute("UPDATE users SET current_industry_1 = :current_industry_1 WHERE id = :id", current_industry_1=request.form.get("current_industry_1"), id=session["user_id"])
        if request.form.get("current_industry_2"):
            db.execute("UPDATE users SET current_industry_2 = :current_industry_2 WHERE id = :id", current_industry_2=request.form.get("current_industry_2"), id=session["user_id"])
        if request.form.get("current_industry_3"):
            db.execute("UPDATE users SET current_industry_3 = :current_industry_3 WHERE id = :id", current_industry_3=request.form.get("current_industry_3"), id=session["user_id"])
        if request.form.get("year_start_1"):
            db.execute("UPDATE users SET year_start_1 = :year_start_1 WHERE id = :id", year_start_1=request.form.get("year_start_1"), id=session["user_id"])
        if request.form.get("year_start_2"):
            db.execute("UPDATE users SET year_start_2 = :year_start_2 WHERE id = :id", year_start_2=request.form.get("year_start_2"), id=session["user_id"])
        if request.form.get("year_start_3"):
            db.execute("UPDATE users SET year_start_3 = :year_start_3 WHERE id = :id", year_start_3=request.form.get("year_start_3"), id=session["user_id"])
        if request.form.get("born"):
            db.execute("UPDATE users SET born = :born WHERE id = :id", born=request.form.get("born"), id=session["user_id"])
        if request.form.get("undergraduate_school"):
            db.execute("UPDATE users SET undergraduate_school = :undergraduate_school WHERE id = :id", undergraduate_school=request.form.get("undergraduate_school"), id=session["user_id"])
        if request.form.get("undergraduate_major"):
            db.execute("UPDATE users SET undergraduate_major = :undergraduate_major WHERE id = :id", undergraduate_major=request.form.get("undergraduate_major"), id=session["user_id"])
        if request.form.get("undergraduate_major_1_2"):
            db.execute("UPDATE users SET undergraduate_major_1_2 = :undergraduate_major_1_2 WHERE id = :id", undergraduate_major_1_2=request.form.get("undergraduate_major_1_2"), id=session["user_id"])
        if request.form.get("undergraduate_major_1_3"):
            db.execute("UPDATE users SET undergraduate_major_1_3 = :undergraduate_major_1_3 WHERE id = :id", undergraduate_major_1_3=request.form.get("undergraduate_major_1_3"), id=session["user_id"])
        if request.form.get("undergraduate_graduation_year"):
            db.execute("UPDATE users SET undergraduate_graduation_year = :undergraduate_graduation_year WHERE id = :id", undergraduate_graduation_year=request.form.get("undergraduate_graduation_year"), id=session["user_id"])
        if request.form.get("undergraduate_school_2"):
            db.execute("UPDATE users SET undergraduate_school_2 = :undergraduate_school_2 WHERE id = :id", undergraduate_school_2=request.form.get("undergraduate_school_2"), id=session["user_id"])
        if request.form.get("undergraduate_major_2"):
            db.execute("UPDATE users SET undergraduate_major_2 = :undergraduate_major_2 WHERE id = :id", undergraduate_major_2=request.form.get("undergraduate_major_2"), id=session["user_id"])
        if request.form.get("undergraduate_major_2_2"):
            db.execute("UPDATE users SET undergraduate_major_2_2 = :undergraduate_major_2_2 WHERE id = :id", undergraduate_major_2_2=request.form.get("undergraduate_major_2_2"), id=session["user_id"])
        if request.form.get("undergraduate_major_2_3"):
            db.execute("UPDATE users SET undergraduate_major_2_3 = :undergraduate_major_2_3 WHERE id = :id", undergraduate_major_2_3=request.form.get("undergraduate_major_2_3"), id=session["user_id"])
        if request.form.get("undergraduate_graduation_year_2"):
            db.execute("UPDATE users SET undergraduate_graduation_year_2 = :undergraduate_graduation_year_2 WHERE id = :id", undergraduate_graduation_year_2=request.form.get("undergraduate_graduation_year_2"), id=session["user_id"])
        if request.form.get("prep_school"):
            db.execute("UPDATE users SET prep_school = :prep_school WHERE id = :id", prep_school=request.form.get("prep_school"), id=session["user_id"])
        if request.form.get("postgraduate_school"):
            db.execute("UPDATE users SET postgraduate_school = :postgraduate_school WHERE id = :id", postgraduate_school=request.form.get("postgraduate_school"), id=session["user_id"])
        if request.form.get("postgraduate_degree_1"):
            db.execute("UPDATE users SET postgraduate_degree_1 = :postgraduate_degree_1 WHERE id = :id", postgraduate_degree_1=request.form.get("postgraduate_degree_1"), id=session["user_id"])
        if request.form.get("field"):
            db.execute("UPDATE users SET field = :field WHERE id = :id", field=request.form.get("field"), id=session["user_id"])
        if request.form.get("postgraduate_graduation_year"):
            db.execute("UPDATE users SET postgraduate_graduation_year = :postgraduate_graduation_year WHERE id = :id", postgraduate_graduation_year=request.form.get("postgraduate_graduation_year"), id=session["user_id"])
        if request.form.get("postgraduate_school_2"):
            db.execute("UPDATE users SET postgraduate_school_2 = :postgraduate_school_2 WHERE id = :id", postgraduate_school_2=request.form.get("postgraduate_school_2"), id=session["user_id"])
        if request.form.get("postgraduate_degree_2"):
            db.execute("UPDATE users SET postgraduate_degree_2 = :postgraduate_degree_2 WHERE id = :id", postgraduate_degree_2=request.form.get("postgraduate_degree_2"), id=session["user_id"])
        if request.form.get("field_2"):
            db.execute("UPDATE users SET field_2 = :field_2 WHERE id = :id", field_2=request.form.get("field_2"), id=session["user_id"])
        if request.form.get("postgraduate_graduation_year_2"):
            db.execute("UPDATE users SET postgraduate_graduation_year_2 = :postgraduate_graduation_year_2 WHERE id = :id", postgraduate_graduation_year_2=request.form.get("postgraduate_graduation_year_2"), id=session["user_id"])
        if request.form.get("initial_career_path_interest_1"):
            db.execute("UPDATE users SET initial_career_path_interest_1 = :initial_career_path_interest_1 WHERE id = :id", initial_career_path_interest_1=request.form.get("initial_career_path_interest_1"), id=session["user_id"])
        if request.form.get("initial_career_path_interest_2"):
            db.execute("UPDATE users SET initial_career_path_interest_2 = :initial_career_path_interest_2 WHERE id = :id", initial_career_path_interest_2=request.form.get("initial_career_path_interest_2"), id=session["user_id"])
        if request.form.get("post_college_job"):
            db.execute("UPDATE users SET post_college_job = :post_college_job WHERE id = :id", post_college_job=request.form.get("post_college_job"), id=session["user_id"])
        if request.form.get("post_college_company"):
            db.execute("UPDATE users SET post_college_company = :post_college_company WHERE id = :id", post_college_company=request.form.get("post_college_company"), id=session["user_id"])
        if request.form.get("post_college_year_start"):
            db.execute("UPDATE users SET post_college_year_start = :post_college_year_start WHERE id = :id", post_college_year_start=request.form.get("post_college_year_start"), id=session["user_id"])
        if request.form.get("post_college_year_end"):
            db.execute("UPDATE users SET post_college_year_end = :post_college_year_end WHERE id = :id", post_college_year_end=request.form.get("post_college_year_end"), id=session["user_id"])
        if request.form.get("past_company_1"):
            db.execute("UPDATE users SET past_company_1 = :past_company_1 WHERE id = :id", past_company_1=request.form.get("past_company_1"), id=session["user_id"])
        if request.form.get("past_position_1"):
            db.execute("UPDATE users SET past_position_1 = :past_position_1 WHERE id = :id", past_position_1=request.form.get("past_position_1"), id=session["user_id"])
        if request.form.get("alternate_past_position_1"):
            db.execute("UPDATE users SET alternate_past_position_1 = :alternate_past_position_1 WHERE id = :id", alternate_past_position_1=request.form.get("alternate_past_position_1"), id=session["user_id"])
        if request.form.get("past_company_2"):
            db.execute("UPDATE users SET past_company_2 = :past_company_2 WHERE id = :id", past_company_2=request.form.get("past_company_2"), id=session["user_id"])
        if request.form.get("past_position_2"):
            db.execute("UPDATE users SET past_position_2 = :past_position_2 WHERE id = :id", past_position_2=request.form.get("past_position_2"), id=session["user_id"])
        if request.form.get("alternate_past_position_2"):
            db.execute("UPDATE users SET alternate_past_position_2 = :alternate_past_position_2 WHERE id = :id", alternate_past_position_2=request.form.get("alternate_past_position_2"), id=session["user_id"])
        if request.form.get("past_company_3"):
            db.execute("UPDATE users SET past_company_3 = :past_company_3 WHERE id = :id", past_company_3=request.form.get("past_company_3"), id=session["user_id"])
        if request.form.get("past_position_3"):
            db.execute("UPDATE users SET past_position_3 = :past_position_3 WHERE id = :id", past_position_3=request.form.get("past_position_3"), id=session["user_id"])
        if request.form.get("alternate_past_position_3"):
            db.execute("UPDATE users SET alternate_past_position_3 = :alternate_past_position_3 WHERE id = :id", alternate_past_position_3=request.form.get("alternate_past_position_3"), id=session["user_id"])
        if request.form.get("past_company_4"):
            db.execute("UPDATE users SET past_company_4 = :past_company_4 WHERE id = :id", past_company_4=request.form.get("past_company_4"), id=session["user_id"])
        if request.form.get("past_position_4"):
            db.execute("UPDATE users SET past_position_4 = :past_position_4 WHERE id = :id", past_position_4=request.form.get("past_position_4"), id=session["user_id"])
        if request.form.get("alternate_past_position_4"):
            db.execute("UPDATE users SET alternate_past_position_4 = :alternate_past_position_4 WHERE id = :id", alternate_past_position_4=request.form.get("alternate_past_position_4"), id=session["user_id"])
        if request.form.get("past_year_start_1"):
            db.execute("UPDATE users SET past_year_start_1 = :past_year_start_1 WHERE id = :id", past_year_start_1=request.form.get("past_year_start_1"), id=session["user_id"])
        if request.form.get("past_year_end_1"):
            db.execute("UPDATE users SET past_year_end_1 = :past_year_end_1 WHERE id = :id", past_year_end_1=request.form.get("past_year_end_1"), id=session["user_id"])
        if request.form.get("past_year_start_2"):
            db.execute("UPDATE users SET past_year_start_2 = :past_year_start_2 WHERE id = :id", past_year_start_2=request.form.get("past_year_start_2"), id=session["user_id"])
        if request.form.get("past_year_end_2"):
            db.execute("UPDATE users SET past_year_end_2 = :past_year_end_2 WHERE id = :id", past_year_end_2=request.form.get("past_year_end_2"), id=session["user_id"])
        if request.form.get("past_year_start_3"):
            db.execute("UPDATE users SET past_year_start_3 = :past_year_start_3 WHERE id = :id", past_year_start_3=request.form.get("past_year_start_3"), id=session["user_id"])
        if request.form.get("past_year_end_3"):
            db.execute("UPDATE users SET past_year_end_3 = :past_year_end_3 WHERE id = :id", past_year_end_3=request.form.get("past_year_end_3"), id=session["user_id"])
        if request.form.get("past_year_start_4"):
            db.execute("UPDATE users SET past_year_start_4 = :past_year_start_4 WHERE id = :id", past_year_start_4=request.form.get("past_year_start_4"), id=session["user_id"])
        if request.form.get("past_year_end_4"):
            db.execute("UPDATE users SET past_year_end_4 = :past_year_end_4 WHERE id = :id", past_year_end_4=request.form.get("past_year_end_4"), id=session["user_id"])
        if request.form.get("career_position_looking_for"):
            db.execute("UPDATE users SET career_position_looking_for = :career_position_looking_for WHERE id = :id", career_position_looking_for=request.form.get("career_position_looking_for"), id=session["user_id"])
        if request.form.get("industry_looking_towards"):
            db.execute("UPDATE users SET industry_looking_towards = :industry_looking_towards WHERE id = :id", industry_looking_towards=request.form.get("industry_looking_towards"), id=session["user_id"])
        if request.form.get("dream_company"):
            db.execute("UPDATE users SET dream_company = :dream_company WHERE id = :id", dream_company=request.form.get("dream_company"), id=session["user_id"])
        if request.form.get("miscellaneous"):
            db.execute("UPDATE users SET miscellaneous = :miscellaneous WHERE id = :id", miscellaneous=request.form.get("miscellaneous"), id=session["user_id"])

        # Render homepage after saving data
        return render_template("index.html")

@app.route("/similarities", methods=["GET", "POST"])
@login_required
def similarities():
    """ Presents list of profiles with image of people who have similarities- eventually make it so specific similarity is noted and can click on name to bring up profile"""

    # Save for each category the name, image, and category of match
    user_info = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])

    # Initialize match row variables
    current_company_match_rows = None
    second_company_match_rows = None
    third_company_match_rows = None
    post_college_company_match_Rows = None
    past_company_1_match_rows = None
    past_company_2_match_rows = None
    past_company_3_match_rows = None
    past_company_4_match_rows = None
    dream_company_match_rows = None
    current_title_1_match_rows = None
    alternate_title_1_match_rows = None
    current_title_2_match_rows = None
    alternate_title_2_match_rows = None
    current_title_3_match_rows = None
    alternate_title_3_match_rows = None
    post_college_job_match_rows = None
    past_position_1_match_rows = None
    alternate_past_position_1_match_rows = None
    past_position_2_match_rows = None
    alternate_past_position_2_match_rows = None
    past_position_3_match_rows = None
    alternate_past_position_3_match_rows = None
    past_position_4_match_rows = None
    alternate_past_position_4_match_rows = None
    career_position_looking_for_match_rows = None
    prep_school_match_rows = None
    undergraduate_school_match_rows = None
    undergraduate_school_2_match_rows = None
    postgraduate_school_match_rows = None
    postgraduate_school_2_match_rows = None
    undergraduate_graduation_year_match_rows = None
    undergraduate_graduation_year_2_match_rows = None
    postgraduate_graduation_year_match_rows = None
    postgraduate_graduation_year_2_match_rows = None
    undergraduate_major_match_rows = None
    undergraduate_major_1_2_match_rows = None
    undergraduate_major_1_3_match_rows = None
    undergraduate_major_2_match_rows = None
    undergraduate_major_2_2_match_rows = None
    undergraduate_major_2_3_match_rows = None
    field_match_rows = None
    field_2_match_rows = None
    current_industry_1_match_rows = None
    current_industry_2_match_rows = None
    current_industry_3_match_rows = None
    initial_career_path_interest_1_match_rows = None
    initial_career_path_interest_2_match_rows = None
    industry_looking_towards_match_rows = None
    born_match_rows = None

    # Match based on companies
    if user_info[0]["current_company"] != None:
        current_company_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :current_company_1=current_company OR :current_company_2=second_company OR :current_company_3=third_company OR :current_company_4=past_company_1 OR :current_company_5=past_company_2 OR :current_company_6=past_company_3 OR :current_company_7=past_company_4 OR :current_company_8=post_college_company", current_company_1=user_info[0]["current_company"], current_company_2=user_info[0]["current_company"], current_company_3=user_info[0]["current_company"], current_company_4=user_info[0]["current_company"], current_company_5=user_info[0]["current_company"], current_company_6=user_info[0]["current_company"], current_company_7=user_info[0]["current_company"], current_company_8=user_info[0]["current_company"])
    if user_info[0]["second_company"] != None:
        second_company_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :second_company_1=current_company OR :second_company_2=second_company OR :second_company_3=third_company OR :second_company_4=past_company_1 OR :second_company_5=past_company_2 OR :second_company_6=past_company_3 OR :second_company_7=past_company_4 OR :second_company_8=post_college_company", second_company_1=user_info[0]["second_company"], second_company_2=user_info[0]["second_company"], second_company_3=user_info[0]["second_company"], second_company_4=user_info[0]["second_company"], second_company_5=user_info[0]["second_company"], second_company_6=user_info[0]["second_company"], second_company_7=user_info[0]["second_company"], second_company_8=user_info[0]["second_company"])
    if user_info[0]["third_company"] != None:
        third_company_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :third_company_1=current_company OR :third_company_2=second_company OR :third_company_3=third_company OR :third_company_4=past_company_1 OR :third_company_5=past_company_2 OR :third_company_6=past_company_3 OR :third_company_7=past_company_4 OR :third_company_8=post_college_company", third_company_1=user_info[0]["third_company"], third_company_2=user_info[0]["third_company"], third_company_3=user_info[0]["third_company"], third_company_4=user_info[0]["third_company"], third_company_5=user_info[0]["third_company"], third_company_6=user_info[0]["third_company"], third_company_7=user_info[0]["third_company"], third_company_8=user_info[0]["third_company"])
    if user_info[0]["past_company_1"] != None:
        past_company_1_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :past_company_1_1=current_company OR :past_company_1_2=second_company OR :past_company_1_3=third_company OR :past_company_1_4=past_company_1 OR :past_company_1_5=past_company_2 OR :past_company_1_6=past_company_3 OR :past_company_1_7=past_company_4 OR :past_company_1_8=post_college_company", past_company_1_1=user_info[0]["past_company_1"], past_company_1_2=user_info[0]["past_company_1"], past_company_1_3=user_info[0]["past_company_1"], past_company_1_4=user_info[0]["past_company_1"], past_company_1_5=user_info[0]["past_company_1"], past_company_1_6=user_info[0]["past_company_1"], past_company_1_7=user_info[0]["past_company_1"], past_company_1_8=user_info[0]["past_company_1"])
    if user_info[0]["past_company_2"] != None:
        past_company_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :past_company_2_1=current_company OR :past_company_2_2=second_company OR :past_company_2_3=third_company OR :past_company_2_4=past_company_1 OR :past_company_2_5=past_company_2 OR :past_company_2_6=past_company_3 OR :past_company_2_7=past_company_4 OR :past_company_2_8=post_college_company", past_company_2_1=user_info[0]["past_company_2"], past_company_2_2=user_info[0]["past_company_2"], past_company_2_3=user_info[0]["past_company_2"], past_company_2_4=user_info[0]["past_company_2"], past_company_2_5=user_info[0]["past_company_2"], past_company_2_6=user_info[0]["past_company_2"], past_company_2_7=user_info[0]["past_company_2"], past_company_2_8=user_info[0]["past_company_2"])
    if user_info[0]["past_company_3"] != None:
        past_company_3_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :past_company_3_1=current_company OR :past_company_3_2=second_company OR :past_company_3_3=third_company OR :past_company_3_4=past_company_1 OR :past_company_3_5=past_company_2 OR :past_company_3_6=past_company_3 OR :past_company_3_7=past_company_4 OR :past_company_3_8=post_college_company", past_company_3_1=user_info[0]["past_company_3"], past_company_3_2=user_info[0]["past_company_3"], past_company_3_3=user_info[0]["past_company_3"], past_company_3_4=user_info[0]["past_company_3"], past_company_3_5=user_info[0]["past_company_3"], past_company_3_6=user_info[0]["past_company_3"], past_company_3_7=user_info[0]["past_company_3"], past_company_3_8=user_info[0]["past_company_3"])
    if user_info[0]["past_company_4"] != None:
        past_company_4_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :past_company_4_1=current_company OR :past_company_4_2=second_company OR :past_company_4_3=third_company OR :past_company_4_4=past_company_1 OR :past_company_4_5=past_company_2 OR :past_company_4_6=past_company_3 OR :past_company_4_7=past_company_4 OR :past_company_4_8=post_college_company", past_company_4_1=user_info[0]["past_company_4"], past_company_4_2=user_info[0]["past_company_4"], past_company_4_3=user_info[0]["past_company_4"], past_company_4_4=user_info[0]["past_company_4"], past_company_4_5=user_info[0]["past_company_4"], past_company_4_6=user_info[0]["past_company_4"], past_company_4_7=user_info[0]["past_company_4"], past_company_4_8=user_info[0]["past_company_4"])
    if user_info[0]["dream_company"] != None:
        dream_company_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :dream_company_1=current_company OR :dream_company_2=second_company OR :dream_company_3=third_company OR :dream_company_4=past_company_1 OR :dream_company_5=past_company_2 OR :dream_company_6=past_company_3 OR :dream_company_7=past_company_4 OR :dream_company_8=post_college_company", dream_company_1=user_info[0]["dream_company"], dream_company_2=user_info[0]["dream_company"], dream_company_3=user_info[0]["dream_company"], dream_company_4=user_info[0]["dream_company"], dream_company_5=user_info[0]["dream_company"], dream_company_6=user_info[0]["dream_company"], dream_company_7=user_info[0]["dream_company"], dream_company_8=user_info[0]["dream_company"])
    if user_info[0]["post_college_company"] != None:
        post_college_company_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :post_college_company_1=current_company OR :post_college_company_2=second_company OR :post_college_company_3=third_company OR :post_college_company_4=past_company_1 OR :post_college_company_5=past_company_2 OR :post_college_company_6=past_company_3 OR :post_college_company_7=past_company_4 OR :post_college_company_8=post_college_company", post_college_company_1=user_info[0]["post_college_company"], post_college_company_2=user_info[0]["post_college_company"], post_college_company_3=user_info[0]["post_college_company"], post_college_company_4=user_info[0]["post_college_company"], post_college_company_5=user_info[0]["post_college_company"], post_college_company_6=user_info[0]["post_college_company"], post_college_company_7=user_info[0]["post_college_company"], post_college_company_8=user_info[0]["post_college_company"])

    # Match based on position title
    if user_info[0]["current_title_1"] != None:
        current_title_1_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :current_title_1_1=current_title_1 OR :current_title_1_2=alternate_title_1 OR :current_title_1_3=alternate_title_1_2 OR :current_title_1_4=current_title_2 OR :current_title_1_5=alternate_title_2 OR :current_title_1_6=alternate_title_2_2 OR :current_title_1_7=current_title_3 OR :current_title_1_8=alternate_title_3 OR :current_title_1_9=alternate_title_3_2 OR :current_title_1_10=post_college_job OR :current_title_1_11=past_position_1 OR :current_title_1_12=alternate_past_position_1 OR :current_title_1_13=alternate_past_position_1_2 OR :current_title_1_14=past_position_2 OR :current_title_1_15=alternate_past_position_2 OR :current_title_1_16=alternate_past_position_2_2 OR :current_title_1_17=past_position_3 OR :current_title_1_18=alternate_past_position_3 OR :current_title_1_19=alternate_past_position_3_2 OR :current_title_1_20=past_position_4 OR :current_title_1_21=alternate_past_position_4 OR :current_title_1_22=alternate_past_position_4_2", current_title_1_1=user_info[0]["current_title_1"], current_title_1_2=user_info[0]["current_title_1"], current_title_1_3=user_info[0]["current_title_1"], current_title_1_4=user_info[0]["current_title_1"], current_title_1_5=user_info[0]["current_title_1"], current_title_1_6=user_info[0]["current_title_1"], current_title_1_7=user_info[0]["current_title_1"], current_title_1_8=user_info[0]["current_title_1"], current_title_1_9=user_info[0]["current_title_1"], current_title_1_10=user_info[0]["current_title_1"], current_title_1_11=user_info[0]["current_title_1"], current_title_1_12=user_info[0]["current_title_1"], current_title_1_13=user_info[0]["current_title_1"], current_title_1_14=user_info[0]["current_title_1"], current_title_1_15=user_info[0]["current_title_1"], current_title_1_16=user_info[0]["current_title_1"], current_title_1_17=user_info[0]["current_title_1"], current_title_1_18=user_info[0]["current_title_1"], current_title_1_19=user_info[0]["current_title_1"], current_title_1_20=user_info[0]["current_title_1"], current_title_1_21=user_info[0]["current_title_1"], current_title_1_22=user_info[0]["current_title_1"])
    if user_info[0]["alternate_title_1"] != None:
        alternate_title_1_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :alternate_title_1_1=current_title_1 OR :alternate_title_1_2=alternate_title_1 OR :alternate_title_1_3=alternate_title_1_2 OR :alternate_title_1_4=current_title_2 OR :alternate_title_1_5=alternate_title_2 OR :alternate_title_1_6=alternate_title_2_2 OR :alternate_title_1_7=current_title_3 OR :alternate_title_1_8=alternate_title_3 OR :alternate_title_1_9=alternate_title_3_2 OR :alternate_title_1_10=post_college_job OR :alternate_title_1_11=past_position_1 OR :alternate_title_1_12=alternate_past_position_1 OR :alternate_title_1_13=alternate_past_position_1_2 OR :alternate_title_1_14=past_position_2 OR :alternate_title_1_15=alternate_past_position_2 OR :alternate_title_1_16=alternate_past_position_2_2 OR :alternate_title_1_17=past_position_3 OR :alternate_title_1_18=alternate_past_position_3 OR :alternate_title_1_19=alternate_past_position_3_2 OR :alternate_title_1_20=past_position_4 OR :alternate_title_1_21=alternate_past_position_4 OR :alternate_title_1_22=alternate_past_position_4_2", alternate_title_1_1=user_info[0]["alternate_title_1"], alternate_title_1_2=user_info[0]["alternate_title_1"], alternate_title_1_3=user_info[0]["alternate_title_1"], alternate_title_1_4=user_info[0]["alternate_title_1"], alternate_title_1_5=user_info[0]["alternate_title_1"], alternate_title_1_6=user_info[0]["alternate_title_1"], alternate_title_1_7=user_info[0]["alternate_title_1"], alternate_title_1_8=user_info[0]["alternate_title_1"], alternate_title_1_9=user_info[0]["alternate_title_1"], alternate_title_1_10=user_info[0]["alternate_title_1"], alternate_title_1_11=user_info[0]["alternate_title_1"], alternate_title_1_12=user_info[0]["alternate_title_1"], alternate_title_1_13=user_info[0]["alternate_title_1"], alternate_title_1_14=user_info[0]["alternate_title_1"], alternate_title_1_15=user_info[0]["alternate_title_1"], alternate_title_1_16=user_info[0]["alternate_title_1"], alternate_title_1_17=user_info[0]["alternate_title_1"], alternate_title_1_18=user_info[0]["alternate_title_1"], alternate_title_1_19=user_info[0]["alternate_title_1"], alternate_title_1_20=user_info[0]["alternate_title_1"], alternate_title_1_21=user_info[0]["alternate_title_1"], alternate_title_1_22=user_info[0]["alternate_title_1"])
    if user_info[0]["current_title_2"] != None:
        current_title_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :current_title_2_1=current_title_1 OR :current_title_2_2=alternate_title_1 OR :current_title_2_3=alternate_title_1_2 OR :current_title_2_4=current_title_2 OR :current_title_2_5=alternate_title_2 OR :current_title_2_6=alternate_title_2_2 OR :current_title_2_7=current_title_3 OR :current_title_2_8=alternate_title_3 OR :current_title_2_9=alternate_title_3_2 OR :current_title_2_10=post_college_job OR :current_title_2_11=past_position_1 OR :current_title_2_12=alternate_past_position_1 OR :current_title_2_13=alternate_past_position_1_2 OR :current_title_2_14=past_position_2 OR :current_title_2_15=alternate_past_position_2 OR :current_title_2_16=alternate_past_position_2_2 OR :current_title_2_17=past_position_3 OR :current_title_2_18=alternate_past_position_3 OR :current_title_2_19=alternate_past_position_3_2 OR :current_title_2_20=past_position_4 OR :current_title_2_21=alternate_past_position_4 OR :current_title_2_22=alternate_past_position_4_2", current_title_2_1=user_info[0]["current_title_2"], current_title_2_2=user_info[0]["current_title_2"], current_title_2_3=user_info[0]["current_title_2"], current_title_2_4=user_info[0]["current_title_2"], current_title_2_5=user_info[0]["current_title_2"], current_title_2_6=user_info[0]["current_title_2"], current_title_2_7=user_info[0]["current_title_2"], current_title_2_8=user_info[0]["current_title_2"], current_title_2_9=user_info[0]["current_title_2"], current_title_2_10=user_info[0]["current_title_2"], current_title_2_11=user_info[0]["current_title_2"], current_title_2_12=user_info[0]["current_title_2"], current_title_2_13=user_info[0]["current_title_2"], current_title_2_14=user_info[0]["current_title_2"], current_title_2_15=user_info[0]["current_title_2"], current_title_2_16=user_info[0]["current_title_2"], current_title_2_17=user_info[0]["current_title_2"], current_title_2_18=user_info[0]["current_title_2"], current_title_2_19=user_info[0]["current_title_2"], current_title_2_20=user_info[0]["current_title_2"], current_title_2_21=user_info[0]["current_title_2"], current_title_2_22=user_info[0]["current_title_2"])
    if user_info[0]["alternate_title_2"] != None:
        alternate_title_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :alternate_title_2_1=current_title_1 OR :alternate_title_2_2=alternate_title_1 OR :alternate_title_2_3=alternate_title_1_2 OR :alternate_title_2_4=current_title_2 OR :alternate_title_2_5=alternate_title_2 OR :alternate_title_2_6=alternate_title_2_2 OR :alternate_title_2_7=current_title_3 OR :alternate_title_2_8=alternate_title_3 OR :alternate_title_2_9=alternate_title_3_2 OR :alternate_title_2_10=post_college_job OR :alternate_title_2_11=past_position_1 OR :alternate_title_2_12=alternate_past_position_1 OR :alternate_title_2_13=alternate_past_position_1_2 OR :alternate_title_2_14=past_position_2 OR :alternate_title_2_15=alternate_past_position_2 OR :alternate_title_2_16=alternate_past_position_2_2 OR :alternate_title_2_17=past_position_3 OR :alternate_title_2_18=alternate_past_position_3 OR :alternate_title_2_19=alternate_past_position_3_2 OR :alternate_title_2_20=past_position_4 OR :alternate_title_2_21=alternate_past_position_4 OR :alternate_title_2_22=alternate_past_position_4_2", alternate_title_2_1=user_info[0]["alternate_title_2"], alternate_title_2_2=user_info[0]["alternate_title_2"], alternate_title_2_3=user_info[0]["alternate_title_2"], alternate_title_2_4=user_info[0]["alternate_title_2"], alternate_title_2_5=user_info[0]["alternate_title_2"], alternate_title_2_6=user_info[0]["alternate_title_2"], alternate_title_2_7=user_info[0]["alternate_title_2"], alternate_title_2_8=user_info[0]["alternate_title_2"], alternate_title_2_9=user_info[0]["alternate_title_2"], alternate_title_2_10=user_info[0]["alternate_title_2"], alternate_title_2_11=user_info[0]["alternate_title_2"], alternate_title_2_12=user_info[0]["alternate_title_2"], alternate_title_2_13=user_info[0]["alternate_title_2"], alternate_title_2_14=user_info[0]["alternate_title_2"], alternate_title_2_15=user_info[0]["alternate_title_2"], alternate_title_2_16=user_info[0]["alternate_title_2"], alternate_title_2_17=user_info[0]["alternate_title_2"], alternate_title_2_18=user_info[0]["alternate_title_2"], alternate_title_2_19=user_info[0]["alternate_title_2"], alternate_title_2_20=user_info[0]["alternate_title_2"], alternate_title_2_21=user_info[0]["alternate_title_2"], alternate_title_2_22=user_info[0]["alternate_title_2"])
    if user_info[0]["current_title_3"] != None:
        current_title_3_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :current_title_3_1=current_title_1 OR :current_title_3_2=alternate_title_1 OR :current_title_3_3=alternate_title_1_2 OR :current_title_3_4=current_title_2 OR :current_title_3_5=alternate_title_2 OR :current_title_3_6=alternate_title_2_2 OR :current_title_3_7=current_title_3 OR :current_title_3_8=alternate_title_3 OR :current_title_3_9=alternate_title_3_2 OR :current_title_3_10=post_college_job OR :current_title_3_11=past_position_1 OR :current_title_3_12=alternate_past_position_1 OR :current_title_3_13=alternate_past_position_1_2 OR :current_title_3_14=past_position_2 OR :current_title_3_15=alternate_past_position_2 OR :current_title_3_16=alternate_past_position_2_2 OR :current_title_3_17=past_position_3 OR :current_title_3_18=alternate_past_position_3 OR :current_title_3_19=alternate_past_position_3_2 OR :current_title_3_20=past_position_4 OR :current_title_3_21=alternate_past_position_4 OR :current_title_3_22=alternate_past_position_4_2", current_title_3_1=user_info[0]["current_title_3"], current_title_3_2=user_info[0]["current_title_3"], current_title_3_3=user_info[0]["current_title_3"], current_title_3_4=user_info[0]["current_title_3"], current_title_3_5=user_info[0]["current_title_3"], current_title_3_6=user_info[0]["current_title_3"], current_title_3_7=user_info[0]["current_title_3"], current_title_3_8=user_info[0]["current_title_3"], current_title_3_9=user_info[0]["current_title_3"], current_title_3_10=user_info[0]["current_title_3"], current_title_3_11=user_info[0]["current_title_3"], current_title_3_12=user_info[0]["current_title_3"], current_title_3_13=user_info[0]["current_title_3"], current_title_3_14=user_info[0]["current_title_3"], current_title_3_15=user_info[0]["current_title_3"], current_title_3_16=user_info[0]["current_title_3"], current_title_3_17=user_info[0]["current_title_3"], current_title_3_18=user_info[0]["current_title_3"], current_title_3_19=user_info[0]["current_title_3"], current_title_3_20=user_info[0]["current_title_3"], current_title_3_21=user_info[0]["current_title_3"], current_title_3_22=user_info[0]["current_title_3"])
    if user_info[0]["alternate_title_3"] != None:
        alternate_title_3_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :alternate_title_3_1=current_title_1 OR :alternate_title_3_2=alternate_title_1 OR :alternate_title_3_3=alternate_title_1_2 OR :alternate_title_3_4=current_title_2 OR :alternate_title_3_5=alternate_title_2 OR :alternate_title_3_6=alternate_title_2_2 OR :alternate_title_3_7=current_title_3 OR :alternate_title_3_8=alternate_title_3 OR :alternate_title_3_9=alternate_title_3_2 OR :alternate_title_3_10=post_college_job OR :alternate_title_3_11=past_position_1 OR :alternate_title_3_12=alternate_past_position_1 OR :alternate_title_3_13=alternate_past_position_1_2 OR :alternate_title_3_14=past_position_2 OR :alternate_title_3_15=alternate_past_position_2 OR :alternate_title_3_16=alternate_past_position_2_2 OR :alternate_title_3_17=past_position_3 OR :alternate_title_3_18=alternate_past_position_3 OR :alternate_title_3_19=alternate_past_position_3_2 OR :alternate_title_3_20=past_position_4 OR :alternate_title_3_21=alternate_past_position_4 OR :alternate_title_3_22=alternate_past_position_4_2", alternate_title_3_1=user_info[0]["alternate_title_3"], alternate_title_3_2=user_info[0]["alternate_title_3"], alternate_title_3_3=user_info[0]["alternate_title_3"], alternate_title_3_4=user_info[0]["alternate_title_3"], alternate_title_3_5=user_info[0]["alternate_title_3"], alternate_title_3_6=user_info[0]["alternate_title_3"], alternate_title_3_7=user_info[0]["alternate_title_3"], alternate_title_3_8=user_info[0]["alternate_title_3"], alternate_title_3_9=user_info[0]["alternate_title_3"], alternate_title_3_10=user_info[0]["alternate_title_3"], alternate_title_3_11=user_info[0]["alternate_title_3"], alternate_title_3_12=user_info[0]["alternate_title_3"], alternate_title_3_13=user_info[0]["alternate_title_3"], alternate_title_3_14=user_info[0]["alternate_title_3"], alternate_title_3_15=user_info[0]["alternate_title_3"], alternate_title_3_16=user_info[0]["alternate_title_3"], alternate_title_3_17=user_info[0]["alternate_title_3"], alternate_title_3_18=user_info[0]["alternate_title_3"], alternate_title_3_19=user_info[0]["alternate_title_3"], alternate_title_3_20=user_info[0]["alternate_title_3"], alternate_title_3_21=user_info[0]["alternate_title_3"], alternate_title_3_22=user_info[0]["alternate_title_3"])
    if user_info[0]["post_college_job"] != None:
        post_college_job_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :post_college_job_1=current_title_1 OR :post_college_job_2=alternate_title_1 OR :post_college_job_3=alternate_title_1_2 OR :post_college_job_4=current_title_2 OR :post_college_job_5=alternate_title_2 OR :post_college_job_6=alternate_title_2_2 OR :post_college_job_7=current_title_3 OR :post_college_job_8=alternate_title_3 OR :post_college_job_9=alternate_title_3_2 OR :post_college_job_10=post_college_job OR :post_college_job_11=past_position_1 OR :post_college_job_12=alternate_past_position_1 OR :post_college_job_13=alternate_past_position_1_2 OR :post_college_job_14=past_position_2 OR :post_college_job_15=alternate_past_position_2 OR :post_college_job_16=alternate_past_position_2_2 OR :post_college_job_17=past_position_3 OR :post_college_job_18=alternate_past_position_3 OR :post_college_job_19=alternate_past_position_3_2 OR :post_college_job_20=past_position_4 OR :post_college_job_21=alternate_past_position_4 OR :post_college_job_22=alternate_past_position_4_2", post_college_job_1=user_info[0]["post_college_job"], post_college_job_2=user_info[0]["post_college_job"], post_college_job_3=user_info[0]["post_college_job"], post_college_job_4=user_info[0]["post_college_job"], post_college_job_5=user_info[0]["post_college_job"], post_college_job_6=user_info[0]["post_college_job"], post_college_job_7=user_info[0]["post_college_job"], post_college_job_8=user_info[0]["post_college_job"], post_college_job_9=user_info[0]["post_college_job"], post_college_job_10=user_info[0]["post_college_job"], post_college_job_11=user_info[0]["post_college_job"], post_college_job_12=user_info[0]["post_college_job"], post_college_job_13=user_info[0]["post_college_job"], post_college_job_14=user_info[0]["post_college_job"], post_college_job_15=user_info[0]["post_college_job"], post_college_job_16=user_info[0]["post_college_job"], post_college_job_17=user_info[0]["post_college_job"], post_college_job_18=user_info[0]["post_college_job"], post_college_job_19=user_info[0]["post_college_job"], post_college_job_20=user_info[0]["post_college_job"], post_college_job_21=user_info[0]["post_college_job"], post_college_job_22=user_info[0]["post_college_job"])
    if user_info[0]["past_position_1"] != None:
        past_position_1_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :past_position_1_1=current_title_1 OR :past_position_1_2=alternate_title_1 OR :past_position_1_3=alternate_title_1_2 OR :past_position_1_4=current_title_2 OR :past_position_1_5=alternate_title_2 OR :past_position_1_6=alternate_title_2_2 OR :past_position_1_7=current_title_3 OR :past_position_1_8=alternate_title_3 OR :past_position_1_9=alternate_title_3_2 OR :past_position_1_10=post_college_job OR :past_position_1_11=past_position_1 OR :past_position_1_12=alternate_past_position_1 OR :past_position_1_13=alternate_past_position_1_2 OR :past_position_1_14=past_position_2 OR :past_position_1_15=alternate_past_position_2 OR :past_position_1_16=alternate_past_position_2_2 OR :past_position_1_17=past_position_3 OR :past_position_1_18=alternate_past_position_3 OR :past_position_1_19=alternate_past_position_3_2 OR :past_position_1_20=past_position_4 OR :past_position_1_21=alternate_past_position_4 OR :past_position_1_22=alternate_past_position_4_2", past_position_1_1=user_info[0]["past_position_1"], past_position_1_2=user_info[0]["past_position_1"], past_position_1_3=user_info[0]["past_position_1"], past_position_1_4=user_info[0]["past_position_1"], past_position_1_5=user_info[0]["past_position_1"], past_position_1_6=user_info[0]["past_position_1"], past_position_1_7=user_info[0]["past_position_1"], past_position_1_8=user_info[0]["past_position_1"], past_position_1_9=user_info[0]["past_position_1"], past_position_1_10=user_info[0]["past_position_1"], past_position_1_11=user_info[0]["past_position_1"], past_position_1_12=user_info[0]["past_position_1"], past_position_1_13=user_info[0]["past_position_1"], past_position_1_14=user_info[0]["past_position_1"], past_position_1_15=user_info[0]["past_position_1"], past_position_1_16=user_info[0]["past_position_1"], past_position_1_17=user_info[0]["past_position_1"], past_position_1_18=user_info[0]["past_position_1"], past_position_1_19=user_info[0]["past_position_1"], past_position_1_20=user_info[0]["past_position_1"], past_position_1_21=user_info[0]["past_position_1"], past_position_1_22=user_info[0]["past_position_1"])
    if user_info[0]["alternate_past_position_1"] != None:
        alternate_past_position_1_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :alternate_past_position_1_1=current_title_1 OR :alternate_past_position_1_2=alternate_title_1 OR :alternate_past_position_1_3=alternate_title_1_2 OR :alternate_past_position_1_4=current_title_2 OR :alternate_past_position_1_5=alternate_title_2 OR :alternate_past_position_1_6=alternate_title_2_2 OR :alternate_past_position_1_7=current_title_3 OR :alternate_past_position_1_8=alternate_title_3 OR :alternate_past_position_1_9=alternate_title_3_2 OR :alternate_past_position_1_10=post_college_job OR :alternate_past_position_1_11=past_position_1 OR :alternate_past_position_1_12=alternate_past_position_1 OR :alternate_past_position_1_13=alternate_past_position_1_2 OR :alternate_past_position_1_14=past_position_2 OR :alternate_past_position_1_15=alternate_past_position_2 OR :alternate_past_position_1_16=alternate_past_position_2_2 OR :alternate_past_position_1_17=past_position_3 OR :alternate_past_position_1_18=alternate_past_position_3 OR :alternate_past_position_1_19=alternate_past_position_3_2 OR :alternate_past_position_1_20=past_position_4 OR :alternate_past_position_1_21=alternate_past_position_4 OR :alternate_past_position_1_22=alternate_past_position_4_2", alternate_past_position_1_1=user_info[0]["alternate_past_position_1"], alternate_past_position_1_2=user_info[0]["alternate_past_position_1"], alternate_past_position_1_3=user_info[0]["alternate_past_position_1"], alternate_past_position_1_4=user_info[0]["alternate_past_position_1"], alternate_past_position_1_5=user_info[0]["alternate_past_position_1"], alternate_past_position_1_6=user_info[0]["alternate_past_position_1"], alternate_past_position_1_7=user_info[0]["alternate_past_position_1"], alternate_past_position_1_8=user_info[0]["alternate_past_position_1"], alternate_past_position_1_9=user_info[0]["alternate_past_position_1"], alternate_past_position_1_10=user_info[0]["alternate_past_position_1"], alternate_past_position_1_11=user_info[0]["alternate_past_position_1"], alternate_past_position_1_12=user_info[0]["alternate_past_position_1"], alternate_past_position_1_13=user_info[0]["alternate_past_position_1"], alternate_past_position_1_14=user_info[0]["alternate_past_position_1"], alternate_past_position_1_15=user_info[0]["alternate_past_position_1"], alternate_past_position_1_16=user_info[0]["alternate_past_position_1"], alternate_past_position_1_17=user_info[0]["alternate_past_position_1"], alternate_past_position_1_18=user_info[0]["alternate_past_position_1"], alternate_past_position_1_19=user_info[0]["alternate_past_position_1"], alternate_past_position_1_20=user_info[0]["alternate_past_position_1"], alternate_past_position_1_21=user_info[0]["alternate_past_position_1"], alternate_past_position_1_22=user_info[0]["alternate_past_position_1"])
    if user_info[0]["past_position_2"] != None:
        past_position_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :past_position_2_1=current_title_1 OR :past_position_2_2=alternate_title_1 OR :past_position_2_3=alternate_title_1_2 OR :past_position_2_4=current_title_2 OR :past_position_2_5=alternate_title_2 OR :past_position_2_6=alternate_title_2_2 OR :past_position_2_7=current_title_3 OR :past_position_2_8=alternate_title_3 OR :past_position_2_9=alternate_title_3_2 OR :past_position_2_10=post_college_job OR :past_position_2_11=past_position_1 OR :past_position_2_12=alternate_past_position_1 OR :past_position_2_13=alternate_past_position_1_2 OR :past_position_2_14=past_position_2 OR :past_position_2_15=alternate_past_position_2 OR :past_position_2_16=alternate_past_position_2_2 OR :past_position_2_17=past_position_3 OR :past_position_2_18=alternate_past_position_3 OR :past_position_2_19=alternate_past_position_3_2 OR :past_position_2_20=past_position_4 OR :past_position_2_21=alternate_past_position_4 OR :past_position_2_22=alternate_past_position_4_2", past_position_2_1=user_info[0]["past_position_2"], past_position_2_2=user_info[0]["past_position_2"], past_position_2_3=user_info[0]["past_position_2"], past_position_2_4=user_info[0]["past_position_2"], past_position_2_5=user_info[0]["past_position_2"], past_position_2_6=user_info[0]["past_position_2"], past_position_2_7=user_info[0]["past_position_2"], past_position_2_8=user_info[0]["past_position_2"], past_position_2_9=user_info[0]["past_position_2"], past_position_2_10=user_info[0]["past_position_2"], past_position_2_11=user_info[0]["past_position_2"], past_position_2_12=user_info[0]["past_position_2"], past_position_2_13=user_info[0]["past_position_2"], past_position_2_14=user_info[0]["past_position_2"], past_position_2_15=user_info[0]["past_position_2"], past_position_2_16=user_info[0]["past_position_2"], past_position_2_17=user_info[0]["past_position_2"], past_position_2_18=user_info[0]["past_position_2"], past_position_2_19=user_info[0]["past_position_2"], past_position_2_20=user_info[0]["past_position_2"], past_position_2_21=user_info[0]["past_position_2"], past_position_2_22=user_info[0]["past_position_2"])
    if user_info[0]["alternate_past_position_2"] != None:
        alternate_past_position_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :alternate_past_position_2_1=current_title_1 OR :alternate_past_position_2_2=alternate_title_1 OR :alternate_past_position_2_3=alternate_title_1_2 OR :alternate_past_position_2_4=current_title_2 OR :alternate_past_position_2_5=alternate_title_2 OR :alternate_past_position_2_6=alternate_title_2_2 OR :alternate_past_position_2_7=current_title_3 OR :alternate_past_position_2_8=alternate_title_3 OR :alternate_past_position_2_9=alternate_title_3_2 OR :alternate_past_position_2_10=post_college_job OR :alternate_past_position_2_11=past_position_1 OR :alternate_past_position_2_12=alternate_past_position_1 OR :alternate_past_position_2_13=alternate_past_position_1_2 OR :alternate_past_position_2_14=past_position_2 OR :alternate_past_position_2_15=alternate_past_position_2 OR :alternate_past_position_2_16=alternate_past_position_2_2 OR :alternate_past_position_2_17=past_position_3 OR :alternate_past_position_2_18=alternate_past_position_3 OR :alternate_past_position_2_19=alternate_past_position_3_2 OR :alternate_past_position_2_20=past_position_4 OR :alternate_past_position_2_21=alternate_past_position_4 OR :alternate_past_position_2_22=alternate_past_position_4_2", alternate_past_position_2_1=user_info[0]["alternate_past_position_2"], alternate_past_position_2_2=user_info[0]["alternate_past_position_2"], alternate_past_position_2_3=user_info[0]["alternate_past_position_2"], alternate_past_position_2_4=user_info[0]["alternate_past_position_2"], alternate_past_position_2_5=user_info[0]["alternate_past_position_2"], alternate_past_position_2_6=user_info[0]["alternate_past_position_2"], alternate_past_position_2_7=user_info[0]["alternate_past_position_2"], alternate_past_position_2_8=user_info[0]["alternate_past_position_2"], alternate_past_position_2_9=user_info[0]["alternate_past_position_2"], alternate_past_position_2_10=user_info[0]["alternate_past_position_2"], alternate_past_position_2_11=user_info[0]["alternate_past_position_2"], alternate_past_position_2_12=user_info[0]["alternate_past_position_2"], alternate_past_position_2_13=user_info[0]["alternate_past_position_2"], alternate_past_position_2_14=user_info[0]["alternate_past_position_2"], alternate_past_position_2_15=user_info[0]["alternate_past_position_2"], alternate_past_position_2_16=user_info[0]["alternate_past_position_2"], alternate_past_position_2_17=user_info[0]["alternate_past_position_2"], alternate_past_position_2_18=user_info[0]["alternate_past_position_2"], alternate_past_position_2_19=user_info[0]["alternate_past_position_2"], alternate_past_position_2_20=user_info[0]["alternate_past_position_2"], alternate_past_position_2_21=user_info[0]["alternate_past_position_2"], alternate_past_position_2_22=user_info[0]["alternate_past_position_2"])
    if user_info[0]["past_position_3"] != None:
        past_position_3_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :past_position_3_1=current_title_1 OR :past_position_3_2=alternate_title_1 OR :past_position_3_3=alternate_title_1_2 OR :past_position_3_4=current_title_2 OR :past_position_3_5=alternate_title_2 OR :past_position_3_6=alternate_title_2_2 OR :past_position_3_7=current_title_3 OR :past_position_3_8=alternate_title_3 OR :past_position_3_9=alternate_title_3_2 OR :past_position_3_10=post_college_job OR :past_position_3_11=past_position_1 OR :past_position_3_12=alternate_past_position_1 OR :past_position_3_13=alternate_past_position_1_2 OR :past_position_3_14=past_position_2 OR :past_position_3_15=alternate_past_position_2 OR :past_position_3_16=alternate_past_position_2_2 OR :past_position_3_17=past_position_3 OR :past_position_3_18=alternate_past_position_3 OR :past_position_3_19=alternate_past_position_3_2 OR :past_position_3_20=past_position_4 OR :past_position_3_21=alternate_past_position_4 OR :past_position_3_22=alternate_past_position_4_2", past_position_3_1=user_info[0]["past_position_3"], past_position_3_2=user_info[0]["past_position_3"], past_position_3_3=user_info[0]["past_position_3"], past_position_3_4=user_info[0]["past_position_3"], past_position_3_5=user_info[0]["past_position_3"], past_position_3_6=user_info[0]["past_position_3"], past_position_3_7=user_info[0]["past_position_3"], past_position_3_8=user_info[0]["past_position_3"], past_position_3_9=user_info[0]["past_position_3"], past_position_3_10=user_info[0]["past_position_3"], past_position_3_11=user_info[0]["past_position_3"], past_position_3_12=user_info[0]["past_position_3"], past_position_3_13=user_info[0]["past_position_3"], past_position_3_14=user_info[0]["past_position_3"], past_position_3_15=user_info[0]["past_position_3"], past_position_3_16=user_info[0]["past_position_3"], past_position_3_17=user_info[0]["past_position_3"], past_position_3_18=user_info[0]["past_position_3"], past_position_3_19=user_info[0]["past_position_3"], past_position_3_20=user_info[0]["past_position_3"], past_position_3_21=user_info[0]["past_position_3"], past_position_3_22=user_info[0]["past_position_3"])
    if User_Info[0]["Alternate_Past_Position_3"] != None:
        Alternate_Past_Position_3_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Alternate_Past_Position_3_1=Current_Title_1 OR :Alternate_Past_Position_3_2=Alternate_Title_1 OR :Alternate_Past_Position_3_3=Alternate_Title_1_2 OR :Alternate_Past_Position_3_4=Current_Title_2 OR :Alternate_Past_Position_3_5=Alternate_Title_2 OR :Alternate_Past_Position_3_6=Alternate_Title_2_2 OR :Alternate_Past_Position_3_7=Current_Title_3 OR :Alternate_Past_Position_3_8=Alternate_Title_3 OR :Alternate_Past_Position_3_9=Alternate_Title_3_2 OR :Alternate_Past_Position_3_10=Post_College_Job OR :Alternate_Past_Position_3_11=Past_Position_1 OR :Alternate_Past_Position_3_12=Alternate_Past_Position_1 OR :Alternate_Past_Position_3_13=Alternate_Past_Position_1_2 OR :Alternate_Past_Position_3_14=Past_Position_2 OR :Alternate_Past_Position_3_15=Alternate_Past_Position_2 OR :Alternate_Past_Position_3_16=Alternate_Past_Position_2_2 OR :Alternate_Past_Position_3_17=Past_Position_3 OR :Alternate_Past_Position_3_18=Alternate_Past_Position_3 OR :Alternate_Past_Position_3_19=Alternate_Past_Position_3_2 OR :Alternate_Past_Position_3_20=Past_Position_4 OR :Alternate_Past_Position_3_21=Alternate_Past_Position_4 OR :Alternate_Past_Position_3_22=Alternate_Past_Position_4_2", Alternate_Past_Position_3_1=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_2=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_3=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_4=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_5=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_6=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_7=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_8=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_9=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_10=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_11=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_12=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_13=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_14=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_15=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_16=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_17=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_18=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_19=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_20=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_21=User_Info[0]["Alternate_Past_Position_3"], Alternate_Past_Position_3_22=User_Info[0]["Alternate_Past_Position_3"])
    if User_Info[0]["Past_Position_4"] != None:
        Past_Position_4_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Past_Position_4_1=Current_Title_1 OR :Past_Position_4_2=Alternate_Title_1 OR :Past_Position_4_3=Alternate_Title_1_2 OR :Past_Position_4_4=Current_Title_2 OR :Past_Position_4_5=Alternate_Title_2 OR :Past_Position_4_6=Alternate_Title_2_2 OR :Past_Position_4_7=Current_Title_3 OR :Past_Position_4_8=Alternate_Title_3 OR :Past_Position_4_9=Alternate_Title_3_2 OR :Past_Position_4_10=Post_College_Job OR :Past_Position_4_11=Past_Position_1 OR :Past_Position_4_12=Alternate_Past_Position_1 OR :Past_Position_4_13=Alternate_Past_Position_1_2 OR :Past_Position_4_14=Past_Position_2 OR :Past_Position_4_15=Alternate_Past_Position_2 OR :Past_Position_4_16=Alternate_Past_Position_2_2 OR :Past_Position_4_17=Past_Position_3 OR :Past_Position_4_18=Alternate_Past_Position_3 OR :Past_Position_4_19=Alternate_Past_Position_3_2 OR :Past_Position_4_20=Past_Position_4 OR :Past_Position_4_21=Alternate_Past_Position_4 OR :Past_Position_4_22=Alternate_Past_Position_4_2", Past_Position_4_1=User_Info[0]["Past_Position_4"], Past_Position_4_2=User_Info[0]["Past_Position_4"], Past_Position_4_3=User_Info[0]["Past_Position_4"], Past_Position_4_4=User_Info[0]["Past_Position_4"], Past_Position_4_5=User_Info[0]["Past_Position_4"], Past_Position_4_6=User_Info[0]["Past_Position_4"], Past_Position_4_7=User_Info[0]["Past_Position_4"], Past_Position_4_8=User_Info[0]["Past_Position_4"], Past_Position_4_9=User_Info[0]["Past_Position_4"], Past_Position_4_10=User_Info[0]["Past_Position_4"], Past_Position_4_11=User_Info[0]["Past_Position_4"], Past_Position_4_12=User_Info[0]["Past_Position_4"], Past_Position_4_13=User_Info[0]["Past_Position_4"], Past_Position_4_14=User_Info[0]["Past_Position_4"], Past_Position_4_15=User_Info[0]["Past_Position_4"], Past_Position_4_16=User_Info[0]["Past_Position_4"], Past_Position_4_17=User_Info[0]["Past_Position_4"], Past_Position_4_18=User_Info[0]["Past_Position_4"], Past_Position_4_19=User_Info[0]["Past_Position_4"], Past_Position_4_20=User_Info[0]["Past_Position_4"], Past_Position_4_21=User_Info[0]["Past_Position_4"], Past_Position_4_22=User_Info[0]["Past_Position_4"])
    if User_Info[0]["Alternate_Past_Position_4"] != None:
        Alternate_Past_Position_4_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Alternate_Past_Position_4_1=Current_Title_1 OR :Alternate_Past_Position_4_2=Alternate_Title_1 OR :Alternate_Past_Position_4_3=Alternate_Title_1_2 OR :Alternate_Past_Position_4_4=Current_Title_2 OR :Alternate_Past_Position_4_5=Alternate_Title_2 OR :Alternate_Past_Position_4_6=Alternate_Title_2_2 OR :Alternate_Past_Position_4_7=Current_Title_3 OR :Alternate_Past_Position_4_8=Alternate_Title_3 OR :Alternate_Past_Position_4_9=Alternate_Title_3_2 OR :Alternate_Past_Position_4_10=Post_College_Job OR :Alternate_Past_Position_4_11=Past_Position_1 OR :Alternate_Past_Position_4_12=Alternate_Past_Position_1 OR :Alternate_Past_Position_4_13=Alternate_Past_Position_1_2 OR :Alternate_Past_Position_4_14=Past_Position_2 OR :Alternate_Past_Position_4_15=Alternate_Past_Position_2 OR :Alternate_Past_Position_4_16=Alternate_Past_Position_2_2 OR :Alternate_Past_Position_4_17=Past_Position_3 OR :Alternate_Past_Position_4_18=Alternate_Past_Position_3 OR :Alternate_Past_Position_4_19=Alternate_Past_Position_3_2 OR :Alternate_Past_Position_4_20=Past_Position_4 OR :Alternate_Past_Position_4_21=Alternate_Past_Position_4 OR :Alternate_Past_Position_4_22=Alternate_Past_Position_4_2", Alternate_Past_Position_4_1=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_2=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_3=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_4=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_5=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_6=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_7=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_8=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_9=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_10=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_11=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_12=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_13=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_14=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_15=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_16=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_17=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_18=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_19=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_20=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_21=User_Info[0]["Alternate_Past_Position_4"], Alternate_Past_Position_4_22=User_Info[0]["Alternate_Past_Position_4"])
    if User_Info[0]["Career_Position_Looking_For"] != None:
        Career_Position_Looking_For_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Career_Position_Looking_For_1=Current_Title_1 OR :Career_Position_Looking_For_2=Alternate_Title_1 OR :Career_Position_Looking_For_3=Alternate_Title_1_2 OR :Career_Position_Looking_For_4=Current_Title_2 OR :Career_Position_Looking_For_5=Alternate_Title_2 OR :Career_Position_Looking_For_6=Alternate_Title_2_2 OR :Career_Position_Looking_For_7=Current_Title_3 OR :Career_Position_Looking_For_8=Alternate_Title_3 OR :Career_Position_Looking_For_9=Alternate_Title_3_2 OR :Career_Position_Looking_For_10=Post_College_Job OR :Career_Position_Looking_For_11=Past_Position_1 OR :Career_Position_Looking_For_12=Alternate_Past_Position_1 OR :Career_Position_Looking_For_13=Alternate_Past_Position_1_2 OR :Career_Position_Looking_For_14=Past_Position_2 OR :Career_Position_Looking_For_15=Alternate_Past_Position_2 OR :Career_Position_Looking_For_16=Alternate_Past_Position_2_2 OR :Career_Position_Looking_For_17=Past_Position_3 OR :Career_Position_Looking_For_18=Alternate_Past_Position_3 OR :Career_Position_Looking_For_19=Alternate_Past_Position_3_2 OR :Career_Position_Looking_For_20=Past_Position_4 OR :Career_Position_Looking_For_21=Alternate_Past_Position_4 OR :Career_Position_Looking_For_22=Alternate_Past_Position_4_2", Career_Position_Looking_For_1=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_2=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_3=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_4=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_5=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_6=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_7=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_8=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_9=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_10=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_11=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_12=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_13=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_14=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_15=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_16=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_17=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_18=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_19=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_20=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_21=User_Info[0]["Career_Position_Looking_For"], Career_Position_Looking_For_22=User_Info[0]["Career_Position_Looking_For"])

    # Match based on schools: prep, undergrad, and grad

    if User_Info[0]["Prep_School"] != None:
        Prep_School_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Prep_School_1=Prep_School", Prep_School_1 = User_Info[0]["Prep_School"])
    if User_Info[0]["Undergraduate_School"] != None:
        Undergraduate_School_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Undergraduate_School_1=Undergraduate_School OR :Undergraduate_School_2=Undergraduate_School_2", Undergraduate_School_1 = User_Info[0]["Undergraduate_School"], Undergraduate_School_2 = User_Info[0]["Undergraduate_School"])
    if User_Info[0]["Undergraduate_School_2"] != None:
        Undergraduate_School_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Undergraduate_School_2_1=Undergraduate_School OR :Undergraduate_School_2_2=Undergraduate_School_2", Undergraduate_School_2_1 = User_Info[0]["Undergraduate_School_2"], Undergraduate_School_2_2 = User_Info[0]["Undergraduate_School_2"])
    if User_Info[0]["Postgraduate_School"] != None:
        Postgraduate_School_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Postgraduate_School_1=Postgraduate_School OR :Postgraduate_School_2=Postgraduate_School_2", Postgraduate_School_1 = User_Info[0]["Postgraduate_School"], Postgraduate_School_2 = User_Info[0]["Postgraduate_School"])
    if User_Info[0]["Postgraduate_School_2"]  != None:
        Postgraduate_School_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Postgraduate_School_2_1=Postgraduate_School OR :Postgraduate_School_2_2=Postgraduate_School_2", Postgraduate_School_2_1 = User_Info[0]["Postgraduate_School_2"], Postgraduate_School_2_2 = User_Info[0]["Postgraduate_School_2"])

    # Match based on graduation year of undergrad and grad school

    if User_Info[0]["Undergraduate_Graduation_Year_2"] != None:
        Undergraduate_Graduation_Year_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Undergraduate_Graduation_Year_2_1=Undergraduate_Graduation_Year OR :Undergraduate_Graduation_Year_2_2=Undergraduate_Graduation_Year_2", Undergraduate_Graduation_Year_2_1 = User_Info[0]["Undergraduate_Graduation_Year_2"], Undergraduate_Graduation_Year_2_2 = User_Info[0]["Undergraduate_Graduation_Year_2"])
    elif User_Info[0]["Undergraduate_Graduation_Year"] != None:
        Undergraduate_Graduation_Year_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Undergraduate_Graduation_Year_1=Undergraduate_Graduation_Year OR :Undergraduate_Graduation_Year_2=Undergraduate_Graduation_Year_2", Undergraduate_Graduation_Year_1 = User_Info[0]["Undergraduate_Graduation_Year"], Undergraduate_Graduation_Year_2 = User_Info[0]["Undergraduate_Graduation_Year"])
    if User_Info[0]["Postgraduate_Graduation_Year"] != None:
        Postgraduate_Graduation_Year_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Postgraduate_Graduation_Year_1=Postgraduate_Graduation_Year OR :Postgraduate_Graduation_Year_2=Postgraduate_Graduation_Year_2", Postgraduate_Graduation_Year_1 = User_Info[0]["Postgraduate_Graduation_Year"], Postgraduate_Graduation_Year_2 = User_Info[0]["Postgraduate_Graduation_Year"])
    if User_Info[0]["Postgraduate_Graduation_Year_2"] != None:
        Postgraduate_Graduation_Year_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Postgraduate_Graduation_Year_2_1=Postgraduate_Graduation_Year OR :Postgraduate_Graduation_Year_2_2=Postgraduate_Graduation_Year_2", Postgraduate_Graduation_Year_2_1 = User_Info[0]["Postgraduate_Graduation_Year_2"], Postgraduate_Graduation_Year_2_2 = User_Info[0]["Postgraduate_Graduation_Year_2"])

    # Match based on field of study for either undergrad or grad

    if User_Info[0]["Undergraduate_Major"] != None:
        Undergraduate_Major_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Undergraduate_Major_1=Undergraduate_Major OR :Undergraduate_Major_2=Undergraduate_Major_1_2 OR :Undergraduate_Major_3=Undergraduate_Major_1_3 OR :Undergraduate_Major_4=Undergraduate_Major_2 OR :Undergraduate_Major_5=Undergraduate_Major_2_2 OR :Undergraduate_Major_6=Undergraduate_Major_2_3 OR :Undergraduate_Major_7=Field OR :Undergraduate_Major_8=Field_2", Undergraduate_Major_1 = User_Info[0]["Undergraduate_Major"], Undergraduate_Major_2 = User_Info[0]["Undergraduate_Major"], Undergraduate_Major_3 = User_Info[0]["Undergraduate_Major"], Undergraduate_Major_4 = User_Info[0]["Undergraduate_Major"], Undergraduate_Major_5 = User_Info[0]["Undergraduate_Major"], Undergraduate_Major_6 = User_Info[0]["Undergraduate_Major"], Undergraduate_Major_7 = User_Info[0]["Undergraduate_Major"], Undergraduate_Major_8 = User_Info[0]["Undergraduate_Major"])
    if User_Info[0]["Undergraduate_Major_1_2"] != None:
        Undergraduate_Major_1_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Undergraduate_Major_1_2_1=Undergraduate_Major OR :Undergraduate_Major_1_2_2=Undergraduate_Major_1_2 OR :Undergraduate_Major_1_2_3=Undergraduate_Major_1_3 OR :Undergraduate_Major_1_2_4=Undergraduate_Major_2 OR :Undergraduate_Major_1_2_5=Undergraduate_Major_2_2 OR :Undergraduate_Major_1_2_6=Undergraduate_Major_2_3 OR :Undergraduate_Major_1_2_7=Field OR :Undergraduate_Major_1_2_8=Field_2", Undergraduate_Major_1_2_1 = User_Info[0]["Undergraduate_Major_1_2"], Undergraduate_Major_1_2_2 = User_Info[0]["Undergraduate_Major_1_2"], Undergraduate_Major_1_2_3 = User_Info[0]["Undergraduate_Major_1_2"], Undergraduate_Major_1_2_4 = User_Info[0]["Undergraduate_Major_1_2"], Undergraduate_Major_1_2_5 = User_Info[0]["Undergraduate_Major_1_2"], Undergraduate_Major_1_2_6 = User_Info[0]["Undergraduate_Major_1_2"], Undergraduate_Major_1_2_7 = User_Info[0]["Undergraduate_Major_1_2"], Undergraduate_Major_1_2_8 = User_Info[0]["Undergraduate_Major_1_2"])
    if User_Info[0]["Undergraduate_Major_1_3"] != None:
        Undergraduate_Major_1_3_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Undergraduate_Major_1_3_1=Undergraduate_Major OR :Undergraduate_Major_1_3_2=Undergraduate_Major_1_2 OR :Undergraduate_Major_1_3_3=Undergraduate_Major_1_3 OR :Undergraduate_Major_1_3_4=Undergraduate_Major_2 OR :Undergraduate_Major_1_3_5=Undergraduate_Major_2_2 OR :Undergraduate_Major_1_3_6=Undergraduate_Major_2_3 OR :Undergraduate_Major_1_3_7=Field OR :Undergraduate_Major_1_3_8=Field_2", Undergraduate_Major_1_3_1 = User_Info[0]["Undergraduate_Major_1_3"], Undergraduate_Major_1_3_2 = User_Info[0]["Undergraduate_Major_1_3"], Undergraduate_Major_1_3_3 = User_Info[0]["Undergraduate_Major_1_3"], Undergraduate_Major_1_3_4 = User_Info[0]["Undergraduate_Major_1_3"], Undergraduate_Major_1_3_5 = User_Info[0]["Undergraduate_Major_1_3"], Undergraduate_Major_1_3_6 = User_Info[0]["Undergraduate_Major_1_3"], Undergraduate_Major_1_3_7 = User_Info[0]["Undergraduate_Major_1_3"], Undergraduate_Major_1_3_8 = User_Info[0]["Undergraduate_Major_1_3"])
    if User_Info[0]["Undergraduate_Major_2"] != None:
        Undergraduate_Major_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Undergraduate_Major_2_1=Undergraduate_Major OR :Undergraduate_Major_2_2=Undergraduate_Major_1_2 OR :Undergraduate_Major_2_3=Undergraduate_Major_1_3 OR :Undergraduate_Major_2_4=Undergraduate_Major_2 OR :Undergraduate_Major_2_5=Undergraduate_Major_2_2 OR :Undergraduate_Major_2_6=Undergraduate_Major_2_3 OR :Undergraduate_Major_2_7=Field OR :Undergraduate_Major_2_8=Field_2", Undergraduate_Major_2_1 = User_Info[0]["Undergraduate_Major_2"], Undergraduate_Major_2_2 = User_Info[0]["Undergraduate_Major_2"], Undergraduate_Major_2_3 = User_Info[0]["Undergraduate_Major_2"], Undergraduate_Major_2_4 = User_Info[0]["Undergraduate_Major_2"], Undergraduate_Major_2_5 = User_Info[0]["Undergraduate_Major_2"], Undergraduate_Major_2_6 = User_Info[0]["Undergraduate_Major_2"], Undergraduate_Major_2_7 = User_Info[0]["Undergraduate_Major_2"], Undergraduate_Major_2_8 = User_Info[0]["Undergraduate_Major_2"])
    if User_Info[0]["Undergraduate_Major_2_2"] != None:
        Undergraduate_Major_2_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Undergraduate_Major_2_2_1=Undergraduate_Major OR :Undergraduate_Major_2_2_2=Undergraduate_Major_1_2 OR :Undergraduate_Major_2_2_3=Undergraduate_Major_1_3 OR :Undergraduate_Major_2_2_4=Undergraduate_Major_2 OR :Undergraduate_Major_2_2_5=Undergraduate_Major_2_2 OR :Undergraduate_Major_2_2_6=Undergraduate_Major_2_3 OR :Undergraduate_Major_2_2_7=Field OR :Undergraduate_Major_2_2_8=Field_2", Undergraduate_Major_2_2_1 = User_Info[0]["Undergraduate_Major_2_2"], Undergraduate_Major_2_2_2 = User_Info[0]["Undergraduate_Major_2_2"], Undergraduate_Major_2_2_3 = User_Info[0]["Undergraduate_Major_2_2"], Undergraduate_Major_2_2_4 = User_Info[0]["Undergraduate_Major_2_2"], Undergraduate_Major_2_2_5 = User_Info[0]["Undergraduate_Major_2_2"], Undergraduate_Major_2_2_6 = User_Info[0]["Undergraduate_Major_2_2"], Undergraduate_Major_2_2_7 = User_Info[0]["Undergraduate_Major_2_2"], Undergraduate_Major_2_2_8 = User_Info[0]["Undergraduate_Major_2_2"])
    if User_Info[0]["Undergraduate_Major_2_3"] != None:
        Undergraduate_Major_2_3_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Undergraduate_Major_2_3_1=Undergraduate_Major OR :Undergraduate_Major_2_3_2=Undergraduate_Major_1_2 OR :Undergraduate_Major_2_3_3=Undergraduate_Major_1_3 OR :Undergraduate_Major_2_3_4=Undergraduate_Major_2 OR :Undergraduate_Major_2_3_5=Undergraduate_Major_2_2 OR :Undergraduate_Major_2_3_6=Undergraduate_Major_2_3 OR :Undergraduate_Major_2_3_7=Field OR :Undergraduate_Major_2_3_8=Field_2", Undergraduate_Major_2_3_1 = User_Info[0]["Undergraduate_Major_2_3"], Undergraduate_Major_2_3_2 = User_Info[0]["Undergraduate_Major_2_3"], Undergraduate_Major_2_3_3 = User_Info[0]["Undergraduate_Major_2_3"], Undergraduate_Major_2_3_4 = User_Info[0]["Undergraduate_Major_2_3"], Undergraduate_Major_2_3_5 = User_Info[0]["Undergraduate_Major_2_3"], Undergraduate_Major_2_3_6 = User_Info[0]["Undergraduate_Major_2_3"], Undergraduate_Major_2_3_7 = User_Info[0]["Undergraduate_Major_2_3"], Undergraduate_Major_2_3_8 = User_Info[0]["Undergraduate_Major_2_3"])
    if User_Info[0]["Field"] != None:
        Field_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Field_1=Undergraduate_Major OR :Field_2=Undergraduate_Major_1_2 OR :Field_3=Undergraduate_Major_1_3 OR :Field_4=Undergraduate_Major_2 OR :Field_5=Undergraduate_Major_2_2 OR :Field_6=Undergraduate_Major_2_3 OR :Field_7=Field OR :Field_8=Field_2", Field_1 = User_Info[0]["Field"], Field_2 = User_Info[0]["Field"], Field_3 = User_Info[0]["Field"], Field_4 = User_Info[0]["Field"], Field_5 = User_Info[0]["Field"], Field_6 = User_Info[0]["Field"], Field_7 = User_Info[0]["Field"], Field_8 = User_Info[0]["Field"])
    if User_Info[0]["Field_2"] != None:
        Field_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Field_2_1=Undergraduate_Major OR :Field_2_2=Undergraduate_Major_1_2 OR :Field_2_3=Undergraduate_Major_1_3 OR :Field_2_4=Undergraduate_Major_2 OR :Field_2_5=Undergraduate_Major_2_2 OR :Field_2_6=Undergraduate_Major_2_3 OR :Field_2_7=Field OR :Field_2_8=Field_2", Field_2_1 = User_Info[0]["Field_2"], Field_2_2 = User_Info[0]["Field_2"], Field_2_3 = User_Info[0]["Field_2"], Field_2_4 = User_Info[0]["Field_2"], Field_2_5 = User_Info[0]["Field_2"], Field_2_6 = User_Info[0]["Field_2"], Field_2_7 = User_Info[0]["Field_2"], Field_2_8 = User_Info[0]["Field_2"])

    # Match based on postgraduate degrees- to do

    if User_Info[0]["Postgraduate_Degree_1"] != None:
        Postgraduate_Degree_1_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Postgraduate_Degree_1_1=Postgraduate_Degree_1 OR :Postgraduate_Degree_1_2=Postgraduate_Degree_2", Postgraduate_Degree_1_1 = User_Info[0]["Postgraduate_Degree_1"], Postgraduate_Degree_1_2 = User_Info[0]["Postgraduate_Degree_1"])
    if User_Info[0]["Postgraduate_Degree_2"] != None:
        Postgraduate_Degree_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Postgraduate_Degree_2_1=Postgraduate_Degree_1 OR :Postgraduate_Degree_2_2=Postgraduate_Degree_2", Postgraduate_Degree_2_1 = User_Info[0]["Postgraduate_Degree_2"], Postgraduate_Degree_2_2 = User_Info[0]["Postgraduate_Degree_2"])

    # Match based on industry and initial career path interest and industry looking towards

    if User_Info[0]["Current_Industry_1"] != None:
        Current_Industry_1_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Current_Industry_1_1=Current_Industry_1 OR :Current_Industry_1_2=Current_Industry_2 OR :Current_Industry_1_3=Current_Industry_3 OR :Current_Industry_1_4=Initial_Career_Path_Interest_1 OR :Current_Industry_1_5=Initial_Career_Path_Interest_2", Current_Industry_1_1 = User_Info[0]["Current_Industry_1"], Current_Industry_1_2 = User_Info[0]["Current_Industry_1"], Current_Industry_1_3 = User_Info[0]["Current_Industry_1"], Current_Industry_1_4 = User_Info[0]["Current_Industry_1"], Current_Industry_1_5 = User_Info[0]["Current_Industry_1"])
    if User_Info[0]["Current_Industry_2"] != None:
        Current_Industry_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Current_Industry_2_1=Current_Industry_1 OR :Current_Industry_2_2=Current_Industry_2 OR :Current_Industry_2_3=Current_Industry_3 OR :Current_Industry_2_4=Initial_Career_Path_Interest_1 OR :Current_Industry_2_5=Initial_Career_Path_Interest_2", Current_Industry_2_1 = User_Info[0]["Current_Industry_2"], Current_Industry_2_2 = User_Info[0]["Current_Industry_2"], Current_Industry_2_3 = User_Info[0]["Current_Industry_2"], Current_Industry_2_4 = User_Info[0]["Current_Industry_2"], Current_Industry_2_5 = User_Info[0]["Current_Industry_2"])
    if User_Info[0]["Current_Industry_3"] != None:
        Current_Industry_3_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Current_Industry_3_1=Current_Industry_1 OR :Current_Industry_3_2=Current_Industry_2 OR :Current_Industry_3_3=Current_Industry_3 OR :Current_Industry_3_4=Initial_Career_Path_Interest_1 OR :Current_Industry_3_5=Initial_Career_Path_Interest_2", Current_Industry_3_1 = User_Info[0]["Current_Industry_3"], Current_Industry_3_2 = User_Info[0]["Current_Industry_3"], Current_Industry_3_3 = User_Info[0]["Current_Industry_3"], Current_Industry_3_4 = User_Info[0]["Current_Industry_3"], Current_Industry_3_5 = User_Info[0]["Current_Industry_3"])
    if User_Info[0]["Initial_Career_Path_Interest_1"] != None:
        Initial_Career_Path_Interest_1_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Initial_Career_Path_Interest_1_1=Current_Industry_1 OR :Initial_Career_Path_Interest_1_2=Current_Industry_2 OR :Initial_Career_Path_Interest_1_3=Current_Industry_3 OR :Initial_Career_Path_Interest_1_4=Initial_Career_Path_Interest_1 OR :Initial_Career_Path_Interest_1_5=Initial_Career_Path_Interest_2", Initial_Career_Path_Interest_1_1 = User_Info[0]["Initial_Career_Path_Interest_1"], Initial_Career_Path_Interest_1_2 = User_Info[0]["Initial_Career_Path_Interest_1"], Initial_Career_Path_Interest_1_3 = User_Info[0]["Initial_Career_Path_Interest_1"], Initial_Career_Path_Interest_1_4 = User_Info[0]["Initial_Career_Path_Interest_1"], Initial_Career_Path_Interest_1_5 = User_Info[0]["Initial_Career_Path_Interest_1"])
    if User_Info[0]["Initial_Career_Path_Interest_2"] != None:
        Initial_Career_Path_Interest_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Initial_Career_Path_Interest_2_1=Current_Industry_1 OR :Initial_Career_Path_Interest_2_2=Current_Industry_2 OR :Initial_Career_Path_Interest_2_3=Current_Industry_3 OR :Initial_Career_Path_Interest_2_4=Initial_Career_Path_Interest_1 OR :Initial_Career_Path_Interest_2_5=Initial_Career_Path_Interest_2", Initial_Career_Path_Interest_2_1 = User_Info[0]["Initial_Career_Path_Interest_2"], Initial_Career_Path_Interest_2_2 = User_Info[0]["Initial_Career_Path_Interest_2"], Initial_Career_Path_Interest_2_3 = User_Info[0]["Initial_Career_Path_Interest_2"], Initial_Career_Path_Interest_2_4 = User_Info[0]["Initial_Career_Path_Interest_2"], Initial_Career_Path_Interest_2_5 = User_Info[0]["Initial_Career_Path_Interest_2"])
    if User_Info[0]["Industry_Looking_Towards"] != None:
        Industry_Looking_Towards_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Industry_Looking_Towards_1=Current_Industry_1 OR :Industry_Looking_Towards_2=Current_Industry_2 OR :Industry_Looking_Towards_3=Current_Industry_3 OR :Industry_Looking_Towards_4=Initial_Career_Path_Interest_1 OR :Industry_Looking_Towards_5=Initial_Career_Path_Interest_2", Industry_Looking_Towards_1 = User_Info[0]["Industry_Looking_Towards"], Industry_Looking_Towards_2 = User_Info[0]["Industry_Looking_Towards"], Industry_Looking_Towards_3 = User_Info[0]["Industry_Looking_Towards"], Industry_Looking_Towards_4 = User_Info[0]["Industry_Looking_Towards"], Industry_Looking_Towards_5 = User_Info[0]["Industry_Looking_Towards"])

    # Match based on birth year

    if User_Info[0]["Born"] != None:
        Born_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Born=Born", Born=User_Info[0]["Born"])

    # Maybe do if statements and if length of rows is 1 or more, then add that category name to an array, and then go through array, and pass through the parameters for the page?
    # Create list with person corresponding to number of matches, variable names that have matches in for each person (profile)
    # Create similarities array with categories of matches
    Similarities_Array = []
    Num_Match = 0

    if User_Info[0]["Current_Company"] != None:
        if len(Current_Company_Match_Rows) > 0:
            Similarities_Array.append("Current_Company")
            Num_Match += 1
        else:
            Current_Company_Match_Rows = None
    if User_Info[0]["Second_Company"] != None:
        if len(Second_Company_Match_Rows) > 0:
            Similarities_Array.append("Second_Company")
            Num_Match += 1
        else:
            Second_Company_Match_Rows = None
    if User_Info[0]["Third_Company"] != None:
        if len(Third_Company_Match_Rows) > 0:
            Similarities_Array.append("Third_Company")
            Num_Match += 1
        else:
            Third_Company_Match_Rows = None
    if User_Info[0]["Post_College_Company"] != None:
        if len(Post_College_Company_Match_Rows) > 0:
            Similarities_Array.append("Post_College_Company")
            Num_Match += 1
        else:
            Post_College_Company_Match_Rows = None
    if User_Info[0]["Past_Company_1"] != None:
        if len(Past_Company_1_Match_Rows) > 0:
            Similarities_Array.append("Past_Company_1")
            Num_Match += 1
        else:
            Past_Company_1_Match_Rows = None
    if User_Info[0]["Past_Company_2"] != None:
        if len(Past_Company_2_Match_Rows) > 0:
            Similarities_Array.append("Past_Company_2")
            Num_Match += 1
        else:
            Past_Company_2_Match_Rows = None
    if User_Info[0]["Past_Company_3"] != None:
        if len(Past_Company_3_Match_Rows) > 0:
            Similarities_Array.append("Past_Company_3")
            Num_Match += 1
        else:
            Past_Company_3_Match_Rows = None
    if User_Info[0]["Past_Company_4"] != None:
        if len(Past_Company_4_Match_Rows) > 0:
            Similarities_Array.append("Past_Company_4")
            Num_Match += 1
        else:
            Past_Company_4_Match_Rows = None
    if User_Info[0]["Dream_Company"] != None:
        if len(Dream_Company_Match_Rows) > 0:
            Similarities_Array.append("Dream_Company")
            Num_Match += 1
        else:
            Dream_Company_Match_Rows = None
    if User_Info[0]["Current_Title_1"] != None:
        if len(Current_Title_1_Match_Rows) > 0:
            Similarities_Array.append("Current_Title_1")
            Num_Match += 1
        else:
            Current_Title_1_Match_Rows = None
    if User_Info[0]["Alternate_Title_1"] != None:
        if len(Alternate_Title_1_Match_Rows) > 0:
            Similarities_Array.append("Alternate_Title_1")
            Num_Match += 1
        else:
            Alternate_Title_1_Match_Rows = None
    if User_Info[0]["Current_Title_2"] != None:
        if len(Current_Title_2_Match_Rows) > 0:
            Similarities_Array.append("Current_Title_2")
            Num_Match += 1
        else:
            Current_Title_2_Match_Rows = None
    if User_Info[0]["Alternate_Title_2"] != None:
        if len(Alternate_Title_2_Match_Rows) > 0:
            Similarities_Array.append("Alternate_Title_2")
            Num_Match += 1
        else:
            Alternate_Title_2_Match_Rows = None
    if User_Info[0]["Current_Title_3"] != None:
        if len(Current_Title_3_Match_Rows) > 0:
            Similarities_Array.append("Current_Title_3")
            Num_Match += 1
        else:
            Current_Title_3_Match_Rows = None
    if User_Info[0]["Alternate_Title_3"] != None:
        if len(Alternate_Title_3_Match_Rows) > 0:
            Similarities_Array.append("Alternate_Title_3")
            Num_Match += 1
        else:
            Alternate_Title_3_Match_Rows = None
    if User_Info[0]["Post_College_Job"] != None:
        if len(Post_College_Job_Match_Rows) > 0:
            Similarities_Array.append("Post_College_Job")
            Num_Match += 1
        else:
            Post_College_Job_Match_Rows = None
    if User_Info[0]["Past_Position_1"] != None:
        if len(Past_Position_1_Match_Rows) > 0:
            Similarities_Array.append("Past_Position_1")
            Num_Match += 1
        else:
            Past_Position_1_Match_Rows = None
    if User_Info[0]["Alternate_Past_Position_1"] != None:
        if len(Alternate_Past_Position_1_Match_Rows) > 0:
            Similarities_Array.append("Alternate_Past_Position_1")
            Num_Match += 1
        else:
            Alternate_Past_Position_1_Match_Rows = None
    if User_Info[0]["Past_Position_2"] != None:
        if len(Past_Position_2_Match_Rows) > 0:
            Similarities_Array.append("Past_Position_2")
            Num_Match += 1
        else:
            Past_Position_2_Match_Rows = None
    if User_Info[0]["Alternate_Past_Position_2"] != None:
        if len(Alternate_Past_Position_2_Match_Rows) > 0:
            Similarities_Array.append("Alternate_Past_Position_2")
            Num_Match += 1
        else:
            Alternate_Past_Position_2_Match_Rows = None
    if User_Info[0]["Past_Position_3"] != None:
        if len(Past_Position_3_Match_Rows) > 0:
            Similarities_Array.append("Past_Position_3")
            Num_Match += 1
        else:
            Past_Position_3_Match_Rows = None
    if User_Info[0]["Alternate_Past_Position_3"] != None:
        if len(Alternate_Past_Position_3_Match_Rows) > 0:
            Similarities_Array.append("Alternate_Past_Position_3")
            Num_Match += 1
        else:
            Alternate_Past_Position_3_Match_Rows = None
    if User_Info[0]["Past_Position_4"] != None:
        if len(Past_Position_4_Match_Rows) > 0:
            Similarities_Array.append("Past_Position_4")
            Num_Match += 1
        else:
            Past_Position_4_Match_Rows = None
    if User_Info[0]["Alternate_Past_Position_4"] != None:
        if len(Alternate_Past_Position_4_Match_Rows) > 0:
            Similarities_Array.append("Alternate_Past_Position_4")
            Num_Match += 1
        else:
            Alternate_Past_Postion_4_Match_Rows = None
    if User_Info[0]["Career_Position_Looking_For"] != None:
        if len(Career_Position_Looking_For_Match_Rows) > 0:
            Similarities_Array.append("Career_Position_Looking_For")
            Num_Match += 1
        else:
            Career_Position_Looking_For_Match_Rows = None
    if User_Info[0]["Prep_School"] != None:
        if len(Prep_School_Match_Rows) > 0:
            Similarities_Array.append("Prep_School")
            Num_Match += 1
        else:
            Prep_School_Match_Rows = None
    if User_Info[0]["Undergraduate_School"] != None:
        if len(Undergraduate_School_Match_Rows) > 0:
            Similarities_Array.append("Undergraduate_School")
            Num_Match += 1
        else:
            Undergraduate_School_Match_Rows = None
    if User_Info[0]["Undergraduate_School_2"] != None:
        if len(Undergraduate_School_2_Match_Rows) > 0:
            Similarities_Array.append("Undergraduate_School_2")
            Num_Match += 1
        else:
            Undergraduate_School_2_Match_Rows = None
    if User_Info[0]["Postgraduate_School"] != None:
        if len(Postgraduate_School_Match_Rows) > 0:
            Similarities_Array.append("Postgraduate_School")
            Num_Match += 1
        else:
            Postgraduate_School_Match_Rows = None
    if User_Info[0]["Postgraduate_School_2"] != None:
        if len(Postgraduate_School_2_Match_Rows) > 0:
            Similarities_Array.append("Postgraduate_School_2")
            Num_Match += 1
        else:
            Postgraduate_School_2_Match_Rows = None
    if User_Info[0]["Undergraduate_Graduation_Year_2"] != None:
        Undergraduate_Graduation_Year_Match_Rows = None
        if len(Undergraduate_Graduation_Year_2_Match_Rows) > 0:
            Similarities_Array.append("Undergraduate_Graduation_Year_2")
            Num_Match += 1
        else:
            Undergraduate_Graduation_Year_2_Match_Rows = None
    elif User_Info[0]["Undergraduate_Graduation_Year"] != None:
        if len(Undergraduate_Graduation_Year_Match_Rows) > 0:
            Similarities_Array.append("Undergraduate_Graduation_Year")
            Num_Match += 1
        else:
            Undergraduate_Graduation_Year_Match_Rows = None
    if User_Info[0]["Postgraduate_Graduation_Year"] != None:
        if len(Postgraduate_Graduation_Year_Match_Rows) > 0:
            Similarities_Array.append("Postgraduate_Graduation_Year")
            Num_Match += 1
        else:
            Postgraduate_Graduation_Year_Match_Rows = None
    if User_Info[0]["Postgraduate_Graduation_Year_2"] != None:
        if len(Postgraduate_Graduation_Year_2_Match_Rows) > 0:
            Similarities_Array.append("Postgraduate_Graduation_Year_2")
            Num_Match += 1
        else:
            Postgraduate_Graduation_Year_2_Match_Rows = None
    if User_Info[0]["Undergraduate_Major"] != None:
        if len(Undergraduate_Major_Match_Rows) > 0:
            Similarities_Array.append("Undergraduate_Major")
            Num_Match += 1
        else:
            Undergraduate_Major_Match_Rows = None
    if User_Info[0]["Undergraduate_Major_1_2"] != None:
        if len(Undergraduate_Major_1_2_Match_Rows) > 0:
            Similarities_Array.append("Undergraduate_Major_1_2")
            Num_Match += 1
        else:
            Undergraduate_Major_1_2_Match_Rows = None
    if User_Info[0]["Undergraduate_Major_1_3"] != None:
        if len(Undergraduate_Major_1_3_Match_Rows) > 0:
            Similarities_Array.append("Undergraduate_Major_1_3")
            Num_Match += 1
        else:
            Undergraduate_Major_1_3_Match_Rows = None
    if User_Info[0]["Undergraduate_Major_2"] != None:
        if len(Undergraduate_Major_2_Match_Rows) > 0:
            Similarities_Array.append("Undergraduate_Major_2")
            Num_Match += 1
        else:
            Undergraduate_Major_2_Match_Rows = None
    if User_Info[0]["Undergraduate_Major_2_2"] != None:
        if len(Undergraduate_Major_2_2_Match_Rows) > 0:
            Similarities_Array.append("Undergraduate_Major_2_2")
            Num_Match += 1
        else:
            Undergraduate_Major_2_2_Match_Rows = None
    if User_Info[0]["Undergraduate_Major_2_3"] != None:
        if len(Undergraduate_Major_2_3_Match_Rows) > 0:
            Similarities_Array.append("Undergraduate_Major_2_3")
            Num_Match += 1
        else:
            Undergraduate_Major_2_3_Match_Rows = None
    if User_Info[0]["Field"] != None:
        if len(Field_Match_Rows) > 0:
            Similarities_Array.append("Field")
            Num_Match += 1
        else:
            Field_Match_Rows = None
    if User_Info[0]["Field_2"] != None:
        if len(Field_2_Match_Rows) > 0:
            Similarities_Array.append("Field_2")
            Num_Match += 1
        else:
            Field_2_Match_Rows = None
    if User_Info[0]["Current_Industry_1"] != None:
        if len(Current_Industry_1_Match_Rows) > 0:
            Similarities_Array.append("Current_Industry_1")
            Num_Match += 1
        else:
            Current_Industry_1_Match_Rows = None
    if User_Info[0]["Current_Industry_2"] != None:
        if len(Current_Industry_2_Match_Rows) > 0:
            Similarities_Array.append("Current_Industry_2")
            Num_Match += 1
        else:
            Current_Industry_2_Match_Rows = None
    if User_Info[0]["Current_Industry_3"] != None:
        if len(Current_Industry_3_Match_Rows) > 0:
            Similarities_Array.append("Current_Industry_3")
            Num_Match += 1
        else:
            Current_Industry_3_Match_Rows = None
    if User_Info[0]["Initial_Career_Path_Interest_1"] != None:
        if len(Initial_Career_Path_Interest_1_Match_Rows) > 0:
            Similarities_Array.append("Initial_Career_Path_Interest_1")
            Num_Match += 1
        else:
            Initial_Career_Path_Interest_1_Match_Rows = None
    if User_Info[0]["Initial_Career_Path_Interest_2"] != None:
        if len(Initial_Career_Path_Interest_2_Match_Rows) > 0:
            Similarities_Array.append("Initial_Career_Path_Interest_2")
            Num_Match += 1
        else:
            Initial_Career_Path_Interest_2_Match_Rows = None
    if User_Info[0]["Industry_Looking_Towards"] != None:
        if len(Industry_Looking_Towards_Match_Rows) > 0:
            Similarities_Array.append("Industry_Looking_Towards")
            Num_Match += 1
        else:
            Industry_Looking_Towards_Match_Rows = None
    if User_Info[0]["Born"] != None:
        if len(Born_Match_Rows) > 0:
            Similarities_Array.append("Born")
            Num_Match += 1
        else:
            Born_Match_Rows = None

    # if number of matches is 0, return apology
    if Num_Match == 0:
        return apology("Surprisingly, we couldn't find any matches. Looks like you are a trailblazer!")
    else:
        return render_template("similarities.html", User_Info=User_Info, Current_Company_Match_Rows=Current_Company_Match_Rows, Second_Company_Match_Rows=Second_Company_Match_Rows, Third_Company_Match_Rows=Third_Company_Match_Rows, Post_College_Job_Match_Rows=Post_College_Job_Match_Rows, Past_Company_1_Match_Rows=Past_Company_1_Match_Rows, Past_Company_2_Match_Rows=Past_Company_2_Match_Rows, Past_Company_3_Match_Rows=Past_Company_3_Match_Rows, Past_Company_4_Match_Rows=Past_Company_4_Match_Rows, Dream_Company_Match_Rows=Dream_Company_Match_Rows, Current_Title_1_Match_Rows=Current_Title_1_Match_Rows, Alternate_Title_1_Match_Rows=Alternate_Title_1_Match_Rows, Current_Title_2_Match_Rows=Current_Title_2_Match_Rows, Alternate_Title_2_Match_Rows=Alternate_Title_2_Match_Rows, Current_Title_3_Match_Rows=Current_Title_3_Match_Rows, Alternate_Title_3_Match_Rows=Alternate_Title_3_Match_Rows, Past_Position_1_Match_Rows=Past_Position_1_Match_Rows, Alternate_Past_Position_1_Match_Rows=Alternate_Past_Position_1_Match_Rows, Past_Position_2_Match_Rows=Past_Position_2_Match_Rows, Alternate_Past_Position_2_Match_Rows=Alternate_Past_Position_2_Match_Rows, Past_Position_3_Match_Rows=Past_Position_3_Match_Rows, Alternate_Past_Position_3_Match_Rows=Alternate_Past_Position_3_Match_Rows, Past_Position_4_Match_Rows=Past_Position_4_Match_Rows, Alternate_Past_Position_4_Match_Rows=Alternate_Past_Position_4_Match_Rows, Career_Position_Looking_For_Match_Rows=Career_Position_Looking_For_Match_Rows, Prep_School_Match_Rows=Prep_School_Match_Rows, Undergraduate_School_Match_Rows=Undergraduate_School_Match_Rows, Undergraduate_School_2_Match_Rows=Undergraduate_School_2_Match_Rows, Postgraduate_School_Match_Rows=Postgraduate_School_Match_Rows, Postgraduate_School_2_Match_Rows=Postgraduate_School_2_Match_Rows, Undergraduate_Graduation_Year_Match_Rows=Undergraduate_Graduation_Year_Match_Rows, Undergraduate_Graduation_Year_2_Match_Rows=Undergraduate_Graduation_Year_2_Match_Rows, Postgraduate_Graduation_Year_Match_Rows=Postgraduate_Graduation_Year_Match_Rows, Postgraduate_Graduation_Year_2_Match_Rows=Postgraduate_Graduation_Year_2_Match_Rows, Undergraduate_Major_Match_Rows=Undergraduate_Major_Match_Rows, Undergraduate_Major_1_2_Match_Rows=Undergraduate_Major_1_2_Match_Rows, Undergraduate_Major_1_3_Match_Rows=Undergraduate_Major_1_3_Match_Rows, Undergraduate_Major_2_Match_Rows=Undergraduate_Major_2_Match_Rows, Undergraduate_Major_2_2_Match_Rows=Undergraduate_Major_2_2_Match_Rows, Undergraduate_Major_2_3_Match_Rows=Undergraduate_Major_2_3_Match_Rows, Field_Match_Rows=Field_Match_Rows, Field_2_Match_Rows=Field_2_Match_Rows, Current_Industry_1_Match_Rows=Current_Industry_1_Match_Rows, Current_Industry_2_Match_Rows=Current_Industry_2_Match_Rows, Current_Industry_3_Match_Rows=Current_Industry_3_Match_Rows, Initial_Career_Path_Interest_1_Match_Rows=Initial_Career_Path_Interest_1_Match_Rows, Initial_Career_Path_Interest_2_Match_Rows=Initial_Career_Path_Interest_2_Match_Rows, Industry_Looking_Towards_Match_Rows=Industry_Looking_Towards_Match_Rows, Born_Match_Rows=Born_Match_Rows)



@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Brings up list of people to click from to view profile"""

    # if user reached route via GET (as by clicking a link)
    if request.method == "GET":
        return render_template("search.html")

    # if user reached route via POST (as by submitting a form via POST)
    else:
        # Reject search if name contains characters other than letters and apostrophe
        for char in request.form.get("Name"):
            if char.isalpha() == False and char != "\'" and char != " ":
                return apology("Invalid search- Try a different spelling")

        # Convert name to only capitalize letters at beginning of each word
        Lower_Name = request.form.get("Name").lower()
        # Source: http://stackoverflow.com/questions/1549641/how-to-capitalize-the-first-letter-of-each-word-in-a-string-python
        Capital_Name = " ".join(word[0].upper() + word[1:] for word in Lower_Name.split())

        # Query database for name
        try:
            Searched_Rows = db.execute("SELECT Template_Name FROM Profiles WHERE Full_Name = :Name", Name= Capital_Name)

        except:
            Searched_Rows = None

        # Calculate number of rows selected
        Num_Searched_Rows = len(Searched_Rows)


        # Return profile(s) or apology
        if len(Searched_Rows) == 1:
            # Return profile of person if only one match
            return render_template(Searched_Rows[0]["Template_Name"] + ".html")
        elif Num_Searched_Rows > 1:
            # Return list of people to choose from- to be implemented later- can maybe present choices of companies work at or just pictures with names that can click on

            # return render_template("searched.html", Searched_Rows = Searched_Rows)
            # for now, give apology
            return apology("Multiple matches found")
        else:
            return apology("No profiles found for " + Capital_Name)

@app.route("/searched")
@login_required
def searched():
    """ Presents user a list of profiles from which they can choose """
    # Implement this feature later after have initial prototype with just one search result

@app.route("/profile")
@login_required
def profile():
    """ Presents user their profile with information they inputted """
    # Get user information from Users database
    User_Rows = db.execute("SELECT * FROM Users WHERE ID = :ID", ID = session["user_id"])

    # Display information by rerouting to profile page
    return render_template("profile.html", Full_Name=User_Rows[0]["Full_Name"], Current_Company=User_Rows[0]["Current_Company"], Second_Company=User_Rows[0]["Second_Company"], Third_Company=User_Rows[0]["Third_Company"], Current_Title_1=User_Rows[0]["Current_Title_1"], Alternate_Title_1=User_Rows[0]["Alternate_Title_1"], Current_Title_2=User_Rows[0]["Current_Title_2"], Alternate_Title_2=User_Rows[0]["Alternate_Title_2"], Current_Title_3=User_Rows[0]["Current_Title_3"], Alternate_Title_3=User_Rows[0]["Alternate_Title_3"], Current_Industry_1=User_Rows[0]["Current_Industry_1"], Current_Industry_2=User_Rows[0]["Current_Industry_2"], Current_Industry_3=User_Rows[0]["Current_Industry_3"], Year_Start_1=User_Rows[0]["Year_Start_1"], Year_Start_2=User_Rows[0]["Year_Start_2"], Year_Start_3=User_Rows[0]["Year_Start_3"], Born=User_Rows[0]["Born"], Undergraduate_School=User_Rows[0]["Undergraduate_School"], Undergraduate_Major=User_Rows[0]["Undergraduate_Major"], Undergraduate_Major_1_2=User_Rows[0]["Undergraduate_Major_1_2"], Undergraduate_Major_1_3=User_Rows[0]["Undergraduate_Major_1_3"], Undergraduate_Graduation_Year=User_Rows[0]["Undergraduate_Graduation_Year"], Undergraduate_School_2=User_Rows[0]["Undergraduate_School_2"], Undergraduate_Major_2=User_Rows[0]["Undergraduate_Major_2"], Undergraduate_Major_2_2=User_Rows[0]["Undergraduate_Major_2_2"], Undergraduate_Major_2_3=User_Rows[0]["Undergraduate_Major_2_3"], Undergraduate_Graduation_Year_2=User_Rows[0]["Undergraduate_Graduation_Year_2"], Prep_School=User_Rows[0]["Prep_School"], Postgraduate_School=User_Rows[0]["Postgraduate_School"], Postgraduate_Degree_1=User_Rows[0]["Postgraduate_Degree_1"], Field=User_Rows[0]["Field"], Postgraduate_Graduation_Year=User_Rows[0]["Postgraduate_Graduation_Year"], Postgraduate_School_2=User_Rows[0]["Postgraduate_School_2"], Postgraduate_Degree_2=User_Rows[0]["Postgraduate_Degree_2"], Field_2=User_Rows[0]["Field_2"], Postgraduate_Graduation_Year_2=User_Rows[0]["Postgraduate_Graduation_Year_2"], Initial_Career_Path_Interest_1=User_Rows[0]["Initial_Career_Path_Interest_1"], Initial_Career_Path_Interest_2=User_Rows[0]["Initial_Career_Path_Interest_2"], Post_College_Job=User_Rows[0]["Post_College_Job"], Post_College_Company=User_Rows[0]["Post_College_Company"], Post_College_Year_Start=User_Rows[0]["Post_College_Year_Start"], Post_College_Year_End=User_Rows[0]["Post_College_Year_End"], Past_Company_1=User_Rows[0]["Past_Company_1"], Past_Position_1=User_Rows[0]["Past_Position_1"], Alternate_Past_Position_1=User_Rows[0]["Alternate_Past_Position_1"], Past_Company_2=User_Rows[0]["Past_Company_2"], Past_Position_2=User_Rows[0]["Past_Position_2"], Alternate_Past_Position_2=User_Rows[0]["Alternate_Past_Position_2"], Past_Company_3=User_Rows[0]["Past_Company_3"], Past_Position_3=User_Rows[0]["Past_Position_3"], Alternate_Past_Position_3=User_Rows[0]["Alternate_Past_Position_3"], Past_Company_4=User_Rows[0]["Past_Company_4"], Past_Position_4=User_Rows[0]["Past_Position_4"], Alternate_Past_Position_4=User_Rows[0]["Alternate_Past_Position_4"], Past_Year_Start_1=User_Rows[0]["Past_Year_Start_1"], Past_Year_End_1=User_Rows[0]["Past_Year_End_1"], Past_Year_Start_2=User_Rows[0]["Past_Year_Start_2"], Past_Year_End_2=User_Rows[0]["Past_Year_End_2"], Past_Year_Start_3=User_Rows[0]["Past_Year_Start_3"], Past_Year_End_3=User_Rows[0]["Past_Year_End_3"], Past_Year_Start_4=User_Rows[0]["Past_Year_Start_4"], Past_Year_End_4=User_Rows[0]["Past_Year_End_4"], Career_Position_Looking_For=User_Rows[0]["Career_Position_Looking_For"], Industry_Looking_Towards=User_Rows[0]["Industry_Looking_Towards"], Dream_Company=User_Rows[0]["Dream_Company"], Miscellaneous=User_Rows[0]["Miscellaneous"])

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

