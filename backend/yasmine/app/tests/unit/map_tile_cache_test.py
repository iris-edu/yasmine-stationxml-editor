# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
# Disk cache for proxied map tiles.

import os
import tempfile
import time
import unittest

from yasmine.app.handlers.xml_bldr import read_cached_tile, tile_cache_path, write_cached_tile


class MapTileCacheTest(unittest.TestCase):

    def test_round_trip_and_expiry(self):
        root = tempfile.mkdtemp()
        path = tile_cache_path('osm', 3, 2, 1, root=root)
        write_cached_tile(path, b'png-bytes')
        self.assertEqual(read_cached_tile(path), b'png-bytes')
        self.assertTrue(path.endswith(os.path.join('osm', '3', '2', '1.png')))
        stale = time.time() + 90000
        self.assertIsNone(read_cached_tile(path, now=stale))
        self.assertIsNone(read_cached_tile(os.path.join(root, 'missing.png')))
