"""
Sensor is an Abstract base classes for a GCCCD Software Sensor
The basic idea of a software sensor is that it can be asked to fetch data from an external Web Service.
The sensor then turns the data into useful information, e.g. telling which city has the nicest weather next weekend.

The sensor may require credentials to access the 3rd party web service; those need to be stored in a JSON file and
read during startup. Also all other configuration data, like location, zip-codes, GPS Coordinates must not be hardcoded,
but loaded from a JSON file.
The sensor must transparently protect itself from being asked to report information too frequently. I.e., the sensor is
responsible for working inside the limits, prescribed by the 3rd party web service, but without becoming unresponsive.
"""
__version__ = "1.0"
__author__ = "Wolf Paulus"
__email__ = "wolf.paulus@gcccd.edu"

from abc import ABC, abstractmethod


class Sensor(ABC):
    def __str__(self):
        return self.__class__.__name__

    @abstractmethod
    def has_updates(self, k):
        """ returns the number of new 'records' that the sensor can provide,
        where k is an identifier previously issued by this sensor."""
        return 0

    @abstractmethod
    def get_content(self, k):
        """ A list of dictionaries: all the new records, since k, newest one last
        E.g.
        [{'k'       : 0  a unique records identifier
          'date'    : string representation of datetime.datetime
          'caption' : 'Grossmont–Cuyamaca Community College District'
          'summary' : 'Grossmont–Cuyamaca Community College District is a California community college district'
          'story'   : (optional, either plaintext or markdown) 'The Grossmont–Cuyamaca Community College District is ..'
          'img'     : (optional link to a jpg or png) 'https://upload.wikimedia.org/wikipedia/.../logo.png'
          'origin'  : (optional link to the source) 'https://en.wikipedia.org/wiki/...'
        }]
        """
        return [{}]

    @abstractmethod
    def get_all(self):
        """ A list containing all available records oldest first. """
        return [{}]
