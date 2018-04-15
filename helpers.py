from flask import redirect, render_template, request, session, url_for
from functools import wraps
from cs50 import SQL

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///timeline.db")

def apology(text):
    """Renders message as an apology to user."""
    return render_template("apology.html", text=text)

def login_required(f):
    """
    Decorate routes to require login.
    
    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function