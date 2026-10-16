# FDSN StationXML 1.2 schema

`fdsn-station-1.2.xsd` is the unmodified schema published by the
International Federation of Digital Seismograph Networks:

<https://www.fdsn.org/xml/station/fdsn-station-1.2.xsd>

Backend validation, response-editor descriptors and contextual help use
this copy. Export sets `schemaVersion` to `1.2` and validates the written
file against it. Generated `catalog.json`, `editor-contexts.json` and
`response-1.2.json` are derived from the XSD annotations, including
`<warning>` and `<example>` notes. The FDSN schema text remains FDSN
documentation and is not licensed as Yasmine LGPL.

If this file is missing, validation falls back to ObsPy's copy of
`fdsn-station-1.2.xsd`.

The schema help HTTP API is `/api/stationxml/help/1.2/`. GATITO content
continues to use `/api/help/` and `/api/helper/`.
