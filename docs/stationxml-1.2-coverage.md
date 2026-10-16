---
layout: page
title: StationXML 1.2 coverage
permalink: /stationxml-1.2-coverage/
---

# StationXML 1.2 coverage

This document is the acceptance checklist for StationXML 1.2 support in
Yasmine. The normative source is the vendored FDSN StationXML 1.2 XSD,
`backend/yasmine/resources/schemas/stationxml/1.2/fdsn-station-1.2.xsd`
(schema version 1.2, 2022-02-25).

Three different “warnings” appear in the product:

- **Help warnings** are `<warning>` annotations from the XSD. The contextual
  help window shows them. They do not block editing or export. Several say
  “This element is likely to be removed.”
- **Validate XML warnings** come from Yasmine recommendations. Code lengths
  follow FDSN / Strict operational limits (network 1–8, station 1–5, channel
  exactly 3, location 0–2). When a code is FDSN-valid but unusual for classic
  SEED (network not 1–2, station not 3–5), Validate also adds a soft
  “SEED classic recommends…” hint. Other recommendations cover `sourceID` as
  a URI, alternate and historical codes, and epoch overlap or inverted dates.
  **File → Validate XML** lists them. They do not block export.
- **Strict Validate XML** repeats schema errors and Validate recommendations,
  then adds further operational warnings (epochs, coordinates, SEED band and
  orientation, response stages). Every Strict finding is a warning; Strict
  never blocks export by itself.
- **Response operational notes** come from `POST /api/channel/response/validate/`.
  They cover stage numbering, unit continuity, a zero stage gain, decimation
  factor and offset, and a missing `InstrumentSensitivity` or
  `InstrumentPolynomial`. They do not make the response invalid. The save
  dialog lists schema errors.

**Errors** are StationXML 1.2 XSD failures. Export refuses the file.

Coverage has three forms:

- **Form**: a typed editor is available in the parameter list.
- **Tree**: the response tree is constrained by a schema descriptor and uses
  typed value and attribute controls.
- **Pass-through**: foreign-namespace elements and attributes are retained
  without an editor.

## Document root

- Form: required `Source`. The string may be empty. The XSD warns that
  `Source` is likely to become a choice with `Sender`.
- Form: optional `Sender`, `Module`, and `ModuleURI`. The XSD warns that
  `Sender` is likely to become a choice with `Source`.
- Form: required UTC `Created`.
- Read-only: **Schema Version**. Export always writes `schemaVersion="1.2"`,
  including after import of a 1.1 document.
- Pass-through: root `xs:any` and `xs:anyAttribute`.

## Network, Station, and Channel base node

- Form: required `code`.
- Form: optional `startDate`, `endDate`, `sourceID`, `restrictedStatus`,
  `alternateCode`, and `historicalCode`.
- Form: optional `Description`.
- Form: repeatable `Identifier`, with separate optional `type` and required
  text value.
- Form: repeatable `Comment`, including optional `id`, `subject`, effective
  dates, and authors.
- Form: `DataAvailability`, including an optional `Extent` and zero or more
  `Span` entries. Extent-only, span-only, and extent-plus-spans values are
  supported. Import of a span-only document adds a temporary `Extent` so
  ObsPy can read the file, then clears that extent before the value is
  stored. Export of a span-only value does not write an `Extent`.
- Pass-through: BaseNode `xs:any` and `xs:anyAttribute`.

## Network

- Form: repeatable `Operator`.
- Form: optional `TotalNumberStations` and `SelectedNumberStations`.
- Help warning: both station-count elements say “This element is likely to
  be removed.” They remain editable.

## Station

- Form: `Latitude`, `Longitude`, `Elevation`, and `Site`.
- Form: optional `WaterLevel`, `Vault`, and `Geology`.
- Form: repeatable `Equipment`, `Operator`, and `ExternalReference`.
- Form: optional `CreationDate`, `TerminationDate`,
  `TotalNumberChannels`, and `SelectedNumberChannels`.
