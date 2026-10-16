---
layout: page
title: StationXML 1.2 contextual help
permalink: /stationxml-context-help/
---

Yasmine shows FDSN StationXML 1.2 schema help when you click **?** in the
inventory editor, the XML document window, a nested Comment, Operator or
Person window, or the wizard header. The wizard **?** uses the field that
last had focus. **Orientation applies** opens Channel **Dip**, because that
question decides whether dip and azimuth are stored. The window title is
**StationXML 1.2**. The text is the original English XSD annotation.
Yasmine does not translate it.

The **Help**, **Model help**, and **Configuration help** buttons on an NRL
breadcrumb are catalog text from NRL, not this schema window.

## What the help window shows

The window always starts from the current editor focus:

- the canonical XML name from the schema. The inventory field list uses the
  same names with spaces (`startDate` appears as **Start Date**, `ClockDrift`
  as **Clock Drift**)
- the absolute path, for example `/FDSNStationXML/Network/Station/Site/Name`
- type, use, cardinality, default and fixed values when the schema defines them
- constraints and conditional structure
- attributes and child elements
- examples and XSD `<warning>` notes, under the headings **Examples** and **Warnings**
- a tree titled **StationXML hierarchy**

Search matches the XML name, path, type or description. **Full schema**
jumps from the current field to the complete hierarchy. Nested editors keep
their place: a comment author opens `Comment/Author`, and an operator
contact opens `Operator/Contact`.

The footer links to the [StationXML 1.2 manual](https://docs.fdsn.org/projects/stationxml/en/v1.2/).

## Two help systems

StationXML schema help is not GATITO helper text.

| UI | API | Source |
| --- | --- | --- |
| Parameter **?** | `/api/stationxml/help/1.2/` | FDSN StationXML 1.2 XSD |
| GATITO lists and HTML help | `/api/helper/` and `/api/help/` | Yasmine helper content |

Do not mix the two URLs. GATITO suggestions stay on `/api/helper/`.

## Provenance

The schema copy lives in
`backend/yasmine/resources/schemas/stationxml/1.2/fdsn-station-1.2.xsd`.
It is the unmodified FDSN StationXML 1.2 schema:

<https://www.fdsn.org/xml/station/fdsn-station-1.2.xsd>

Generated catalogs (`catalog.json`, `editor-contexts.json`,
`response-1.2.json`) are derived from that XSD. The FDSN prose remains
FDSN documentation; it is not redistributed under the Yasmine LGPL
license.

Regenerate the catalogs after an XSD update:

```bash
python backend/tools/generate_stationxml_help.py
```

## Export and validation

Export writes `schemaVersion="1.2"` and validates the file against this XSD.
Schema errors block the download with HTTP 400 and the reason
`StationXML 1.2 export blocked`.

**File → Validate XML** shows those XSD errors and separate Yasmine
recommendations (code lengths, `sourceID` URI form, epoch overlap). The
recommendations do not block export.

XSD `<warning>` text, including “This element is likely to be removed”, is
help text. It is not a validation warning and it does not block editing or
export.
