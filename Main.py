import BetterDocApi
import asyncio
import BetterDocModels
from flask import Flask, request
import json
import sys
import asyncio
from twilio.rest import Client

'''
We have not hosted this service on a internet accessible web server.
In the meantime you can run an instance locally using ngrok.

Steps to get this script running locally on your laptop/desktop
1) make sure you have a https://www.twilio.com account,
buy a Twilio number which acts the SMS service number
and if you have a trial Twilio account, then get the sender's number verified

2) import all the required python packages

3) run the script "python3 Main.py", you should see:
 // * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit) //

4) now download https://ngrok.com/download and start on port 5000 using the command "./ngrok http 5000"

5) login to your Twilio account, under console > phone-number > edit your Twilio phone number, under messaging, in webhook add the ngrok ssh tunnel address.
you can follow the instructions here: https://www.youtube.com/watch?v=cZeCz_QOoXw

6) now your service is running, send test sms: MentalHelpSMS <cta_stop_id> to <twilio_number> and you should get 3 suited doctors nearby.
'''
global matchedLocations
matchedLocations = []
resultLocations = []
displayMessages = []
viewedRecords = 0
recordLimit = 100
# Twilio account details
account_sid = ""
auth_token = ""
# Twilio number to which 'MentalHelpSMS <stop_id>' should be sent to'
fromPhone = ""

app = Flask(__name__)

def get_location_coordinates(stopID):

	with open('CTA_BusStops.geojson') as data_file:
		data = json.load(data_file)
    
	for feature in data['features']:           
            convertedStopId = "{}.0".format(stopID)
            selected_sys_stop = feature['properties']['SYSTEMSTOP']
            selected_sys_coordinates = feature['geometry']['coordinates']
            if (str(selected_sys_stop) == convertedStopId):
                return selected_sys_coordinates

def generateMessageInfo(name, address, phone, isMedicare, isMedicaid):
    if (isMedicare):
        medicareResponse = "Yes"
    else:
        medicareResponse = "No"

    if (isMedicaid):
        medicaidResponse = "Yes"
    else:
        medicaidResponse = "No"

    return "{} at {} ({}): Medicare status ({}); Medicaid status ({})".format(name, address, phone, medicareResponse, medicaidResponse)

async def aggregate_provider_results(gisInfo, limit, skipCount):
    result = await BetterDocApi.GetProviders(gisInfo, limit, skipCount)
    global viewedRecords
    global matchedLocations

    viewedRecords += result.fetched
    
    for provider in result.providers:
        matchedLocations.append(provider)

    if (len(matchedLocations) < 10 and viewedRecords < result.total):
        await aggregate_provider_results(recordLimit, viewedRecords)
    else:
        hasMedicare = False
        # The BetterDoctors API has already sorted results by distance
        # If time permitted, a more sophisticated ranking algorithm would be nice, i.e.,
        # Yelp reviews, BetterDoctor Reviews, cross reference with VitalSigns data, etc

        # For now, include the top three locations by geographic distance:
        # If none of the top three take medicare/medicaid, see if any of the remaining results do
        # If so, replace the third result with the medicare/medicaid provider
        for location in matchedLocations:
            if (len(resultLocations) < 3):
                resultLocations.append(location)
                if (location.isMedicare or location.isMedicaid):
                    hasMedicare = True

            if (len(resultLocations) == 3 and hasMedicare == False and (location.isMedicare or location.isMedicaid)):
                resultLocations.pop()
                resultLocations.append(location)

        for x in resultLocations:
            displayMessages.append(generateMessageInfo(x.name, x.locationAddress, x.landlinePhone, x.isMedicare, x.isMedicaid))

@app.route('/sms', methods=['POST'])
def sms():
    number = request.form['From']
    # user sends help text message including stop_id to (608) 514-1593
    # for example, user sends "YELPCARE 1871" to (608) 514-1593
    
    message_body = request.form['Body']
    # split the user_sent text based on white-space
    
    keywords = message_body.split(" ")
    stop_id = keywords[1]
    print(stop_id)
    coordinates = get_location_coordinates(stop_id)

    gis = BetterDocModels.geoInfo()
    gis.longitude = coordinates[0]
    gis.latitude = coordinates[1]
    
    gis.searchAreaMiles = 1

    loop = asyncio.get_event_loop()
    loop.run_until_complete(aggregate_provider_results(gis, recordLimit, viewedRecords))    
 
    emergencyInfo = "If this is an emergency, please contact 911 or 1-800-273-TALK."
    headerText = "Based on your stop id, here are nearby locations that provide mental health service:"
        
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        to=number, 
        from_=fromPhone,
        body=emergencyInfo)

    message = client.messages.create(
        to=number, 
        from_=fromPhone,
        body=headerText)

    cnt = len(displayMessages)

    if cnt > 0:
        message = client.messages.create(
            to=number, 
            from_=fromPhone,
            body=displayMessages[0])
    if cnt > 1:
        message = client.messages.create(
            to=number, 
            from_=fromPhone,
            body=displayMessages[1])
    if cnt > 2:
        message = client.messages.create(
            to=number, 
            from_=fromPhone,
            body=displayMessages[2])

    return ""  
if __name__ == '__main__':
        app.run()