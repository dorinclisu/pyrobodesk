

import pyrobodesk.manager
from pyrobodesk.manager import *



def do_this_that_and_the_other():
    manager = pyrobodesk.manager.FunctionManager('~/.pyrobodesk/functions')
    manager.load_functions()

    city = 'new york'
    #weather = manager.get_weather(city=city)
    weather = manager.play('get_weather', city=city)

    #output = manager.calc_celsius_to_fahrenheit(tc=weather['temperature'])
    output = manager.play('calc_celsius_to_fahrenheit', tc=weather['temperature'])

    print('There are {} degrees F in {}'.format(output['tf'], city))



if __name__ == '__main__':
    do_this_that_and_the_other()
