class location():
    phones = []
    distance = 0
    acceptedInsurance = []
    doctors = []
    name = []
    isMedicare = False;
    isMedicaid = False;
    landlinePhone = ""

    def __init__(self, addressInfo, phones, acceptedInsurance, doctors, name):
        self.locationAddress = addressInfo
        self.phones = phones
        self.acceptedInsurance = acceptedInsurance
        self.doctors = doctors
        self.name = name

class flattenedInfo():
    locationAddress = ""
    landlinePhone = ""
    isMedicare = False;
    isMedicaid = False;
    name = ""
    doctors = []
    distance = 0

class apiResponse():
    providers = flattenedInfo();
    fetched = 0
    total = 0

class doctorInfo():
    specialties = []
    npi = ""

class geoInfo():
    latitude = "",
    longitude = "",
    searchAreaMiles = 0