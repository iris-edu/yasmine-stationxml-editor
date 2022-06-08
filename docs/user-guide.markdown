---
layout: page
title: User Guide
permalink: /user-guide/
---

- FDSN StationXML
- Overview
- The 5 Levels of Response Detail
- Instrument Response Libraries


## FDSN StationXML

    Namespace: http://www.fdsn.org/xml/station/1

[StationXML](www.fdsn.org/xml/station) was developed through the International Federation of Digital Seismograph Networks (FDSN) to provide a standard format for geophysical metadata. It was intended as a sucessor to [SEED 2.4](http://www.fdsn.org/publications.htm).

<em>Example 1</em>  A StationXML file
```xml
<?xml version="1.0" encoding="UTF-8"?>
<FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.fdsn.org/xml/station/1 http://www.fdsn.org/xml/station/fdsn-station-1.2.xsd" schemaVersion="1.2">
    <Source>IRISDMC</Source>
    <Sender>IRISDMC</Sender>
    <Module>Yasmine</Module>
    <Created>2022-02-21T20:27:54.6270Z</Created>
    <Network code="IU" startDate="1988-01-01T00:00:00Z">
        <Description>Global Seismograph Network - IRIS/USGS (GSN)</Description>
        <Identifier type="DOI">10.7914/SN/IU
        </Identifier>
        <Station code="ANMO" startDate="2002-11-19T21:07:00Z">
            <Description>(GSN) IRIS/USGS (IU) and ANSS</Description>
            <Latitude>34.94591</Latitude>
            <Longitude>-106.4572</Longitude>
            <Elevation>1820.0</Elevation>
            <Site>
                <Name>Albuquerque, New Mexico, USA</Name>
            </Site>
            <Channel code="BHZ" locationCode="00" startDate="2018-07-09T20:45:00Z">
                <Latitude>34.94591</Latitude>
                <Longitude>-106.4572</Longitude>
                <Elevation>1632.7</Elevation>
                <Depth>188</Depth>
                <Azimuth>0</Azimuth>
                <Dip>-90</Dip>
                <SampleRate>40</SampleRate>
                <Sensor>
                    <Description>Streckeisen STS-6A VBB Seismometer</Description>
                </Sensor>
                <Response>
                    <InstrumentSensitivity>
                        <Value>1.98475E9</Value>
                        <Frequency>0.02</Frequency>
                        <InputUnits>
                            <Name>m/s</Name>
                        </InputUnits>
                        <OutputUnits>
                            <Name>count</Name>
                        </OutputUnits>
                    </InstrumentSensitivity>
                </Response>
            </Channel>
        </Station>
    </Network>
</FDSNStationXML>
```

### The 5 Levels of Response Detail

In this tutorial, we will walk through this heirarchy from the top-down, beginning with 
the FDSN StationXML declaration itself and adding increasingly more specific metadata at 
subsequent levels.

1. FDSNStationXML
2. Network
3. Station
4. Channel
5. Response

<div class="mermaid">
graph LR
FDSNStationXML-->Network
Network-->Station
Station-->Channel
Channel-->Response
</div> 

#### I Create a StationXML file
#### II Create a network
#### III Create a station
#### IV Create a channel
#### V Create a response

### Instrument Response

- https://docs.fdsn.org/_/downloads/stationxml/en/latest/pdf/
- https://www.analog.com/en/analog-dialogue/articles/analog-to-digital-converter-clock-optimization.html
A recording system comprises two parts:
1. Sensor
2. Datalogger, or a Analog-to-Digital Converter (ADC)

def. instrument response : The signature a recording instruments imparts on the geophysical data.


#### Instrument Response Libraries

1. [NRL](https://ds.iris.edu/ds/nrl/)
2. [The Atomic Response Objects Library (AROL)](https://gitlab.com/resif/arol/) 

The AROL contains metadata descriptions of earth science observation instruments.