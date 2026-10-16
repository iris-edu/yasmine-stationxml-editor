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
* 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
*
* ****************************************************************************/


Ext.define('yasmine.view.about.AboutInfo', {
  extend: 'Ext.panel.Panel',
  xtype: 'about-info',
  title: 'About Yasmine',
  frame: false,
  cls: 'yasmine-screen yasmine-about-screen',
  bodyPadding: 24,
  scrollable: true,
  bind: {
    html: `<div class="yasmine-about-content"><div class="yasmine-about-brand">
      <img class="yasmine-about-logo" src="{logoUrl}" alt="">
      <div class="yasmine-about-wordmark">
        <div class="yasmine-about-name">Yasmine</div>
        <div class="yasmine-about-tagline">StationXML Editor</div>
      </div>
    </div>
    <div class="yasmine-about-copy">{acknowledgement}</div>
    <div class="yasmine-about-build">
      <div><b>Version</b><span>{releaseVersion}</span></div>
      <div><b>Build date</b><span>{buildTimestamp}</span></div>
      <div><b>Revision</b><span>{commitRevision}</span></div>
    </div></div>`
  }
});
