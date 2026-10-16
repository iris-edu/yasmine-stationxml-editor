# 2026-09-25, version 4.3.3-beta: ASGSR, Alexey Emanov
# About-page build date and revision.

import datetime
import os
import tempfile
import unittest
from unittest.mock import patch

from yasmine.app.utils.build_info import (
    build_info,
    format_build_timestamp,
    parse_reflog_line,
    write_image_build_info,
)


class BuildInfoTest(unittest.TestCase):

    def test_parse_reflog_line(self):
        line = (
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa '
            'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb '
            'Alex <a@b.c> 1727150000 +0300\tcommit: msg\n'
        )
        self.assertEqual(
            parse_reflog_line(line),
            (1727150000, 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'),
        )

    def test_format_build_timestamp_is_utc(self):
        self.assertEqual(
            format_build_timestamp(0),
            'Thu, 01 Jan 1970 00:00:00 +0000',
        )

    def test_env_overrides_git(self):
        env = {
            'YASMINE_BUILD_DATE': 'from-env',
            'YASMINE_REVISION': 'abc12345',
        }
        with patch.dict(os.environ, env, clear=False):
            info = build_info()
        self.assertEqual(info['build_timestamp'], 'from-env')
        self.assertEqual(info['commit_revision'], 'abc12345')

    def test_reads_git_dir(self):
        with tempfile.TemporaryDirectory() as root:
            git_dir = os.path.join(root, '.git')
            os.makedirs(os.path.join(git_dir, 'refs', 'heads'))
            os.makedirs(os.path.join(git_dir, 'logs'))
            sha = 'cccccccccccccccccccccccccccccccccccccccc'
            head = os.path.join(git_dir, 'HEAD')
            with open(head, 'w', encoding='utf-8') as handle:
                handle.write('ref: refs/heads/main\n')
            ref = os.path.join(git_dir, 'refs', 'heads', 'main')
            with open(ref, 'w', encoding='utf-8') as handle:
                handle.write(sha + '\n')
            log = os.path.join(git_dir, 'logs', 'HEAD')
            with open(log, 'w', encoding='utf-8') as handle:
                handle.write(
                    '0000000000000000000000000000000000000000 %s '
                    'Alex <a@b.c> 1727150000 +0000\tcommit: init\n' % sha
                )
            env = {
                'YASMINE_GIT_DIR': git_dir,
                'YASMINE_BUILD_DATE': '',
                'YASMINE_REVISION': '',
                'YASMINE_BUILD_INFO_FILE': os.path.join(root, 'missing-build-info.json'),
            }
            with patch.dict(os.environ, env, clear=False):
                info = build_info()
        self.assertEqual(info['commit_revision'], 'cccccccc')
        self.assertEqual(
            info['build_timestamp'], format_build_timestamp(1727150000))

    def test_image_file_supplies_build_date_and_revision(self):
        with tempfile.TemporaryDirectory() as root:
            git_dir = os.path.join(root, '.git')
            os.makedirs(os.path.join(git_dir, 'refs', 'heads'))
            sha = 'dddddddddddddddddddddddddddddddddddddddd'
            with open(os.path.join(git_dir, 'HEAD'), 'w', encoding='utf-8') as handle:
                handle.write('ref: refs/heads/main\n')
            with open(os.path.join(git_dir, 'refs', 'heads', 'main'), 'w', encoding='utf-8') as handle:
                handle.write(sha + '\n')
            dest = os.path.join(root, 'build-info.json')
            when = datetime.datetime(2026, 9, 24, 16, 11, 0, tzinfo=datetime.timezone.utc)
            written = write_image_build_info(git_dir, dest, when=when)
            env = {
                'YASMINE_BUILD_INFO_FILE': dest,
                'YASMINE_BUILD_DATE': '',
                'YASMINE_REVISION': '',
                'YASMINE_GIT_DIR': os.path.join(root, 'missing-git'),
            }
            with patch.dict(os.environ, env, clear=False):
                info = build_info()
        self.assertEqual(written['commit_revision'], 'dddddddd')
        self.assertEqual(info['commit_revision'], 'dddddddd')
        self.assertEqual(info['build_timestamp'], format_build_timestamp(when.timestamp()))
