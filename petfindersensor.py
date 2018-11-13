"""
A Sensor to retrieve a list of animals available for adoption at
the El Cajon Animal Shelter using the PetFinder API
"""

__version__ = "1.0"
__author__ = "Roger Hinson"
__email__ = "roger.hinson@gmail.com"

from sensor import Sensor
import json
import os
import time
import requests
import logging
from datetime import datetime


class PetFinderSensor(Sensor):
    logging.basicConfig(
        level=logging.INFO,
        filename=os.path.join(os.getcwd(), 'logs', 'petfinder.log'),
        filemode='a',
        format='%(asctime)s - %(lineno)d - %(levelname)s - %(message)s')

    __CONFIG_FILE = 'petfindersensor.json'
    __SAVED_RECORDS = 'petfinder_saved_records.json'

    logging.info("\n")  # Add a new line in log to start run

    def __init__(self):
        """ Create new PetFinderSensor object and read sensor settings from config file """
        try:
            with open(PetFinderSensor.__CONFIG_FILE) as json_text:
                self.d = json.load(json_text)
            logging.info("This sensor just woke up .. ready to call " + self.d['service_url'])
        except (Exception, OSError, ValueError) as e:
            logging.critical("Not able to read __CONFIG_FILE " + PetFinderSensor.__CONFIG_FILE)
            logging.critical("Error was: " + str(e))
            exit()

    def has_updates(self, k):
        """
        k doesn't matter.  Need to check if animal lastUpdated is greater than PetFinderSensor last_has_update

        Returns value of 1 if any animals found with newer date than last check for updates
        """
        update_available = 0
        if self._request_allowed():
            has_update = self.get_all()
            for pet in has_update:
                if datetime.strptime(pet['pet_update'], "%Y-%m-%d"'T'"%H:%M:%S"'Z') > datetime.fromtimestamp(self.d['last_has_update']):
                    update_available = 1
                    break
            logging.info("Updates are available")
            return update_available
        else:
            return 0

    def get_content(self, k):
        """
        k doesn't matter.  Need to check if animal lastUpdated is greater than PetFinderSensor last_has_update

        Returns a list of dictionaries for each updated pet
        """
        newContent = []
        time.sleep(11)  # Since the has_updates ran a get_all it updated the last_get_all time
        if self._request_allowed():
            content = self.get_all()  # Returns all pets with only the data we're looking for
            for pet in content:
                if datetime.strptime(pet['pet_update'], "%Y-%m-%d"'T'"%H:%M:%S"'Z') > datetime.fromtimestamp(self.d['last_has_update']):
                    newContent.append(pet)
        self.d['last_has_update'] = int(time.time())
        self._save_settings()  # Saves that a request has been made to the service
        return newContent

    def get_all(self):
        """ Request information on all animals available for adoption """
        if self._request_allowed():
            url = self.d['service_url']+"%s?key=%s&count=%d&id=%s&format=%s"
            try:
                response = requests.get(url % (self.d['service_method'], self.d['key'], self.d['return_count'], self.d['shelter_id'], self.d['format']))
            except (requests.ConnectionError, requests.ConnectTimeout) as e:
                logging.warning("HTTP Request failed for: " + str(e))
            self.d['last_get_all'] = int(time.time())
            self._save_settings()  # Saves that a request has been made to the service
            logging.info("Settings saved in get_all")
            try:
                # URL should return JSON, if not, something went wrong
                response_json = json.loads(response.text)
                logging.info("The response from %s was JSON" % (self.d['service_url']))
            except (Exception, OSError, ValueError) as e:
                # The data we received from the response was not in JSON
                # Something went wrong, so load the saved data
                logging.warning("The response from %s was not JSON" % (self.d['service_url']))
                response = self._read_saved_data()
                return self._create_record(json.loads(response))
            if response is not None and response.status_code == 200:
                try:
                    with open(PetFinderSensor.__SAVED_RECORDS, 'w') as backup:
                        backup.write(response.text)
                        logging.info("Saved response from %s" % (self.d['service_url']))
                except (Exception, OSError, ValueError) as e:
                    logging.warning("File response write failed: " + str(e))
                finally:
                    return self._create_record(response_json)
            else:
                logging.warning("The response was bad, using saved data")
                response = self._read_saved_data()
                return self._create_record(json.loads(response))
        else:
            logging.warning("The request was not allowed, using saved data")
            response = self._read_saved_data()
            return self._create_record(json.loads(response))

    @staticmethod
    def _create_record(d):
        """ Create a list of dictionaries with details about each pet available from the shelter """
        record = []
        for pet in range(len(d['petfinder']['pets']['pet'])):
            for photo in range(len(d['petfinder']['pets']['pet'][pet]['media']['photos']['photo'])):
                if d['petfinder']['pets']['pet'][pet]['media']['photos']['photo'][photo]['@size'] == 'x':
                    use_this_photo = d['petfinder']['pets']['pet'][pet]['media']['photos']['photo'][photo]['$t']
                    break
            record.append({'pet_name': d['petfinder']['pets']['pet'][pet]['name']['$t'],
                           'pet_id': d['petfinder']['pets']['pet'][pet]['id']['$t'],
                           'pet_age': d['petfinder']['pets']['pet'][pet]['age']['$t'],
                           'pet_sex': d['petfinder']['pets']['pet'][pet]['sex']['$t'],
                           'pet_type': d['petfinder']['pets']['pet'][pet]['animal']['$t'],
                           'pet_update': d['petfinder']['pets']['pet'][pet]['lastUpdate']['$t'],
                           'pet_description': d['petfinder']['pets']['pet'][pet]['description']['$t'],
                           'pet_photo': use_this_photo
                           })
        return record

    def _request_allowed(self):
        # This use to capture the real allowance of 10,000 times per day
        # Simplified to new variation for easier grading  :)
        return not self.d['offline_mode'] and (int(time.time()) - self.d['last_get_all']) > self.d['update_frequency']

    def _save_settings(self):
        # Save JSON settings to config file
        try:
            with open(os.path.join(os.path.dirname(__file__), PetFinderSensor.__CONFIG_FILE), 'w') as outfile:
                json.dump(self.d, outfile)
        except (Exception, OSError, ValueError) as e:
            logging.warning("Unable to save JSON settings : " + str(e))

    def _read_saved_data(self):
        # Read saved reponse.text data from saved file in case URL can't be accessed
        try:
            with open(PetFinderSensor.__SAVED_RECORDS) as saved_data:
                response = saved_data.read()
                logging.info("Read response from saved file")
            return response
        except (Exception, OSError, ValueError) as e:
            logging.critical("Reading saved data error is: " + str(e))
            return None


if __name__ == "__main__":
    sr = PetFinderSensor()
    print("This is me : " + str(sr))
    print("let's go ..")
    json_doc = sr.get_all()
    print(json_doc)

    print("\n")

    for pet in json_doc:
        print(pet)

    print("\nChecking for Pet Updates\n")

    time.sleep(11)  # Need to wait 10 seconds before getting an update

    if sr.has_updates(datetime.now()):
        json_doc = sr.get_content(datetime.now())
        for pet in json_doc:
            print(pet)
