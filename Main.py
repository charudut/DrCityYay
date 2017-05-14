import BetterDocApi
import asyncio
import BetterDocModels
from flask import Flask, request
from twilio import twiml
import json
import sys

global matchedLocations
matchedLocations = []
resultLocations = []
displayMessages = []
viewedRecords = 0
recordLimit = 100

app = Flask(__name__)

def get_location_coordinates(stopID):
	with open('CTA_BusStops.geojson') as data_file:    
		data = json.load(data_file)

	for feature in data['features']:
            selected_sys_stop = feature['properties']['SYSTEMSTOP']
            selected_sys_coordinates = feature['geometry']['coordinates']
            if (str(selected_sys_stop) == stopID):
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

loopIndex =0
hasMedicare = False
# The BetterDoctors API has already sorted results by distance
# If time permitted, a more sophisticated ranking algorithm would be nice, i.e.,
# Yelp reviews, BetterDoctor Reviews, cross reference with VitalSigns data, etc

# For now, include the top three locations by geographic distance:
# If none of the top three take medicare/medicaid, see if any of the remaining results do
# If so, replace the third result with the medicare/medicaid provider
for location in matchedLocations:

    loopIndex += 1

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
    gis.latitude = coordinates[0]
    gis.longitude = coordinates[1]
    gis.searchAreaMiles = 1

    loop = asyncio.get_event_loop()
    loop.run_until_complete(aggregate_provider_results(gis, recordLimit, viewedRecords))
    loop.close()
 
    resp = twiml.Response()
    resp.message('Hello {}, based on your stopID your location is: {}'.format(number, coordinates))
    print(displayMessages[2])
    return str(resp)

if __name__ == '__main__':
    app.run()