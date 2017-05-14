import json
import requests
import asyncio
import BetterDocModels

async def GetProviders(location_coordinates, recordLimit, skipCount):
    mentalHealthSpecialties = ["mental-health-counselor", 'psychiatrist', "mental-health-nurse-practitioner",'clinical-psychologist', 'counseling-pshychologist', 'cognitive-behavioral-psychologist', 'psychologist']

    baseUrl = 'https://api.betterdoctor.com/2016-03-01/practices'
    user_key = '253c06706096f138941a110dbf3b0dfa'
    parameterizedUrl = "{}?location={},{},{}&user_key={}&sort=distance-asc&limit={}&skip={}".format(baseUrl, location_coordinates.latitude, location_coordinates.longitude,
                            location_coordinates.searchAreaMiles, user_key, recordLimit, skipCount)

    betterDocResponse = requests.get(parameterizedUrl)
    json_data = json.loads(betterDocResponse.text)
    fetchedCount = json_data['meta']['count']
    totalCount = json_data['meta']['total']

    willAcceptNewPatients = []
    matchedLocations = []

    for key in json_data['data']:

        #Collect some location specific information if the practice is accepting new patients
        if key['accepts_new_patients']:
            doctorName = ""

            # Some doctors don't have names so check before assiging
            # For now, ignore locations that don't provide a primary name
            if 'name' in key: 
                practiceInfo = BetterDocModels.location(key['visit_address'], key['phones'], key['insurance_uids'], key['doctors'], key['name'])

            if 'distance' in key:
                practiceInfo.distance = key['distance']    
        
            willAcceptNewPatients.append(practiceInfo)

    for locations in willAcceptNewPatients:
        for insurance in locations.acceptedInsurance:
            if insurance == "medicaid-medicaid":
                locations.isMedicaid = True

            if insurance == "medicare-medicare":
                locations.isMedicare = True

        for phone in locations.phones:
            if (phone["type"] == "landline"):
                locations.landlinePhone = phone["number"]

        for doctor in locations.doctors:
            info = BetterDocModels.doctorInfo()
            #Hack since I dont' know how to create new instance of object
            info.specialties = []
            info.npi = ""

            if 'specialties' in doctor:
                for specialty in doctor['specialties']:
                    doctorSpecialty = specialty["uid"] 
                    if doctorSpecialty in mentalHealthSpecialties:
                        info.npi = doctor["npi"]
                        info.specialties.append(doctorSpecialty)

                if (len(info.specialties) > 0):
                    displayInfo = BetterDocModels.flattenedInfo()
                    displayInfo.distance = locations.distance
                    displayInfo.isMedicaid = locations.isMedicaid
                    displayInfo.isMedicare = locations.isMedicare
                    displayInfo.name = locations.name
                    displayInfo.doctors = info
                    displayInfo.landlinePhone = "({}) {}-{}".format(locations.landlinePhone[0:3], locations.landlinePhone[3:6], locations.landlinePhone[6:10])

                    if 'street' in locations.locationAddress:
                        displayInfo.locationAddress = locations.locationAddress['street']
                    if 'street2' in locations.locationAddress:
                        displayInfo.locationAddress += ", " + locations.locationAddress['street2']
                    if 'city' in locations.locationAddress:
                        displayInfo.locationAddress += ", " + locations.locationAddress["city"]

                    matchedLocations.append(displayInfo)

    response = BetterDocModels.apiResponse()
    response.providers = matchedLocations
    response.fetched = fetchedCount
    response.total = totalCount

    return response