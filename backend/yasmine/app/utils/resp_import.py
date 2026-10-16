# 2026-09-24, version 4.3.3-beta: ASGSR, Alexey Emanov
# 2026-10-04, version 4.4.0-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# Import an external RESP file into a channel Response attribute.
# Optionally set Sensor/DataLogger Description and SampleRate from decimation.
#
# ****************************************************************************

import io

from obspy.core.inventory import Equipment

from yasmine.app.enums.xml_node import XmlNodeAttrEnum
from yasmine.app.helpers.nrl.nrl_helper import response_from_resp
from yasmine.app.models.inventory import XmlNodeAttrModel, XmlNodeAttrValModel, XmlNodeInstModel
from yasmine.app.services.xml_service import XmlService
from yasmine.app.utils.db import db_transaction
from yasmine.app.utils.response_plot import polynomial_or_polezero_response
from yasmine.app.utils.response_sensitivity import response_obj_to_tree_json


def sample_rate_from_response(response):
    """Derive output sample rate from last stage; None if missing/unsafe."""
    if not response or not getattr(response, 'response_stages', None):
        return None
    last = response.response_stages[-1]
    factor = getattr(last, 'decimation_factor', None)
    input_rate = getattr(last, 'decimation_input_sample_rate', None)
    if factor in (None, 0) or input_rate is None:
        return None
    return input_rate / factor


def _trim_name(value):
    if value is None:
        return ''
    return str(value).strip()


def _recreate_attr(db, node_inst, attr_name):
    attr_model = db.query(XmlNodeAttrModel).filter(
        XmlNodeAttrModel.name == attr_name
    ).one()
    if node_inst.id:
        db.query(XmlNodeAttrValModel) \
            .filter(XmlNodeAttrValModel.attr_id == attr_model.id) \
            .filter(XmlNodeAttrValModel.node_inst_id == node_inst.id) \
            .delete(synchronize_session=False)
    attr_val = XmlNodeAttrValModel(
        node_inst_id=node_inst.id,
        attr_id=attr_model.id,
        attr=attr_model,
    )
    db.add(attr_val)
    return attr_val


def import_resp_into_channel(
    owner,
    node_inst_id,
    resp_bytes,
    sensor_name=None,
    datalogger_name=None,
    create_equipment=False,
):
    """Store the first RESP channel response on the channel and return its tree.

    ``owner`` is a handler or mixin with a ``db`` session.
    Non-empty ``sensor_name`` / ``datalogger_name`` set Equipment.description.
    ``create_equipment`` always writes Sensor and DataLogger (Upload RESP form).
    SampleRate is set when the last stage has usable decimation.
    """
    response = response_from_resp(io.BytesIO(resp_bytes))
    try:
        node_id = int(node_inst_id)
    except (TypeError, ValueError):
        raise ValueError('nodeInstanceId is required')
    node = owner.db.get(XmlNodeInstModel, node_id)
    if node is None:
        raise ValueError('Channel not found')

    write_sensor = create_equipment or sensor_name is not None
    write_datalogger = create_equipment or datalogger_name is not None
    sensor_name = _trim_name(sensor_name)
    datalogger_name = _trim_name(datalogger_name)
    if not create_equipment:
        write_sensor = bool(sensor_name)
        write_datalogger = bool(datalogger_name)
    sample_rate = sample_rate_from_response(response)

    with db_transaction(owner.db):
        response_attr = owner.db.query(XmlNodeAttrValModel).join(
            XmlNodeAttrValModel.attr
        ).filter(
            XmlNodeAttrValModel.node_inst_id == node.id,
            XmlNodeAttrModel.name == XmlNodeAttrEnum.RESPONSE,
        ).first()
        if response_attr is None:
            attr = owner.db.query(XmlNodeAttrModel).filter(
                XmlNodeAttrModel.name == XmlNodeAttrEnum.RESPONSE
            ).one()
            response_attr = XmlNodeAttrValModel(
                node_inst_id=node.id,
                attr_id=attr.id,
                attr=attr,
            )
            owner.db.add(response_attr)
        response_attr.value_obj = response

        if write_sensor:
            sensor_attr = _recreate_attr(owner.db, node, XmlNodeAttrEnum.SENSOR)
            sensor_attr.value_obj = Equipment(description=sensor_name)

        if write_datalogger:
            datalogger_attr = _recreate_attr(owner.db, node, XmlNodeAttrEnum.DATA_LOGGER)
            datalogger_attr.value_obj = Equipment(description=datalogger_name)

        if sample_rate is not None:
            sample_rate_attr = _recreate_attr(owner.db, node, XmlNodeAttrEnum.SAMPLE_RATE)
            sample_rate_attr.value_obj = sample_rate

        if node.xml_id:
            XmlService(owner).update_timestamp(node.xml_id)
        owner.db.flush()
        response_id = response_attr.id

    result = {
        'id': response_id,
        'response': response,
        'data': response_obj_to_tree_json(response, node.id, owner),
        'text': polynomial_or_polezero_response(response),
    }
    if sample_rate is not None:
        result['sample_rate'] = sample_rate
    return result
