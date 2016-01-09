import sqlite3
import time
from flask import Flask, request, g, render_template, redirect, flash
from flask.ext.login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
import datetime
import time
import requests
from SMSGateway import send, receive
import json

app = Flask(__name__)
app.secret_key = "AnYtHiNg"
login_manager = LoginManager()
login_manager.init_app(app)
app.config.from_object("db_config")
db = SQLAlchemy(app)

import models


@login_manager.user_loader
def user_loader(id0):
    registered_user = models.User.query.filter_by(id=id0).first()
    if registered_user is None:
        return
    else:
        return registered_user

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    password = request.form.get('password')
    registered_user = models.User.query.filter_by(username=username,password=password).first()
    if registered_user is None:
        return
    else:
        registered_user.is_authenticated = True
        return registered_user


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    username = request.form.get('username')
    password = request.form.get('password')
    registered_user = models.User.query.filter_by(username=username,password=password).first()
    if registered_user is None:
        return redirect("/badlogin")
    else:
        login_user(registered_user)
        user_id = registered_user.id
        global user_id
        return redirect("/userdashboard")


@app.route("/badlogin", methods=["GET", "POST"])
def badlogin():
    if request.method == "GET":
        return render_template("login.html", error="Bad login. Either your username or password was not recognized. Please try again.")
    username = request.form.get('username')
    password = request.form.get('password')
    registered_user = models.User.query.filter_by(username=username,password=password).first()
    if registered_user is None:
        return redirect("/badlogin")
    else:
        login_user(registered_user)
        return redirect("/userdashboard")


@app.route("/userdashboard", methods=["GET"])
@login_required
def userdash():
    return render_template("userdash.html")

@app.route("/newsession", methods=["GET"])
@login_required
def newsessionbutton():
    return render_template("createnewsession.html")

@app.route("/newsession/gotosessionsettings", methods=["POST","GET"])
@login_required
def newsessionsettings():
    rightnow = datetime.datetime.now()
    dateandtime = str(rightnow)
    date = dateandtime[:10]
    time = "15:00"
    feedertime = date+"T"+time
    if request.method == "GET":
        return render_template("gotosessionsettings.html", timedate=feedertime)
    driverstxt = request.form.get("driverstxt")
    riderstxt = request.form.get("riderstxt")
    timedateclose = request.form.get("timedateclose")
    checkboxeslst = request.form.getlist("diffplace") + request.form.getlist("latesttime") + request.form.getlist("ridethere") + request.form.getlist("rideback")
    global driverstxt, riderstxt, timedateclose, checkboxeslst
    return redirect("newsession/waiting")

