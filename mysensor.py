""" ... """
from sensor import Sensor
import json
import os
import time
import requests
from datetime import datetime


class MySensor(Sensor):

    __CONFIG_FILE = 'mysensor.json'
    __SAVED_RECORDS = 'saved_records.json'


    def __init__(self):
        """ read sensor settings from config file """
        with open(MySensor.__CONFIG_FILE) as json_text:
            self.d = json.load(json_text)
        print("This sensor just woke up .. ready to call " + self.d['service_url'])


    def has_updates(self, k):
        """ ignoring k for now """
        return 1 if self._request_allowed() else 0

    def get_content(self, k):
        """ ignoring k for now .. just sending the whole thing """
        return self.get_all()

    def get_all(self):
        if self._request_allowed():
            url = self.d['service_url']+self.d['service_method']+"?key=%s&count=%d&location=%s&animal=%s&age=%s&format=%s"
            response = requests.get(url % (self.d['key'], self.d['return_count'], self.d['location'], self.d['animal'], self.d['age'], self.d['format']))
            self.d['times_used'] += 1
            self._save_settings()  # Saves that I've made a request to the service
            if response is not None and response.status_code == 20:
                with open(MySensor.__SAVED_RECORDS, 'w') as backup:
                    backup.write(response.text)
                return [self._create_record(json.loads(response.text))]
            else:
                with open(MySensor.__SAVED_RECORDS) as saved_data:
                    response = saved_data.read()
                return [self._create_record(json.loads(response))]

    @staticmethod
    def _create_record(d):
        record = {
                    'k': d['petfinder']['header']['timestamp']['$t'],
                    'pets_found': len(d['petfinder']['pets']['pet'])
                  }
        for pet in range(len(d['petfinder']['pets']['pet'])):
            pet_id = d['petfinder']['pets']['pet'][pet]['id']['$t']
            photo_list = []
            for photo in range(len(d['petfinder']['pets']['pet'][pet]['media']['photos']['photo'])):
                if d['petfinder']['pets']['pet'][pet]['media']['photos']['photo'][photo]['@size'] == 'x':
                    this_photo = d['petfinder']['pets']['pet'][pet]['media']['photos']['photo'][photo]['$t']
                    photo_list.append(this_photo)
            record[pet_id] = (d['petfinder']['pets']['pet'][pet]['name']['$t'],
                              d['petfinder']['pets']['pet'][pet]['sex']['$t'],
                              d['petfinder']['pets']['pet'][pet]['lastUpdate']['$t'],
                              photo_list)
        return record

    def _request_allowed(self):
        return int(self.d['times_used'] < self.d['request_delta'])

    def _save_settings(self):
        with open(os.path.join(os.path.dirname(__file__), MySensor.__CONFIG_FILE), 'w') as outfile:
            json.dump(self.d, outfile)


if __name__ == "__main__":
    sr = MySensor()
    print("This is me : " + str(sr))
    print("let's go ..")
    json_doc = sr.get_all()
    print(json_doc)


