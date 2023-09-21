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

FROM python:3.6.5-slim
WORKDIR /opt/yasmine/src

RUN mv /etc/apt/sources.list /etc/apt/sources.list.old
RUN echo " deb http://deb.debian.org/debian buster main contrib non-free " > /etc/apt/sources.list 
RUN echo " deb http://deb.debian.org/debian buster-backports main contrib non-free" >> /etc/apt/sources.list

RUN apt-get update && apt-get install -y --allow-unauthenticated wget unzip gnupg gcc

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
RUN apt-get update
RUN apt-get -y --allow-unauthenticated install google-chrome-stable

RUN cd /tmp && \
    wget https://chromedriver.storage.googleapis.com/2.39/chromedriver_linux64.zip -O chromedriver.zip --progress=bar:force && \
    mkdir /opt/chromedriver && unzip -q -p chromedriver.zip > /opt/chromedriver/chromedriver && \
    ln -s /opt/chromedriver/chromedriver /usr/local/bin/chromedriver && \
    rm chromedriver.zip && \
    chmod +x /opt/chromedriver/chromedriver

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
COPY . .
CMD python yasmineapp.py syncdb upgrade heads ; python yasmineapp.py runserver --debug
