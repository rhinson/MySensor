# 2018FA-CSIS-250-3580-Project2

## A Sensor using the PetFinder API

Inheriting from Sensor, PetFinderSensor is a simple software sensor, using the web service available 
at https://api.petfinder.com/, which is documented here: https://www.petfinder.com/developers/api-docs

While the imposed rate limit from PetFinder is 10,000 requests per day, for this demo 
I have set the rate limit to once every 10 seconds

Therefore, the sensor will request a complete, or updated, list of pets from the El Cajon Animal Shelter 
when asked, but not more frequently than once per ten seconds.

To provide a list of pets, even after a restart (with downtime of less than 10 secs) or during request within  
the 10 second window, the processed webservice data gets cached as a text file.

Data is returned as a list of dictionaries with each pet contained within their own dictionary.

Data Returned per pet is:
* pet_name
* pet_id
* pet_age
* pet_sex
* pet_type
* pet_update
* pet_description
* pet_photo
