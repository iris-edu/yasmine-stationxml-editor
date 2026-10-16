# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
# 2026-09-29, version 4.4.0-beta: ASGSR, Alexey Emanov
# Safe ZIP extraction: reject traversal and cap uncompressed size / entries.

import os
import re

MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024
MAX_ZIP_ENTRIES = 10000
COPY_CHUNK = 64 * 1024

_DRIVE_OR_UNC = re.compile(r'^([A-Za-z]:|/|//)')


class UnsafeZipError(ValueError):
    pass


def _is_within_directory(directory, target):
    directory = os.path.realpath(directory)
    target = os.path.realpath(target)
    return target == directory or target.startswith(directory + os.sep)


def _normalized_member_name(filename):
    return (filename or '').replace('\\', '/')


def _reject_unsafe_member_name(name, original):
    if not name or name == '..':
        raise UnsafeZipError('Unsafe zip path: %s' % original)
    if name.startswith('/') or name.startswith('../') or '/../' in name:
        raise UnsafeZipError('Unsafe zip path: %s' % original)
    # Windows drive (C:/...) or UNC (//server/share) after slash normalize.
    if _DRIVE_OR_UNC.match(name) or (len(name) >= 2 and name[1] == ':'):
        raise UnsafeZipError('Unsafe zip path: %s' % original)


def _ensure_entry_budget(zip_file, max_entries=MAX_ZIP_ENTRIES):
    count = len(zip_file.infolist())
    if count > max_entries:
        raise UnsafeZipError('Zip has too many entries (%s > %s)' % (count, max_entries))


def safe_extractall(zip_file, dest_dir, max_bytes=MAX_UNCOMPRESSED_BYTES,
                    max_entries=MAX_ZIP_ENTRIES):
    dest_dir = os.path.realpath(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)
    _ensure_entry_budget(zip_file, max_entries)
    total = 0
    for info in zip_file.infolist():
        name = _normalized_member_name(info.filename)
        _reject_unsafe_member_name(name, info.filename)
        target = os.path.realpath(os.path.join(dest_dir, name))
        if not _is_within_directory(dest_dir, target):
            raise UnsafeZipError('Zip slip: %s' % info.filename)
        if name.endswith('/') or (hasattr(info, 'is_dir') and info.is_dir()):
            os.makedirs(target, exist_ok=True)
            continue
        os.makedirs(os.path.dirname(target), exist_ok=True)
        remaining = max_bytes - total
        written = 0
        with zip_file.open(info) as source, open(target, 'wb') as dest:
            while True:
                chunk = source.read(COPY_CHUNK)
                if not chunk:
                    break
                written += len(chunk)
                if written > remaining:
                    dest.close()
                    os.remove(target)
                    raise UnsafeZipError('Zip uncompressed size exceeds limit')
                dest.write(chunk)
        total += written
    return dest_dir


def safe_extract_flat(zip_file, dest_dir, max_bytes=MAX_UNCOMPRESSED_BYTES,
                      max_entries=MAX_ZIP_ENTRIES):
    dest_dir = os.path.realpath(dest_dir)
    os.makedirs(dest_dir, exist_ok=True)
    _ensure_entry_budget(zip_file, max_entries)
    total = 0
    for info in zip_file.infolist():
        name = _normalized_member_name(info.filename)
        if name.endswith('/') or (hasattr(info, 'is_dir') and info.is_dir()):
            continue
        filename = os.path.basename(name.rstrip('/'))
        if not filename or filename in ('.', '..'):
            continue
        target = os.path.realpath(os.path.join(dest_dir, filename))
        if not _is_within_directory(dest_dir, target):
            raise UnsafeZipError('Zip slip: %s' % info.filename)
        remaining = max_bytes - total
        written = 0
        with zip_file.open(info) as source, open(target, 'wb') as dest:
            while True:
                chunk = source.read(COPY_CHUNK)
                if not chunk:
                    break
                written += len(chunk)
                if written > remaining:
                    dest.close()
                    os.remove(target)
                    raise UnsafeZipError('Zip uncompressed size exceeds limit')
                dest.write(chunk)
        total += written
    return dest_dir
