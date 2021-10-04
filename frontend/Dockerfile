# ****************************************************************************
#
# This file is part of the yasmine editing tool.
#
# yasmine (Yet Another Station Metadata INformation Editor), a tool to
# create and edit station metadata information in FDSN stationXML format,
# is a common development of IRIS and RESIF.
# Development and addition of new features is shared and agreed between * IRIS and RESIF.
#
#
# Version 1.0 of the software was funded by SAGE, a major facility fully
# funded by the National Science Foundation (EAR-1261681-SAGE),
# development done by ISTI and led by IRIS Data Services.
# Version 2.0 of the software was funded by CNRS and development led by * RESIF.
#
# This program is free software; you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version. *
# This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License (GNU-LGPL) for more details. *
# You should have received a copy of the GNU Lesser General Public
# License along with this software. If not, see
# <https://www.gnu.org/licenses/>
#
#
# 2019/10/07 : version 2.0.0 initial commit
#
# ****************************************************************************/


FROM openjdk:8-jre-stretch

RUN apt-get update && \
    apt-get install -y wget unzip

RUN useradd -m sencha && \
    cd && cp -R .bashrc .profile /home/sencha && \
    mkdir -p /code /opt/Sencha/SDK /opt/Sencha/Cmd/6.5.3.6 && \
    chown -R sencha:sencha /home/sencha /code /opt/Sencha

USER sencha
ENV HOME /home/sencha

RUN cd /home/sencha && \
	wget http://cdn.sencha.com/cmd/6.5.3.6/no-jre/SenchaCmd-6.5.3.6-linux-amd64.sh.zip -O senchacmd.zip --progress=bar:force && \
	unzip -q -p senchacmd.zip > SenchaCmd-6.5.3.6-linux-amd64.sh && \
	rm senchacmd.zip && \
	chmod +x SenchaCmd-6.5.3.6-linux-amd64.sh

RUN /home/sencha/SenchaCmd-6.5.3.6-linux-amd64.sh -q -dir /opt/Sencha/Cmd/6.5.3.6 -Dall=true
RUN rm /home/sencha/SenchaCmd-6.5.3.6-linux-amd64.sh && chmod +x /opt/Sencha/Cmd/6.5.3.6/sencha

RUN cd opt/Sencha/SDK && wget http://cdn.sencha.com/ext/gpl/ext-6.2.0-gpl.zip --progress=bar:force && unzip -q ext-6.2.0-gpl.zip

ENV PATH="$PATH:/opt/Sencha/Cmd/6.5.3.6"
WORKDIR /code/frontend
CMD sencha app watch --j2ee
