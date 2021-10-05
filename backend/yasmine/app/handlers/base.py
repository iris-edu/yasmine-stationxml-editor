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


# -*- coding: utf-8 -*-
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import mmap
import os

from humanize.filesize import naturalsize
from sqlalchemy import DateTime
from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql.expression import extract
from tornado.concurrent import run_on_executor
from tornado.web import addslash
import tornado

from yasmine.app.settings import DATE_FORMAT_SYSTEM
from yasmine.app.utils.date import datetime_to_utc, strptime
from yasmine.app.utils.facade import HandlerMixin
from yasmine.app.utils.ujson import json_dump, json_load
from yasmine.app.exceptions.exceptions import ResponseEditException


class AsyncThreadMixin(object):
    executor = ThreadPoolExecutor(max_workers=5)

    @run_on_executor
    def async_call(self, func, *args, **kwargs):
        return func(*args, **kwargs)

    def async_get(self, *args, **kwargs):
        raise Exception("Not implemented")

    def async_post(self, *args, **kwargs):
        raise Exception("Not implemented")

    def async_put(self, *args, **kwargs):
        raise Exception("Not implemented")

    def async_delete(self, *args, **kwargs):
        raise Exception("Not implemented")

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):
        res = yield self.async_call(self.async_get, *args, **kwargs)
        self.write(res)

    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        res = yield self.async_call(self.async_post, *args, **kwargs)
        self.write(res)

    @tornado.gen.coroutine
    def put(self, *args, **kwargs):
        res = yield self.async_call(self.async_put, *args, **kwargs)
        self.write(res)

    @tornado.gen.coroutine
    def delete(self, *args, **kwargs):
        res = yield self.async_call(self.async_delete, *args, **kwargs)
        self.write(res)


class BaseHandler(tornado.web.RequestHandler, HandlerMixin):
    USER_COOKIE = "current_user"

    def initialize(self):
        pass

    def write(self, chunk):
        if isinstance(chunk, dict) or isinstance(chunk, list):
            chunk = json_dump(chunk)
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        super(BaseHandler, self).write(chunk)

    @property
    def request_params(self):
        if not hasattr(self, 'json_body_cache'):
            if self.request.method in ['POST', 'PUT']:
                self.json_body_cache = json_load(self.request.body)
            else:
                tmp = {}
                for p_name, p_value in self.request.arguments.items():
                    if p_name not in ['_dc']:
                        tmp[p_name] = json_load(p_value[0])
                self.json_body_cache = tmp
        return self.json_body_cache

    @property
    def is_ajax(self):
        return self.request.headers.get("X-Requested-With") == 'XMLHttpRequest'

    def get_current_user(self):
        return None

    def write_error(self, *_, **__):
        if self.is_ajax:
            self.write({'success': False, 'data': self._reason})
        else:
            self.render("500.html", message=self._reason)

    def write_file_data(self, file_name, data):
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=' + file_name)
        super(BaseHandler, self).write(data)

    def write_file(self, folder, file_name):
        buf_size = 4096
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=' + file_name)
        with open(os.path.join(folder, file_name), 'rb') as f:
            while True:
                data = f.read(buf_size)
                if not data:
                    break
                self.write(data)
        self.finish()

    def set_secure_cookie(self, name, value, expires=None,  version=None, **kwargs):
        self.set_cookie(name, self.create_signed_value(name, value, version=version), expires=expires, **kwargs)


class LoginRequiredHandler(BaseHandler):

    def prepare(self):
        if not self.current_user:
            if self.is_ajax:
                self.send_error(403, reason='Access denied!')
            else:
                self.redirect(self.reverse_url('LoginHandler'))
                return


class SuperuserRequiredHandler(LoginRequiredHandler):

    def prepare(self):
        super(SuperuserRequiredHandler, self).prepare()
        if self.current_user and not self.current_user.is_superuser():
            self.send_error(403, reason='Access denied!')


class ErrorHandler(BaseHandler):

    def write_error(self, *_, **__):
        if self.is_ajax:
            self.write({'success': False, 'data': self._reason})
        else:
            self.render("403.html", message=self._reason)

    @addslash
    def prepare(self):
        super(ErrorHandler, self).prepare()


