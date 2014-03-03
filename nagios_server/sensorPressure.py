from re import compile
from sensor import Sensor
from locale import atof

class pressure(Sensor):
    def __init__(self, time=''):
        if time:
            super(pressure,self).__init__('CPD','Pressure',time)
            self.reset()
            self.setExternal()
        self.reset()

    def reset(self):
        super(pressure,self).reset()
        self._outputString="Could not obtain pressure data"

    def readSensor(self,line):
        extractData=compile(r'Pressure: ([0-9.]*) hPa, Temperature: ([0-9.]*) C')
        pressureData=extractData.search(line)
        if pressureData:            
            self._run=True
            self._perfdata=line[:-1]
            [self._pressure, self._temperature]=[ atof(x) for x in
                                                  pressureData.groups() ]
            if self._pressure>self._highCritical or self._pressure<self._lowCritical:
                self._error=True
            elif self._pressure<self._lowWarning or self._pressure>self._highWarning:
                self._warn=True

                    
    def process(self):
        if self._run:
            if self._error or self._warn:
                str="The pressure is %s." % self._pressure
                if self._error:
                    self._outputString="ERROR: "+str
                    self._exitCode=2
                else:
                    self._outputString="WARNING: "+str
                    self._exitCode=1
            else:
                self._outputString="Pressure is OK."
                self._exitCode=0
                
def main(argv):
    from re import match
    from optparse import OptionParser
    from sys import stdin
    
    testArgs=compile(r'(\d+):(\d+)')
    errorString="%s limits: The lower limit must be smaller than the higher limit"
    parser=OptionParser()
    parser.add_option('-c','--criticalrange', action='store',
                      default='940:1020',dest='criticalRange',
                      help="Range of critical values in the form low:highhPa")
    parser.add_option('-w','--warningrange', action='store',
                      default='920:1040', dest='warningRange',
                      help="Range of Warning values in the form low:highhPa")
    (options,args)=parser.parse_args(argv)

    try:
        check=pressure()
    except Exception, error:
        print("Could not instantiate class: %s" % error)
        return -1

    returnCode=check.processParameters(options.criticalRange,
                                       options.warningRange)
    if not returnCode['OK']:
        print(returnCode['Message'])
        return -1
    
    for line in stdin:
        if match(r'Pressure.*',line):
            check.readSensor(line)
            check.process()
            
    print check.getOutputString()
    return check.getExitCode()

if __name__=="__main__":
    from sys import argv,exit
    exit(main(argv))
