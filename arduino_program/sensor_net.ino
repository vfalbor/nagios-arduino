// Environment Sensor
// Measures temperature, pressure and humidity on request via
// the serial port.
//
// Temperature sensors are located in group of six on different 
// Arduino pins
//
//
// Uses external power
// 
// Arduino Board              DS18B20  ...  DS18B20
//
//                     +5 VDC
//                     |       2(DQ)         2(DQ)
//                    4.7K       |             |
// 22 -----------------|---------|----...------| 
// Note that term 1 is connected to a +5V source and 
//   term 3 is grounded.
//
// 

#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>

#include <Adafruit_Sensor.h>
#include <Adafruit_BMP085.h>

Adafruit_BMP085 bmp = Adafruit_BMP085(10085);

#include <Sensirion.h>

#define TEMPERATURE_SENSORS_PER_CABLE 6

byte sensors[4][6][8]={{{0x28,0x47,0x36,0xA9,0x02,0x00,0x00,0x83},{0x28,0x83,0x87,0xBB,0x02,0x00,0x00,0x7D},{0x28,0x46,0xE9,0x2A,0x03,0x00,0x00,0x7F},      
                        {0x28,0x99,0x69,0xBB,0x02,0x00,0x00,0x91},{0x28,0x9A,0xE2,0x08,0x03,0x00,0x00,0xC1},{0x28,0xD5,0x54,0xBB,0x02,0x00,0x00,0xF1}},
                       {{0x28,0xDF,0xD8,0x08,0x03,0x00,0x00,0x66},{0x28,0xD2,0x1E,0xA9,0x02,0x00,0x00,0x1F},{0x28,0xC4,0x2E,0xA9,0x02,0x00,0x00,0x72},
                        {0x28,0x61,0x47,0xBB,0x02,0x00,0x00,0x18},{0x28,0x76,0x8D,0xF1,0x03,0x00,0x00,0x09},{0x28,0xC8,0x99,0xF1,0x03,0x00,0x00,0x7E}},
                       {{0x28,0x36,0x85,0xF1,0x03,0x00,0x00,0x42},{0x28,0x3F,0xB6,0xF1,0x03,0x00,0x00,0x1E},{0x28,0x56,0xBE,0xF1,0x03,0x00,0x00,0x75},
                        {0x28,0xF8,0x98,0xF1,0x03,0x00,0x00,0x5E},{0x28,0x04,0xC1,0xF1,0x03,0x00,0x00,0x37},{0x28,0x70,0x9E,0xF1,0x03,0x00,0x00,0x89}},
                       {{0x28,0x66,0xBA,0xF1,0x03,0x00,0x00,0x87},{0x28,0x9E,0x8C,0xF1,0x03,0x00,0x00,0x4C},{0x28,0xCA,0x9A,0xF1,0x03,0x00,0x00,0x5E},
                        {0x28,0x52,0xC2,0xF1,0x03,0x00,0x00,0xE5},{0x28,0x54,0xC6,0xF1,0x03,0x00,0x00,0x48},{0x28,0xFE,0xBF,0xF1,0x03,0x00,0x00,0x45}}};

OneWire sensor_line[4]={OneWire(22),OneWire(24),OneWire(26),OneWire(28)};
DallasTemperature lines[4]={DallasTemperature(&sensor_line[0]),DallasTemperature(&sensor_line[1]),DallasTemperature(&sensor_line[2]),DallasTemperature(&sensor_line[3])};

int bmpaccesible;

const uint8_t dataPin =  9;              // SHT serial data
const uint8_t sclkPin =  8;              // SHT serial clock

Sensirion sht = Sensirion(dataPin, sclkPin);

void setup() {
  int i;

  Serial.begin(115200);
  bmpaccesible=1;
  if(!bmp.begin())
  {
    /* There was a problem detecting the BMP085 ... check your connections */
    Serial.println("Ooops, no BMP085 detected ... Check your wiring or I2C ADDR!");
    bmpaccesible=0;
  }

  for(i=0;i<4;i++) {
    lines[i].begin();
  }

  delay(100);
}

