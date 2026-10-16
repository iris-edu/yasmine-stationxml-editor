# Frontend unit tests

The StationXML help path algorithms and other Ext-free helpers can be run without Sencha:

```bash
node --test frontend/test/unit/*.test.js
```

Jasmine specs under `frontend/test/specs/` document the Ext JS contracts for
`StationXmlHelpContext`, `HelpUtil`, and the StationXML help controller. They
expect the Classic application classes to be loaded.
