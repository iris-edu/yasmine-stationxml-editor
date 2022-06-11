---
layout: page
title: User Guide
permalink: /user-guide/
---
- [Seismic Instrumentation](#seismic-instrumentation)
- [Instrument Response](#instrument-response)
- [FDSN StationXML](#fdsn-stationxml)
  - [Managing Metadata with Yasmine](#managing-metadata-with-yasmine)
- [Levels of Response Detail](#levels-of-response-detail)
  - [Creating Metadata with Yasmine](#creating-metadata-with-yasmine)
- [Instrument Response Libraries](#instrument-response-libraries)

Before you begin, follow the [Installation](installation) instructions to get Yasmine up and running.

## Seismic Instrumentation

---

<img src="/yasmine-stationxml-editor/assets/images/from-instrument-to-data.drawio.png"/>

<em> Figure: An abstreact representation of a seismic network</em>

Modern seismic networks are desinged to support the communication of ground motion data between analog sensors and digital computers. ocmmuniaground motion into digital machine-readable sequences to central archiving facilities for storage.

Each observation made by a senso
Most seismic data is sent to central datacenters like the DMC for .
Seismic signals are measured, recorded, and transmitt

Modern seismic networks are local, regional, and global in nature.

## Instrument Response

> "The fundamental problem of communication is that of reproducing at one point either exactly or approximately a messaage selected at another point."

*Claude Shannon (1948)*

Geophysical data are recorded by an instrument that imparts its own signature onto the data.

## FDSN StationXML

---

```xml
 <?xml version="1.0" encoding="UTF-8"?>
 <FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1" 
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xsi:schemaLocation="http://www.fdsn.org/xml/station/1  http://www.fdsn.org/xml/station/fdsn-station-1.2.xsd" 
    schemaVersion="1.2">
```

<em>Figure: StationXML file declaration</em>

[FDSN StationXML](http://www.fdsn.org/xml/station) is a standard XML format to represent geophysical metadata developed by the International Federation of Digital Seismograph Networks (FDSN) as a sucessor to [SEED 2.4](http://www.fdsn.org/publications.htm). The current version of [StationXML v1.2](https://docs.fdsn.org/projects/stationxml/en/latest/) is described here:

> Namespace: <http://www.fdsn.org/xml/station/1><br/>
> Schema: <https://www.fdsn.org/xml/station/fdsn-station-1.2.xsd>

### Managing Metadata with Yasmine

The quickest way to become familiar with how to work with metadata in Yasmine is to import existing StationXML files. Yasmine uses this version of the schema without applying additional organization-specific rules such as those required by IRIS and used by the [StationXML Validator](http://github.com/iris-edu/stationxml-validator).


<img src="/yasmine-stationxml-editor/assets/images/xml-button.png" />

<details>

<summary>Exercise: Import XML</summary>

<input type="checkbox" /> Select an existing StationXML file or fetch one from the IRIS [fdsnws-station](http://service.iris.edu/fdsnws/station/1) service:

```bash
 curl --output out.xml 'https://service.iris.edu/fdsnws/station/1/query?net=XB&station=ELYSE&channel=MHU&level=response'
```

<input type="checkbox" /> From the `XML` tab, select `Import XML` then  your file

</details>

<details>

   <summary>Exercise: Validate XML</summary>

<input type="checkbox" /> From the `XML` tab, double-click a filename then `File -> Validate`

</details>

<details>

   <summary>Exercise: Extract XML</summary>

<input type="checkbox" /> From the `User Library` tab, select `Create a new library` and provide a name

<input type="checkbox" /> From the `XML` tab, double-click a filename and select a Network element then `Export -> Extract a selected network to user library`

</details>

<details>

<summary>Exercise: Export XML</summary>

<input type="checkbox" /> From the `XML` tab, highlight the filename then `Export as XML`

</details>

## Levels of Response Detail

---

<img src="/yasmine-stationxml-editor/assets/images/response-level-details.drawio.png"/>

<em>Figure: Levels of StationXML metadata</em>

The XML data model is semistructured and describes relations heirarchically where top-level elements releate to lower ones and those at the bottom are most specific.

### Creating Metadata with Yasmine


It is helpful to keep the data model in constructing your own StationXML. Yasmine facilitates a top-down approach to the creation of StationXML, beginning with the FDSN StationXML declaration itself and adding increasingly more specific metadata at subsequent levels

<details>
   <summary>Network</summary>
</details>

<details>
   <summary>Station</summary>
</details>

<details>

   <summary>Channel</summary>

- Location code
- Start date
- End date
- Latitude
- Longitude
- Elevation
- Depth

</details>

<details>

   <summary>Response</summary>

    1. Sensors
    2. Dataloggers

To convert the analog signal of a seismometer into into a machine-readable
digital signal, we use a Dataloggers, otherwise known as Digitizers orAnalog to Digital Converters (ADC).

    1. Select an Instrument Response Library
        a. AROL, NRL or I don't need a response
    2. Describe the response
       a. Describe the Datalogger
           - Manufacturer, Kinemetrics
           - Model, e.g. Etna
           - Pre-amplifier gain. e.g. 6db
           - Sample rate, e.g. 1000 sps
           - Final filter phase type, e.g. Linear Phase
      B. Describe the Sensor
         - Manufacturer, e.g. Streckeisen
         - Model, e.g. STS-1
         - Gain or samples per second
      C. Response
    3. Channel prefix and orientation
    4. Channel, dip, azimuth

## Instrument Response Libraries

---

> Schema: <https://ds.iris.edu/files/xml/station/fdsn-station-response-1.1.xsd>

These dictionaries provide access to schema object definition files for well-known components that fall into these classes.

1. [The Nominal Response Library (NRL)](https://ds.iris.edu/ds/nrl/)

- A library of recommended nominal responses created by IRIS from docunentation or  direct communication with the manufacturer's documentation and checked validty

1. [The Atomic Response Objects Library (AROL)](https://gitlab.com/resif/arol/)
   - Contains metadata descriptions of earth science observation instruments.
   - A new instrument response library under development by Résif
   - Easier, faster selection of instrument configurations
   - Includes a smaller set of instruments

</details>