void loop() {
  int cable,sensor,i;
  byte readByte;
  
  while( Serial.available() < 1 );
  
  readByte=Serial.read();
  switch( char(readByte) ) {
    case 'A':
      for (i=1;i<=4;i++) {
        readCableDS18B20s(i);
      }
      readSHT75(HUMI);
      readBMP085Pressure();
      Serial.println("End");
      break;
    case 'T':
      readByte=Serial.read();
      cable=int(readByte)-48;
      if ( (cable > 0) && (cable < 5) ) {
        while ( !Serial.available() );
        readByte=Serial.read();
        if ( char(readByte) == 'A' ) {
          readCableDS18B20s(cable);
        } else {
          sensor=int(readByte)-48;
          if ( (sensor > 0) && (sensor < 7) ) {
            readDS18B20(cable, sensor);
          }
        }
      }
      break;
    case 'H':
      readByte=Serial.read();
      //Serial.println("Reading Humidity sensor ");
      if ( char(readByte) == 'h' ) {
        readSHT75(HUMI);
      } else if ( char(readByte) == 't' ) {
        readSHT75(TEMP);
      }
      break;
    case 'P':
      readByte=Serial.read();
      //Serial.println("Reading Pressure sensor ");
      if ( bmpaccesible && char(readByte) == 'p' ) {
        readBMP085Pressure();
      } else if ( bmpaccesible && char(readByte) == 't' ) {
        readBMP085Temperature();
      }
      break;
  }
       
  delay(5000);
}

void readSHT75(byte measType) {
  float temperature, humidity, dewpoint;
  uint16_t rawData;
  
  sht.measTemp(&rawData);
  temperature = sht.calcTemp(rawData);
  
  if ( measType == HUMI ) {
    sht.measHumi(&rawData);
    humidity = sht.calcHumi(rawData, temperature); // Convert raw sensor data
    dewpoint = sht.calcDewpoint(humidity, temperature); 
    Serial.print("Humidity: ");
    Serial.print(humidity,2);
    Serial.print(" %, ");
    Serial.print("Dew Point: ");
    Serial.print(dewpoint,2);
    Serial.print(" C, ");
    Serial.print("Temperature: ");
  } else {
    Serial.print("SHT75 Temperature: ");
  }
  
  Serial.print(temperature,2);
  Serial.println(" C");
}

void readBMP085Pressure() {
  /* Get a new sensor event */ 
  sensors_event_t event;
  float temperature;
  bmp.getEvent(&event);
  bmp.getTemperature(&temperature);

 
  /* Display the results (barometric pressure is measure in hPa) */
  if (event.pressure)
  {
    /* Display atmospheric pressure in hPa */
    Serial.print("Pressure: ");
    Serial.print(event.pressure,2);
    Serial.print(" hPa, Temperature: ");
    Serial.print(temperature,2);
    Serial.println(" C");
  }
}

void readBMP085Temperature() {
  /* Get a new sensor event */ 
  float temperature;
  bmp.getTemperature(&temperature);
 
  /* Display temperature */    
  Serial.print("BMP085 Temperature: ");
  Serial.print(temperature,2);
  Serial.println(" C");
}

void readDS18B20(int cable,int sensor){
  float temperature;
  
  /* Substract one unit from cable and sensors because
     C arrays start at 0 */
  cable=cable-1;
  sensor=sensor-1;
  
  lines[cable].requestTemperaturesByAddress(sensors[cable][sensor]);
  temperature=lines[cable].getTempC(sensors[cable][sensor]);
  
  Serial.print("DS18B20 Temperature: ");
  Serial.print(temperature,2);
  Serial.println(" C");
}

void readCableDS18B20s(int cable) {
  float temperatures[6]={0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
  int i;

  /* Substract one unit from cable because C arrays start at 0 */
  cable=cable-1;
  
  lines[cable].requestTemperatures();
  
  for (i=0;i<TEMPERATURE_SENSORS_PER_CABLE;i++) {
    temperatures[i]=lines[cable].getTempC(sensors[cable][i]);
  }
  Serial.print("Temperature Rack ");
  Serial.print(cable+1);
  Serial.print(": ");
  for (i=0;i<TEMPERATURE_SENSORS_PER_CABLE-1;i++) {
    Serial.print(temperatures[i],2);
    Serial.print(", ");
  }
  Serial.println(temperatures[TEMPERATURE_SENSORS_PER_CABLE-1],2);
}