- Help warning: creation date, termination date and both channel-count
  elements say “This element is likely to be removed.” They remain editable.

## Channel

- Form: required, possibly empty, `locationCode`.
- Form: repeatable `ExternalReference`.
- Form: `Latitude`, `Longitude`, `Elevation`, and `Depth`.
- Form: optional `Azimuth`, `Dip`, and `WaterLevel`.
- Form: repeatable `Type`. The editor lists every XSD enumeration:
  `TRIGGERED`, `CONTINUOUS`, `HEALTH`, `GEOPHYSICAL`, `WEATHER`, `FLAG`,
  `SYNTHESIZED`, `INPUT`, `EXPERIMENTAL`, `MAINTENANCE`, `BEAM`.
- Help warning: `Type` says “This element is likely to be removed.” The XSD
  text also says it should not be used for new StationXML. It remains editable.
- Absent: Channel `StorageFormat` is not in StationXML 1.2 and has no editor.
- Form: optional `SampleRate` and `SampleRateRatio`.
- Form: optional `ClockDrift` and `CalibrationUnits`.
- Form: optional `Sensor`, `PreAmplifier`, `DataLogger`, and repeatable
  `Equipment`.

## Measured numeric values

The scalar value can still be edited inline. The metadata editor retains:

- `plusError`, `minusError`, and `measurementMethod` where the XSD type
  permits uncertainty metadata;
- `datum` for latitude and longitude;
- editable `unit` for open-unit values;
- the fixed unit as read-only information for constrained types.

The profile applies to latitude, longitude, elevation, depth, azimuth, dip,
water level, sample rate, and clock drift. Editing only the scalar value does
not remove imported metadata.

## Nested standard types

- Form: all `Site` fields; `Name` is required.
- Form: all `Equipment` fields, repeatable calibration dates, and optional
  `resourceId`.
- Form: `Operator` with required `Agency`, contacts, and optional `WebSite`.
- Form: `Person` names, agencies, emails, and phones.
- Form: phone optional country code, required area code, required patterned
  number, and optional description.
- Form: `ExternalReference` required URI and description.
- Form: `Units` required name and optional description.

## Response

- Tree: optional `Response@resourceId` and an explicitly empty Response.
- Tree: mutually exclusive `InstrumentSensitivity` and
  `InstrumentPolynomial`.
- Tree: ordered, repeatable `Stage` with required non-negative `number` and
  optional `resourceId`.
- Tree: the stage choice between `Polynomial` and the
  filter/Decimation/StageGain branch.
- Tree: complete `PolesZeros`, `Coefficients`, `FIR`, `ResponseList`, and
  `Polynomial` branches.
- Tree: response units, numeric uncertainty attributes, enums, child order,
  cardinality, and all required values and attributes.
- Pass-through: foreign elements and attributes at Response, Stage, and filter
  extension points.

## Extension pass-through

The importer stores foreign-namespace XML as opaque sidecar data for every
StationXML 1.2 extension point. The exporter restores QName, namespace
declarations, attributes, text, child content, and owner position. Standard
editors do not allow extension XML to be changed. Deleting the owning
standard object intentionally deletes its extension sidecar.

**Inventory / Hierarchy.** Use **Extensions** on the Hierarchy toolbar for a
read-only summary of foreign elements and attributes on the selected node and
its children. Delete confirmation reports how many sidecars will be removed
(including in the User Library builder).

**Channel Response tree.** Foreign QNames inside a response are shown as
read-only nodes in the response tree editor; that path is separate from
inventory `extension_sidecar` columns.

## Acceptance fixtures

The integration suite covers:

- a minimal StationXML 1.2 document;
- every standard non-response field and optional omission;
- all measured-value metadata;
- extent-only, span-only, and extent-plus-spans DataAvailability;
- Station and Channel external references;
- empty Response and every response filter/polynomial branch;
- foreign elements and attributes at each XSD extension point;
- import, unrelated edit, export, XSD validation, and semantic XML comparison;
- migration of a database created at the previous Alembic head.
