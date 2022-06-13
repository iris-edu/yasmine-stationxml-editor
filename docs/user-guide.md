---
layout: page
title: User Guide
permalink: /user-guide/
---
- [FDSN StationXML](#fdsn-stationxml)
- [Instrument Response](#instrument-response)
  - [Exercise: Create StationXML With Yasmine](#exercise-create-stationxml-with-yasmine)
  - [Exercise: Manage Metadata With Yasmine](#exercise-manage-metadata-with-yasmine)

**Yasmine (Yet Another Station Metadata INformation Editor)** v4.1.0-beta is an editor designed to facilitate the creation of geophysical station metadata in FDSN StationXML format.

Before you begin, follow the [Installation](/yasmine-stationxml-editor/installation) instructions to get Yasmine up and running.

## FDSN StationXML

<figure>
   <img alt="Figure: Levels of StationXML Response Detail" src="/yasmine-stationxml-editor/assets/images/response-level-details.drawio.png" />
   <figcaption>Figure: Levels of StationXML Response Detail</figcaption>
</figure>

[FDSN StationXML](http://www.fdsn.org/xml/station) is a standard XML format to represent geophysical metadata developed by the International Federation of Digital Seismograph Networks (FDSN) as a successor to [SEED 2.4](http://www.fdsn.org/publications.htm).

Yasmine validates against the latest version of the schema [StationXML v1.2](https://docs.fdsn.org/projects/stationxml/en/latest/). Note that some organizations require rules in addition to those defined by the FDSN. For instance, IRIS verifies StationXML according to its [StationXML Validator](http://github.com/iris-edu/stationxml-validator).

To understand how StationXML is organized, it is helpful to keep in mind the XML data model describes hierarchal relations where top-level elements are most general and the lower ones most specific. StationXML begins with the FDSN StationXML declaration itself and adds increasingly specific metadata at subsequent levels.

```xml
 <?xml version="1.0" encoding="UTF-8"?>
 <FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://www.fdsn.org/xml/station/1  http://www.fdsn.org/xml/station/fdsn-station-1.2.xsd"
   schemaVersion="1.2">
```
Figure: StationXML v1.2 file declaration ([schema](https://www.fdsn.org/xml/station/fdsn-station-1.2.xsd))

## Instrument Response

Instrument response libraries provide access metadata descriptions and schema object definition files for well-known Earth-science observation instruments such as sensors and digitizers.

[The Nominal Response Library (NRL)](https://ds.iris.edu/ds/nrl/)
: A comprehensive library of recommended nominal 1. responses created by IRIS from documentation from and direct communication with the manufacturer and checked for validity

[The Atomic Response Objects Library (AROL)](https://gitlab.com/resif/arol/)
: A new instrument response library under development by Résif containing a smaller albeit easier and faster set of descriptions than the NRL

<figure>
   <img alt="Figure: Communication in a Modern Seismic Network" src="/yasmine-stationxml-editor/assets/images/communication-in-a-modern-seismic-network.drawio.png" />
   <figcaption>Figure: Communication in a Modern Seismic Network</figcaption>
</figure>

### Exercise: Create StationXML With Yasmine

Yasmine provides a wizard to step you though the process from the top-down of creating StationXML from scratch.  


<details><summary>Create User Library and XML</summary>

   <table>
      <td>    
         <input type="checkbox" />
         From the <code>User Library</code> tab, select <code>Create a new library</code> and provide a name
      </td>
      <tr>
         <td>
            <input type="checkbox" />
            From the <code>XML</code> tab, select <code>Create</code> then provide the XML container name for Yasmine and top-level <a href="https://docs.fdsn.org/projects/stationxml/en/latest/reference.html#fdsnstationxml-required">FDSN StationXML</a> information
         </td>
      </tr>
   </table>
</details>

<details><summary>Add a Network</summary>

   <table>
      <tr>
         <td>
            <input type="checkbox" />
           Select <code>Inventory</code> and <code>Add -> Add a network using a wizard</code>
         </td>
      </tr>
      <tr>
         <td>
            <input type="checkbox" />
            Provide <a href="https://docs.fdsn.org/projects/stationxml/en/latest/reference.html#network-required">Network</a> information and select <code>Next</code>
         </td>
      </tr>
   </table>

</details>

<details><summary>Add Stations</summary>

   <table>
      <td>
         <input type="checkbox" />
         Provide <a href="https://docs.fdsn.org/projects/stationxml/en/latest/reference.html#station">Station</a> information and select <code>Next</code>
      </td>
   </table>

</details>

<details><summary>Add Channels</summary>

   <table>
      <td>
         <input type="checkbox" />
         Provide <a href="https://docs.fdsn.org/projects/stationxml/en/latest/reference.html#channel">Channel</a> information and select <code>Next</code>
      </td>
   </table>

</details>

<details><summary>Add Responses</summary>

   <table>
      <tr>
         <td>
            <input type="checkbox" />
            Provide <a href="https://docs.fdsn.org/projects/stationxml/en/latest/reference.html#response">Response</a> information and select <code>Next</code>
         </td>
      </tr>
      <tr>
         <td>
            <input type="checkbox" />
            Provide remaining <a href="https://docs.fdsn.org/projects/stationxml/en/latest/reference.html#channel">Channel</a> information and select <code>Next</code>
         </td>
      </tr>
       <tr>
         <td>
          <input type="checkbox" />
            Select to save Network, Station, and Channel information to your User Library then <code>Complete Wizard</code>
         </td>
      </tr>
   </table>
   
</details>


### Exercise: Manage Metadata With Yasmine

The quickest way to become familiar with how to work with metadata in Yasmine is to import existing StationXML files.

<details><summary>Import XML</summary>

   <table>
      <tr>
         <td>
            <input type="checkbox" />
            Choose an existing StationXML file or one from the IRIS <a href="http://service.iris.edu/fdsnws/station/1">fdsnws-station</a> service (e.g. <a href="https://service.iris.edu/fdsnws/station/1/query?net=UW&station=QARB&channel=HNE&location=01&level=channel&nodata=404">here</a>)
         </td>
      </tr>
      <tr>
         <td>
            <input type="checkbox" />
            From the <code>XML</code> tab, select <code>Import XML</code> then your file
         </td>
      </tr>
   </table>

</details>

<details><summary>Validate XML</summary>

   <table>
      <tr>
         <td>
            <input type="checkbox" />
            From the <code>XML</code> tab, double-click your filename then <code>File -> Validate</code>
         </td>
      </tr>
      <tr>
         <td>
            <input type="checkbox" />
            Bonus: Why won't <a href="https://service.iris.edu/fdsnws/station/1/query?net=XB&station=ELYSE&channel=MHU&level=response&nodata=404">this</a> file validate?
         </td>
      </tr>
   </table>

</details>


<details><summary>Extract XML</summary>

   <table>
      <tr>
         <td>
            <input type="checkbox" />
            From the <code>XML</code> tab, double-click your filename
         </td>
      </tr>
      <tr>
         <td>
            <input type="checkbox" />
            Select a Network and <code>Extract -> Extract a selected Network to user library</code>
         </td>
      </tr>
   </table>

</details>

<details><summary>Export XML</summary>

   <table>
   <tr>
      <td>
         <input type="checkbox" />
         From the <code>XML</code> tab, highlight the filename then <code>Export as XML</code>
      </td>
      </tr>
   </table>

</details>