---
layout: page
title: User Guide
permalink: /user-guide/
---

- Seismic Instrumentation
- FDSN StationXML
- Overview
- The 5 Levels of Response Detail
- Instrument Response

### 1. Seismic Instrumentation

Geophysical data are recorded by an instrument that imparts its own signature onto the data.

### 2. The 5 Levels of Response Detail

In this tutorial, we will walk through this heirarchy from the top-down, beginning with the FDSN StationXML declaration itself and adding increasingly more specific metadata at subsequent levels.

1. FDSN StationXML
2. Network
3. Station
4. Channel
5. Response

#### 2.1. FDSN StationXML

> **Note:**
> If you are are unfamiliar with the format, read this introduction to [FDSN StationXML](yasmine-stationxml-editor/stationxml).

The quickest way to start producing metadata with Yasmine is work from existing StationXML files.

#### 2.2. Network

#### 2.3. Station

#### 2.4. Channel

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

#### 2.5. Instrument Response

A recording system comprises two parts:

1. Sensors
2. Dataloggers

Instrument response libraries provide access to schema object definition files for well-known components that fall into these classes.

From within Yasmine, you have access to the following repositories:

1. [The Nominal Response Library](https://ds.iris.edu/ds/nrl/)
2. [The Atomic Response Objects Library (AROL)](https://gitlab.com/resif/arol/)
    - The AROL contains metadata descriptions of earth science observation instruments.
  
##### 2.5.1. Sensors

##### 2.5.2. Dataloggers

To convert the analog signal of a seismometer into into a machine-readable digital signal, we use a Dataloggers, otherwise known as Digitizers or Analog to Digital Converters (ADC).

### 3. Definitions

*def.*  instrument response : The signature a recording instruments imparts on the geophysical data.

*def.*  sampling rate : How often the digitizer takes a voltage and converts it to counts, typically measure in Hertz or samples per second