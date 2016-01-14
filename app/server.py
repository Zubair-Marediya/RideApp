import sqlite3
import time
from flask import Flask, request, g, render_template, redirect, flash
from flask.ext.login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
import datetime
import time
import requests
from SMSGateway import send, receive, normalizenumber
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
        user_id = registered_user.id
        global user_id
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
    checkboxeslst = request.form.getlist("diffplace")[0].encode("ascii") + ", " + request.form.getlist("latesttime")[0].encode("ascii") + ", " + request.form.getlist("ridethere")[0].encode("ascii") + ", " + request.form.getlist("rideback")[0].encode("ascii")
    global driverstxt, riderstxt, timedateclose, checkboxeslst
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
    global driverphlst, riderphlst
    return redirect("newsession/waiting")

@app.route("/newsession/waiting", methods=["POST","GET"])
@login_required
def waitingscreen():
    #SEND OUT RIDER TEXTS
    newfeedingtime = timedateclose[:10] + ", " + timedateclose[11:]
    if request.method == "GET":
    	return render_template("waitingscreen.html", drivetxt=driverstxt, ridertxt=riderstxt, timedateclose=newfeedingtime, specialreqs=str(checkboxeslst).encode("ascii"))
    elif request.method == "POST":
	    t = (int(timedateclose[:4]),int(timedateclose[5:7]), int(timedateclose[8:10]), int(timedateclose[11:13]), int(timedateclose[14:]), 
	        0, datetime.datetime.today().weekday(), datetime.datetime.now().timetuple().tm_yday, -1)
	    timeclose = time.mktime(t)

	    current_time = int(time.time())
	    firsttextyes = [{"riders": []}, {"drivers": []}]
	    while current_time <= timeclose:
	        time.sleep(30)
	        all_texts = json.loads(receive())
	        lastcheckedtime = 0
	        n = 0
	        while not lastcheckedtime:
	        	lastcheckedtime = all_texts["result"][n]["sent_at"]
	        	n += 1
	        assert lastcheckedtime != 0, all_texts["result"][0]["status"]
	        for text in all_texts["result"]:
	            phone_number = normalizenumber(text["contact"]["number"])
	            #assert text["received_at"] >= lastcheckedtime, "recieved at " + str(text["received_at"]) + " lastcheckedtime " + str(lastcheckedtime)
	            if text["received_at"] >= lastcheckedtime or text["received_at"] == 0: #out-of-order by about 5 hrs (behind)
	            	if text["status"] == "received":
	            		confirmedriders = models.Todaystableriders.query.filter_by(phone_number=str(phone_number)).all()
	        			confirmeddrivers = models.Todaystabledrivers.query.filter_by(phone_number=str(phone_number)).all()
	        			if confirmeddrivers == [] or confirmedriders == []:
	        				pass
		                #assert text["message"].lower() == "yes", text["message"] + " id: " + str(text["id"])
		                elif "yes" in text["message"].lower() and phone_number not in firsttextyes[0]["riders"] and phone_number not in firsttextyes[1]["drivers"]:
		                	if phone_number in driverphlst:
		                		send(phone_number, "What time would you be leaving? (Give the latest possible time please in a 24-hour clock format. E.g. 7 pm = 19:00)")
		                		firsttextyes[1]["drivers"].append(phone_number)
		                	if phone_number in riderphlst:
		                		send(phone_number, "Do you require any of these special accommodations?" + " " + str(checkboxeslst).encode("ascii"))
		                		firsttextyes[0]["riders"].append(phone_number)
		                elif phone_number in firsttextyes[0]["riders"]:
		                    #Check for special requests and then add to TempDB
		                    riderspecialreqs = []
		                    if "1" in text["message"].lower():
		                        riderspecialreqs.append(1)
		                    if "2" in text["message"].lower():
		                        riderspecialreqs.append(2)
		                    if "3" in text["message"].lower():
		                        riderspecialreqs.append(3)
		                    if "4" in text["message"].lower():
		                        riderspecialreqs.append(4)
		                    if "no" in text["message"].lower():
		                    	riderspecialreqs.append("No")
		                    #Find user info and append to Todaystableriders
		                    assert riderspecialreqs != [], "Must have one of the above options."
		                    rider = models.Riders.query.filter_by(user_id=user_id, rider_phone_number=str(phone_number)).first()
		                    thisrider = models.Todaystableriders(name=rider.rider_name, phone_number=rider.rider_phone_number, res_latitude=rider.rider_residence_latitude, res_longitude=rider.rider_residence_longitude, special_requests=str(riderspecialreqs))
		                    db.session.add(thisrider)
		                    db.session.commit()
		                    send(phone_number, "Thanks! Youve been added to todays ride list. Please contact us at 5:00 pm if you havent received your ride assignment.")															
		                elif phone_number in firsttextyes[1]["drivers"]:
		                    #Note down time leaving and then add to Todaystabledrivers
		                    try:
		                        t= timedate.time(text["message"][:2], text["message"][3:])
		                    except ValueError:
		                        try:
		                            t = timedate.time(text["message"][:1], text["message"][2:])
		                        except ValueError:
		                            send(phone_number, "This is not a valid time format. Please respond with the latest time you will be leaving in a 24-hour clock format.")
		                            break
		                        else:
		                            driver = models.Drivers.query.filter_by(user_id=user_id, driver_phone_number=str(phone_number)).first()
		                            thisdriver = models.Todaystabledrivers(name=driver.driver_name, phone_number=driver.driver_phone_number, res_latitude=driver.driver_residence_latitude, res_longitude=driver.driver_residence_longitude, time_leaving=text["message"])
		                            db.session.add(thisdriver)
		                            db.session.commit()
		                            send(phone_number, "Thanks! Youve been added to today's ride list. Please contact us at 5:00 pm if you havent received your ride assignment.")							
		                    else:
		                        driver = models.Drivers.query.filter_by(user_id=user_id, driver_phone_number=str(phone_number)).first()
		                        thisdriver = models.Todaystabledrivers(name=driver.driver_name, phone_number=driver.driver_phone_number, res_latitude=driver.driver_residence_latitude, res_longitude=driver.driver_residence_longitude, time_leaving=text["message"])
		                        db.session.add(thisdriver)
		                        db.session.commit()
		                        send(phone_number, "Thanks! Youve been added to today's ride list. Please contact us at 5:00 pm if you havent received your ride assignment.")
	            else:
	            	break

	            	#return render_template("waitingscreen.html", drivetxt=current_time, timedateclose=lastcheckedtime, ridertxt=text["message"], specialreqs=text["received_at"])
	        #     else:
	        #     	return render_template("waitingscreen.html", drivetxt=current_time, timedateclose=timeclose, ridertxt=text["message"])
	        # #program to sleep and then change current_time AND REPEAT
	        #time.sleep(45)
	        current_time = int(time.time())
	    return redirect("/newsession/confirmation")

    #REDIRECT TO NEXT PAGE

@app.route("/newsession/confirmation", methods=["GET"])
@login_required
def confirmation():
    #put while loop (while less than timedateclose), keep querrying msgs and then send out responses to .the ones that are the ones you want.
    if request.method == "GET":
        return render_template("confirmation.html")

@app.route('/logout')
def logout():
    logout_user()
    return 'Logged out'

if __name__ == "__main__":
    app.debug = True
    app.run()