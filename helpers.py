from flask import redirect, render_template, request, session, url_for
from functools import wraps
# from cs50 import SQL

import os
import sqlalchemy
import psycopg2

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])

conn = psycopg2.connect(
   database=url.path[1:],
   user=url.username,
   password=url.password,
   host=url.hostname,
   port=url.port
)

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

# configure CS50 Library to use SQLite database
db = SQL(os.environ["DATABASE_URL"])

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
