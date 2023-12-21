# pylint: disable=wrong-import-position, wrong-import-order, missing-function-docstring
import os
import hashlib

from dotenv import load_dotenv

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from flask_mysqldb import MySQL
import MySQLdb.cursors

from helpers import login_required
from datetime import datetime

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST")
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD")
app.config["MYSQL_DB"] = os.getenv("MYSQL_DB")


mysql = MySQL(app)


# set the connection to the database
# def sql_open():
#     con = sql.connect("tmp/database2.db")
#     con.row_factory = sql.Row

#     return con


# base route
@app.route("/")
def root():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(
        "SELECT * FROM ruts WHERE public= %s AND solved = %s",
        (
            1,
            0,
        ),
    )
    data = cur.fetchall()
    cur.close()
    return render_template("landing.html", data=data)

    # OLD VERSION WITH SQLITE WITH LOCAL DATABASE
    # con = sql_open()
    # cursor = con.cursor()
    # cursor.execute(
    #     "SELECT * FROM ruts WHERE public=? AND solved = ?", ("true", "false")
    # )
    # data = cursor.fetchall()
    # cursor.close()
    # return render_template("landing.html", data=data)


# route for logging in
@app.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        # get input from user
        username = request.form.get("username")
        password = request.form.get("password")
        # get hash from inputed password
        hashed_pw = hashlib.md5(password.encode()).hexdigest()
        # get data from db
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT username, hash FROM users WHERE username = %s", (username,))
        userdata = cur.fetchone()
        cur.close()
        # OLD VERSION WITH SQLITE IN LOCAL DB
        # con = sql_open()
        # cursor = con.cursor()
        # cursor.execute("SELECT username, hash FROM users")
        # userdata = cursor.fetchone()
        # cursor.close()

        # if inputed data checks with db, render menu
        if userdata["hash"] == hashed_pw and userdata["username"] == username:
            session["name"] = username
            flash("Welcome, " + session["name"])
            return render_template("menu.html")

        # else, return to login
        else:
            flash("Username e/ou password incorretos")
            return redirect("/login")
    # if request is no POST typr, return to login
    else:
        return render_template("login.html")


# route for logging out
@app.route("/logout")
def logout():
    # clear session and return to base route
    session["name"] = None
    flash("Logged out")
    return redirect("/")


# route for app menu
@app.route("/menu")
@login_required
def menu():
    return render_template("menu.html")


# route to insert new data
@app.route("/newform", methods=("GET", "POST"))
def newform():
    # if request method is POST
    if request.method == "POST":
        # get data from form
        data = request.form
        # manage some trouble data (checkboxes), changed it to select boxed so they always have a value
        # try:
        #     public = data["public"]
        # except:
        #     public = "false"
        # try:
        #     solved = data["solved"]
        # except:
        #     solved = "false"

        # generate created timestamp
        now = datetime.now()
        created = now.strftime("%Y-%m-%d %H:%M:%S")

        # open db connection and insert data
        try:
            # MySQLdb.cursors.DictCursor
            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO ruts (code, desig, forn, order_nr, end_date, last_date, alternative, detail, obs, created, public, solved) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    data["code"],
                    data["desig"],
                    data["forn"],
                    data["order"],
                    data["enddate"],
                    data["lastdate"],
                    data["alter"],
                    data["detail"],
                    data["obs"],
                    created,
                    data["public"],
                    data["solved"],
                ),
            )
            mysql.connection.commit()
            cur.close()

        except Exception as e:
            print(e)
            flash("Error creating data, please try again", "flash-error")
            return render_template("newform.html")

        # OLD VERSION WITH SQLITE LOCAL DATABASE
        # con = sql_open()
        # con.execute(
        #     "INSERT INTO ruts (code, desig, forn, order_nr, end_date, last_date, alternative, detail, obs, created, public, solved) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        #     (
        #         data["code"],
        #         data["desig"],
        #         data["forn"],
        #         data["order"],
        #         data["enddate"],
        #         data["lastdate"],
        #         data["alter"],
        #         data["detail"],
        #         data["obs"],
        #         created,
        #         data["public"],
        #         data["solved"],
        #     ),
        # )
        # con.commit()
        # con.close()

        # confirm data entry and render app menu
        flash("Data successfully created")
        return render_template("menu.html")

    # if not post, return to form
    return render_template("newform.html")


