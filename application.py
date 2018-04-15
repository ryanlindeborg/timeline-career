# from cs50 import SQL
from flask import Flask, jsonify, flash, redirect, render_template, request, session, url_for
from flask_session import Session
#from flask_Jglue import JSGlue
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir

from helpers import *

import os
import sqlalchemy

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

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///timeline.db")

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
        if not request.form.get("Username"):
            return apology("Must provide username")

        # ensure password was submitted
        elif not request.form.get("Password"):
            return apology("Must provide password")

        # query database for username
        rows = db.execute("SELECT ID,Hash FROM Users WHERE Username = :Username", Username=request.form.get("Username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("Password"), rows[0]["Hash"]):
            return apology("Invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["ID"]

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
        if not request.form.get("Username"):
            return apology("Must provide username")
        # ensure passwords submitted and match
        elif not request.form.get("Password"):
            return apology("Must provide password")
        elif not request.form.get("Confirm_password"):
            return apology("Must confirm password")
        elif request.form.get("Password") != request.form.get("Confirm_password"):
            return apology("Passwords don't match")

        # Search database and check to see if username taken
        rows = db.execute("SELECT ID FROM Users WHERE Username = :Username", Username=request.form.get("Username"))
        if len(rows) == 1:
            return apology("Username is already taken. Please select another")

        # Add new user to users database, with hashed password
        db.execute("INSERT INTO Users (Username, Hash) VALUES(:Username, :Hash)", Username=request.form.get("Username"), Hash=pwd_context.encrypt(request.form.get("Password")))

        # Query database for user data just inputted
        updated_rows = db.execute("SELECT ID FROM Users WHERE Username = :Username", Username=request.form.get("Username"))

        # remember which user has logged in
        session["user_id"] = updated_rows[0]["ID"]

        # Create row in Users database with id
        db.execute("INSERT INTO Users (ID) VALUES(:ID)", ID=session["user_id"])

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
        if request.form.get("First_Name"):
            db.execute("UPDATE Users SET First_Name = :First_Name WHERE ID = :ID", First_Name=request.form.get("First_Name"), ID=session["user_id"])
        if request.form.get("Last_Name"):
            db.execute("UPDATE Users SET Last_Name = :Last_Name WHERE ID = :ID", Last_Name=request.form.get("Last_Name"), ID=session["user_id"])
        if request.form.get("First_Name") and request.form.get("Last_Name"):
            db.execute("UPDATE Users SET Full_Name = :Full_Name WHERE ID = :ID", Full_Name=request.form.get("First_Name") + " " + request.form.get("Last_Name"), ID=session["user_id"])
        if request.form.get("Current_Company"):
            db.execute("UPDATE Users SET Current_Company = :Current_Company WHERE ID = :ID", Current_Company=request.form.get("Current_Company"), ID=session["user_id"])
        if request.form.get("Second_Company"):
            db.execute("UPDATE Users SET Second_Company = :Second_Company WHERE ID = :ID", Second_Company=request.form.get("Second_Company"), ID=session["user_id"])
        if request.form.get("Third_Company"):
            db.execute("UPDATE Users SET Third_Company = :Third_Company WHERE ID = :ID", Third_Company=request.form.get("Third_Company"), ID=session["user_id"])
        if request.form.get("Current_Title_1"):
            db.execute("UPDATE Users SET Current_Title_1 = :Current_Title_1 WHERE ID = :ID", Current_Title_1=request.form.get("Current_Title_1"), ID=session["user_id"])
        if request.form.get("Alternate_Title_1"):
            db.execute("UPDATE Users SET Alternate_Title_1 = :Alternate_Title_1 WHERE ID = :ID", Alternate_Title_1=request.form.get("Alternate_Title_1"), ID=session["user_id"])
        if request.form.get("Current_Title_2"):
            db.execute("UPDATE Users SET Current_Title_2 = :Current_Title_2 WHERE ID = :ID", Current_Title_2=request.form.get("Current_Title_2"), ID=session["user_id"])
        if request.form.get("Alternate_Title_2"):
            db.execute("UPDATE Users SET Alternate_Title_2 = :Alternate_Title_2 WHERE ID = :ID", Alternate_Title_2=request.form.get("Alternate_Title_2"), ID=session["user_id"])
        if request.form.get("Current_Title_3"):
            db.execute("UPDATE Users SET Current_Title_3 = :Current_Title_3 WHERE ID = :ID", Current_Title_3=request.form.get("Current_Title_3"), ID=session["user_id"])
        if request.form.get("Alternate_Title_3"):
            db.execute("UPDATE Users SET Alternate_Title_3 = :Alternate_Title_3 WHERE ID = :ID", Alternate_Title_3=request.form.get("Alternate_Title_3"), ID=session["user_id"])
        if request.form.get("Current_Industry_1"):
            db.execute("UPDATE Users SET Current_Industry_1 = :Current_Industry_1 WHERE ID = :ID", Current_Industry_1=request.form.get("Current_Industry_1"), ID=session["user_id"])
        if request.form.get("Current_Industry_2"):
            db.execute("UPDATE Users SET Current_Industry_2 = :Current_Industry_2 WHERE ID = :ID", Current_Industry_2=request.form.get("Current_Industry_2"), ID=session["user_id"])
        if request.form.get("Current_Industry_3"):
            db.execute("UPDATE Users SET Current_Industry_3 = :Current_Industry_3 WHERE ID = :ID", Current_Industry_3=request.form.get("Current_Industry_3"), ID=session["user_id"])
        if request.form.get("Year_Start_1"):
            db.execute("UPDATE Users SET Year_Start_1 = :Year_Start_1 WHERE ID = :ID", Year_Start_1=request.form.get("Year_Start_1"), ID=session["user_id"])
        if request.form.get("Year_Start_2"):
            db.execute("UPDATE Users SET Year_Start_2 = :Year_Start_2 WHERE ID = :ID", Year_Start_2=request.form.get("Year_Start_2"), ID=session["user_id"])
        if request.form.get("Year_Start_3"):
            db.execute("UPDATE Users SET Year_Start_3 = :Year_Start_3 WHERE ID = :ID", Year_Start_3=request.form.get("Year_Start_3"), ID=session["user_id"])
        if request.form.get("Born"):
            db.execute("UPDATE Users SET Born = :Born WHERE ID = :ID", Born=request.form.get("Born"), ID=session["user_id"])
        if request.form.get("Undergraduate_School"):
            db.execute("UPDATE Users SET Undergraduate_School = :Undergraduate_School WHERE ID = :ID", Undergraduate_School=request.form.get("Undergraduate_School"), ID=session["user_id"])
        if request.form.get("Undergraduate_Major"):
            db.execute("UPDATE Users SET Undergraduate_Major = :Undergraduate_Major WHERE ID = :ID", Undergraduate_Major=request.form.get("Undergraduate_Major"), ID=session["user_id"])
        if request.form.get("Undergraduate_Major_1_2"):
            db.execute("UPDATE Users SET Undergraduate_Major_1_2 = :Undergraduate_Major_1_2 WHERE ID = :ID", Undergraduate_Major_1_2=request.form.get("Undergraduate_Major_1_2"), ID=session["user_id"])
        if request.form.get("Undergraduate_Major_1_3"):
            db.execute("UPDATE Users SET Undergraduate_Major_1_3 = :Undergraduate_Major_1_3 WHERE ID = :ID", Undergraduate_Major_1_3=request.form.get("Undergraduate_Major_1_3"), ID=session["user_id"])
        if request.form.get("Undergraduate_Graduation_Year"):
            db.execute("UPDATE Users SET Undergraduate_Graduation_Year = :Undergraduate_Graduation_Year WHERE ID = :ID", Undergraduate_Graduation_Year=request.form.get("Undergraduate_Graduation_Year"), ID=session["user_id"])
        if request.form.get("Undergraduate_School_2"):
            db.execute("UPDATE Users SET Undergraduate_School_2 = :Undergraduate_School_2 WHERE ID = :ID", Undergraduate_School_2=request.form.get("Undergraduate_School_2"), ID=session["user_id"])
        if request.form.get("Undergraduate_Major_2"):
            db.execute("UPDATE Users SET Undergraduate_Major_2 = :Undergraduate_Major_2 WHERE ID = :ID", Undergraduate_Major_2=request.form.get("Undergraduate_Major_2"), ID=session["user_id"])
        if request.form.get("Undergraduate_Major_2_2"):
            db.execute("UPDATE Users SET Undergraduate_Major_2_2 = :Undergraduate_Major_2_2 WHERE ID = :ID", Undergraduate_Major_2_2=request.form.get("Undergraduate_Major_2_2"), ID=session["user_id"])
        if request.form.get("Undergraduate_Major_2_3"):
            db.execute("UPDATE Users SET Undergraduate_Major_2_3 = :Undergraduate_Major_2_3 WHERE ID = :ID", Undergraduate_Major_2_3=request.form.get("Undergraduate_Major_2_3"), ID=session["user_id"])
        if request.form.get("Undergraduate_Graduation_Year_2"):
            db.execute("UPDATE Users SET Undergraduate_Graduation_Year_2 = :Undergraduate_Graduation_Year_2 WHERE ID = :ID", Undergraduate_Graduation_Year_2=request.form.get("Undergraduate_Graduation_Year_2"), ID=session["user_id"])
        if request.form.get("Prep_School"):
            db.execute("UPDATE Users SET Prep_School = :Prep_School WHERE ID = :ID", Prep_School=request.form.get("Prep_School"), ID=session["user_id"])
        if request.form.get("Postgraduate_School"):
            db.execute("UPDATE Users SET Postgraduate_School = :Postgraduate_School WHERE ID = :ID", Postgraduate_School=request.form.get("Postgraduate_School"), ID=session["user_id"])
        if request.form.get("Postgraduate_Degree_1"):
            db.execute("UPDATE Users SET Postgraduate_Degree_1 = :Postgraduate_Degree_1 WHERE ID = :ID", Postgraduate_Degree_1=request.form.get("Postgraduate_Degree_1"), ID=session["user_id"])
        if request.form.get("Field"):
            db.execute("UPDATE Users SET Field = :Field WHERE ID = :ID", Field=request.form.get("Field"), ID=session["user_id"])
        if request.form.get("Postgraduate_Graduation_Year"):
            db.execute("UPDATE Users SET Postgraduate_Graduation_Year = :Postgraduate_Graduation_Year WHERE ID = :ID", Postgraduate_Graduation_Year=request.form.get("Postgraduate_Graduation_Year"), ID=session["user_id"])
        if request.form.get("Postgraduate_School_2"):
            db.execute("UPDATE Users SET Postgraduate_School_2 = :Postgraduate_School_2 WHERE ID = :ID", Postgraduate_School_2=request.form.get("Postgraduate_School_2"), ID=session["user_id"])
        if request.form.get("Postgraduate_Degree_2"):
            db.execute("UPDATE Users SET Postgraduate_Degree_2 = :Postgraduate_Degree_2 WHERE ID = :ID", Postgraduate_Degree_2=request.form.get("Postgraduate_Degree_2"), ID=session["user_id"])
        if request.form.get("Field_2"):
            db.execute("UPDATE Users SET Field_2 = :Field_2 WHERE ID = :ID", Field_2=request.form.get("Field_2"), ID=session["user_id"])
        if request.form.get("Postgraduate_Graduation_Year_2"):
            db.execute("UPDATE Users SET Postgraduate_Graduation_Year_2 = :Postgraduate_Graduation_Year_2 WHERE ID = :ID", Postgraduate_Graduation_Year_2=request.form.get("Postgraduate_Graduation_Year_2"), ID=session["user_id"])
        if request.form.get("Initial_Career_Path_Interest_1"):
            db.execute("UPDATE Users SET Initial_Career_Path_Interest_1 = :Initial_Career_Path_Interest_1 WHERE ID = :ID", Initial_Career_Path_Interest_1=request.form.get("Initial_Career_Path_Interest_1"), ID=session["user_id"])
        if request.form.get("Initial_Career_Path_Interest_2"):
            db.execute("UPDATE Users SET Initial_Career_Path_Interest_2 = :Initial_Career_Path_Interest_2 WHERE ID = :ID", Initial_Career_Path_Interest_2=request.form.get("Initial_Career_Path_Interest_2"), ID=session["user_id"])
        if request.form.get("Post_College_Job"):
            db.execute("UPDATE Users SET Post_College_Job = :Post_College_Job WHERE ID = :ID", Post_College_Job=request.form.get("Post_College_Job"), ID=session["user_id"])
        if request.form.get("Post_College_Company"):
            db.execute("UPDATE Users SET Post_College_Company = :Post_College_Company WHERE ID = :ID", Post_College_Company=request.form.get("Post_College_Company"), ID=session["user_id"])
        if request.form.get("Post_College_Year_Start"):
            db.execute("UPDATE Users SET Post_College_Year_Start = :Post_College_Year_Start WHERE ID = :ID", Post_College_Year_Start=request.form.get("Post_College_Year_Start"), ID=session["user_id"])
        if request.form.get("Post_College_Year_End"):
            db.execute("UPDATE Users SET Post_College_Year_End = :Post_College_Year_End WHERE ID = :ID", Post_College_Year_End=request.form.get("Post_College_Year_End"), ID=session["user_id"])
        if request.form.get("Past_Company_1"):
            db.execute("UPDATE Users SET Past_Company_1 = :Past_Company_1 WHERE ID = :ID", Past_Company_1=request.form.get("Past_Company_1"), ID=session["user_id"])
        if request.form.get("Past_Position_1"):
            db.execute("UPDATE Users SET Past_Position_1 = :Past_Position_1 WHERE ID = :ID", Past_Position_1=request.form.get("Past_Position_1"), ID=session["user_id"])
        if request.form.get("Alternate_Past_Position_1"):
            db.execute("UPDATE Users SET Alternate_Past_Position_1 = :Alternate_Past_Position_1 WHERE ID = :ID", Alternate_Past_Position_1=request.form.get("Alternate_Past_Position_1"), ID=session["user_id"])
        if request.form.get("Past_Company_2"):
            db.execute("UPDATE Users SET Past_Company_2 = :Past_Company_2 WHERE ID = :ID", Past_Company_2=request.form.get("Past_Company_2"), ID=session["user_id"])
        if request.form.get("Past_Position_2"):
            db.execute("UPDATE Users SET Past_Position_2 = :Past_Position_2 WHERE ID = :ID", Past_Position_2=request.form.get("Past_Position_2"), ID=session["user_id"])
        if request.form.get("Alternate_Past_Position_2"):
            db.execute("UPDATE Users SET Alternate_Past_Position_2 = :Alternate_Past_Position_2 WHERE ID = :ID", Alternate_Past_Position_2=request.form.get("Alternate_Past_Position_2"), ID=session["user_id"])
        if request.form.get("Past_Company_3"):
            db.execute("UPDATE Users SET Past_Company_3 = :Past_Company_3 WHERE ID = :ID", Past_Company_3=request.form.get("Past_Company_3"), ID=session["user_id"])
        if request.form.get("Past_Position_3"):
            db.execute("UPDATE Users SET Past_Position_3 = :Past_Position_3 WHERE ID = :ID", Past_Position_3=request.form.get("Past_Position_3"), ID=session["user_id"])
        if request.form.get("Alternate_Past_Position_3"):
            db.execute("UPDATE Users SET Alternate_Past_Position_3 = :Alternate_Past_Position_3 WHERE ID = :ID", Alternate_Past_Position_3=request.form.get("Alternate_Past_Position_3"), ID=session["user_id"])
        if request.form.get("Past_Company_4"):
            db.execute("UPDATE Users SET Past_Company_4 = :Past_Company_4 WHERE ID = :ID", Past_Company_4=request.form.get("Past_Company_4"), ID=session["user_id"])
        if request.form.get("Past_Position_4"):
            db.execute("UPDATE Users SET Past_Position_4 = :Past_Position_4 WHERE ID = :ID", Past_Position_4=request.form.get("Past_Position_4"), ID=session["user_id"])
        if request.form.get("Alternate_Past_Position_4"):
            db.execute("UPDATE Users SET Alternate_Past_Position_4 = :Alternate_Past_Position_4 WHERE ID = :ID", Alternate_Past_Position_4=request.form.get("Alternate_Past_Position_4"), ID=session["user_id"])
        if request.form.get("Past_Year_Start_1"):
            db.execute("UPDATE Users SET Past_Year_Start_1 = :Past_Year_Start_1 WHERE ID = :ID", Past_Year_Start_1=request.form.get("Past_Year_Start_1"), ID=session["user_id"])
        if request.form.get("Past_Year_End_1"):
            db.execute("UPDATE Users SET Past_Year_End_1 = :Past_Year_End_1 WHERE ID = :ID", Past_Year_End_1=request.form.get("Past_Year_End_1"), ID=session["user_id"])
        if request.form.get("Past_Year_Start_2"):
            db.execute("UPDATE Users SET Past_Year_Start_2 = :Past_Year_Start_2 WHERE ID = :ID", Past_Year_Start_2=request.form.get("Past_Year_Start_2"), ID=session["user_id"])
        if request.form.get("Past_Year_End_2"):
            db.execute("UPDATE Users SET Past_Year_End_2 = :Past_Year_End_2 WHERE ID = :ID", Past_Year_End_2=request.form.get("Past_Year_End_2"), ID=session["user_id"])
        if request.form.get("Past_Year_Start_3"):
            db.execute("UPDATE Users SET Past_Year_Start_3 = :Past_Year_Start_3 WHERE ID = :ID", Past_Year_Start_3=request.form.get("Past_Year_Start_3"), ID=session["user_id"])
        if request.form.get("Past_Year_End_3"):
            db.execute("UPDATE Users SET Past_Year_End_3 = :Past_Year_End_3 WHERE ID = :ID", Past_Year_End_3=request.form.get("Past_Year_End_3"), ID=session["user_id"])
        if request.form.get("Past_Year_Start_4"):
            db.execute("UPDATE Users SET Past_Year_Start_4 = :Past_Year_Start_4 WHERE ID = :ID", Past_Year_Start_4=request.form.get("Past_Year_Start_4"), ID=session["user_id"])
        if request.form.get("Past_Year_End_4"):
            db.execute("UPDATE Users SET Past_Year_End_4 = :Past_Year_End_4 WHERE ID = :ID", Past_Year_End_4=request.form.get("Past_Year_End_4"), ID=session["user_id"])
        if request.form.get("Career_Position_Looking_For"):
            db.execute("UPDATE Users SET Career_Position_Looking_For = :Career_Position_Looking_For WHERE ID = :ID", Career_Position_Looking_For=request.form.get("Career_Position_Looking_For"), ID=session["user_id"])
        if request.form.get("Industry_Looking_Towards"):
            db.execute("UPDATE Users SET Industry_Looking_Towards = :Industry_Looking_Towards WHERE ID = :ID", Industry_Looking_Towards=request.form.get("Industry_Looking_Towards"), ID=session["user_id"])
        if request.form.get("Dream_Company"):
            db.execute("UPDATE Users SET Dream_Company = :Dream_Company WHERE ID = :ID", Dream_Company=request.form.get("Dream_Company"), ID=session["user_id"])
        if request.form.get("Miscellaneous"):
            db.execute("UPDATE Users SET Miscellaneous = :Miscellaneous WHERE ID = :ID", Miscellaneous=request.form.get("Miscellaneous"), ID=session["user_id"])

        # Render homepage after saving data
        return render_template("index.html")

@app.route("/similarities", methods=["GET", "POST"])
@login_required
def similarities():
    """ Presents list of profiles with image of people who have similarities- eventually make it so specific similarity is noted and can click on name to bring up profile"""

    # Save for each category the name, image, and category of match
    User_Info = db.execute("SELECT * FROM Users WHERE ID = :ID", ID=session["user_id"])

    # Initialize match row variables
    Current_Company_Match_Rows = None
    Second_Company_Match_Rows = None
    Third_Company_Match_Rows = None
    Post_College_Company_Match_Rows = None
    Past_Company_1_Match_Rows = None
    Past_Company_2_Match_Rows = None
    Past_Company_3_Match_Rows = None
    Past_Company_4_Match_Rows = None
    Dream_Company_Match_Rows = None
    Current_Title_1_Match_Rows = None
    Alternate_Title_1_Match_Rows = None
    Current_Title_2_Match_Rows = None
    Alternate_Title_2_Match_Rows = None
    Current_Title_3_Match_Rows = None
    Alternate_Title_3_Match_Rows = None
    Post_College_Job_Match_Rows = None
    Past_Position_1_Match_Rows = None
    Alternate_Past_Position_1_Match_Rows = None
    Past_Position_2_Match_Rows = None
    Alternate_Past_Position_2_Match_Rows = None
    Past_Position_3_Match_Rows = None
    Alternate_Past_Position_3_Match_Rows = None
    Past_Position_4_Match_Rows = None
    Alternate_Past_Position_4_Match_Rows = None
    Career_Position_Looking_For_Match_Rows = None
    Prep_School_Match_Rows = None
    Undergraduate_School_Match_Rows = None
    Undergraduate_School_2_Match_Rows = None
    Postgraduate_School_Match_Rows = None
    Postgraduate_School_2_Match_Rows = None
    Undergraduate_Graduation_Year_Match_Rows = None
    Undergraduate_Graduation_Year_2_Match_Rows = None
    Postgraduate_Graduation_Year_Match_Rows = None
    Postgraduate_Graduation_Year_2_Match_Rows = None
    Undergraduate_Major_Match_Rows = None
    Undergraduate_Major_1_2_Match_Rows = None
    Undergraduate_Major_1_3_Match_Rows = None
    Undergraduate_Major_2_Match_Rows = None
    Undergraduate_Major_2_2_Match_Rows = None
    Undergraduate_Major_2_3_Match_Rows = None
    Field_Match_Rows = None
    Field_2_Match_Rows = None
    Current_Industry_1_Match_Rows = None
    Current_Industry_2_Match_Rows = None
    Current_Industry_3_Match_Rows = None
    Initial_Career_Path_Interest_1_Match_Rows = None
    Initial_Career_Path_Interest_2_Match_Rows = None
    Industry_Looking_Towards_Match_Rows = None
    Born_Match_Rows = None

    # Match based on companies
    if User_Info[0]["Current_Company"] != None:
        Current_Company_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Current_Company_1=Current_Company OR :Current_Company_2=Second_Company OR :Current_Company_3=Third_Company OR :Current_Company_4=Past_Company_1 OR :Current_Company_5=Past_Company_2 OR :Current_Company_6=Past_Company_3 OR :Current_Company_7=Past_Company_4 OR :Current_Company_8=Post_College_Company", Current_Company_1=User_Info[0]["Current_Company"], Current_Company_2=User_Info[0]["Current_Company"], Current_Company_3=User_Info[0]["Current_Company"], Current_Company_4=User_Info[0]["Current_Company"], Current_Company_5=User_Info[0]["Current_Company"], Current_Company_6=User_Info[0]["Current_Company"], Current_Company_7=User_Info[0]["Current_Company"], Current_Company_8=User_Info[0]["Current_Company"])
    if User_Info[0]["Second_Company"] != None:
        Second_Company_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Second_Company_1=Current_Company OR :Second_Company_2=Second_Company OR :Second_Company_3=Third_Company OR :Second_Company_4=Past_Company_1 OR :Second_Company_5=Past_Company_2 OR :Second_Company_6=Past_Company_3 OR :Second_Company_7=Past_Company_4 OR :Second_Company_8=Post_College_Company", Second_Company_1=User_Info[0]["Second_Company"], Second_Company_2=User_Info[0]["Second_Company"], Second_Company_3=User_Info[0]["Second_Company"], Second_Company_4=User_Info[0]["Second_Company"], Second_Company_5=User_Info[0]["Second_Company"], Second_Company_6=User_Info[0]["Second_Company"], Second_Company_7=User_Info[0]["Second_Company"], Second_Company_8=User_Info[0]["Second_Company"])
    if User_Info[0]["Third_Company"] != None:
        Third_Company_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Third_Company_1=Current_Company OR :Third_Company_2=Second_Company OR :Third_Company_3=Third_Company OR :Third_Company_4=Past_Company_1 OR :Third_Company_5=Past_Company_2 OR :Third_Company_6=Past_Company_3 OR :Third_Company_7=Past_Company_4 OR :Third_Company_8=Post_College_Company", Third_Company_1=User_Info[0]["Third_Company"], Third_Company_2=User_Info[0]["Third_Company"], Third_Company_3=User_Info[0]["Third_Company"], Third_Company_4=User_Info[0]["Third_Company"], Third_Company_5=User_Info[0]["Third_Company"], Third_Company_6=User_Info[0]["Third_Company"], Third_Company_7=User_Info[0]["Third_Company"], Third_Company_8=User_Info[0]["Third_Company"])
    if User_Info[0]["Past_Company_1"] != None:
        Past_Company_1_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Past_Company_1_1=Current_Company OR :Past_Company_1_2=Second_Company OR :Past_Company_1_3=Third_Company OR :Past_Company_1_4=Past_Company_1 OR :Past_Company_1_5=Past_Company_2 OR :Past_Company_1_6=Past_Company_3 OR :Past_Company_1_7=Past_Company_4 OR :Past_Company_1_8=Post_College_Company", Past_Company_1_1=User_Info[0]["Past_Company_1"], Past_Company_1_2=User_Info[0]["Past_Company_1"], Past_Company_1_3=User_Info[0]["Past_Company_1"], Past_Company_1_4=User_Info[0]["Past_Company_1"], Past_Company_1_5=User_Info[0]["Past_Company_1"], Past_Company_1_6=User_Info[0]["Past_Company_1"], Past_Company_1_7=User_Info[0]["Past_Company_1"], Past_Company_1_8=User_Info[0]["Past_Company_1"])
    if User_Info[0]["Past_Company_2"] != None:
        Past_Company_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Past_Company_2_1=Current_Company OR :Past_Company_2_2=Second_Company OR :Past_Company_2_3=Third_Company OR :Past_Company_2_4=Past_Company_1 OR :Past_Company_2_5=Past_Company_2 OR :Past_Company_2_6=Past_Company_3 OR :Past_Company_2_7=Past_Company_4 OR :Past_Company_2_8=Post_College_Company", Past_Company_2_1=User_Info[0]["Past_Company_2"], Past_Company_2_2=User_Info[0]["Past_Company_2"], Past_Company_2_3=User_Info[0]["Past_Company_2"], Past_Company_2_4=User_Info[0]["Past_Company_2"], Past_Company_2_5=User_Info[0]["Past_Company_2"], Past_Company_2_6=User_Info[0]["Past_Company_2"], Past_Company_2_7=User_Info[0]["Past_Company_2"], Past_Company_2_8=User_Info[0]["Past_Company_2"])
    if User_Info[0]["Past_Company_3"] != None:
        Past_Company_3_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Past_Company_3_1=Current_Company OR :Past_Company_3_2=Second_Company OR :Past_Company_3_3=Third_Company OR :Past_Company_3_4=Past_Company_1 OR :Past_Company_3_5=Past_Company_2 OR :Past_Company_3_6=Past_Company_3 OR :Past_Company_3_7=Past_Company_4 OR :Past_Company_3_8=Post_College_Company", Past_Company_3_1=User_Info[0]["Past_Company_3"], Past_Company_3_2=User_Info[0]["Past_Company_3"], Past_Company_3_3=User_Info[0]["Past_Company_3"], Past_Company_3_4=User_Info[0]["Past_Company_3"], Past_Company_3_5=User_Info[0]["Past_Company_3"], Past_Company_3_6=User_Info[0]["Past_Company_3"], Past_Company_3_7=User_Info[0]["Past_Company_3"], Past_Company_3_8=User_Info[0]["Past_Company_3"])
    if User_Info[0]["Past_Company_4"] != None:
        Past_Company_4_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Past_Company_4_1=Current_Company OR :Past_Company_4_2=Second_Company OR :Past_Company_4_3=Third_Company OR :Past_Company_4_4=Past_Company_1 OR :Past_Company_4_5=Past_Company_2 OR :Past_Company_4_6=Past_Company_3 OR :Past_Company_4_7=Past_Company_4 OR :Past_Company_4_8=Post_College_Company", Past_Company_4_1=User_Info[0]["Past_Company_4"], Past_Company_4_2=User_Info[0]["Past_Company_4"], Past_Company_4_3=User_Info[0]["Past_Company_4"], Past_Company_4_4=User_Info[0]["Past_Company_4"], Past_Company_4_5=User_Info[0]["Past_Company_4"], Past_Company_4_6=User_Info[0]["Past_Company_4"], Past_Company_4_7=User_Info[0]["Past_Company_4"], Past_Company_4_8=User_Info[0]["Past_Company_4"])
    if User_Info[0]["Dream_Company"] != None:
        Dream_Company_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Dream_Company_1=Current_Company OR :Dream_Company_2=Second_Company OR :Dream_Company_3=Third_Company OR :Dream_Company_4=Past_Company_1 OR :Dream_Company_5=Past_Company_2 OR :Dream_Company_6=Past_Company_3 OR :Dream_Company_7=Past_Company_4 OR :Dream_Company_8=Post_College_Company", Dream_Company_1=User_Info[0]["Dream_Company"], Dream_Company_2=User_Info[0]["Dream_Company"], Dream_Company_3=User_Info[0]["Dream_Company"], Dream_Company_4=User_Info[0]["Dream_Company"], Dream_Company_5=User_Info[0]["Dream_Company"], Dream_Company_6=User_Info[0]["Dream_Company"], Dream_Company_7=User_Info[0]["Dream_Company"], Dream_Company_8=User_Info[0]["Dream_Company"])
    if User_Info[0]["Post_College_Company"] != None:
        Post_College_Company_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Post_College_Company_1=Current_Company OR :Post_College_Company_2=Second_Company OR :Post_College_Company_3=Third_Company OR :Post_College_Company_4=Past_Company_1 OR :Post_College_Company_5=Past_Company_2 OR :Post_College_Company_6=Past_Company_3 OR :Post_College_Company_7=Past_Company_4 OR :Post_College_Company_8=Post_College_Company", Post_College_Company_1=User_Info[0]["Post_College_Company"], Post_College_Company_2=User_Info[0]["Post_College_Company"], Post_College_Company_3=User_Info[0]["Post_College_Company"], Post_College_Company_4=User_Info[0]["Post_College_Company"], Post_College_Company_5=User_Info[0]["Post_College_Company"], Post_College_Company_6=User_Info[0]["Post_College_Company"], Post_College_Company_7=User_Info[0]["Post_College_Company"], Post_College_Company_8=User_Info[0]["Post_College_Company"])

    # Match based on position title
    if User_Info[0]["Current_Title_1"] != None:
        Current_Title_1_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Current_Title_1_1=Current_Title_1 OR :Current_Title_1_2=Alternate_Title_1 OR :Current_Title_1_3=Alternate_Title_1_2 OR :Current_Title_1_4=Current_Title_2 OR :Current_Title_1_5=Alternate_Title_2 OR :Current_Title_1_6=Alternate_Title_2_2 OR :Current_Title_1_7=Current_Title_3 OR :Current_Title_1_8=Alternate_Title_3 OR :Current_Title_1_9=Alternate_Title_3_2 OR :Current_Title_1_10=Post_College_Job OR :Current_Title_1_11=Past_Position_1 OR :Current_Title_1_12=Alternate_Past_Position_1 OR :Current_Title_1_13=Alternate_Past_Position_1_2 OR :Current_Title_1_14=Past_Position_2 OR :Current_Title_1_15=Alternate_Past_Position_2 OR :Current_Title_1_16=Alternate_Past_Position_2_2 OR :Current_Title_1_17=Past_Position_3 OR :Current_Title_1_18=Alternate_Past_Position_3 OR :Current_Title_1_19=Alternate_Past_Position_3_2 OR :Current_Title_1_20=Past_Position_4 OR :Current_Title_1_21=Alternate_Past_Position_4 OR :Current_Title_1_22=Alternate_Past_Position_4_2", Current_Title_1_1=User_Info[0]["Current_Title_1"], Current_Title_1_2=User_Info[0]["Current_Title_1"], Current_Title_1_3=User_Info[0]["Current_Title_1"], Current_Title_1_4=User_Info[0]["Current_Title_1"], Current_Title_1_5=User_Info[0]["Current_Title_1"], Current_Title_1_6=User_Info[0]["Current_Title_1"], Current_Title_1_7=User_Info[0]["Current_Title_1"], Current_Title_1_8=User_Info[0]["Current_Title_1"], Current_Title_1_9=User_Info[0]["Current_Title_1"], Current_Title_1_10=User_Info[0]["Current_Title_1"], Current_Title_1_11=User_Info[0]["Current_Title_1"], Current_Title_1_12=User_Info[0]["Current_Title_1"], Current_Title_1_13=User_Info[0]["Current_Title_1"], Current_Title_1_14=User_Info[0]["Current_Title_1"], Current_Title_1_15=User_Info[0]["Current_Title_1"], Current_Title_1_16=User_Info[0]["Current_Title_1"], Current_Title_1_17=User_Info[0]["Current_Title_1"], Current_Title_1_18=User_Info[0]["Current_Title_1"], Current_Title_1_19=User_Info[0]["Current_Title_1"], Current_Title_1_20=User_Info[0]["Current_Title_1"], Current_Title_1_21=User_Info[0]["Current_Title_1"], Current_Title_1_22=User_Info[0]["Current_Title_1"])
    if User_Info[0]["Alternate_Title_1"] != None:
        Alternate_Title_1_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Alternate_Title_1_1=Current_Title_1 OR :Alternate_Title_1_2=Alternate_Title_1 OR :Alternate_Title_1_3=Alternate_Title_1_2 OR :Alternate_Title_1_4=Current_Title_2 OR :Alternate_Title_1_5=Alternate_Title_2 OR :Alternate_Title_1_6=Alternate_Title_2_2 OR :Alternate_Title_1_7=Current_Title_3 OR :Alternate_Title_1_8=Alternate_Title_3 OR :Alternate_Title_1_9=Alternate_Title_3_2 OR :Alternate_Title_1_10=Post_College_Job OR :Alternate_Title_1_11=Past_Position_1 OR :Alternate_Title_1_12=Alternate_Past_Position_1 OR :Alternate_Title_1_13=Alternate_Past_Position_1_2 OR :Alternate_Title_1_14=Past_Position_2 OR :Alternate_Title_1_15=Alternate_Past_Position_2 OR :Alternate_Title_1_16=Alternate_Past_Position_2_2 OR :Alternate_Title_1_17=Past_Position_3 OR :Alternate_Title_1_18=Alternate_Past_Position_3 OR :Alternate_Title_1_19=Alternate_Past_Position_3_2 OR :Alternate_Title_1_20=Past_Position_4 OR :Alternate_Title_1_21=Alternate_Past_Position_4 OR :Alternate_Title_1_22=Alternate_Past_Position_4_2", Alternate_Title_1_1=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_2=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_3=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_4=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_5=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_6=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_7=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_8=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_9=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_10=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_11=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_12=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_13=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_14=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_15=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_16=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_17=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_18=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_19=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_20=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_21=User_Info[0]["Alternate_Title_1"], Alternate_Title_1_22=User_Info[0]["Alternate_Title_1"])
    if User_Info[0]["Current_Title_2"] != None:
        Current_Title_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Current_Title_2_1=Current_Title_1 OR :Current_Title_2_2=Alternate_Title_1 OR :Current_Title_2_3=Alternate_Title_1_2 OR :Current_Title_2_4=Current_Title_2 OR :Current_Title_2_5=Alternate_Title_2 OR :Current_Title_2_6=Alternate_Title_2_2 OR :Current_Title_2_7=Current_Title_3 OR :Current_Title_2_8=Alternate_Title_3 OR :Current_Title_2_9=Alternate_Title_3_2 OR :Current_Title_2_10=Post_College_Job OR :Current_Title_2_11=Past_Position_1 OR :Current_Title_2_12=Alternate_Past_Position_1 OR :Current_Title_2_13=Alternate_Past_Position_1_2 OR :Current_Title_2_14=Past_Position_2 OR :Current_Title_2_15=Alternate_Past_Position_2 OR :Current_Title_2_16=Alternate_Past_Position_2_2 OR :Current_Title_2_17=Past_Position_3 OR :Current_Title_2_18=Alternate_Past_Position_3 OR :Current_Title_2_19=Alternate_Past_Position_3_2 OR :Current_Title_2_20=Past_Position_4 OR :Current_Title_2_21=Alternate_Past_Position_4 OR :Current_Title_2_22=Alternate_Past_Position_4_2", Current_Title_2_1=User_Info[0]["Current_Title_2"], Current_Title_2_2=User_Info[0]["Current_Title_2"], Current_Title_2_3=User_Info[0]["Current_Title_2"], Current_Title_2_4=User_Info[0]["Current_Title_2"], Current_Title_2_5=User_Info[0]["Current_Title_2"], Current_Title_2_6=User_Info[0]["Current_Title_2"], Current_Title_2_7=User_Info[0]["Current_Title_2"], Current_Title_2_8=User_Info[0]["Current_Title_2"], Current_Title_2_9=User_Info[0]["Current_Title_2"], Current_Title_2_10=User_Info[0]["Current_Title_2"], Current_Title_2_11=User_Info[0]["Current_Title_2"], Current_Title_2_12=User_Info[0]["Current_Title_2"], Current_Title_2_13=User_Info[0]["Current_Title_2"], Current_Title_2_14=User_Info[0]["Current_Title_2"], Current_Title_2_15=User_Info[0]["Current_Title_2"], Current_Title_2_16=User_Info[0]["Current_Title_2"], Current_Title_2_17=User_Info[0]["Current_Title_2"], Current_Title_2_18=User_Info[0]["Current_Title_2"], Current_Title_2_19=User_Info[0]["Current_Title_2"], Current_Title_2_20=User_Info[0]["Current_Title_2"], Current_Title_2_21=User_Info[0]["Current_Title_2"], Current_Title_2_22=User_Info[0]["Current_Title_2"])
    if User_Info[0]["Alternate_Title_2"] != None:
        Alternate_Title_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Alternate_Title_2_1=Current_Title_1 OR :Alternate_Title_2_2=Alternate_Title_1 OR :Alternate_Title_2_3=Alternate_Title_1_2 OR :Alternate_Title_2_4=Current_Title_2 OR :Alternate_Title_2_5=Alternate_Title_2 OR :Alternate_Title_2_6=Alternate_Title_2_2 OR :Alternate_Title_2_7=Current_Title_3 OR :Alternate_Title_2_8=Alternate_Title_3 OR :Alternate_Title_2_9=Alternate_Title_3_2 OR :Alternate_Title_2_10=Post_College_Job OR :Alternate_Title_2_11=Past_Position_1 OR :Alternate_Title_2_12=Alternate_Past_Position_1 OR :Alternate_Title_2_13=Alternate_Past_Position_1_2 OR :Alternate_Title_2_14=Past_Position_2 OR :Alternate_Title_2_15=Alternate_Past_Position_2 OR :Alternate_Title_2_16=Alternate_Past_Position_2_2 OR :Alternate_Title_2_17=Past_Position_3 OR :Alternate_Title_2_18=Alternate_Past_Position_3 OR :Alternate_Title_2_19=Alternate_Past_Position_3_2 OR :Alternate_Title_2_20=Past_Position_4 OR :Alternate_Title_2_21=Alternate_Past_Position_4 OR :Alternate_Title_2_22=Alternate_Past_Position_4_2", Alternate_Title_2_1=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_2=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_3=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_4=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_5=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_6=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_7=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_8=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_9=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_10=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_11=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_12=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_13=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_14=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_15=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_16=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_17=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_18=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_19=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_20=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_21=User_Info[0]["Alternate_Title_2"], Alternate_Title_2_22=User_Info[0]["Alternate_Title_2"])
    if User_Info[0]["Current_Title_3"] != None:
        Current_Title_3_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Current_Title_3_1=Current_Title_1 OR :Current_Title_3_2=Alternate_Title_1 OR :Current_Title_3_3=Alternate_Title_1_2 OR :Current_Title_3_4=Current_Title_2 OR :Current_Title_3_5=Alternate_Title_2 OR :Current_Title_3_6=Alternate_Title_2_2 OR :Current_Title_3_7=Current_Title_3 OR :Current_Title_3_8=Alternate_Title_3 OR :Current_Title_3_9=Alternate_Title_3_2 OR :Current_Title_3_10=Post_College_Job OR :Current_Title_3_11=Past_Position_1 OR :Current_Title_3_12=Alternate_Past_Position_1 OR :Current_Title_3_13=Alternate_Past_Position_1_2 OR :Current_Title_3_14=Past_Position_2 OR :Current_Title_3_15=Alternate_Past_Position_2 OR :Current_Title_3_16=Alternate_Past_Position_2_2 OR :Current_Title_3_17=Past_Position_3 OR :Current_Title_3_18=Alternate_Past_Position_3 OR :Current_Title_3_19=Alternate_Past_Position_3_2 OR :Current_Title_3_20=Past_Position_4 OR :Current_Title_3_21=Alternate_Past_Position_4 OR :Current_Title_3_22=Alternate_Past_Position_4_2", Current_Title_3_1=User_Info[0]["Current_Title_3"], Current_Title_3_2=User_Info[0]["Current_Title_3"], Current_Title_3_3=User_Info[0]["Current_Title_3"], Current_Title_3_4=User_Info[0]["Current_Title_3"], Current_Title_3_5=User_Info[0]["Current_Title_3"], Current_Title_3_6=User_Info[0]["Current_Title_3"], Current_Title_3_7=User_Info[0]["Current_Title_3"], Current_Title_3_8=User_Info[0]["Current_Title_3"], Current_Title_3_9=User_Info[0]["Current_Title_3"], Current_Title_3_10=User_Info[0]["Current_Title_3"], Current_Title_3_11=User_Info[0]["Current_Title_3"], Current_Title_3_12=User_Info[0]["Current_Title_3"], Current_Title_3_13=User_Info[0]["Current_Title_3"], Current_Title_3_14=User_Info[0]["Current_Title_3"], Current_Title_3_15=User_Info[0]["Current_Title_3"], Current_Title_3_16=User_Info[0]["Current_Title_3"], Current_Title_3_17=User_Info[0]["Current_Title_3"], Current_Title_3_18=User_Info[0]["Current_Title_3"], Current_Title_3_19=User_Info[0]["Current_Title_3"], Current_Title_3_20=User_Info[0]["Current_Title_3"], Current_Title_3_21=User_Info[0]["Current_Title_3"], Current_Title_3_22=User_Info[0]["Current_Title_3"])
    if User_Info[0]["Alternate_Title_3"] != None:
        Alternate_Title_3_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Alternate_Title_3_1=Current_Title_1 OR :Alternate_Title_3_2=Alternate_Title_1 OR :Alternate_Title_3_3=Alternate_Title_1_2 OR :Alternate_Title_3_4=Current_Title_2 OR :Alternate_Title_3_5=Alternate_Title_2 OR :Alternate_Title_3_6=Alternate_Title_2_2 OR :Alternate_Title_3_7=Current_Title_3 OR :Alternate_Title_3_8=Alternate_Title_3 OR :Alternate_Title_3_9=Alternate_Title_3_2 OR :Alternate_Title_3_10=Post_College_Job OR :Alternate_Title_3_11=Past_Position_1 OR :Alternate_Title_3_12=Alternate_Past_Position_1 OR :Alternate_Title_3_13=Alternate_Past_Position_1_2 OR :Alternate_Title_3_14=Past_Position_2 OR :Alternate_Title_3_15=Alternate_Past_Position_2 OR :Alternate_Title_3_16=Alternate_Past_Position_2_2 OR :Alternate_Title_3_17=Past_Position_3 OR :Alternate_Title_3_18=Alternate_Past_Position_3 OR :Alternate_Title_3_19=Alternate_Past_Position_3_2 OR :Alternate_Title_3_20=Past_Position_4 OR :Alternate_Title_3_21=Alternate_Past_Position_4 OR :Alternate_Title_3_22=Alternate_Past_Position_4_2", Alternate_Title_3_1=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_2=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_3=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_4=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_5=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_6=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_7=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_8=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_9=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_10=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_11=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_12=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_13=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_14=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_15=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_16=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_17=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_18=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_19=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_20=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_21=User_Info[0]["Alternate_Title_3"], Alternate_Title_3_22=User_Info[0]["Alternate_Title_3"])
    if User_Info[0]["Post_College_Job"] != None:
        Post_College_Job_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Post_College_Job_1=Current_Title_1 OR :Post_College_Job_2=Alternate_Title_1 OR :Post_College_Job_3=Alternate_Title_1_2 OR :Post_College_Job_4=Current_Title_2 OR :Post_College_Job_5=Alternate_Title_2 OR :Post_College_Job_6=Alternate_Title_2_2 OR :Post_College_Job_7=Current_Title_3 OR :Post_College_Job_8=Alternate_Title_3 OR :Post_College_Job_9=Alternate_Title_3_2 OR :Post_College_Job_10=Post_College_Job OR :Post_College_Job_11=Past_Position_1 OR :Post_College_Job_12=Alternate_Past_Position_1 OR :Post_College_Job_13=Alternate_Past_Position_1_2 OR :Post_College_Job_14=Past_Position_2 OR :Post_College_Job_15=Alternate_Past_Position_2 OR :Post_College_Job_16=Alternate_Past_Position_2_2 OR :Post_College_Job_17=Past_Position_3 OR :Post_College_Job_18=Alternate_Past_Position_3 OR :Post_College_Job_19=Alternate_Past_Position_3_2 OR :Post_College_Job_20=Past_Position_4 OR :Post_College_Job_21=Alternate_Past_Position_4 OR :Post_College_Job_22=Alternate_Past_Position_4_2", Post_College_Job_1=User_Info[0]["Post_College_Job"], Post_College_Job_2=User_Info[0]["Post_College_Job"], Post_College_Job_3=User_Info[0]["Post_College_Job"], Post_College_Job_4=User_Info[0]["Post_College_Job"], Post_College_Job_5=User_Info[0]["Post_College_Job"], Post_College_Job_6=User_Info[0]["Post_College_Job"], Post_College_Job_7=User_Info[0]["Post_College_Job"], Post_College_Job_8=User_Info[0]["Post_College_Job"], Post_College_Job_9=User_Info[0]["Post_College_Job"], Post_College_Job_10=User_Info[0]["Post_College_Job"], Post_College_Job_11=User_Info[0]["Post_College_Job"], Post_College_Job_12=User_Info[0]["Post_College_Job"], Post_College_Job_13=User_Info[0]["Post_College_Job"], Post_College_Job_14=User_Info[0]["Post_College_Job"], Post_College_Job_15=User_Info[0]["Post_College_Job"], Post_College_Job_16=User_Info[0]["Post_College_Job"], Post_College_Job_17=User_Info[0]["Post_College_Job"], Post_College_Job_18=User_Info[0]["Post_College_Job"], Post_College_Job_19=User_Info[0]["Post_College_Job"], Post_College_Job_20=User_Info[0]["Post_College_Job"], Post_College_Job_21=User_Info[0]["Post_College_Job"], Post_College_Job_22=User_Info[0]["Post_College_Job"])
    if User_Info[0]["Past_Position_1"] != None:
        Past_Position_1_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Past_Position_1_1=Current_Title_1 OR :Past_Position_1_2=Alternate_Title_1 OR :Past_Position_1_3=Alternate_Title_1_2 OR :Past_Position_1_4=Current_Title_2 OR :Past_Position_1_5=Alternate_Title_2 OR :Past_Position_1_6=Alternate_Title_2_2 OR :Past_Position_1_7=Current_Title_3 OR :Past_Position_1_8=Alternate_Title_3 OR :Past_Position_1_9=Alternate_Title_3_2 OR :Past_Position_1_10=Post_College_Job OR :Past_Position_1_11=Past_Position_1 OR :Past_Position_1_12=Alternate_Past_Position_1 OR :Past_Position_1_13=Alternate_Past_Position_1_2 OR :Past_Position_1_14=Past_Position_2 OR :Past_Position_1_15=Alternate_Past_Position_2 OR :Past_Position_1_16=Alternate_Past_Position_2_2 OR :Past_Position_1_17=Past_Position_3 OR :Past_Position_1_18=Alternate_Past_Position_3 OR :Past_Position_1_19=Alternate_Past_Position_3_2 OR :Past_Position_1_20=Past_Position_4 OR :Past_Position_1_21=Alternate_Past_Position_4 OR :Past_Position_1_22=Alternate_Past_Position_4_2", Past_Position_1_1=User_Info[0]["Past_Position_1"], Past_Position_1_2=User_Info[0]["Past_Position_1"], Past_Position_1_3=User_Info[0]["Past_Position_1"], Past_Position_1_4=User_Info[0]["Past_Position_1"], Past_Position_1_5=User_Info[0]["Past_Position_1"], Past_Position_1_6=User_Info[0]["Past_Position_1"], Past_Position_1_7=User_Info[0]["Past_Position_1"], Past_Position_1_8=User_Info[0]["Past_Position_1"], Past_Position_1_9=User_Info[0]["Past_Position_1"], Past_Position_1_10=User_Info[0]["Past_Position_1"], Past_Position_1_11=User_Info[0]["Past_Position_1"], Past_Position_1_12=User_Info[0]["Past_Position_1"], Past_Position_1_13=User_Info[0]["Past_Position_1"], Past_Position_1_14=User_Info[0]["Past_Position_1"], Past_Position_1_15=User_Info[0]["Past_Position_1"], Past_Position_1_16=User_Info[0]["Past_Position_1"], Past_Position_1_17=User_Info[0]["Past_Position_1"], Past_Position_1_18=User_Info[0]["Past_Position_1"], Past_Position_1_19=User_Info[0]["Past_Position_1"], Past_Position_1_20=User_Info[0]["Past_Position_1"], Past_Position_1_21=User_Info[0]["Past_Position_1"], Past_Position_1_22=User_Info[0]["Past_Position_1"])
    if User_Info[0]["Alternate_Past_Position_1"] != None:
        Alternate_Past_Position_1_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Alternate_Past_Position_1_1=Current_Title_1 OR :Alternate_Past_Position_1_2=Alternate_Title_1 OR :Alternate_Past_Position_1_3=Alternate_Title_1_2 OR :Alternate_Past_Position_1_4=Current_Title_2 OR :Alternate_Past_Position_1_5=Alternate_Title_2 OR :Alternate_Past_Position_1_6=Alternate_Title_2_2 OR :Alternate_Past_Position_1_7=Current_Title_3 OR :Alternate_Past_Position_1_8=Alternate_Title_3 OR :Alternate_Past_Position_1_9=Alternate_Title_3_2 OR :Alternate_Past_Position_1_10=Post_College_Job OR :Alternate_Past_Position_1_11=Past_Position_1 OR :Alternate_Past_Position_1_12=Alternate_Past_Position_1 OR :Alternate_Past_Position_1_13=Alternate_Past_Position_1_2 OR :Alternate_Past_Position_1_14=Past_Position_2 OR :Alternate_Past_Position_1_15=Alternate_Past_Position_2 OR :Alternate_Past_Position_1_16=Alternate_Past_Position_2_2 OR :Alternate_Past_Position_1_17=Past_Position_3 OR :Alternate_Past_Position_1_18=Alternate_Past_Position_3 OR :Alternate_Past_Position_1_19=Alternate_Past_Position_3_2 OR :Alternate_Past_Position_1_20=Past_Position_4 OR :Alternate_Past_Position_1_21=Alternate_Past_Position_4 OR :Alternate_Past_Position_1_22=Alternate_Past_Position_4_2", Alternate_Past_Position_1_1=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_2=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_3=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_4=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_5=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_6=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_7=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_8=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_9=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_10=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_11=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_12=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_13=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_14=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_15=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_16=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_17=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_18=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_19=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_20=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_21=User_Info[0]["Alternate_Past_Position_1"], Alternate_Past_Position_1_22=User_Info[0]["Alternate_Past_Position_1"])
    if User_Info[0]["Past_Position_2"] != None:
        Past_Position_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Past_Position_2_1=Current_Title_1 OR :Past_Position_2_2=Alternate_Title_1 OR :Past_Position_2_3=Alternate_Title_1_2 OR :Past_Position_2_4=Current_Title_2 OR :Past_Position_2_5=Alternate_Title_2 OR :Past_Position_2_6=Alternate_Title_2_2 OR :Past_Position_2_7=Current_Title_3 OR :Past_Position_2_8=Alternate_Title_3 OR :Past_Position_2_9=Alternate_Title_3_2 OR :Past_Position_2_10=Post_College_Job OR :Past_Position_2_11=Past_Position_1 OR :Past_Position_2_12=Alternate_Past_Position_1 OR :Past_Position_2_13=Alternate_Past_Position_1_2 OR :Past_Position_2_14=Past_Position_2 OR :Past_Position_2_15=Alternate_Past_Position_2 OR :Past_Position_2_16=Alternate_Past_Position_2_2 OR :Past_Position_2_17=Past_Position_3 OR :Past_Position_2_18=Alternate_Past_Position_3 OR :Past_Position_2_19=Alternate_Past_Position_3_2 OR :Past_Position_2_20=Past_Position_4 OR :Past_Position_2_21=Alternate_Past_Position_4 OR :Past_Position_2_22=Alternate_Past_Position_4_2", Past_Position_2_1=User_Info[0]["Past_Position_2"], Past_Position_2_2=User_Info[0]["Past_Position_2"], Past_Position_2_3=User_Info[0]["Past_Position_2"], Past_Position_2_4=User_Info[0]["Past_Position_2"], Past_Position_2_5=User_Info[0]["Past_Position_2"], Past_Position_2_6=User_Info[0]["Past_Position_2"], Past_Position_2_7=User_Info[0]["Past_Position_2"], Past_Position_2_8=User_Info[0]["Past_Position_2"], Past_Position_2_9=User_Info[0]["Past_Position_2"], Past_Position_2_10=User_Info[0]["Past_Position_2"], Past_Position_2_11=User_Info[0]["Past_Position_2"], Past_Position_2_12=User_Info[0]["Past_Position_2"], Past_Position_2_13=User_Info[0]["Past_Position_2"], Past_Position_2_14=User_Info[0]["Past_Position_2"], Past_Position_2_15=User_Info[0]["Past_Position_2"], Past_Position_2_16=User_Info[0]["Past_Position_2"], Past_Position_2_17=User_Info[0]["Past_Position_2"], Past_Position_2_18=User_Info[0]["Past_Position_2"], Past_Position_2_19=User_Info[0]["Past_Position_2"], Past_Position_2_20=User_Info[0]["Past_Position_2"], Past_Position_2_21=User_Info[0]["Past_Position_2"], Past_Position_2_22=User_Info[0]["Past_Position_2"])
    if User_Info[0]["Alternate_Past_Position_2"] != None:
        Alternate_Past_Position_2_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Alternate_Past_Position_2_1=Current_Title_1 OR :Alternate_Past_Position_2_2=Alternate_Title_1 OR :Alternate_Past_Position_2_3=Alternate_Title_1_2 OR :Alternate_Past_Position_2_4=Current_Title_2 OR :Alternate_Past_Position_2_5=Alternate_Title_2 OR :Alternate_Past_Position_2_6=Alternate_Title_2_2 OR :Alternate_Past_Position_2_7=Current_Title_3 OR :Alternate_Past_Position_2_8=Alternate_Title_3 OR :Alternate_Past_Position_2_9=Alternate_Title_3_2 OR :Alternate_Past_Position_2_10=Post_College_Job OR :Alternate_Past_Position_2_11=Past_Position_1 OR :Alternate_Past_Position_2_12=Alternate_Past_Position_1 OR :Alternate_Past_Position_2_13=Alternate_Past_Position_1_2 OR :Alternate_Past_Position_2_14=Past_Position_2 OR :Alternate_Past_Position_2_15=Alternate_Past_Position_2 OR :Alternate_Past_Position_2_16=Alternate_Past_Position_2_2 OR :Alternate_Past_Position_2_17=Past_Position_3 OR :Alternate_Past_Position_2_18=Alternate_Past_Position_3 OR :Alternate_Past_Position_2_19=Alternate_Past_Position_3_2 OR :Alternate_Past_Position_2_20=Past_Position_4 OR :Alternate_Past_Position_2_21=Alternate_Past_Position_4 OR :Alternate_Past_Position_2_22=Alternate_Past_Position_4_2", Alternate_Past_Position_2_1=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_2=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_3=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_4=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_5=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_6=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_7=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_8=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_9=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_10=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_11=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_12=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_13=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_14=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_15=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_16=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_17=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_18=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_19=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_20=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_21=User_Info[0]["Alternate_Past_Position_2"], Alternate_Past_Position_2_22=User_Info[0]["Alternate_Past_Position_2"])
    if User_Info[0]["Past_Position_3"] != None:
        Past_Position_3_Match_Rows = db.execute("SELECT Full_Name,Image FROM Profiles WHERE :Past_Position_3_1=Current_Title_1 OR :Past_Position_3_2=Alternate_Title_1 OR :Past_Position_3_3=Alternate_Title_1_2 OR :Past_Position_3_4=Current_Title_2 OR :Past_Position_3_5=Alternate_Title_2 OR :Past_Position_3_6=Alternate_Title_2_2 OR :Past_Position_3_7=Current_Title_3 OR :Past_Position_3_8=Alternate_Title_3 OR :Past_Position_3_9=Alternate_Title_3_2 OR :Past_Position_3_10=Post_College_Job OR :Past_Position_3_11=Past_Position_1 OR :Past_Position_3_12=Alternate_Past_Position_1 OR :Past_Position_3_13=Alternate_Past_Position_1_2 OR :Past_Position_3_14=Past_Position_2 OR :Past_Position_3_15=Alternate_Past_Position_2 OR :Past_Position_3_16=Alternate_Past_Position_2_2 OR :Past_Position_3_17=Past_Position_3 OR :Past_Position_3_18=Alternate_Past_Position_3 OR :Past_Position_3_19=Alternate_Past_Position_3_2 OR :Past_Position_3_20=Past_Position_4 OR :Past_Position_3_21=Alternate_Past_Position_4 OR :Past_Position_3_22=Alternate_Past_Position_4_2", Past_Position_3_1=User_Info[0]["Past_Position_3"], Past_Position_3_2=User_Info[0]["Past_Position_3"], Past_Position_3_3=User_Info[0]["Past_Position_3"], Past_Position_3_4=User_Info[0]["Past_Position_3"], Past_Position_3_5=User_Info[0]["Past_Position_3"], Past_Position_3_6=User_Info[0]["Past_Position_3"], Past_Position_3_7=User_Info[0]["Past_Position_3"], Past_Position_3_8=User_Info[0]["Past_Position_3"], Past_Position_3_9=User_Info[0]["Past_Position_3"], Past_Position_3_10=User_Info[0]["Past_Position_3"], Past_Position_3_11=User_Info[0]["Past_Position_3"], Past_Position_3_12=User_Info[0]["Past_Position_3"], Past_Position_3_13=User_Info[0]["Past_Position_3"], Past_Position_3_14=User_Info[0]["Past_Position_3"], Past_Position_3_15=User_Info[0]["Past_Position_3"], Past_Position_3_16=User_Info[0]["Past_Position_3"], Past_Position_3_17=User_Info[0]["Past_Position_3"], Past_Position_3_18=User_Info[0]["Past_Position_3"], Past_Position_3_19=User_Info[0]["Past_Position_3"], Past_Position_3_20=User_Info[0]["Past_Position_3"], Past_Position_3_21=User_Info[0]["Past_Position_3"], Past_Position_3_22=User_Info[0]["Past_Position_3"])
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

