""" ... """

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
        """ k doesn't matter.  Need to check if animal lastUpdated is greater than PatFinderSenor last_updated """
        update_available = 0
        if not self._request_allowed():
            has_update = self.get_all()
            for pet in has_update[0]:
                if datetime.strptime(pet['pet_update'], "%Y-%m-%d"'T'"%H:%M:%S"'Z') > datetime.fromtimestamp(self.d['last_updated']):
                    update_available = 1
                    break
            #fileTime = datetime.strptime(self.d['last_updated'], )
            #diffTime = k - datetime.strptime("2018-11-08T22:41:24Z", "%Y-%m-%d"'T'"%H:%M:%S"'Z')
            return update_available
        else:
            return 0

    def get_content(self, k):
        """ ignoring k for now .. just sending the whole thing """
        return self.get_all()

    def get_all(self):
        """ Request information on all animals available for adoption """
        if self._request_allowed():
            url = self.d['service_url']+"%s?key=%s&count=%d&id=%s&format=%s"
            response = requests.get(url % (self.d['service_method'], self.d['key'], self.d['return_count'], self.d['shelter_id'], self.d['format']))
            self.d['times_used'] += 1
            self.d['date'] = str(time.strftime("%m %d %y", time.gmtime()))
            self.d['last_updated'] = int(time.time())
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
                return self._read_saved_data()
            if response is not None and response.status_code == 200:
                try:
                    with open(PetFinderSensor.__SAVED_RECORDS, 'w') as backup:
                        backup.write(response.text)
                        logging.info("Saved response from %s" % (self.d['service_url']))
                except (Exception, OSError, ValueError) as e:
                    logging.warning("File response write failed: " + str(e))
                finally:
                    return [self._create_record(response_json)]
            else:
                logging.warning("The response was bad, using saved data")
                return self._read_saved_data()
        else:
            logging.warning("The request was not allowed, using saved data")
            return self._read_saved_data()

    @staticmethod
    def _create_record(d):
        """ Request a list of dictionaries with details about each pet available from the shelter """
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
                           'pet_desciption': d['petfinder']['pets']['pet'][pet]['description']['$t'],
                           'pet_photo': use_this_photo
                           })
        return record

    def _request_allowed(self):
        # This captured the real allowance of 10,000 times per day
        # Simplified to new variation for easier grading  :)
        # if self.d['times_used'] < self.d['request_delta']:
        #     return True
        # else:
        #     delta = datetime.now() - datetime.strptime(self.d['date'], "%m %d %y")
        #     if delta.days < 1:
        #         # print("Too soon, use Offline status")
        #         return False
        #     else:
        #         self.d['times_used'] = 1
        #         self.d['date'] = str(time.strftime("%m %d %y", time.gmtime()))
        #         self._save_settings()  # Saves that a request has been made to the service
        #         return True
        return not self.d['offline_mode'] and (int(time.time()) - self.d['last_updated']) > self.d['update_frequency']

    def _save_settings(self):
        with open(os.path.join(os.path.dirname(__file__), PetFinderSensor.__CONFIG_FILE), 'w') as outfile:
            json.dump(self.d, outfile)

    def _read_saved_data(self):
        try:
            with open(PetFinderSensor.__SAVED_RECORDS) as saved_data:
                response = saved_data.read()
                logging.info("Read response from saved file")
            return [self._create_record(json.loads(response))]
        except (Exception, OSError, ValueError) as e:
            logging.critical("Reading saved data error is: " + str(e))
            return None


if __name__ == "__main__":
    sr = PetFinderSensor()
    print("This is me : " + str(sr))
    print("let's go ..")
    #json_doc = sr.get_all()
    #print(json_doc)

    if sr.has_updates(datetime.now()):
        sr.get_content(datetime.now())

