from flask import Flask, request
from twilio import twiml
import json
import sys
 
app = Flask(__name__)

def get_location_coordinates(stopID):
	with open('CTA_BusStops.geojson') as data_file:    
		data = json.load(data_file)

	for feature in data['features']:
    		selected_sys_stop = feature['properties']['SYSTEMSTOP']
    		selected_sys_coordinates = feature['geometry']['coordinates']
    		if (str(selected_sys_stop) == stopID):
        		return selected_sys_coordinates 
 
@app.route('/sms', methods=['POST'])
def sms():
    number = request.form['From']
    # user sends help text message including stop_id to (608) 514-1593
    # for example, user sends "YELPCARE 1871" to (608) 514-1593
    
    message_body = request.form['Body']
    # split the user_sent text based on white-space
    
    keywords = message_body.split(" ")
    stop_id = keywords[1]
    print stop_id
    coordinates = get_location_coordinates(stop_id)
 
    resp = twiml.Response()
    resp.message('Hello {}, based on your stopID your location is: {}'.format(number, coordinates))
    return str(resp)
 
if __name__ == '__main__':
    app.run()
