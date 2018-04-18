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
    if user_info[0]["alternate_past_position_3"] != None:
        alternate_past_position_3_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :alternate_past_position_3_1=current_title_1 OR :alternate_past_position_3_2=alternate_title_1 OR :alternate_past_position_3_3=alternate_title_1_2 OR :alternate_past_position_3_4=current_title_2 OR :alternate_past_position_3_5=alternate_title_2 OR :alternate_past_position_3_6=alternate_title_2_2 OR :alternate_past_position_3_7=current_title_3 OR :alternate_past_position_3_8=alternate_title_3 OR :alternate_past_position_3_9=alternate_title_3_2 OR :alternate_past_position_3_10=post_college_job OR :alternate_past_position_3_11=past_position_1 OR :alternate_past_position_3_12=alternate_past_position_1 OR :alternate_past_position_3_13=alternate_past_position_1_2 OR :alternate_past_position_3_14=past_position_2 OR :alternate_past_position_3_15=alternate_past_position_2 OR :alternate_past_position_3_16=alternate_past_position_2_2 OR :alternate_past_position_3_17=past_position_3 OR :alternate_past_position_3_18=alternate_past_position_3 OR :alternate_past_position_3_19=alternate_past_position_3_2 OR :alternate_past_position_3_20=past_position_4 OR :alternate_past_position_3_21=alternate_past_position_4 OR :alternate_past_position_3_22=alternate_past_position_4_2", alternate_past_position_3_1=user_info[0]["alternate_past_position_3"], alternate_past_position_3_2=user_info[0]["alternate_past_position_3"], alternate_past_position_3_3=user_info[0]["alternate_past_position_3"], alternate_past_position_3_4=user_info[0]["alternate_past_position_3"], alternate_past_position_3_5=user_info[0]["alternate_past_position_3"], alternate_past_position_3_6=user_info[0]["alternate_past_position_3"], alternate_past_position_3_7=user_info[0]["alternate_past_position_3"], alternate_past_position_3_8=user_info[0]["alternate_past_position_3"], alternate_past_position_3_9=user_info[0]["alternate_past_position_3"], alternate_past_position_3_10=user_info[0]["alternate_past_position_3"], alternate_past_position_3_11=user_info[0]["alternate_past_position_3"], alternate_past_position_3_12=user_info[0]["alternate_past_position_3"], alternate_past_position_3_13=user_info[0]["alternate_past_position_3"], alternate_past_position_3_14=user_info[0]["alternate_past_position_3"], alternate_past_position_3_15=user_info[0]["alternate_past_position_3"], alternate_past_position_3_16=user_info[0]["alternate_past_position_3"], alternate_past_position_3_17=user_info[0]["alternate_past_position_3"], alternate_past_position_3_18=user_info[0]["alternate_past_position_3"], alternate_past_position_3_19=user_info[0]["alternate_past_position_3"], alternate_past_position_3_20=user_info[0]["alternate_past_position_3"], alternate_past_position_3_21=user_info[0]["alternate_past_position_3"], alternate_past_position_3_22=user_info[0]["alternate_past_position_3"])
    if user_info[0]["past_position_4"] != None:
        past_position_4_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :past_position_4_1=current_title_1 OR :past_position_4_2=alternate_title_1 OR :past_position_4_3=alternate_title_1_2 OR :past_position_4_4=current_title_2 OR :past_position_4_5=alternate_title_2 OR :past_position_4_6=alternate_title_2_2 OR :past_position_4_7=current_title_3 OR :past_position_4_8=alternate_title_3 OR :past_position_4_9=alternate_title_3_2 OR :past_position_4_10=post_college_job OR :past_position_4_11=past_position_1 OR :past_position_4_12=alternate_past_position_1 OR :past_position_4_13=alternate_past_position_1_2 OR :past_position_4_14=past_position_2 OR :past_position_4_15=alternate_past_position_2 OR :past_position_4_16=alternate_past_position_2_2 OR :past_position_4_17=past_position_3 OR :past_position_4_18=alternate_past_position_3 OR :past_position_4_19=alternate_past_position_3_2 OR :past_position_4_20=past_position_4 OR :past_position_4_21=alternate_past_position_4 OR :past_position_4_22=alternate_past_position_4_2", past_position_4_1=user_info[0]["past_position_4"], past_position_4_2=user_info[0]["past_position_4"], past_position_4_3=user_info[0]["past_position_4"], past_position_4_4=user_info[0]["past_position_4"], past_position_4_5=user_info[0]["past_position_4"], past_position_4_6=user_info[0]["past_position_4"], past_position_4_7=user_info[0]["past_position_4"], past_position_4_8=user_info[0]["past_position_4"], past_position_4_9=user_info[0]["past_position_4"], past_position_4_10=user_info[0]["past_position_4"], past_position_4_11=user_info[0]["past_position_4"], past_position_4_12=user_info[0]["past_position_4"], past_position_4_13=user_info[0]["past_position_4"], past_position_4_14=user_info[0]["past_position_4"], past_position_4_15=user_info[0]["past_position_4"], past_position_4_16=user_info[0]["past_position_4"], past_position_4_17=user_info[0]["past_position_4"], past_position_4_18=user_info[0]["past_position_4"], past_position_4_19=user_info[0]["past_position_4"], past_position_4_20=user_info[0]["past_position_4"], past_position_4_21=user_info[0]["past_position_4"], past_position_4_22=user_info[0]["past_position_4"])
    if user_info[0]["alternate_past_position_4"] != None:
        alternate_past_position_4_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :alternate_past_position_4_1=current_title_1 OR :alternate_past_position_4_2=alternate_title_1 OR :alternate_past_position_4_3=alternate_title_1_2 OR :alternate_past_position_4_4=current_title_2 OR :alternate_past_position_4_5=alternate_title_2 OR :alternate_past_position_4_6=alternate_title_2_2 OR :alternate_past_position_4_7=current_title_3 OR :alternate_past_position_4_8=alternate_title_3 OR :alternate_past_position_4_9=alternate_title_3_2 OR :alternate_past_position_4_10=post_college_job OR :alternate_past_position_4_11=past_position_1 OR :alternate_past_position_4_12=alternate_past_position_1 OR :alternate_past_position_4_13=alternate_past_position_1_2 OR :alternate_past_position_4_14=past_position_2 OR :alternate_past_position_4_15=alternate_past_position_2 OR :alternate_past_position_4_16=alternate_past_position_2_2 OR :alternate_past_position_4_17=past_position_3 OR :alternate_past_position_4_18=alternate_past_position_3 OR :alternate_past_position_4_19=alternate_past_position_3_2 OR :alternate_past_position_4_20=past_position_4 OR :alternate_past_position_4_21=alternate_past_position_4 OR :alternate_past_position_4_22=alternate_past_position_4_2", alternate_past_position_4_1=user_info[0]["alternate_past_position_4"], alternate_past_position_4_2=user_info[0]["alternate_past_position_4"], alternate_past_position_4_3=user_info[0]["alternate_past_position_4"], alternate_past_position_4_4=user_info[0]["alternate_past_position_4"], alternate_past_position_4_5=user_info[0]["alternate_past_position_4"], alternate_past_position_4_6=user_info[0]["alternate_past_position_4"], alternate_past_position_4_7=user_info[0]["alternate_past_position_4"], alternate_past_position_4_8=user_info[0]["alternate_past_position_4"], alternate_past_position_4_9=user_info[0]["alternate_past_position_4"], alternate_past_position_4_10=user_info[0]["alternate_past_position_4"], alternate_past_position_4_11=user_info[0]["alternate_past_position_4"], alternate_past_position_4_12=user_info[0]["alternate_past_position_4"], alternate_past_position_4_13=user_info[0]["alternate_past_position_4"], alternate_past_position_4_14=user_info[0]["alternate_past_position_4"], alternate_past_position_4_15=user_info[0]["alternate_past_position_4"], alternate_past_position_4_16=user_info[0]["alternate_past_position_4"], alternate_past_position_4_17=user_info[0]["alternate_past_position_4"], alternate_past_position_4_18=user_info[0]["alternate_past_position_4"], alternate_past_position_4_19=user_info[0]["alternate_past_position_4"], alternate_past_position_4_20=user_info[0]["alternate_past_position_4"], alternate_past_position_4_21=user_info[0]["alternate_past_position_4"], alternate_past_position_4_22=user_info[0]["alternate_past_position_4"])
    if user_info[0]["career_position_looking_for"] != None:
        career_position_looking_for_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :career_position_looking_for_1=current_title_1 OR :career_position_looking_for_2=alternate_title_1 OR :career_position_looking_for_3=alternate_title_1_2 OR :career_position_looking_for_4=current_title_2 OR :career_position_looking_for_5=alternate_title_2 OR :career_position_looking_for_6=alternate_title_2_2 OR :career_position_looking_for_7=current_title_3 OR :career_position_looking_for_8=alternate_title_3 OR :career_position_looking_for_9=alternate_title_3_2 OR :career_position_looking_for_10=post_college_job OR :career_position_looking_for_11=past_position_1 OR :career_position_looking_for_12=alternate_past_position_1 OR :career_position_looking_for_13=alternate_past_position_1_2 OR :career_position_looking_for_14=past_position_2 OR :career_position_looking_for_15=alternate_past_position_2 OR :career_position_looking_for_16=alternate_past_position_2_2 OR :career_position_looking_for_17=past_position_3 OR :career_position_looking_for_18=alternate_past_position_3 OR :career_position_looking_for_19=alternate_past_position_3_2 OR :career_position_looking_for_20=past_position_4 OR :career_position_looking_for_21=alternate_past_position_4 OR :career_position_looking_for_22=alternate_past_position_4_2", career_position_looking_for_1=user_info[0]["career_position_looking_for"], career_position_looking_for_2=user_info[0]["career_position_looking_for"], career_position_looking_for_3=user_info[0]["career_position_looking_for"], career_position_looking_for_4=user_info[0]["career_position_looking_for"], career_position_looking_for_5=user_info[0]["career_position_looking_for"], career_position_looking_for_6=user_info[0]["career_position_looking_for"], career_position_looking_for_7=user_info[0]["career_position_looking_for"], career_position_looking_for_8=user_info[0]["career_position_looking_for"], career_position_looking_for_9=user_info[0]["career_position_looking_for"], career_position_looking_for_10=user_info[0]["career_position_looking_for"], career_position_looking_for_11=user_info[0]["career_position_looking_for"], career_position_looking_for_12=user_info[0]["career_position_looking_for"], career_position_looking_for_13=user_info[0]["career_position_looking_for"], career_position_looking_for_14=user_info[0]["career_position_looking_for"], career_position_looking_for_15=user_info[0]["career_position_looking_for"], career_position_looking_for_16=user_info[0]["career_position_looking_for"], career_position_looking_for_17=user_info[0]["career_position_looking_for"], career_position_looking_for_18=user_info[0]["career_position_looking_for"], career_position_looking_for_19=user_info[0]["career_position_looking_for"], career_position_looking_for_20=user_info[0]["career_position_looking_for"], career_position_looking_for_21=user_info[0]["career_position_looking_for"], career_position_looking_for_22=user_info[0]["career_position_looking_for"])

    # Match based on schools: prep, undergrad, and grad

    if user_info[0]["prep_school"] != None:
        prep_school_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :prep_school_1=prep_school", prep_school_1 = user_info[0]["prep_school"])
    if user_info[0]["undergraduate_school"] != None:
        undergraduate_school_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :undergraduate_school_1=undergraduate_school OR :undergraduate_school_2=undergraduate_school_2", undergraduate_school_1 = user_info[0]["undergraduate_school"], undergraduate_school_2 = user_info[0]["undergraduate_school"])
    if user_info[0]["undergraduate_school_2"] != None:
        undergraduate_school_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :undergraduate_school_2_1=undergraduate_school OR :undergraduate_school_2_2=undergraduate_school_2", undergraduate_school_2_1 = user_info[0]["undergraduate_school_2"], undergraduate_school_2_2 = user_info[0]["undergraduate_school_2"])
    if user_info[0]["postgraduate_school"] != None:
        postgraduate_school_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :postgraduate_school_1=postgraduate_school OR :postgraduate_school_2=postgraduate_school_2", postgraduate_school_1 = user_info[0]["postgraduate_school"], postgraduate_school_2 = user_info[0]["postgraduate_school"])
    if user_info[0]["postgraduate_school_2"]  != None:
        postgraduate_school_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :postgraduate_school_2_1=postgraduate_school OR :postgraduate_school_2_2=postgraduate_school_2", postgraduate_school_2_1 = user_info[0]["postgraduate_school_2"], postgraduate_school_2_2 = user_info[0]["postgraduate_school_2"])

    # Match based on graduation year of undergrad and grad school

    if user_info[0]["undergraduate_graduation_year_2"] != None:
        undergraduate_graduation_year_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :undergraduate_graduation_year_2_1=undergraduate_graduation_year OR :undergraduate_graduation_year_2_2=undergraduate_graduation_year_2", undergraduate_graduation_year_2_1 = user_info[0]["undergraduate_graduation_year_2"], undergraduate_graduation_year_2_2 = user_info[0]["undergraduate_graduation_year_2"])
    elif user_info[0]["undergraduate_graduation_year"] != None:
        undergraduate_graduation_year_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :undergraduate_graduation_year_1=undergraduate_graduation_year OR :undergraduate_graduation_year_2=undergraduate_graduation_year_2", undergraduate_graduation_year_1 = user_info[0]["undergraduate_graduation_year"], undergraduate_graduation_year_2 = user_info[0]["undergraduate_graduation_year"])
    if user_info[0]["postgraduate_graduation_year"] != None:
        postgraduate_graduation_year_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :postgraduate_graduation_year_1=postgraduate_graduation_year OR :postgraduate_graduation_year_2=postgraduate_graduation_year_2", postgraduate_graduation_year_1 = user_info[0]["postgraduate_graduation_year"], postgraduate_graduation_year_2 = user_info[0]["postgraduate_graduation_year"])
    if user_info[0]["postgraduate_graduation_year_2"] != None:
        postgraduate_graduation_year_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :postgraduate_graduation_year_2_1=postgraduate_graduation_year OR :postgraduate_graduation_year_2_2=postgraduate_graduation_year_2", postgraduate_graduation_year_2_1 = user_info[0]["postgraduate_graduation_year_2"], postgraduate_graduation_year_2_2 = user_info[0]["postgraduate_graduation_year_2"])

    # Match based on field of study for either undergrad or grad

    if user_info[0]["undergraduate_major"] != None:
        undergraduate_major_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :undergraduate_major_1=undergraduate_major OR :undergraduate_major_2=undergraduate_major_1_2 OR :undergraduate_major_3=undergraduate_major_1_3 OR :undergraduate_major_4=undergraduate_major_2 OR :undergraduate_major_5=undergraduate_major_2_2 OR :undergraduate_major_6=undergraduate_major_2_3 OR :undergraduate_major_7=field OR :undergraduate_major_8=field_2", undergraduate_major_1 = user_info[0]["undergraduate_major"], undergraduate_major_2 = user_info[0]["undergraduate_major"], undergraduate_major_3 = user_info[0]["undergraduate_major"], undergraduate_major_4 = user_info[0]["undergraduate_major"], undergraduate_major_5 = user_info[0]["undergraduate_major"], undergraduate_major_6 = user_info[0]["undergraduate_major"], undergraduate_major_7 = user_info[0]["undergraduate_major"], undergraduate_major_8 = user_info[0]["undergraduate_major"])
    if user_info[0]["undergraduate_major_1_2"] != None:
        undergraduate_major_1_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :undergraduate_major_1_2_1=undergraduate_major OR :undergraduate_major_1_2_2=undergraduate_major_1_2 OR :undergraduate_major_1_2_3=undergraduate_major_1_3 OR :undergraduate_major_1_2_4=undergraduate_major_2 OR :undergraduate_major_1_2_5=undergraduate_major_2_2 OR :undergraduate_major_1_2_6=undergraduate_major_2_3 OR :undergraduate_major_1_2_7=field OR :undergraduate_major_1_2_8=field_2", undergraduate_major_1_2_1 = user_info[0]["undergraduate_major_1_2"], undergraduate_major_1_2_2 = user_info[0]["undergraduate_major_1_2"], undergraduate_major_1_2_3 = user_info[0]["undergraduate_major_1_2"], undergraduate_major_1_2_4 = user_info[0]["undergraduate_major_1_2"], undergraduate_major_1_2_5 = user_info[0]["undergraduate_major_1_2"], undergraduate_major_1_2_6 = user_info[0]["undergraduate_major_1_2"], undergraduate_major_1_2_7 = user_info[0]["undergraduate_major_1_2"], undergraduate_major_1_2_8 = user_info[0]["undergraduate_major_1_2"])
    if user_info[0]["undergraduate_major_1_3"] != None:
        undergraduate_major_1_3_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :undergraduate_major_1_3_1=undergraduate_major OR :undergraduate_major_1_3_2=undergraduate_major_1_2 OR :undergraduate_major_1_3_3=undergraduate_major_1_3 OR :undergraduate_major_1_3_4=undergraduate_major_2 OR :undergraduate_major_1_3_5=undergraduate_major_2_2 OR :undergraduate_major_1_3_6=undergraduate_major_2_3 OR :undergraduate_major_1_3_7=field OR :undergraduate_major_1_3_8=field_2", undergraduate_major_1_3_1 = user_info[0]["undergraduate_major_1_3"], undergraduate_major_1_3_2 = user_info[0]["undergraduate_major_1_3"], undergraduate_major_1_3_3 = user_info[0]["undergraduate_major_1_3"], undergraduate_major_1_3_4 = user_info[0]["undergraduate_major_1_3"], undergraduate_major_1_3_5 = user_info[0]["undergraduate_major_1_3"], undergraduate_major_1_3_6 = user_info[0]["undergraduate_major_1_3"], undergraduate_major_1_3_7 = user_info[0]["undergraduate_major_1_3"], undergraduate_major_1_3_8 = user_info[0]["undergraduate_major_1_3"])
    if user_info[0]["undergraduate_major_2"] != None:
        undergraduate_major_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :undergraduate_major_2_1=undergraduate_major OR :undergraduate_major_2_2=undergraduate_major_1_2 OR :undergraduate_major_2_3=undergraduate_major_1_3 OR :undergraduate_major_2_4=undergraduate_major_2 OR :undergraduate_major_2_5=undergraduate_major_2_2 OR :undergraduate_major_2_6=undergraduate_major_2_3 OR :undergraduate_major_2_7=field OR :undergraduate_major_2_8=field_2", undergraduate_major_2_1 = user_info[0]["undergraduate_major_2"], undergraduate_major_2_2 = user_info[0]["undergraduate_major_2"], undergraduate_major_2_3 = user_info[0]["undergraduate_major_2"], undergraduate_major_2_4 = user_info[0]["undergraduate_major_2"], undergraduate_major_2_5 = user_info[0]["undergraduate_major_2"], undergraduate_major_2_6 = user_info[0]["undergraduate_major_2"], undergraduate_major_2_7 = user_info[0]["undergraduate_major_2"], undergraduate_major_2_8 = user_info[0]["undergraduate_major_2"])
    if user_info[0]["undergraduate_major_2_2"] != None:
        undergraduate_major_2_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :undergraduate_major_2_2_1=undergraduate_major OR :undergraduate_major_2_2_2=undergraduate_major_1_2 OR :undergraduate_major_2_2_3=undergraduate_major_1_3 OR :undergraduate_major_2_2_4=undergraduate_major_2 OR :undergraduate_major_2_2_5=undergraduate_major_2_2 OR :undergraduate_major_2_2_6=undergraduate_major_2_3 OR :undergraduate_major_2_2_7=field OR :undergraduate_major_2_2_8=field_2", undergraduate_major_2_2_1 = user_info[0]["undergraduate_major_2_2"], undergraduate_major_2_2_2 = user_info[0]["undergraduate_major_2_2"], undergraduate_major_2_2_3 = user_info[0]["undergraduate_major_2_2"], undergraduate_major_2_2_4 = user_info[0]["undergraduate_major_2_2"], undergraduate_major_2_2_5 = user_info[0]["undergraduate_major_2_2"], undergraduate_major_2_2_6 = user_info[0]["undergraduate_major_2_2"], undergraduate_major_2_2_7 = user_info[0]["undergraduate_major_2_2"], undergraduate_major_2_2_8 = user_info[0]["undergraduate_major_2_2"])
    if user_info[0]["undergraduate_major_2_3"] != None:
        undergraduate_major_2_3_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :undergraduate_major_2_3_1=undergraduate_major OR :undergraduate_major_2_3_2=undergraduate_major_1_2 OR :undergraduate_major_2_3_3=undergraduate_major_1_3 OR :undergraduate_major_2_3_4=undergraduate_major_2 OR :undergraduate_major_2_3_5=undergraduate_major_2_2 OR :undergraduate_major_2_3_6=undergraduate_major_2_3 OR :undergraduate_major_2_3_7=field OR :undergraduate_major_2_3_8=field_2", undergraduate_major_2_3_1 = user_info[0]["undergraduate_major_2_3"], undergraduate_major_2_3_2 = user_info[0]["undergraduate_major_2_3"], undergraduate_major_2_3_3 = user_info[0]["undergraduate_major_2_3"], undergraduate_major_2_3_4 = user_info[0]["undergraduate_major_2_3"], undergraduate_major_2_3_5 = user_info[0]["undergraduate_major_2_3"], undergraduate_major_2_3_6 = user_info[0]["undergraduate_major_2_3"], undergraduate_major_2_3_7 = user_info[0]["undergraduate_major_2_3"], undergraduate_major_2_3_8 = user_info[0]["undergraduate_major_2_3"])
    if user_info[0]["field"] != None:
        field_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :field_1=undergraduate_major OR :field_2=undergraduate_major_1_2 OR :field_3=undergraduate_major_1_3 OR :field_4=undergraduate_major_2 OR :field_5=undergraduate_major_2_2 OR :field_6=undergraduate_major_2_3 OR :field_7=field OR :field_8=field_2", field_1 = user_info[0]["field"], field_2 = user_info[0]["field"], field_3 = user_info[0]["field"], field_4 = user_info[0]["field"], field_5 = user_info[0]["field"], field_6 = user_info[0]["field"], field_7 = user_info[0]["field"], field_8 = user_info[0]["field"])
    if user_info[0]["field_2"] != None:
        field_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :field_2_1=undergraduate_major OR :field_2_2=undergraduate_major_1_2 OR :field_2_3=undergraduate_major_1_3 OR :field_2_4=undergraduate_major_2 OR :field_2_5=undergraduate_major_2_2 OR :field_2_6=undergraduate_major_2_3 OR :field_2_7=field OR :field_2_8=field_2", field_2_1 = user_info[0]["field_2"], field_2_2 = user_info[0]["field_2"], field_2_3 = user_info[0]["field_2"], field_2_4 = user_info[0]["field_2"], field_2_5 = user_info[0]["field_2"], field_2_6 = user_info[0]["field_2"], field_2_7 = user_info[0]["field_2"], field_2_8 = user_info[0]["field_2"])

    # Match based on postgraduate degrees- to do

    if user_info[0]["postgraduate_degree_1"] != None:
        postgraduate_degree_1_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :postgraduate_degree_1_1=postgraduate_degree_1 OR :postgraduate_degree_1_2=postgraduate_degree_2", postgraduate_degree_1_1 = user_info[0]["postgraduate_degree_1"], postgraduate_degree_1_2 = user_info[0]["postgraduate_degree_1"])
    if user_info[0]["postgraduate_degree_2"] != None:
        postgraduate_degree_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :postgraduate_degree_2_1=postgraduate_degree_1 OR :postgraduate_degree_2_2=postgraduate_degree_2", postgraduate_degree_2_1 = user_info[0]["postgraduate_degree_2"], postgraduate_degree_2_2 = user_info[0]["postgraduate_degree_2"])

    # Match based on industry and initial career path interest and industry looking towards

    if user_info[0]["current_industry_1"] != None:
        current_industry_1_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :current_industry_1_1=current_industry_1 OR :current_industry_1_2=current_industry_2 OR :current_industry_1_3=current_industry_3 OR :current_industry_1_4=initial_career_path_interest_1 OR :current_industry_1_5=initial_career_path_interest_2", current_industry_1_1 = user_info[0]["current_industry_1"], current_industry_1_2 = user_info[0]["current_industry_1"], current_industry_1_3 = user_info[0]["current_industry_1"], current_industry_1_4 = user_info[0]["current_industry_1"], current_industry_1_5 = user_info[0]["current_industry_1"])
    if user_info[0]["current_industry_2"] != None:
        current_industry_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :current_industry_2_1=current_industry_1 OR :current_industry_2_2=current_industry_2 OR :current_industry_2_3=current_industry_3 OR :current_industry_2_4=initial_career_path_interest_1 OR :current_industry_2_5=initial_career_path_interest_2", current_industry_2_1 = user_info[0]["current_industry_2"], current_industry_2_2 = user_info[0]["current_industry_2"], current_industry_2_3 = user_info[0]["current_industry_2"], current_industry_2_4 = user_info[0]["current_industry_2"], current_industry_2_5 = user_info[0]["current_industry_2"])
    if user_info[0]["current_industry_3"] != None:
        current_industry_3_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :current_industry_3_1=current_industry_1 OR :current_industry_3_2=current_industry_2 OR :current_industry_3_3=current_industry_3 OR :current_industry_3_4=initial_career_path_interest_1 OR :current_industry_3_5=initial_career_path_interest_2", current_industry_3_1 = user_info[0]["current_industry_3"], current_industry_3_2 = user_info[0]["current_industry_3"], current_industry_3_3 = user_info[0]["current_industry_3"], current_industry_3_4 = user_info[0]["current_industry_3"], current_industry_3_5 = user_info[0]["current_industry_3"])
    if user_info[0]["initial_career_path_interest_1"] != None:
        initial_career_path_interest_1_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :initial_career_path_interest_1_1=current_industry_1 OR :initial_career_path_interest_1_2=current_industry_2 OR :initial_career_path_interest_1_3=current_industry_3 OR :initial_career_path_interest_1_4=initial_career_path_interest_1 OR :initial_career_path_interest_1_5=initial_career_path_interest_2", initial_career_path_interest_1_1 = user_info[0]["initial_career_path_interest_1"], initial_career_path_interest_1_2 = user_info[0]["initial_career_path_interest_1"], initial_career_path_interest_1_3 = user_info[0]["initial_career_path_interest_1"], initial_career_path_interest_1_4 = user_info[0]["initial_career_path_interest_1"], initial_career_path_interest_1_5 = user_info[0]["initial_career_path_interest_1"])
    if user_info[0]["initial_career_path_interest_2"] != None:
        initial_career_path_interest_2_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :initial_career_path_interest_2_1=current_industry_1 OR :initial_career_path_interest_2_2=current_industry_2 OR :initial_career_path_interest_2_3=current_industry_3 OR :initial_career_path_interest_2_4=initial_career_path_interest_1 OR :initial_career_path_interest_2_5=initial_career_path_interest_2", initial_career_path_interest_2_1 = user_info[0]["initial_career_path_interest_2"], initial_career_path_interest_2_2 = user_info[0]["initial_career_path_interest_2"], initial_career_path_interest_2_3 = user_info[0]["initial_career_path_interest_2"], initial_career_path_interest_2_4 = user_info[0]["initial_career_path_interest_2"], initial_career_path_interest_2_5 = user_info[0]["initial_career_path_interest_2"])
    if user_info[0]["industry_looking_towards"] != None:
        industry_looking_towards_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :industry_looking_towards_1=current_industry_1 OR :industry_looking_towards_2=current_industry_2 OR :industry_looking_towards_3=current_industry_3 OR :industry_looking_towards_4=initial_career_path_interest_1 OR :industry_looking_towards_5=initial_career_path_interest_2", industry_looking_towards_1 = user_info[0]["industry_looking_towards"], industry_looking_towards_2 = user_info[0]["industry_looking_towards"], industry_looking_towards_3 = user_info[0]["industry_looking_towards"], industry_looking_towards_4 = user_info[0]["industry_looking_towards"], industry_looking_towards_5 = user_info[0]["industry_looking_towards"])

    # Match based on birth year

    if user_info[0]["born"] != None:
        born_match_rows = db.execute("SELECT full_name,image FROM profiles WHERE :born=born", born=user_info[0]["born"])

    # Maybe do if statements and if length of rows is 1 or more, then add that category name to an array, and then go through array, and pass through the parameters for the page?
    # Create list with person corresponding to number of matches, variable names that have matches in for each person (profile)
    # Create similarities array with categories of matches
    similarities_array = []
    num_match = 0

    if user_info[0]["current_company"] != None:
        if len(current_company_match_rows) > 0:
            similarities_array.append("current_company")
            num_match += 1
        else:
            current_company_match_rows = None
    if user_info[0]["second_company"] != None:
        if len(second_company_match_rows) > 0:
            similarities_array.append("second_company")
            num_match += 1
        else:
            second_company_match_rows = None
    if user_info[0]["third_company"] != None:
        if len(third_company_match_rows) > 0:
            similarities_array.append("third_company")
            num_match += 1
        else:
            third_company_match_rows = None
    if user_info[0]["post_college_company"] != None:
        if len(post_college_company_match_rows) > 0:
            similarities_array.append("post_college_company")
            num_match += 1
        else:
            post_college_company_match_rows = None
    if user_info[0]["past_company_1"] != None:
        if len(past_company_1_match_rows) > 0:
            similarities_array.append("past_company_1")
            num_match += 1
        else:
            past_company_1_match_rows = None
    if user_info[0]["past_company_2"] != None:
        if len(past_company_2_match_rows) > 0:
            similarities_array.append("past_company_2")
            num_match += 1
        else:
            past_company_2_match_rows = None
    if user_info[0]["past_company_3"] != None:
        if len(past_company_3_match_rows) > 0:
            similarities_array.append("past_company_3")
            num_match += 1
        else:
            past_company_3_match_rows = None
    if user_info[0]["past_company_4"] != None:
        if len(past_company_4_match_rows) > 0:
            similarities_array.append("past_company_4")
            num_match += 1
        else:
            past_company_4_match_rows = None
    if user_info[0]["dream_company"] != None:
        if len(dream_company_match_rows) > 0:
            similarities_array.append("dream_company")
            num_match += 1
        else:
            dream_company_match_rows = None
    if user_info[0]["current_title_1"] != None:
        if len(current_title_1_match_rows) > 0:
            similarities_array.append("current_title_1")
            num_match += 1
        else:
            current_title_1_match_rows = None
    if user_info[0]["alternate_title_1"] != None:
        if len(alternate_title_1_match_rows) > 0:
            similarities_array.append("alternate_title_1")
            num_match += 1
        else:
            alternate_title_1_match_rows = None
    if user_info[0]["current_title_2"] != None:
        if len(current_title_2_match_rows) > 0:
            similarities_array.append("current_title_2")
            num_match += 1
        else:
            current_title_2_match_rows = None
    if user_info[0]["alternate_title_2"] != None:
        if len(alternate_title_2_match_rows) > 0:
            similarities_array.append("alternate_title_2")
            num_match += 1
        else:
            alternate_title_2_match_rows = None
    if user_info[0]["current_title_3"] != None:
        if len(current_title_3_match_rows) > 0:
            similarities_array.append("current_title_3")
            num_match += 1
        else:
            current_title_3_match_rows = None
    if user_info[0]["alternate_title_3"] != None:
        if len(alternate_title_3_match_rows) > 0:
            similarities_array.append("alternate_title_3")
            num_match += 1
        else:
            alternate_title_3_match_rows = None
    if user_info[0]["post_college_job"] != None:
        if len(post_college_job_match_rows) > 0:
            similarities_array.append("post_college_job")
            num_match += 1
        else:
            post_college_job_match_rows = None
    if user_info[0]["past_position_1"] != None:
        if len(past_position_1_match_rows) > 0:
            similarities_array.append("past_position_1")
            num_match += 1
        else:
            past_position_1_match_rows = None
    if user_info[0]["alternate_past_position_1"] != None:
        if len(alternate_past_position_1_match_rows) > 0:
            similarities_array.append("alternate_past_position_1")
            num_match += 1
        else:
            alternate_past_position_1_match_rows = None
    if user_info[0]["past_position_2"] != None:
        if len(past_position_2_match_rows) > 0:
            similarities_array.append("past_position_2")
            num_match += 1
        else:
            past_position_2_match_rows = None
    if user_info[0]["alternate_past_position_2"] != None:
        if len(alternate_past_position_2_match_rows) > 0:
            similarities_array.append("alternate_past_position_2")
            num_match += 1
        else:
            alternate_past_position_2_match_rows = None
    if user_info[0]["past_position_3"] != None:
        if len(past_position_3_match_rows) > 0:
            similarities_array.append("past_position_3")
            num_match += 1
        else:
            past_position_3_match_rows = None
    if user_info[0]["alternate_past_position_3"] != None:
        if len(alternate_past_position_3_match_rows) > 0:
            similarities_array.append("alternate_past_position_3")
            num_match += 1
        else:
            alternate_past_position_3_match_rows = None
    if user_info[0]["past_position_4"] != None:
        if len(past_position_4_match_rows) > 0:
            similarities_array.append("past_position_4")
            num_match += 1
        else:
            past_position_4_match_rows = None
    if user_info[0]["alternate_past_position_4"] != None:
        if len(alternate_past_position_4_match_rows) > 0:
            similarities_array.append("alternate_past_position_4")
            num_match += 1
        else:
            alternate_past_postion_4_match_rows = None
    if user_info[0]["career_position_looking_for"] != None:
        if len(career_position_looking_for_match_rows) > 0:
            similarities_array.append("career_position_looking_for")
            num_match += 1
        else:
            career_position_looking_for_match_rows = None
    if user_info[0]["prep_school"] != None:
        if len(prep_school_match_rows) > 0:
            similarities_array.append("prep_school")
            num_match += 1
        else:
            prep_school_match_rows = None
    if user_info[0]["undergraduate_school"] != None:
        if len(undergraduate_school_match_rows) > 0:
            similarities_array.append("undergraduate_school")
            num_match += 1
        else:
            undergraduate_school_match_rows = None
    if user_info[0]["undergraduate_school_2"] != None:
        if len(undergraduate_school_2_match_rows) > 0:
            similarities_array.append("undergraduate_school_2")
            num_match += 1
        else:
            undergraduate_school_2_match_rows = None
    if user_info[0]["postgraduate_school"] != None:
        if len(postgraduate_school_match_rows) > 0:
            similarities_array.append("postgraduate_school")
            num_match += 1
        else:
            postgraduate_school_match_rows = None
    if user_info[0]["postgraduate_school_2"] != None:
        if len(postgraduate_school_2_match_rows) > 0:
            similarities_array.append("postgraduate_school_2")
            num_match += 1
        else:
            postgraduate_school_2_match_rows = None
    if user_info[0]["undergraduate_graduation_year_2"] != None:
        undergraduate_graduation_year_match_rows = None
        if len(undergraduate_graduation_year_2_match_rows) > 0:
            similarities_array.append("undergraduate_graduation_year_2")
            num_match += 1
        else:
            undergraduate_graduation_year_2_match_rows = None
    elif user_info[0]["undergraduate_graduation_year"] != None:
        if len(undergraduate_graduation_year_match_rows) > 0:
            similarities_array.append("undergraduate_graduation_year")
            num_match += 1
        else:
            undergraduate_graduation_year_match_rows = None
    if user_info[0]["postgraduate_graduation_year"] != None:
        if len(postgraduate_graduation_year_match_rows) > 0:
            similarities_array.append("Postgraduate_Graduation_Year")
            num_match += 1
        else:
            postgraduate_graduation_year_match_rows = None
    if user_info[0]["postgraduate_graduation_year_2"] != None:
        if len(postgraduate_graduation_year_2_match_rows) > 0:
            similarities_array.append("postgraduate_graduation_year_2")
            num_match += 1
        else:
            postgraduate_graduation_year_2_match_rows = None
    if user_info[0]["undergraduate_major"] != None:
        if len(undergraduate_major_match_rows) > 0:
            similarities_array.append("undergraduate_major")
            num_match += 1
        else:
            undergraduate_major_match_rows = None
    if user_info[0]["undergraduate_major_1_2"] != None:
        if len(undergraduate_major_1_2_match_rows) > 0:
            similarities_array.append("undergraduate_major_1_2")
            num_match += 1
        else:
            undergraduate_major_1_2_match_rows = None
    if user_info[0]["undergraduate_major_1_3"] != None:
        if len(undergraduate_major_1_3_match_rows) > 0:
            similarities_array.append("undergraduate_major_1_3")
            num_match += 1
        else:
            undergraduate_major_1_3_match_rows = None
    if user_info[0]["undergraduate_major_2"] != None:
        if len(undergraduate_major_2_match_rows) > 0:
            similarities_array.append("undergraduate_major_2")
            num_match += 1
        else:
            undergraduate_major_2_match_rows = None
    if user_info[0]["undergraduate_major_2_2"] != None:
        if len(undergraduate_major_2_2_match_rows) > 0:
            similarities_array.append("undergraduate_major_2_2")
            num_match += 1
        else:
            undergraduate_major_2_2_match_rows = None
    if user_info[0]["undergraduate_major_2_3"] != None:
        if len(undergraduate_major_2_3_match_rows) > 0:
            similarities_array.append("undergraduate_major_2_3")
            num_match += 1
        else:
            undergraduate_major_2_3_match_rows = None
    if user_info[0]["field"] != None:
        if len(field_match_rows) > 0:
            similarities_array.append("field")
            num_match += 1
        else:
            field_match_rows = None
    if user_info[0]["field_2"] != None:
        if len(field_2_match_rows) > 0:
            similarities_array.append("field_2")
            num_match += 1
        else:
            field_2_match_rows = None
    if user_info[0]["current_industry_1"] != None:
        if len(current_industry_1_match_rows) > 0:
            similarities_array.append("current_industry_1")
            num_match += 1
        else:
            current_industry_1_match_rows = None
    if user_info[0]["current_industry_2"] != None:
        if len(current_industry_2_match_rows) > 0:
            similarities_array.append("current_industry_2")
            num_match += 1
        else:
            current_industry_2_match_rows = None
    if user_info[0]["current_industry_3"] != None:
        if len(current_industry_3_match_rows) > 0:
            similarities_array.append("current_industry_3")
            num_match += 1
        else:
            current_industry_3_match_rows = None
    if user_info[0]["initial_career_path_interest_1"] != None:
        if len(initial_career_path_interest_1_match_rows) > 0:
            similarities_array.append("initial_career_path_interest_1")
            num_match += 1
        else:
            initial_career_path_interest_1_match_rows = None
    if user_info[0]["initial_career_path_interest_2"] != None:
        if len(initial_career_path_interest_2_match_rows) > 0:
            similarities_array.append("initial_career_path_interest_2")
            num_match += 1
        else:
            initial_career_path_interest_2_match_rows = None
    if user_info[0]["industry_looking_towards"] != None:
        if len(industry_looking_towards_match_rows) > 0:
            similarities_array.append("industry_looking_towards")
            num_match += 1
        else:
            industry_looking_towards_match_rows = None
    if user_info[0]["born"] != None:
        if len(born_match_rows) > 0:
            similarities_array.append("born")
            num_match += 1
        else:
            born_match_rows = None

    # if number of matches is 0, return apology
    if num_match == 0:
        return apology("Surprisingly, we couldn't find any matches. Looks like you are a trailblazer!")
    else:
        return render_template("similarities.html", user_info=user_info, current_company_match_rows=current_company_match_rows, second_company_match_rows=second_company_match_rows, third_company_match_rows=third_company_match_rows, post_college_job_match_rows=post_college_job_match_rows, past_company_1_match_rows=past_company_1_match_rows, past_company_2_match_rows=past_company_2_match_rows, past_company_3_match_rows=past_company_3_match_rows, past_company_4_match_rows=past_company_4_match_rows, dream_company_match_rows=dream_company_match_rows, current_title_1_match_rows=current_title_1_match_rows, alternate_title_1_match_rows=alternate_title_1_match_rows, current_title_2_match_rows=current_title_2_match_rows, alternate_title_2_match_rows=alternate_title_2_match_rows, current_title_3_match_rows=current_title_3_match_rows, alternate_title_3_match_rows=alternate_title_3_match_rows, past_position_1_match_rows=past_position_1_match_rows, alternate_past_position_1_match_rows=alternate_past_position_1_match_rows, past_position_2_match_rows=past_position_2_match_rows, alternate_past_position_2_match_rows=alternate_past_position_2_match_rows, past_position_3_match_rows=past_position_3_match_rows, alternate_past_position_3_match_rows=alternate_past_position_3_match_rows, past_position_4_match_rows=past_position_4_match_rows, alternate_past_position_4_match_rows=alternate_past_position_4_match_rows, career_position_looking_for_match_rows=career_position_looking_for_match_rows, prep_school_match_rows=prep_school_match_rows, undergraduate_school_match_rows=undergraduate_school_match_rows, undergraduate_school_2_match_rows=undergraduate_school_2_match_rows, postgraduate_school_match_rows=postgraduate_school_match_rows, postgraduate_school_2_match_rows=postgraduate_school_2_match_rows, undergraduate_graduation_year_match_rows=undergraduate_graduation_year_match_rows, undergraduate_graduation_year_2_match_rows=undergraduate_graduation_year_2_match_rows, postgraduate_graduation_year_match_rows=postgraduate_graduation_year_match_rows, postgraduate_graduation_year_2_match_rows=postgraduate_graduation_year_2_match_rows, undergraduate_major_match_rows=undergraduate_major_match_rows, undergraduate_major_1_2_match_rows=undergraduate_major_1_2_match_rows, undergraduate_major_1_3_match_rows=undergraduate_major_1_3_match_rows, undergraduate_major_2_match_rows=undergraduate_major_2_match_rows, undergraduate_major_2_2_match_rows=undergraduate_major_2_2_match_rows, undergraduate_major_2_3_match_rows=undergraduate_major_2_3_match_rows, field_match_rows=field_match_rows, field_2_match_rows=field_2_match_rows, current_industry_1_match_rows=current_industry_1_match_rows, current_industry_2_match_rows=current_industry_2_match_rows, current_industry_3_match_rows=current_industry_3_match_rows, initial_career_path_interest_1_match_rows=initial_career_path_interest_1_match_rows, initial_career_path_interest_2_match_rows=initial_career_path_interest_2_match_rows, industry_looking_towards_match_rows=industry_looking_towards_match_rows, born_match_rows=born_match_rows)



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
        for char in request.form.get("name"):
            if char.isalpha() == False and char != "\'" and char != " ":
                return apology("Invalid search - Try a different spelling")

        # Convert name to only capitalize letters at beginning of each word
        lower_name = request.form.get("name").lower()
        # Source: http://stackoverflow.com/questions/1549641/how-to-capitalize-the-first-letter-of-each-word-in-a-string-python
        capital_name = " ".join(word[0].upper() + word[1:] for word in lower_name.split())

        # Query database for name
        try:
            searched_rows = db.execute("SELECT template_name FROM profiles WHERE full_name = :name", name= capital_name)

        except:
            searched_rows = None

        # Calculate number of rows selected
        num_searched_rows = len(searched_rows)


        # Return profile(s) or apology
        if len(searched_rows) == 1:
            # Return profile of person if only one match
            return render_template(searched_rows[0]["template_name"] + ".html")
        elif num_searched_rows > 1:
            # Return list of people to choose from- to be implemented later- can maybe present choices of companies work at or just pictures with names that can click on

            # return render_template("searched.html", searched_rows = searched_rows)
            # for now, give apology
            return apology("Multiple matches found")
        else:
            return apology("No profiles found for " + capital_name)

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
    user_rows = db.execute("SELECT * FROM users WHERE id = :id", id = session["user_id"])

    # Display information by rerouting to profile page
    return render_template("profile.html", full_name=user_rows[0]["full_name"], current_company=user_rows[0]["current_company"], second_company=user_rows[0]["second_company"], third_company=user_rows[0]["third_company"], current_title_1=user_rows[0]["current_title_1"], alternate_title_1=user_rows[0]["alternate_title_1"], current_title_2=user_rows[0]["current_title_2"], alternate_title_2=user_rows[0]["alternate_title_2"], current_title_3=user_rows[0]["current_title_3"], alternate_title_3=user_rows[0]["alternate_title_3"], current_industry_1=user_rows[0]["current_industry_1"], current_industry_2=user_rows[0]["current_industry_2"], current_industry_3=user_rows[0]["current_industry_3"], year_start_1=user_rows[0]["year_start_1"], year_start_2=user_rows[0]["year_start_2"], year_start_3=user_rows[0]["year_start_3"], born=user_rows[0]["born"], undergraduate_school=user_rows[0]["undergraduate_school"], undergraduate_major=user_rows[0]["undergraduate_major"], undergraduate_major_1_2=user_rows[0]["undergraduate_major_1_2"], undergraduate_major_1_3=user_rows[0]["undergraduate_major_1_3"], undergraduate_graduation_year=user_rows[0]["undergraduate_graduation_year"], undergraduate_school_2=user_rows[0]["undergraduate_school_2"], undergraduate_major_2=user_rows[0]["undergraduate_major_2"], undergraduate_major_2_2=user_rows[0]["undergraduate_major_2_2"], undergraduate_major_2_3=user_rows[0]["undergraduate_major_2_3"], undergraduate_graduation_year_2=user_rows[0]["undergraduate_graduation_year_2"], prep_school=user_rows[0]["prep_school"], postgraduate_school=user_rows[0]["postgraduate_school"], postgraduate_degree_1=user_rows[0]["postgraduate_degree_1"], field=user_rows[0]["field"], postgraduate_graduation_year=user_rows[0]["postgraduate_graduation_year"], postgraduate_school_2=user_rows[0]["postgraduate_school_2"], postgraduate_degree_2=user_rows[0]["postgraduate_degree_2"], field_2=user_rows[0]["field_2"], postgraduate_graduation_year_2=user_rows[0]["postgraduate_graduation_year_2"], initial_career_path_interest_1=user_rows[0]["initial_career_path_interest_1"], initial_career_path_interest_2=user_rows[0]["initial_career_path_interest_2"], post_college_job=user_rows[0]["post_college_job"], post_college_company=user_rows[0]["post_college_company"], post_college_year_start=user_rows[0]["post_college_year_start"], post_college_year_end=user_rows[0]["post_college_year_end"], past_company_1=user_rows[0]["past_company_1"], past_position_1=user_rows[0]["past_position_1"], alternate_past_position_1=user_rows[0]["alternate_past_position_1"], past_company_2=user_rows[0]["past_company_2"], past_position_2=user_rows[0]["past_position_2"], alternate_past_position_2=user_rows[0]["alternate_past_position_2"], past_company_3=user_rows[0]["past_company_3"], past_position_3=user_rows[0]["past_position_3"], alternate_past_position_3=user_rows[0]["alternate_past_position_3"], past_company_4=user_rows[0]["past_company_4"], past_position_4=user_rows[0]["past_position_4"], alternate_past_position_4=user_rows[0]["alternate_past_position_4"], past_year_start_1=user_rows[0]["past_year_start_1"], past_year_end_1=user_rows[0]["past_year_end_1"], past_year_start_2=user_rows[0]["past_year_start_2"], past_year_end_2=user_rows[0]["past_year_end_2"], past_year_start_3=user_rows[0]["past_year_start_3"], past_year_end_3=user_rows[0]["past_year_end_3"], past_year_start_4=user_rows[0]["past_year_start_4"], past_year_end_4=user_rows[0]["past_year_end_4"], career_position_looking_for=user_rows[0]["career_position_looking_for"], industry_looking_towards=user_rows[0]["industry_looking_towards"], dream_company=user_rows[0]["dream_company"], miscellaneous=user_rows[0]["miscellaneous"])

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