class ExtJsHandler(AsyncThreadMixin, BaseHandler):
    ''' General view for the REST request/responses.'''
    # object ID field
    key_field = 'id'
    related = []
    exclude_fields = []
    send_total_count = True

    def determine_fields(self, *_):
        ''' Determines fields to persist or extract.'''
        fields = []
        # if request body contains fields list
        if 'fields' in self.request_params:
            fields = self.request_params['fields']
            del self.request_params['fields']
        else:
            # get list from model
            fields = self.model.__table__.columns._data.keys()
        return set(fields) - set(self.exclude_fields)

    def extract_criteria(self, property_name, value, operator):
        return property_name, value, operator

    def get_model_field(self, name):
        if '__' in name:
            field_names = name.split('__')
            my_model = self.model
            # iterate to get field type
            for field_name in field_names:
                field = getattr(my_model, field_name)
                if isinstance(field.property, RelationshipProperty):
                    my_model = field.property.argument
        else:
            field = getattr(self.model, name)
        return field

    def get_value(self, field, filter_criteria):
        value = ''
        if 'value' in filter_criteria:
            value = filter_criteria['value']
        # convert if required
        if isinstance(field.type, DateTime):
            if isinstance(value, str):
                value = strptime(value, DATE_FORMAT_SYSTEM)
        return value

    def process_criteria(self, query, *_, **__):
        ''' Converts clients criteria to the ORM django to make database query.'''
        # combobox criteria
        if 'query' in self.request_params:
            query = query.filter(func.upper(getattr(self.model, self.request_params['property'])).like("%%%s%%" % self.request_params['query'].upper()))
        # find grid filter criteria
        if 'filter' in self.request_params:
            for filter_criteria in self.request_params['filter']:
                # if fk then iterate to get field type
                property_name = filter_criteria['property']

                field = self.get_model_field(property_name)
                value = self.get_value(field, filter_criteria)
                # convert extjs criteria in to django
                if 'anyMatch' in filter_criteria:
                    any_match = filter_criteria['anyMatch']
                    case_sensitive = filter_criteria['caseSensitive']
                    if any_match:
                        if case_sensitive:
                            query = query.filter(field.like("%%s%%" % value))
                        else:
                            query = query.filter(func.upper(field).like("%%%s%%" % value.upper()))
                    else:
                        if case_sensitive:
                            query = query.filter(field.like("%s%%" % value))
                        else:
                            query = query.filter(func.upper(field).like("%s%%" % value.upper()))

                elif 'operator' in filter_criteria:
                    property_name, value, operator = self.extract_criteria(property_name, value, filter_criteria['operator'])
                    if operator == 'like':
                        query = query.filter(field.ilike("%%%s%%" % value.upper()))
                    elif operator == 'eq':
                        query = query.filter(field == value)
                    elif operator == 'neq':
                        query = query.filter(or_(field != value, field == None))  # nopep8
                    elif operator == 'lt':
                        query = query.filter(field < value)
                    elif operator == 'gt':
                        query = query.filter(field > value)
                    elif operator == '=':
                        query = query.filter(field == value)
                    elif operator == 'isnull':
                        query = query.filter(field == None)  # nopep8
                    elif operator == 'in':
                        query = query.filter(field.in_(value))
                    elif operator == 'eq_year':
                        query = query.filter(extract('year', field) == value)
                    elif operator == 'endswith':
                        query = query.filter(func.upper(field).endswith(value.upper()))
                    elif operator == 'notendswith':
                        query = query.filter(func.upper(field).notilike("%%%s" % value.upper()))
                else:
                    query = query.filter(field == value)
        return query

    def process_group(self, query):
        ''' Converts order request in to the ORM format. '''
        if 'group' in self.request_params:
            group_criteria = self.request_params['group']
            query = query.order_by(getattr(self.get_model_field(group_criteria['property']), group_criteria['direction'].lower())())
        return query

    def process_order(self, query):
        ''' Converts order request in to the ORM format. '''
        if 'sort' in self.request_params:
            for sort_criteria in self.request_params['sort']:
                query = query.order_by(getattr(self.get_model_field(sort_criteria['property']), sort_criteria['direction'].lower())())
        else:
            query = query.order_by(getattr(self.model, self.key_field))
        return query

    def get_query_page(self, query):
        ''' Converts paging request in to the ORM format. '''
        if 'limit' in self.request_params and 'page' in self.request_params:
            # page = self.request_params['page']
            limit = self.request_params['limit']
            start = self.request_params['start']
            return query.limit(limit).offset(start)
        else:
            return query

    def get_data_query(self):
        query = self.db.query(self.model)
        for entity in self.related:
            query = query.outerjoin(entity).options(joinedload(entity))
        return query

    def get_count_query(self):
        return self.db.query(func.count(self.model.id))

    def async_get(self, db_id=None, **kwargs):
        if db_id is None:
            return self.get_list(kwargs)
        else:
            return self.get_obj(db_id)

    def get_obj(self, db_id):
        fields = self.determine_fields(self.model)
        obj = self.db.query(self.model).get(db_id)
        return {'success': True,  'data': self.serialize(obj, fields)}

    def serialize(self, q_object, fields):
        return dict((name, getattr(q_object, name)) for name in fields)

    def get_list(self, *args, **kwargs):
        ''' POST HTTP request is used to get extract data by model according to criteria and return in the JSON format. '''
        fields = self.determine_fields(self.model)

        # to improve query adds related joins
        data_query = self.get_data_query()
        data_query = self.process_criteria(data_query, self.model, *args, **kwargs)
        data_query = self.process_order(data_query)
        data_query_result = self.get_query_page(data_query)

        count_query_result = 0
        if self.send_total_count:
            count_query = self.get_count_query()
            count_query = self.process_criteria(count_query, self.model, *args, **kwargs)
            count_query_result = count_query.scalar()

        # converts to the JSON suitable format
        data = []
        for q_object in data_query_result:
            data.append(self.serialize(q_object, fields))

        return {'success': True, 'totalCount': count_query_result, 'data': data}

    def create_obj(self):
        return self.model(**self.request_params)

    def update_obj(self, obj):
        for key, value in self.request_params.items():
            if key != self.key_field:
                setattr(obj, key, value)

    def async_put(self, db_id, **__):
        fields = self.determine_fields(self.model)
        self.obj = None
        with self.db.begin():
            self.obj = self.db.query(self.model).get(db_id)
            # updates object
            try:
                self.update_obj(self.obj)
            except ResponseEditException as response_err:
                return {'success': False, 'data': f'{response_err}'}
        return {'success': True, 'data': self.serialize(self.obj, fields)}

    def async_post(self, *_, **__):
        fields = self.determine_fields(self.model)
        self.obj = None
        with self.db.begin():
            # creates object if id is not pointed
            self.obj = self.create_obj()
            self.db.add(self.obj)
        return {'success': True, 'data': self.serialize(self.obj, fields)}

    def async_delete(self, db_id, **__):
        with self.db.begin():
            try:
                getattr(self.model, 'deleted')
                for obj in self.db.query(self.model).filter(getattr(self.model, self.key_field) == db_id):
                    obj.deleted = True
                    obj.save()
            except AttributeError:
                obj = self.db.query(self.model).filter(getattr(self.model, self.key_field) == db_id).delete()
        return {'success': True}


