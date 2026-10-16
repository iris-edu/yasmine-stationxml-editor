# 2026-09-27, version 4.4.0-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# Background strict StationXML check. The HTTP request only starts the job
# and polls its percent, so a large warning list does not time out the scan.
#
# ****************************************************************************

import threading
import uuid

from yasmine.app.services.xml_service import XmlService


class StrictValidationJob(object):
    def __init__(self):
        self.percent = 0
        self.done = False
        self.failed = False
        self.message = ''
        self.result = None
        self.lock = threading.Lock()

    def set_percent(self, percent):
        with self.lock:
            if self.done:
                return
            try:
                percent = int(percent)
            except (TypeError, ValueError):
                return
            percent = max(0, min(99, percent))
            if percent > self.percent:
                self.percent = percent

    def snapshot(self):
        with self.lock:
            payload = {
                'success': not self.failed,
                'percent': 100 if self.done else self.percent,
                'done': self.done,
                'failed': self.failed,
                'message': self.message,
            }
            if self.done and self.result is not None:
                payload.update(self.result)
                payload['success'] = True
                payload['failed'] = False
            return payload


_guard = threading.Lock()
_jobs = {}
_by_xml = {}


def start_strict_validation(application, xml_id):
    """Start a check, or return the id of the one already running for this file."""
    xml_id = str(xml_id)
    with _guard:
        current = _by_xml.get(xml_id)
        if current is not None:
            running = _jobs.get(current)
            if running is not None and not running.done:
                return current
        job_id = uuid.uuid4().hex
        job = StrictValidationJob()
        _jobs[job_id] = job
        _by_xml[xml_id] = job_id
    thread = threading.Thread(
        target=_run_strict_validation,
        args=(application, xml_id, job),
        name='strict-xml-%s' % xml_id,
        daemon=True,
    )
    thread.start()
    return job_id


def get_strict_validation(job_id):
    with _guard:
        return _jobs.get(job_id)


def _run_strict_validation(application, xml_id, job):
    try:
        result = XmlService(application).validate_strict(xml_id, progress=job.set_percent)
        with job.lock:
            job.result = result
            job.percent = 100
            job.done = True
            job.failed = False
    except Exception as exc:
        reason = getattr(exc, 'reason', None) or str(exc)
        with job.lock:
            job.failed = True
            job.done = True
            job.percent = 100
            job.message = reason or 'Strict XML check failed.'
    finally:
        try:
            application.db.remove()
        except Exception:
            pass
