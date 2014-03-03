from re import compile
from sensorHumidity import humidity
from sensorPressure import pressure
from sensorTemperature import temperature


from optparse import Option

class MultipleOption(Option):
    ACTIONS = Option.ACTIONS + ("extend",)
    STORE_ACTIONS = Option.STORE_ACTIONS + ("extend",)
    TYPED_ACTIONS = Option.TYPED_ACTIONS + ("extend",)
    ALWAYS_TYPED_ACTIONS = Option.ALWAYS_TYPED_ACTIONS + ("extend",)
    __HUMIDITYREGEX = compile(r'^(\d+):(\d+)%$')
    __PRESSUREREGEX = compile(r'^(\d+):(\d+)hPa$')
    __TEMPERATUREREGEX = compile(r'^(\d+):(\d+)C$')
    __DEWPOINTREGEX = compile(r'^(\d+)DP')
    __SPLITREGEX = compile(r',\s*')
    
    def take_action(self, action, dest, opt, value, values, parser):
        if action == "extend":
            if not hasattr(self,'_extended'):
                self.__extended=False
                self.__count=0
            self.__count+=1
            if self.__extended and self.__count>4:
                values.ensure_value(dest, []).append(value)
            else:
                data=vars(values)[dest]
                temp=self.__SPLITREGEX.split(value)
                for item in temp:
                    if self.__PRESSUREREGEX.search(item):
                        data[0]=':'.join(self.__PRESSUREREGEX.search(item).groups())
                    elif self.__TEMPERATUREREGEX.search(item):
                        data[1]=':'.join(self.__TEMPERATUREREGEX.search(item).groups())
                    elif self.__HUMIDITYREGEX.search(item):
                        data[2]=':'.join(self.__HUMIDITYREGEX.search(item).groups())
                    elif self.__DEWPOINTREGEX.search(item):
                        data[3]=self.__DEWPOINTREGEX.sub(r'\1',item)
                values._update_careful({dest: data})
            self.__extended=True
        else:
            Option.take_action(self, action, dest, opt, value, values, parser)

def main(argv):
    from time import time, sleep
    from sys import stdin
    from re import match
    from optparse import OptionParser

    timeMeassurement=int(time())

    tempRegex=compile(r'Temperature Rack (\d+): (.*)$')
    
    parser=OptionParser(option_class=MultipleOption)
    parser.add_option('-c','--criticalrange', action='extend',
                      default=['940:1020', '13:38', '20:80', '18'],
                      dest='criticalRange',
                      help="Range of critical values in the form low:high[%,C,hPa] for humidity, temperature and pressure values and numberDP for Dew point temperatures")
    parser.add_option('-w','--warningrange', action='extend',
                      default=['920:1040', '16:30', '25:75', '13'],
                      dest='warningRange',
                      help="Range of Warning values in the form low:high[%,C,hPa] for humidity, temperature and pressure values and numberDP for Dew point temperatures")
    parser.add_option('-s','--sensorline',action='extend',
                      default=1,dest='sensorLine',
                      help="Sensor line to read")
    parser.add_option('-f','--sensorSet',action='extend', type='choice',
                      choices=['Front', 'Back', 'front', 'back', 'f','b'],
                      default='Front', dest='sensorSet',
                      help="Whether to meassure the sensors at the front or the back of a rack") 
    (options,args)=parser.parse_args(argv)

    try:
        press=pressure()
    except Exception, error:
        print("Could not instantiate class: %s" % error)
        return -1

    returnCode=press.processParameters(options.criticalRange[0],
                                       options.warningRange[0])
    if not returnCode['OK']:
        print(returnCode['Message'])
        return -1

    try:
        temp=temperature('Rack1',timeMeassurement)
    except Exception, error:
        print("Could not instantiate class: %s" % error)
        return -1

    returnCode=temp.processParameters(options.criticalRange[1],
                                       options.warningRange[1])
    if not returnCode['OK']:
        print(returnCode['Message'])
        return -1

    try:
        hum=humidity(timeMeassurement)
    except Exception, error:
        print("Could not instantiate class: %s" % error)
        return -1
    
    returnCode=hum.processParameters(options.criticalRange[2],
                                     options.warningRange[2],
                                     options.criticalRange[3],
                                     options.warningRange[3])

    if not returnCode['OK']:
        print(returnCode['Message'])
        return -1

    for line in stdin:
        tempData=tempRegex.search(line)
        if match(r'Pressure.*',line):
            press.readSensor(line)
            press.process()
        elif tempData:
            temp.reset()
            temp.setHost('Rack%s' % tempData.group(1))
            temp.readSensor(tempData.group(2))
            temp.process()
            temp.submitExternalCommand()
	    #sleep(5)
        elif match("Humidity:.*",line):
            hum.readSensor(line)
            hum.process()
            hum.submitExternalCommand()

    print press.getOutputString()
    return press.getExitCode()

if __name__=="__main__":
    from sys import argv,exit
    exit(main(argv))
