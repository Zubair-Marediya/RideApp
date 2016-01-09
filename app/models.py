from server import db
from flask.ext.login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(18), index=True, unique=True)
    password = db.Column(db.String(18), index=True, unique=True)
    riders = db.relationship("Riders", backref="user", lazy="dynamic")
    drivers = db.relationship("Drivers", backref="user", lazy="dynamic")

    def __repr__(self):
        return '<User %r>' % (self.username)

class Riders(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	rider_name = db.Column(db.String(100))
	rider_phone_number = db.Column(db.String(10))
	rider_residence_latitude = db.Column(db.Float)
	rider_residence_longitude = db.Column(db.Float)
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
	
	def __repr__(self):
		return '<Rider %r>' % (self.rider_name)

class Drivers(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	driver_name = db.Column(db.String(100))
	driver_phone_number = db.Column(db.String(10))
	driver_residence_latitude = db.Column(db.Float)
	driver_residence_longitude = db.Column(db.Float)
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
	
	def __repr__(self):
		return '<Driver %r>' % (self.driver_name)

class Todaystableriders(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100))
	phone_number = db.Column(db.String(10))
	res_latitude = db.Column(db.Float)
	res_longitude = db.Column(db.Float)
	special_requests = db.Column(db.String(20))

	def __repr__(self):
		return "<Rider %r>" % (self.name)

class Todaystabledrivers(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100))
	phone_number = db.Column(db.String(10))
	res_latitude = db.Column(db.Float)
	res_longitude = db.Column(db.Float)
	time_leaving = db.Column(db.String(4))

	def __repr__(self):
		return "<Driver %r>" % (self.name)

class Previousrides(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	rider_name = db.Column(db.String(100))
	driver_name = db.Column(db.String(100))
	meeting_place_latitude = db.Column(db.Float)
	meeting_place_longitude = db.Column(db.Float)

	def __repr__(self):
		return "<Driver: %r, Rider: %r>" % (self.driver_name, self.rider_name)