# route to get list of data in database, 3 types of list according to user selection in menu the status is passed to the function
@app.route("/list/<status>", methods=["GET"])
@login_required
def render_list(status):
    # open db connection
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # unsolved shortages
    if status == "other":
        cur.execute("SELECT * FROM ruts WHERE solved = %s", (0,))
        list_type = "(not resolved)"

    # public data
    elif status == "public":
        cur.execute("SELECT * FROM ruts WHERE public = %s", (1,))
        list_type = "(public info)"

    # all data
    else:
        cur.execute("SELECT * FROM ruts")
        list_type = "(all)"

    # assign fetched data to variable and pass it to list template
    data = cur.fetchall()
    cur.close()
    return render_template("list.html", data=data, listType=list_type)


# route to see all details from db entry, the id is passed to the function
@app.route("/details/<reg_id>")
@login_required
def details(reg_id):
    # open db connection and get data according to passed id
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM ruts WHERE id=%s", (reg_id,))
    data = cur.fetchone()
    cur.close()
    # render data on details template
    return render_template("details.html", data=data)


# route to edit data entry
@app.route("/edit/<reg_id>", methods=("GET", "POST"))
@login_required
def edit(reg_id):
    # if changes are submitted
    if request.method == "POST":
        # get data from form
        data = request.form

        # # manage checkboxes, not needed as they have been replace by select boxes
        # try:
        #     public = data["public"]
        # except ValueError:
        #     public = "false"
        # try:
        #     solved = data["solved"]
        # except ValueError:
        #     solved = "false"

        # open db connection and update data entry
        try:
            cur = mysql.connection.cursor()
            cur.execute(
                "UPDATE ruts SET code = %s, desig = %s, forn = %s, order_nr = %s, end_date = %s, last_date = %s, alternative = %s, detail = %s, obs = %s, public = %s, solved = %s WHERE id = %s",
                (
                    data["code"],
                    data["desig"],
                    data["forn"],
                    data["order"],
                    data["enddate"],
                    data["lastdate"],
                    data["alter"],
                    data["detail"],
                    data["obs"],
                    data["public"],
                    data["solved"],
                    reg_id,
                ),
            )
            mysql.connection.commit()
            cur.close()
        except Exception as e:
            print(e)
            flash("An error occured during data update, please try again", "flash-error")
            address = "/edit/" + reg_id
            return redirect(address)

        # set address to go to after update
        address = "/details/" + reg_id
        # confirm update success and show updated details

        flash("Data successfully updated")
        return redirect(address)

    # if method is GET, render form with data from passed id
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM ruts WHERE id=%s", (reg_id,))
    data = cur.fetchone()
    cur.close()
    # pass data to javascript in editform to change select box option according to data in db
    return render_template(
        "editform.html",
        data=data,
        public=data["public"],
        solved=data["solved"],
    )        
        ## OLD VERSION WITH LOCAL SQLITE DB
        # con = sql_open()
        # cursor = con.cursor()
        # cursor.execute("SELECT * FROM ruts WHERE id=?", (reg_id,))
        # data = cursor.fetchone()
        # # pass data to javascript in editform to change select box option according to data in db
        # alter = json.dumps(data["alternative"])
        # return render_template("editform.html", data=data, alter=alter)


# route to delete data entry, entry to delete id is passed to function
@app.route("/delete/<reg_id>", methods=["POST"])
@login_required
def delete(reg_id):
    # open db connection and delete entry
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM ruts WHERE id = %s", (reg_id,))
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        print(e)
        flash("Não foi possível apagar o registo, tente de novo", "flash-error")
        return redirect(url_for("menu"))

    ## OLD VERSION WITH LOCAL SQLITE DB
    # con = sql_open()
    # con.execute("DELETE FROM ruts WHERE id = ?", (reg_id,))
    # con.commit()
    # con.close()
    # confirm successful delete and return to menu
    flash("Data successfully deleted")
    return redirect(url_for("menu"))


if __name__ == "__main__":
    app.run()
