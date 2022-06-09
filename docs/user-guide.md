---
layout: page
title: User Guide
permalink: /user-guide/
---

- Seismic Instrumentation
- FDSN StationXML
- Overview
- The 5 Levels of Response Detail
- Instrument Response Libraries

### 1. Seismic Instrumentation

Geophysical data are recorded by an instrument that imparts its own signature onto the data.

A recording system (sensor + datalogger)

### 2. FDSN StationXML

```Namespace: http://www.fdsn.org/xml/station/1```

[StationXML](http://www.fdsn.org/xml/station) was developed through the International Federation of Digital Seismograph Networks (FDSN) to provide a standard format 
for geophysical metadata. It was intended as a sucessor to [SEED 2.4](http://www.fdsn.org/publications.htm).

<em>Example 1: A sample StationXML file</em>

```xml
 <FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1" 
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xsi:schemaLocation="http://www.fdsn.org/xml/station/1  http://www.fdsn.org/xml/station/fdsn-station-1.2.xsd" 
    schemaVersion="1.2">
    <Source>IRISDMC</Source>
    <Sender>IRISDMC</Sender>
    <Module>Yasmine</Module>
    <Created>2022-02-21T20:27:54.6270Z</Created>
    <Network code="IU" startDate="1988-01-01T00:00:00Z">
        <Description>Global Seismograph Network - IRIS/USGS (GSN)</Description>
        <Identifier type="DOI">10.7914/SN/IU</Identifier>
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
 <FDSNStationXML>
```

### 3. The 5 Levels of Response Detail

In this tutorial, we will walk through this heirarchy from the top-down, beginning with 
the FDSN StationXML declaration itself and adding increasingly more specific metadata at 
subsequent levels.

1. FDSNStationXML
2. Network
3. Station
4. Channel
5. Response

#### 3.1. Create a StationXML file
#### 3.2. Create a network
#### 3.3. Create a station
#### 3.4. Create a channel
1. Describe a channel
   - Location code
   - Start date
   - End date
   - Latitude
   - Longitude
   - Elevation
   - Depth
2. Select an Instrument Response Library
    - AROL, NRL or I don't need a response
3. Describe the response
   1. Describe the Datalogger
      - Manufacturer, Kinemetrics
      - Model, e.g. Etna
      - Pre-amplifier gain. e.g. 6db
      - Sample rate, e.g. 1000 sps
      - Final filter phase type, e.g. Linear Phase
   2. Describe the Sensor
      - Manufacturer, e.g. Streckeisen
      - Model, e.g. STS-1
      - Gain or samples per second
   3. Response
Channel prefix and orientation
Channel, dip, azimuth

#### 3.5. Create a response

### 4. Digitizers

 
To convert the analog signal of a seismometer into into a machine-readable digital signal, we use a Digitizers, otherwise known as Dataloggers or Analog to Digital Converters (ADC).

### 5. Instrument Response

A recording system comprises two parts:
1. Sensors
2. Dataloggers

Instrument response libraries provide access to schema object definition files for well-known components that fall into these classes.

From within Yasmine, you have access to the following repositories:

1. [The Nominal Response Library](https://ds.iris.edu/ds/nrl/)
2. [The Atomic Response Objects Library (AROL)](https://gitlab.com/resif/arol/)
    - The AROL contains metadata descriptions of earth science observation instruments.

#### 5.1. Definitions

    def.  instrument response : The signature a recording instruments imparts on the geophysical data.
    def.  sampling rate : How often the digitizer takes a voltage and converts it to counts, typically measure in Hertz or samples per second