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


import pickle

from sqlalchemy import Column, Text, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql.functions import func

from yasmine.app.models import UserLibraryModel
from yasmine.app.models.base import Base, BaseMixin


class XmlNodeAttrRelationModel(Base):
    node_id = Column(ForeignKey('xml_node.id', ondelete='CASCADE'), primary_key=True)
    attr_id = Column(ForeignKey('xml_node_attribute.id', ondelete='CASCADE'), primary_key=True)

    node = relationship("XmlNodeModel", back_populates="attrs")
    attr = relationship("XmlNodeAttrModel")

    __tablename__ = 'xml_node_attribute_relation'


class XmlNodeModel(Base, BaseMixin):
    id = Column(Integer, primary_key=True, index=True, unique=True)
    clazz = Column(Text, nullable=False)
    parent_id = Column(ForeignKey('xml_node.id', ondelete='CASCADE'), nullable=True)

    attrs = relationship("XmlNodeAttrRelationModel", back_populates="node")
    parent = relationship("XmlNodeModel", backref="children", remote_side=[id])

    __tablename__ = 'xml_node'


class XmlNodeAttrWidgetModel(Base, BaseMixin):
    name = Column(Text, nullable=False)

    __tablename__ = 'xml_node_attr_type'


class XmlNodeAttrModel(Base, BaseMixin):
    name = Column(Text, nullable=False)
    widget_id = Column(ForeignKey(XmlNodeAttrWidgetModel.id, ondelete='CASCADE'), nullable=False)
    index = Column(Integer, nullable=False, server_default='0')

    widget = relationship(XmlNodeAttrWidgetModel)

    __tablename__ = 'xml_node_attribute'


class XmlModel(Base, BaseMixin):
    name = Column(Text, nullable=False)
    source = Column(Text, nullable=True)
    module = Column(Text, nullable=True)
    uri = Column(Text, nullable=True)
    sender = Column(Text, nullable=True)
    created_at = Column(DateTime(), default=func.now(), nullable=False)
    updated_at = Column(DateTime(), nullable=False, default=func.now(), onupdate=func.now())

    nodes = relationship('XmlNodeInstModel', lazy='dynamic')
    __tablename__ = 'xml'


class XmlNodeInstModel(Base, BaseMixin):
    id = Column(Integer, primary_key=True, index=True, unique=True)
    code = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    xml_id = Column(ForeignKey(XmlModel.id, ondelete='CASCADE'), nullable=True)
    node_id = Column(ForeignKey(XmlNodeModel.id, ondelete='CASCADE'), nullable=False)
    parent_id = Column(ForeignKey('xml_node_instance.id', ondelete='CASCADE'), nullable=True)
    user_library_id = Column(ForeignKey(UserLibraryModel.id, ondelete='CASCADE'), nullable=True)

    parent = relationship('XmlNodeInstModel', backref=backref('children', lazy='dynamic'), remote_side=[id, xml_id])
    node = relationship(XmlNodeModel)
    xml = relationship(XmlModel)
    attr_vals = relationship('XmlNodeAttrValModel', lazy="dynamic")

    __tablename__ = 'xml_node_instance'


class XmlNodeAttrValModel(Base, BaseMixin):
    value = Column(Text, nullable=True)

    attr_id = Column(ForeignKey(XmlNodeAttrModel.id, ondelete='CASCADE'), nullable=False)
    node_inst_id = Column(ForeignKey(XmlNodeInstModel.id, ondelete='CASCADE'), nullable=True)
    node_id = Column(ForeignKey(XmlNodeModel.id, ondelete='CASCADE'), nullable=True)

    attr = relationship(XmlNodeAttrModel)
    node_inst = relationship(XmlNodeInstModel)

    __tablename__ = 'xml_node_attr_value'

    @property
    def attr_class(self):
        return self.attr.widget.name

    @property
    def attr_name(self):
        return self.attr.name

    @property
    def attr_index(self):
        return self.attr.index

    @property
    def value_obj(self):
        return pickle.loads(self.value)

    @value_obj.setter
    def value_obj(self, data):
        self.value = pickle.dumps(data)

    @property
    def node_type_id(self):
        return self.node_inst.node_id
