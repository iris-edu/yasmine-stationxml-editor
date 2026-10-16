/* ****************************************************************************
*
* This file is part of the yasmine editing tool.
*
* yasmine (Yet Another Station Metadata INformation Editor), a tool to
* create and edit station metadata information in FDSN stationXML format,
* is a common development of IRIS and RESIF.
* Development and addition of new features is shared and agreed between * IRIS and RESIF.
*
*
* Version 1.0 of the software was funded by SAGE, a major facility fully
* funded by the National Science Foundation (EAR-1261681-SAGE),
* development done by ISTI and led by IRIS Data Services.
* Version 2.0 of the software was funded by CNRS and development led by * RESIF.
*
* This program is free software; you can redistribute it
* and/or modify it under the terms of the GNU Lesser General Public
* License as published by the Free Software Foundation; either
* version 3 of the License, or (at your option) any later version. *
* This program is distributed in the hope that it will be
* useful, but WITHOUT ANY WARRANTY; without even the implied warranty
* of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU Lesser General Public License (GNU-LGPL) for more details. *
* You should have received a copy of the GNU Lesser General Public
* License along with this software. If not, see
* <https://www.gnu.org/licenses/>
*
*
* 2019/10/07 : version 2.0.0 initial commit
* 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.main.MainModel', {
  extend: 'Ext.app.ViewModel',
  alias: 'viewmodel.main',
  data: {
    name: 'Yasmine',
    acknowledgement: `
    <b>YASMINE</b> (Yet Another Station Metadata INformation Editor), a tool to
    create and edit station metadata informations in FDSN stationXML format,
    is a common development of IRIS and RESIF. <br>
    Development and addition of new features is shared and agreed between IRIS and RESIF.
    <br><br>

    Version 1.* of the software was funded by SAGE, a major facility fully
    funded by the National Science Foundation (EAR-1261681-SAGE),
    development done by ISTI and led by IRIS Data Services.<br>
    Version 2.* of the software was funded by CNRS and development led by RESIF.<br>
    Version 4.4.0 of the software was developed by ASGSR, the Altay-Sayan Branch of the Geophysical Survey of the Russian Academy of Science.
    <br><br>
    This program is free software; you can redistribute it
    and/or modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 3 of the License, or (at your option) any later version. <br>
    This program is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty
    of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU Lesser General Public License (GNU-LGPL) for more details. <br>
    You should have received a copy of the GNU Lesser General Public
    License along with this software. If not, see <a href="https://www.gnu.org/licenses/" target="_blank">https://www.gnu.org/licenses/</a>
    `,
    serverBuildTimestamp: '',
    serverCommitRevision: ''
  },
  formulas: {
    logoUrl: function () {
      return yasmine.Globals.logoUrl('logo-mark.svg') + '?brand=original-vector';
    },
    logoIconUrl: function () {
      return yasmine.Globals.logoUrl('logo-icon.svg') + '?brand=header-icon';
    },
    buildTimestamp: function (get) {
      var loaded = get('serverBuildTimestamp');
      if (loaded) {
        return loaded;
      }
      return (typeof buildTimestamp !== 'undefined' && buildTimestamp) ? buildTimestamp : '';
    },
    releaseVersion: function (get) {
      return (typeof releaseVersion !== 'undefined' && releaseVersion) ? releaseVersion : `${Ext.manifest.version}`;
    },
    commitRevision: function (get) {
      var loaded = get('serverCommitRevision');
      if (loaded) {
        return loaded;
      }
      return (typeof commitRevision !== 'undefined' && commitRevision) ? commitRevision : '';
    },
  }
});
