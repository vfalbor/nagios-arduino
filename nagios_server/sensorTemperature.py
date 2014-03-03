from re import compile,match
from sensor import Sensor
from locale import atof

class temperature(Sensor):
    def __init__(self, rack='', time=''):
        if rack and time:
            super(temperature,self).__init__(rack,'RackTemperature',time)
            self.reset()
            self.setExternal()
        elif rack or time:
            if time:
                raise Exception("Rack identification must be provided")
            else:
                raise Exception("Unix time must be provided")
        else:
            self.reset()

    def reset(self):
        super(temperature,self).reset()
        self._outputString="Could not obtain temperature data"
        self._errorSensor={'f':[],'b':[]}
        self._warningSensor={'f':[],'b':[]}

    def readSensor(self, line, place='Front'):
        extractTemp=compile(r'Sensor [0-9]: ')
        if place[0].lower()=='f' or place[0].lower()!='b':
            pos='f'
            sensorPos=range(0,3)
            Temps=[]
        else:
            pos='b'
            sensorPos=range(3,6)
            Temps=['0','0','0']
                        
        sensors=line.split(', ')
        if len(sensors)>5:            
            self._run=True
            self._perfdata=', '.join(['Sensor %s: %s' % (i+1,sensors[i])\
                                      for i in range(0,6)])
            for i in sensorPos:
                temp=extractTemp.sub(r'',sensors[i])
                Temps.append(temp)
                temp=atof(temp)
                if temp>self._highCritical or temp<self._lowCritical:
                    self._error=self._error | (1<<i)
                    self._errorSensor[pos].append([i+1,Temps[i]])
                elif temp<self._lowWarning or temp>self._highWarning:
                    self._warn=self._warn | (1<<i)
                    self._warningSensor[pos].append([i+1,Temps[i]])
                    
    def process(self):
        if self._run:
            if self._error or self._warn:
                str="The temperature is "
                if self._error&7:
                    str=str+"critical at sensors: " + \
                         "%s in the front" % self._errorSensor['f']
                    if self._error>7:
                        str = str + ' and  ' + self._errorSensor['b'] + \
                              ' in the back.' 
                elif self._error:
                    str = str + "critical at sensors: " + \
                         "%s in the back" % self._errorSensor['b']
                if self._warn and self._error:
                    str = str + " and it is "
                if self._warn&7:
                    str = str + "near critical at sensors: " + \
                         "%s in the front" % self._warningSensor['f']
                    if self._warn>7:
                        str = str + ' and  ' + self._warningSensor['b'] + \
                              ' in the back.' 
                elif self._warn:
                    str = str + "near critical at sensors: " + \
                         "%s in the back" % self._warningSensor['b']
                self._outputString=str+'.'
                if self._error:
                    self._exitCode=2
                else:
                    self._exitCode=1
            else:
                self._outputString="All Temperatures are OK."
                self._exitCode=0
    
def main(argv):
    from re import search
    from optparse import OptionParser
    from sys import stdin
    
    parser=OptionParser()
    parser.add_option('-c','--criticalrange', action='store',
                      default='13:38',dest='criticalRange',
                      help="Range of critical values in the form low:high")
    parser.add_option('-w','--warningrange', action='store',
                      default='16:30', dest='warningRange',
                      help="Range of Warning values in the form low:high")
    parser.add_option('-s','--sensorline',action='store',
                      default=1,dest='sensorLine',
                      help="Sensor line to read")
    parser.add_option('-f','--sensorSet',action='store', type='choice',
                      choices=['Front', 'Back', 'front', 'back', 'f','b'],
                      default='Front', dest='sensorSet',
                      help="Whether to meassure the sensors at the front or the back of a rack") 
    (options,args)=parser.parse_args(argv)

    try:
        check=temperature()
    except Exception, error:
        print("Could not instantiate class: %s" % error)
        return -1

    returnCode=check.processParameters(options.criticalRange,
                                       options.warningRange)
    if not returnCode['OK']:
        print(returnCode['Message'])
        return -1
    
    for line in stdin:
        tempData=search(r'Temperature Rack %s: (.*)$' % options.sensorLine,
                        line)
        if tempData:
            check.readSensor(tempData.group(1),options.sensorSet)
            check.process()

    print(check.getOutputString())
    return check.getExitCode()

if __name__=="__main__":
    from sys import argv,exit
    exit(main(argv))
