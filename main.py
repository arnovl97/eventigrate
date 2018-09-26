import requests
import json
import datetime
import sqlite3
import csv

def main():
    exchange_dict = {}
    results_list = []
    countries = ['AUS', 'BRA', 'CHN', 'GBR', 'USA']

    json_countries = get_countries(countries)
    exchange_dict = populate_exchange_dict(json_countries)
    exchange_dict = get_average_exchange_rate(exchange_dict, 5)
    results_list = create_list(json_countries, exchange_dict)

    add_to_db(results_list)
    create_csv(results_list)

# make a rest get request to the countries api
# codes are the three letter codes from which the info is needed
# returns the json
def get_countries(codes):
    codes.sort()            # get the list in alphabetical order (for esthetic purposes)

    country_url = create_country_url(codes)
    results = requests.get(country_url)
    json_result = json.loads(results.text)

    return json_result

# will simply populate the provided dictionary with all the currency codes provided in
# the argument, the argument is the json result from a get request to country rest services
# returns the populated dictionary
def populate_exchange_dict(countries):
    exchange_dict = {}
    for country in countries:
        exchange_dict[country['currencies'][0]['code']] = 0
    return exchange_dict

# Calculates the average of the exchange rates over the provided period of days
# Exchange dict is a dictionary with all the three letter codes for the currencies
# the dictionary can be obtained by populate_exchange_dict
# returns the dictionary with the values averaged
def get_average_exchange_rate(exchange_dict, no_of_days):
    url_options = "?access_key=9bf5d2d3c8fde4df7abd69556b721898&base=EUR&symbols="
    for rate in exchange_dict:
        url_options = url_options + rate + ","
    url_options = url_options[:-1]

    date = datetime.date.today()
    end_date = date - datetime.timedelta(days=no_of_days)
    while (date != end_date):
        json_result = get_exchange_rate(date, url_options)
        
        for rate in exchange_dict:
            exchange_dict[rate] += json_result['rates'][rate]

        date = date - datetime.timedelta(days=1)

    # average all the rates
    for rate in exchange_dict:
        exchange_dict[rate] = exchange_dict[rate]/no_of_days

    return exchange_dict

# Makes rest get call the the server with the provided date and options
# returns the json from the call
def get_exchange_rate(date, options):
    url = "http://data.fixer.io/api/"       
    get_url = url + str(date) + options     # Create the url for the api
    results = requests.get(get_url)             # Send the get request
    json_result = json.loads(results.text)      # Load the results as a json Object    

    return json_result

# Creates a python list with lists with data as its content
# Ex. [["Belgium", ...], [...], ...]
def create_list(json_countries, exchange_dict):
    result_list = []
    for country in json_countries:
        result_list.append(list_from_json(country, exchange_dict))
    
    return result_list

# Function to create the url used for the countries api
def create_country_url(codes):
    base_url = "https://restcountries.eu/rest/v2/alpha?codes="
    url_arg = ""

    for code in codes:
        url_arg = url_arg + code + ";"

    get_url = base_url + url_arg
    get_url = get_url[:-1] # remove the last ';' from the url

    return get_url

# Simple helper function to create a list to reduce code in get_info function
# Expects a single json object from the api call to restcountries
# Returns the created list
def list_from_json(country, exchange_dict):
    dummy_list = []
    dummy_list.append(country['name'])
    dummy_list.append(country['callingCodes'][0])
    dummy_list.append(country['capital'])
    dummy_list.append(country['population'])
    dummy_list.append(country['currencies'][0]['code'])
    dummy_list.append(exchange_dict[country['currencies'][0]['code']])
    dummy_list.append(country['flag'])

    return dummy_list

# Add all the data in the database, expects a list containing lists per country
# The argument should be a list created by the function create_list()
def add_to_db(countries):
    db = sqlite3.connect('eventigrate.db')
    cursor = db.cursor()

    # Create the database table if it does not already exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 
            countries(id INTEGER PRIMARY KEY, name TEXT,
                    calling_code INTEGER, capital TEXT,
                    population INTEGER, currency TEXT,
                    exchange_rate DOUBLE, flag TEXT)
    ''')
    db.commit()

    for country in countries:
        cursor.execute('''
            INSERT INTO 
                countries(name, calling_code, capital, population,
                          currency, exchange_rate, flag)
            VALUES(?,?,?,?,?,?,?)
            ''', (country[0], country[1], country[2], country[3], country[4], 
                  country[5],country[6])
        )
        db.commit()

    db.close()

# Creates a csv file with the provided data
# The argument should be a list created by the function create_list()
def create_csv(countries):
    with open('eventigrate.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerows(countries)

main()