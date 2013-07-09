# Generates the codes2names.js file, which maps country codes ("US") to
# their full names ("United States"). This downloads country information
# from the World Bank.

import json
import urllib
import sys

COUNTRY_DATA_URL = 'http://api.worldbank.org/country?per_page=500&format=json'

inputFile = urllib.urlopen(COUNTRY_DATA_URL)
countryData = json.load(inputFile)
inputFile.close()

countryEntries = countryData[1]
countryCodes = dict()
for countryEntry in countryEntries:
    iso2Code = countryEntry.get(u'iso2Code')
    name = countryEntry.get(u'name')
    if not iso2Code:
        continue
    countryCodes[iso2Code] = name

sys.stdout.write('var CountryCodes = ')
json.dump(countryCodes, sys.stdout) 
