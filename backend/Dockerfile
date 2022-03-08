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

FROM python:3.10-slim AS python-deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev
COPY requirements.txt /
RUN pip install --no-cache-dir --upgrade pip setuptools
RUN pip install --no-cache-dir -r /requirements.txt

FROM python:3.10-slim
WORKDIR /opt/YASMINE/src
COPY . .

RUN apt-get update && apt-get install -y wget unzip gnupg gcc

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
RUN apt-get update
RUN apt-get -y install google-chrome-stable

RUN cd /tmp && \
    wget https://chromedriver.storage.googleapis.com/2.39/chromedriver_linux64.zip -O chromedriver.zip --progress=bar:force && \
    mkdir /opt/chromedriver && unzip -q -p chromedriver.zip > /opt/chromedriver/chromedriver && \
    ln -s /opt/chromedriver/chromedriver /usr/local/bin/chromedriver && \
    rm chromedriver.zip && \
    chmod +x /opt/chromedriver/chromedriver


# Get the dependencies from previous stage
COPY --from=python-deps /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
CMD python yasmineapp.py syncdb upgrade heads ; python yasmineapp.py runserver --debug
