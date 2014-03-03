from re import compile
from sensor import Sensor
from locale import atof

def S_ERROR( messageString = '' ):
  return { 'OK' : False, 'Message' : str( messageString )  }

class humidity(Sensor):
    def __init__(self,time=''):
        if time:
            super(humidity,self).__init__('CPD','Humidity',time)
            self.reset()
            self.setExternal()
        self.reset()

    def reset(self):
        super(humidity,self).reset()        
        self._outputString="Could not obtain humidity data"

    def processParameters(self,*strings):
        try:
            self._DPCritical=atof(strings[2])
        except ValueError, error:
            return S_ERROR("Dew Point Critical: %s" % error)
        try:
            self._DPWarning=atof(strings[3])
        except ValueError, error:
            return S_ERROR("Dew Point Warning: %s" % error)
        return super(humidity,self).processParameters(*strings[0:2])
                              
    def readSensor(self,line):
        extractData=compile(r'Humidity: ([0-9.]*) %, '+ \
                            r'Dew Point: ([0-9.]*) C, ' + \
                            r'Temperature: ([0-9.]*) C')
        humidityData=extractData.search(line)
        if humidityData:
            self._run=True
            self._perfdata=line[:-1]
            [self._humidity, self._dewPoint, self._temperature]=[atof(x) for x in humidityData.groups() ]
            if self._humidity>self._highCritical or self._humidity<self._lowCritical:
                self._error=self._error | 1
            elif self._humidity>self._highWarning or self._humidity<self._lowWarning:
                self._warn=self._warn | 1
            if self._dewPoint>=self._DPCritical:
                self._error=self._error | 2
            elif self._dewPoint>=self._DPWarning:
                self._warn=self._warn | 2

    def process(self):
        if self._run:
            if self._error or self._warn:
                if self._error&1:
                    str = "CRITICAL: "
                else:
                    str = "WARNING: "
                str = str + "The humidity is %s" % self._humidity
                if self._error>2 or self._warn>2:
                    if (self._error|self._warn)==2:
                        str='T'
                    else:
                        str=str+' and t'
                    str=str+"he Dew Point is %s" % self._dewPoint
                self._outputString=str+'.'
                if self._error:
                    self._exitCode=2
                else:
                    self._exitCode=1
            else:
                self._outputString="Humidity OK." 
                self._exitCode=0

from optparse import Option

class MultipleOption(Option):
    ACTIONS = Option.ACTIONS + ("extend",)
    STORE_ACTIONS = Option.STORE_ACTIONS + ("extend",)
    TYPED_ACTIONS = Option.TYPED_ACTIONS + ("extend",)
    ALWAYS_TYPED_ACTIONS = Option.ALWAYS_TYPED_ACTIONS + ("extend",)
    __HUMIDITYREGEX = compile(r'^(\d+):(\d+)%$')
    __DEWPOINTREGEX = compile(r'^(\d+)DP')
    __SPLITREGEX = compile(r',\s*')
    
    def take_action(self, action, dest, opt, value, values, parser):
        if action == "extend":
            if not hasattr(self,'_extended'):
                self.__extended=False
                self.__count=0
            self.__count+=1
            if self.__extended and self.__count>2:
                values.ensure_value(dest, []).append(value)
            else:
                data=vars(values)[dest]
                temp=self.__SPLITREGEX.split(value)
                for item in temp:
                    if self.__HUMIDITYREGEX.search(item):
                        data[0]=':'.join(self.__HUMIDITYREGEX.search(item).groups())
                    elif self.__DEWPOINTREGEX.search(item):
                        data[1]=self.__DEWPOINTREGEX.sub(r'\1',item)
                values._update_careful({dest: data})
            self.__extended=True
        else:
            Option.take_action(self, action, dest, opt, value, values, parser)


def main(argv):
    from re import match
    from optparse import OptionParser
    from sys import stdin
    
    parser=OptionParser(option_class=MultipleOption)
    parser.add_option('-c','--criticalrange', action='extend',
                      default=['20:80','18'], dest='criticalRange',
                      help="Range of critical values in the form low:high% for humidity values and numberDP for Dew point temperatures")
    parser.add_option('-w','--warningrange', action='extend',
                      default=['30:70','13'], dest='warningRange',
                      help="Range of Warning values in the form low:high% for humidity values and numberDP for Dew point temperatures")
    (options,args)=parser.parse_args(argv)

    try:
        check=humidity()
    except Exception, error:
        print("Could not instantiate class: %s" % error)
        return -1
    
    returnCode=check.processParameters(options.criticalRange[0],
                                       options.warningRange[0],
                                       options.criticalRange[1],
                                       options.warningRange[1])
    if not returnCode['OK']:
        print(returnCode['Message'])
        return -1

    for line in stdin:
        if match(r'Humidity.*',line):
            check.readSensor(line)
            check.process()

    print check.getOutputString()
    return check.getExitCode()

if __name__=="__main__":
    from sys import argv,exit
    exit(main(argv))