class FileHangler(AsyncThreadMixin, BaseHandler):
    ''' Backup manager view. '''

    @property
    def request_params(self):
        if not hasattr(self, 'json_body_cache'):
            self.json_body_cache = json_load(self.request.body)
        return self.json_body_cache

    def get_folder(self):
        raise Exception('Not implemented')

    def get(self, filename, *_, **__):
        return self.write_file(self.get_folder(), filename)

    def filter_func(self, record):
        for filter_criteria in self.request_params['filter']:
            filer_property = filter_criteria['property']
            if filer_property == 'date':
                filter_value = strptime(filter_criteria['value'], DATE_FORMAT_SYSTEM)
            else:
                filter_value = filter_criteria['value']
            if filer_property == 'content':
                if filter_value:
                    with open(os.path.join(self.get_folder(), record['name']), "r+b") as f:
                        if os.fstat(f.fileno()).st_size > 0:
                            mm = mmap.mmap(f.fileno(), 0)
                            if mm.find(filter_value.encode('utf-8')) >= 0:
                                return True
                        return False
            else:
                record_value = record[filer_property]
                if filter_criteria['operator'] == 'like':
                    if filter_value.lower() not in record_value.lower():
                        return False
                elif filter_criteria['operator'] == 'lt':
                    if not(record_value < filter_value):
                        return False
                elif filter_criteria['operator'] == 'gt':
                    if not(record_value > filter_value):
                        return False
                elif filter_criteria['operator'] == 'eq':
                    if not(record_value == filter_value):
                        return False
        return True

    def async_post(self, *_, **__):
        data = []
        # filter backups by criteria
        filter_func = False
        folder = self.get_folder()
        if 'filter' in self.request_params:
            filter_func = True
        for file_name in os.listdir(folder):
            file_path = os.path.join(folder, file_name)
            if os.path.isfile(file_path):
                info = os.stat(file_path)
                record = {'name': file_name, 'date': datetime_to_utc(datetime.fromtimestamp(info.st_ctime)), 'size': info.st_size}
                if not filter_func or self.filter_func(record):
                    data.append(record)
        totalCount = len(data)
        if 'sort' in self.request_params:
            for sort_criteria in self.request_params['sort']:
                sort_property = sort_criteria['property']
                reverse = True if sort_criteria['direction'].lower() == 'asc' else False
                data.sort(key=lambda record: record[sort_property], reverse=reverse)
        bottom = (self.request_params['page'] - 1) * self.request_params['limit']
        top = bottom + self.request_params['limit']
        data = data[bottom:top]
        for record in data:
            record['size'] = naturalsize(record['size'])
        return {'totalCount': totalCount, 'data': data}

    def async_delete(self, *_, **__):
        '''Detete backup'''
        folder = self.get_folder()
        if 'property' in self.request_params:
            prop = self.request_params['property']
            del self.request_params['property']
        else:
            prop = 'name'
        for _, value in self.request_params.iteritems():
            file_apth = os.path.join(folder, value[prop])
            if os.path.isfile(file_apth):
                os.remove(file_apth)
        return {'success': True}
