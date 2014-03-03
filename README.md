nagios-arduino
==============

Software for the Integration of Nagios and arduino

The data centre at the Galician Institute of High Energy Physics (IGFAE) of the
Santiago de Compostela University (USC) is a computing cluster with about 150 nodes and
1250 cores that hosts the LHCb Tiers 2 and 3. In this small data centre, and of course in
similar or bigger ones, it is very important to keep optimal conditions of temperature, humidity
and pressure. Therefore, it is a necessity to monitor the environment and be able to trigger
alarms when operating outside the recommended settings.
There are currently many tools and systems developed for data centre monitoring, but
until recent years all of them were of commercial nature and expensive. In recent years there
has been an increasing interest in the use of technologies based on Arduino due to its open
hardware licensing and the low cost of this type of components. In this article we describe
the system developed to monitor IGFAE’s data centre, which integrates an Arduino controlled
sensor network with the Nagios monitoring software. Sensors of several types, temperature,
humidity and pressure, are connected to the Arduino board. The Nagios software is in charge of
monitoring the various sensors and, with the help of Nagiosgraph, to keep track of the historic
data and to produce the plots. An Arduino program, developed in house, provides the Nagios
plugin with the readout of one or several sensors depending on the plugin’s request. The Nagios
plugin for reading the temperature sensors also broadcasts an SNMP trap when the temperature
gets out of the allowed operating range.



