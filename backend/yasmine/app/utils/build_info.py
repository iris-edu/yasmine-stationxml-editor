# 2026-09-25, version 4.3.3-beta: ASGSR, Alexey Emanov
# Build date and git revision shown on the About page.

import calendar
import datetime
import json
import os
import re

from yasmine.app.settings import ROOT_DIR

BUILD_INFO_FILE = '/opt/yasmine/build-info.json'

_REFlog_SHA = re.compile(
    r'^[0-9a-fA-F]{40} ([0-9a-fA-F]{40}) .* ([0-9]+) [+-][0-9]{4}\t'
)
_SHA = re.compile(r'^[0-9a-fA-F]{40}$')


def build_info():
    """Return build date and revision for the About page."""
    timestamp = os.environ.get('YASMINE_BUILD_DATE', '').strip()
    revision = os.environ.get('YASMINE_REVISION', '').strip()
    if timestamp and revision:
        return {'build_timestamp': timestamp, 'commit_revision': revision}

    file_timestamp, file_revision = _from_file()
    timestamp = timestamp or file_timestamp
    revision = revision or file_revision
    if timestamp and revision:
        return {'build_timestamp': timestamp, 'commit_revision': revision}

    git_timestamp, git_revision = _from_git()
    return {
        'build_timestamp': timestamp or git_timestamp,
        'commit_revision': revision or git_revision,
    }


def write_image_build_info(git_dir, dest_path, when=None):
    """Write the About-page stamp installed into the image at build time."""
    revision = _revision(git_dir)
    moment = when or datetime.datetime.now(datetime.timezone.utc)
    payload = {
        'build_timestamp': format_build_timestamp(moment.timestamp()),
        'commit_revision': revision[:8] if revision else '',
    }
    parent = os.path.dirname(dest_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(dest_path, 'w', encoding='utf-8') as handle:
        json.dump(payload, handle)
        handle.write('\n')
    return payload


def parse_reflog_line(line):
    """Return unix time and full sha from a reflog line."""
    match = _REFlog_SHA.match(line.strip())
    if not match:
        return None
    return int(match.group(2)), match.group(1)


def format_build_timestamp(unix_timestamp):
    moment = datetime.datetime.fromtimestamp(
        int(unix_timestamp), datetime.timezone.utc)
    return '%s, %02d %s %04d %02d:%02d:%02d +0000' % (
        calendar.day_abbr[moment.weekday()],
        moment.day,
        calendar.month_abbr[moment.month],
        moment.year,
        moment.hour,
        moment.minute,
        moment.second,
    )


def _build_info_path():
    configured = os.environ.get('YASMINE_BUILD_INFO_FILE', '').strip()
    return configured or BUILD_INFO_FILE


def _from_file():
    path = _build_info_path()
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            payload = json.load(handle)
    except (OSError, ValueError):
        return '', ''
    if not isinstance(payload, dict):
        return '', ''
    timestamp = payload.get('build_timestamp') or ''
    revision = payload.get('commit_revision') or ''
    return str(timestamp).strip(), str(revision).strip()


def _from_git():
    for git_dir in _git_dirs():
        revision = _revision(git_dir)
        timestamp = _timestamp(git_dir)
        if revision or timestamp:
            return timestamp, revision[:8] if revision else ''
    return '', ''


def _git_dirs():
    seen = set()
    candidates = []
    configured = os.environ.get('YASMINE_GIT_DIR', '').strip()
    if configured:
        candidates.append(configured)
    current = os.path.abspath(ROOT_DIR)
    while True:
        candidates.append(os.path.join(current, '.git'))
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    for candidate in candidates:
        resolved = _resolve_git_dir(candidate)
        if resolved and resolved not in seen and os.path.isdir(resolved):
            seen.add(resolved)
            yield resolved


def _resolve_git_dir(path):
    if os.path.isdir(path):
        return path
    if not os.path.isfile(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            line = handle.read().strip()
    except OSError:
        return None
    if not line.startswith('gitdir:'):
        return None
    git_dir = line.split(':', 1)[1].strip()
    if not os.path.isabs(git_dir):
        git_dir = os.path.normpath(
            os.path.join(os.path.dirname(path), git_dir))
    return git_dir


def _revision(git_dir):
    head = _read(os.path.join(git_dir, 'HEAD')).strip()
    if _SHA.match(head):
        return head
    if not head.startswith('ref:'):
        return ''
    ref = head.split(':', 1)[1].strip()
    pointed = _read(os.path.join(git_dir, ref)).strip()
    if _SHA.match(pointed):
        return pointed
    packed = os.path.join(git_dir, 'packed-refs')
    try:
        with open(packed, 'r', encoding='utf-8') as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('^'):
                    continue
                sha, name = line.split(' ', 1)
                if name == ref and _SHA.match(sha):
                    return sha
    except OSError:
        return ''
    return ''


def _timestamp(git_dir):
    log_path = os.path.join(git_dir, 'logs', 'HEAD')
    try:
        with open(log_path, 'r', encoding='utf-8', errors='replace') as handle:
            last = None
            for line in handle:
                if line.strip():
                    last = line
    except OSError:
        return ''
    if not last:
        return ''
    parsed = parse_reflog_line(last)
    if not parsed:
        return ''
    return format_build_timestamp(parsed[0])


def _read(path):
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            return handle.read()
    except OSError:
        return ''
