import csv
import random


def import_csv():
        countries = []
        with open('resources/world-data-2023.csv',encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                doc = {"country":row[0].strip(),"agricoltural":row[1],"land_area":row[2],"armed_force":row[3], 
                       "calling_code":row[4],"fertility":row[5], "forest":row[6],"gdp":row[7],
                       "life_expectancy":row[8],"unemployed":row[9], "population":row[10],"language":row[11],"currency":row[12],
                       "capital":row[13]}
                countries.append(doc)
        return countries

def check_input(random_country, user_input):
     if str(random_country['country']).lower() == str(user_input).lower().strip():
          return True
     return False

def prompt_question(input_str):
    user_input = input(input_str)      
    if check_input(random_country, user_input):
        print(MSG)
        exit()

MSG = "CORRECT!"     
countries = import_csv()
random_country = random.choice(countries)
print("Guess the country: ")
prompt_question("Agricoltural Area % -> " + random_country['agricoltural'] + ": ")
prompt_question("Land Area -> " + random_country['land_area'] + ": ")
prompt_question("Armed Forces Size -> " + random_country['armed_force'] + ": ")
prompt_question("Calling Code -> " + random_country['calling_code'] + ": ")
prompt_question("Fertility -> " + random_country['fertility'] + ": ")
prompt_question("Forested Area % -> " + random_country['forest'] + ": ")
prompt_question("GDP -> " + random_country['gdp'] + ": ")
prompt_question("Life Expectancy -> " + random_country['life_expectancy'] + ": ")
prompt_question("Unemployment Rate -> " + random_country['unemployed'] + ": ")
prompt_question("Population -> " + random_country['population'] + ": ")
prompt_question("Language -> " + random_country['language'] + ": ")
prompt_question("Currency -> " + random_country['currency'] + ": ")
prompt_question("Capital -> " + random_country['capital'] + ": ")
print("Sorry, you LOST, it was " + random_country['country'])