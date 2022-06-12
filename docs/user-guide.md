---
layout: page
title: User Guide
permalink: /user-guide/
---
- [Seismic Networks](#seismic-networks)
- [FDSN StationXML](#fdsn-stationxml)
  - [Exercise: Managing StationXML with Yasmine](#exercise-managing-stationxml-with-yasmine)
- [Levels of Response Detail](#levels-of-response-detail)
  - [Instrument Response Libraries](#instrument-response-libraries)
  - [Exercise: Create StationXML With Yasmine](#exercise-create-stationxml-with-yasmine)

Before you begin, follow the [Installation](installation) instructions to get Yasmine up and running.

## Seismic Networks

![Figure: An abstract representation of a modern seismic network](/yasmine-stationxml-editor/assets/images/from-instrument-to-data.drawio.png)

*Figure: Abstraction of modern seismic network*


**Yasmine (Yet Another Station Metadata INformation Editor)** v4.1.0-beta is an editor designed to facilitate the creation of geophysical station metadata in FDSN StationXML format.

## FDSN StationXML

```xml
 <?xml version="1.0" encoding="UTF-8"?>
 <FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1" 
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xsi:schemaLocation="http://www.fdsn.org/xml/station/1  http://www.fdsn.org/xml/station/fdsn-station-1.2.xsd" 
    schemaVersion="1.2">
```
*Figure: StationXML v1.2 file declaration ([schema](https://www.fdsn.org/xml/station/fdsn-station-1.2.xsd))*

[FDSN StationXML](http://www.fdsn.org/xml/station) is a standard XML format to represent geophysical metadata developed by the International Federation of Digital Seismograph Networks (FDSN) as a successor to [SEED 2.4](http://www.fdsn.org/publications.htm).

The current version of [StationXML v1.2](https://docs.fdsn.org/projects/stationxml/en/latest/) and is recognized by Yasmine. Some organizations require rules to validate in addition to those defined by the FDSN. For this reason, StationXML sent to IRIS should be verified with the [StationXML Validator](http://github.com/iris-edu/stationxml-validator).

### Exercise: Managing StationXML with Yasmine

The quickest way to become familiar with how to work with metadata in Yasmine is to import existing StationXML files.

<details>

<summary>Import XML</summary>

<input type="checkbox" /> Select an existing StationXML file or fetch one from the IRIS [fdsnws-station](http://service.iris.edu/fdsnws/station/1) service:

```bash
 curl --output out.xml 'https://service.iris.edu/fdsnws/station/1/query?net=XB&station=ELYSE&channel=MHU&level=response'
```

<input type="checkbox" /> From the `XML` tab, select `Import XML` then  your file

</details>

<details>

   <summary>Validate XML</summary>

<input type="checkbox" /> From the `XML` tab, double-click a filename then `File -> Validate`

</details>

<details>

   <summary>Extract XML</summary>

<input type="checkbox" /> From the `User Library` tab, select `Create a new library` and provide a name

</details>

<details>

<summary>Export XML</summary>

<input type="checkbox" /> From the `XML` tab, highlight the filename then `Export as XML`

</details>

## Levels of Response Detail

![Levels of StationXML metadata description](/yasmine-stationxml-editor/assets/images/response-level-details.drawio.png)

*Figure: Levels of StationXML metadata*

To understand how StationXML is organized, it is helpful to keep in mind the XML data model describes hierarchal relations where top-level elements are most general and the lower ones most specific. StationXML beginning with the FDSN StationXML declaration itself and adding increasingly more specific metadata at subsequent levels

### Instrument Response Libraries

Instrument response libraries provide access metadata descriptions and schema object definition files for well-known Earth-science observation instruments such as sensors and digitizers

[The Nominal Response Library (NRL)](https://ds.iris.edu/ds/nrl/)
:  A comprehensive library of recommended nominal responses created by IRIS from documentation from and direct communication with the manufacturer and checked for validity

[The Atomic Response Objects Library (AROL)](https://gitlab.com/resif/arol/)
: A new instrument response library under development by Résif containing a smaller albeit easier and faster set of descriptions than the NRL

### Exercise: Create StationXML With Yasmine 

Yasmine encourages a top-down approach when creating StationXML . A wizard is provided to step you though this process.

<details>

   <summary>Step 1: Create a StationXML file</summary>

<input type="checkbox" /> From the `XML` tab, select `Create` then provide the name of the file in Yasmine and [FDSN StationXML](https://docs.fdsn.org/projects/stationxml/en/latest/reference.html#fdsnstationxml-required) information

</details>

<details>

   <summary>Step 2. Add a Network</summary>

<input type="checkbox" />Select `Inventory` and `Add -> Add a network using a wizard`. Provide [Network](https://docs.fdsn.org/projects/stationxml/en/latest/reference.html#network-required) information and select `Next`

</details>

<details>
   <summary>Step 3: Add a Station</summary>

<input type="checkbox" />Provide [Station](https://docs.fdsn.org/projects/stationxml/en/latest/reference.html#station) information and select `Next`

</details>

<details>

   <summary>Step 4: Add a Channel</summary>

<input type="checkbox" /> Provide [Channel](https://docs.fdsn.org/projects/stationxml/en/latest/reference.html#channel) information and select `Next`

</details>

<details>

   <summary>Step 5: Add a Response</summary>

<input type="checkbox" /> Provide [Response](https://docs.fdsn.org/projects/stationxml/en/latest/reference.html#response) information and select `Next`

<input type="checkbox" /> Provide remaining [Channel](https://docs.fdsn.org/projects/stationxml/en/latest/reference.html#channel) information and select `Next`

<input type="checkbox" /> Save the Network, Station, and Channel information to your User Library and select `Complete Wizard`

</details>
