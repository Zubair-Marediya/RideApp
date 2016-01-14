import requests

#SEND MESSAGES
def send(phone, msg):
	parameters = {"email": "adnan.h@berkeley.edu", "password": "abcd1234", "device": 16208, "number": phone, "message": msg}
	response = requests.post("http://smsgateway.me/api/v3/messages/send", data=parameters)

#RECIEVE ONE Message
# parameters = {"email": "adnan.h@berkeley.edu", "password": "abcd1234"}
# response = requests.get("http://smsgateway.me/api/v3/messages/view/[ID]?email=adnan.h@berkeley.edu&password=abcd1234")
# print(response)

#LIST Messages
def receive():
	parameters = {"email": "adnan.h@berkeley.edu", "password": "abcd1234"}
	response = requests.get("http://smsgateway.me/api/v3/messages?email=adnan.h@berkeley.edu&password=abcd1234")
	return response.content

def normalizenumber(number):
	if "+1" in number:
		number = number[2:]
	number = int(number)
	return number

#Google Maps API Key: AIzaSyBOxAw53OouSgBi7TDgbP45GRu2z8HXC4g
