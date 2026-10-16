---
layout: page
title: Resources
permalink: /resources/
---

- [Yasmine StationXML Editor GitHub](https://github.com/iris-edu/yasmine-stationxml-editor)
- [Yasmine StationXML CLI GitHub](https://github.com/iris-edu/yasmine-stationxml-cli)
- [StationXML 1.2 manual](https://docs.fdsn.org/projects/stationxml/en/v1.2/)
- [StationXML 1.2 reference](https://docs.fdsn.org/projects/stationxml/en/v1.2/reference.html)
- [StationXML 1.2 XSD](https://www.fdsn.org/xml/station/fdsn-station-1.2.xsd)
- [Yasmine StationXML 1.2 contextual help](/yasmine-stationxml-editor/stationxml-context-help)
- [Yasmine StationXML 1.2 coverage](/yasmine-stationxml-editor/stationxml-1.2-coverage)
- [FDSN StationXML GitHub](https://github.com/FDSN/StationXML.git)
- [FDSNWS Station](https://service.earthscope.org/fdsnws/station/1/)
- [NRL Web Service](https://service.earthscope.org/irisws/nrl/1/)
- [NRL full archive used by NRL Offline](https://service.earthscope.org/irisws/nrl/1/combine?instconfig=full_NRL_v2_zip&format=resp.zip&nodata=404)
- [NRL catalog (text, configuration level)](https://service.earthscope.org/irisws/nrl/1/catalog?element=*&format=text&level=configuration)
- [AROL archive](https://gitlab.com/resif/arol/-/archive/master/arol-master.zip)
- [SAGE/GAGE 2021 Short Course Slides](https://docs.google.com/presentation/d/e/2PACX-1vRIzOPJ8qSMLAKw6uxw-mbcdz86Axc4nMJDgxr4cproHFeLQF67HDvCZ-o2scG3P-rUInfcnSH5oKeb/embed?start=false&loop=false&delayms=3000)

NRL responses are stored as StationXML 1.2 `Response` elements and validated with `fdsn-station-1.2.xsd`. Yasmine does not validate them against the older response-only schema. The NRL elements Yasmine reads are `sensor`, `datalogger`, `integrated`, and `soh`.