@app.route("/newsession/waiting", methods=["POST","GET"])
@login_required
def waitingscreen():
    #SEND OUT RIDER TEXTS
    newfeedingtime = timedateclose[:10] + ", " + timedateclose[11:]
    r = models.Riders.query.filter_by(user_id=user_id).all()
    riderphlst = []
    for rider in r:
        riderph = int(rider.rider_phone_number)
        riderphlst.append(riderph)
        send(riderph, riderstxt)
    #SEND OUT DRIVER TEXTS
    d = models.Drivers.query.all()
    driverphlst = []
    for driver in d:
        driverph = int(driver.driver_phone_number)
        driverphlst.append(driverph)
        send(driverph, driverstxt)

    #put while loop (while less than timedateclose), keep querrying msgs and then send out responses to .the ones that are the ones you want.
    t = (int(timedateclose[:4]),int(timedateclose[5:7]), int(timedateclose[8:10]), int(timedateclose[11:13]), int(timedateclose[14:]), 
        0, datetime.datetime.today().weekday(), datetime.datetime.now().timetuple().tm_yday, -1)
    timeclose = time.mktime(t)

    current_time = int(time.time())
    firsttextyes = [{"riders": []}, {"drivers": []}]
    while current_time <= timeclose:
        all_texts = json.loads(receive())
        lastcheckedtime = int(time.time())
        for text in all_texts["result"]:
            while text["received_at"] >= lastcheckedtime or text["received_at"] == 0:
                if ("yes" in text["message"].lower) and (text["status"] == "received") and (text["contact"]["number"] not in firsttextyes[0]["riders"]) and (text["contact"]["number"] not in firsttextyes[1]["drivers"]):
                    if text["contact"]["number"] in driverphlst:
                        send(text["contact"]["number"], "What time would you be leaving? (Give the latest possible time please in a 24-hour clock format. E.g. 7 pm = 19:00)")
                        firsttextyes[1]["drivers"].append(text["contact"]["number"])
                    if text["contact"]["number"] in riderphlst:
                        send(text["contact"]["number"], "Do you require any of these special accommodations? Please respond with the the number associated with all of the options that apply." + str(checkboxeslst))
                        firsttextyes[0]["riders"].append(text["contact"]["number"])
                if text["contact"]["number"] in firsttextyes[0]["riders"]:
                    #Check for special requests and then add to TempDB
                    riderspecialreqs = []
                    if "1" in text["result"]["message"].lower:
                        riderspecialreqs.append(1)
                    if "2" in text["result"]["message"].lower:
                        riderspecialreqs.append(2)
                    if "3" in text["result"]["message"].lower:
                        riderspecialreqs.append(3)
                    if "4" in text["result"]["message"].lower:
                        riderspecialreqs.append(4)
                    #Find user info and append to Todaystableriders
                    ridernumber = text["result"]["contact"]["number"]
                    if "+1" in ridernumber:
                        ridernumber = ridernumber[2:]
                    rider = models.Riders.query.filter_by(user_id=user_id, rider_phone_number=ridernumber).first()
                    thisrider = models.Todaystableriders(name=rider.rider_name, phone_number=rider.rider_phone_number, res_latitude=rider.rider_residence_latitude, res_longitude=rider.rider_residence_longitude, special_requests=str(specialreqs))
                    db.session.add(thisrider)
                    db.session.commit()
                if text["contact"]["number"] in firsttextyes[1]["drivers"]:
                    #Note down time leaving and then add to Todaystabledrivers
                    try:
                        t= timedate.time(text["message"][:2], text["message"][3:])
                    except ValueError:
                        try:
                            t = timedate.time(text["message"][:1], text["message"][2:])
                        except ValueError:
                            send(text["contact"]["number"], "This is not a valid time format. Please respond with the latest time you will be leaving in a 24-hour clock format.")
                            break
                        else:
                            drivernumber = text["contact"]["number"]
                            if "+1" in drivernumber:
                                drivernumber = drivernumber[2:]
                            driver = models.Drivers.query.filter_by(user_id=user_id, driver_phone_number=drivernumber).first()
                            thisdriver = models.Todaystabledrivers(name=driver.driver_name, phone_number=driver.driver_phone_number, res_latitude=driver.driver_residence_latitude, res_longitude=driver.driver_residence_longitude, time_leaving=text["message"])
                            db.session.add(thisdriver)
                            db.session.commit()
                    else:
                        drivernumber = text["contact"]["number"]
                        if "+1" in drivernumber:
                            drivernumber = drivernumber[2:]
                        driver = models.Drivers.query.filter_by(user_id=user_id, driver_phone_number=drivernumber).first()
                        thisdriver = models.Todaystabledrivers(name=driver.driver_name, phone_number=driver.driver_phone_number, res_latitude=driver.driver_residence_latitude, res_longitude=driver.driver_residence_longitude, time_leaving=text["message"])
                        db.session.add(thisdriver)
                        db.session.commit()
            break
        #program to sleep and then change current_time AND REPEAT
        time.sleep(45)
        current_time = int(time.time())

    if request.method == "GET":
        return render_template("waitingscreen.html", drivetxt=driverstxt, ridertxt=riderstxt, timedateclose=newfeedingtime, specialreqs=checkboxeslst)
    #REDIRECT TO NEXT PAGE
    return redirect("/newsession/confirmation")

@app.route("/newsession/confirmation", methods=["GET"])
@login_required
def confirmation():
    if request.method == "GET":
        return render_template("confirmation.html")

@app.route('/logout')
def logout():
    logout_user()
    return 'Logged out'

if __name__ == "__main__":
    app.debug = True
    app.run()