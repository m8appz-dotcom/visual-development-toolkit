"""Synthetic regression tests. Never opens or writes a user's Blender model."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

MODULE = Path(__file__).resolve().parents[1] / 'server/overlay/asset_preservation.py'
spec = importlib.util.spec_from_file_location('asset_preservation', MODULE)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def png(pixels=None, mode=0):
    w = h = 16
    rows = [bytearray([150, 110, 80, 255] * w) for _ in range(h)]
    for x, y, rgba in pixels or []:
        rows[y][x * 4:x * 4 + 4] = bytes(rgba)
    raw = bytearray()
    prev = bytearray(w * 4)
    for row in rows:
        raw.append(mode)
        for x, val in enumerate(row):
            left, up, corner = row[x - 4] if x >= 4 else 0, prev[x], prev[x - 4] if x >= 4 else 0
            if mode == 0: prediction = 0
            elif mode == 1: prediction = left
            elif mode == 2: prediction = up
            elif mode == 3: prediction = (left + up) // 2
            else:
                p = left + up - corner
                prediction = min(((abs(p - left), 0, left), (abs(p - up), 1, up), (abs(p - corner), 2, corner)))[2]
            raw.append((val - prediction) & 255)
        prev = row
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xFFFFFFFF)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


def fixture(path, mutations=None):
    m = mutations or {}
    binary = bytearray()
    views, accessors = [], []
    def data_view(payload):
        binary.extend(b'\0' * (-len(binary) % 4))
        views.append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(payload)})
        binary.extend(payload)
        return len(views) - 1
    def accessor(rows, typ, component=5126):
        fmt = {5126: 'f', 5123: 'H'}[component]
        payload = b''.join(struct.pack('<' + fmt * len(row), *row) for row in rows)
        accessors.append({'bufferView': data_view(payload), 'componentType': component, 'count': len(rows), 'type': typ})
        return len(accessors) - 1
    pos = [[float(i), 0., 0.] for i in range(6)]
    if 'position' in m:
        pos[m['position']][1] = .1
    if m.get('nan'):
        pos[0][0] = float('nan')
    colors = [[1., 1., 1., 1.] for _ in pos]
    if m.get('eye_alpha'):
        colors[0][3] = colors[1][3] = 0.
    if m.get('nose_color'):
        colors[2][0] = .8
    uv = [[.125, .125], [.25, .125], [.55, .55], [.1, .8], [.8, .1], [.8, .8]]
    if m.get('uv'):
        uv[0][0] = .2
    weights = [[1., 0., 0., 0.] for _ in pos]
    if m.get('weights'):
        weights[0] = [.8, .2, 0., 0.]
    attrs = {'POSITION': accessor(pos, 'VEC3'), 'COLOR_0': accessor(colors, 'VEC4'), 'TEXCOORD_0': accessor(uv, 'VEC2'),
             'JOINTS_0': accessor([[0, 0, 0, 0] for _ in pos], 'VEC4', 5123), 'WEIGHTS_0': accessor(weights, 'VEC4')}
    indices = accessor([[i] for i in (0, 1, 2, 3, 4, 5)], 'SCALAR', 5123)
    bind = [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]
    if m.get('bind'): bind[12] = 1.
    ib = accessor([bind], 'MAT4')
    time = accessor([[0.], [1.]], 'SCALAR')
    motion = [[0., 0., 0., 1.], [0., 0., .1 if m.get('animation') else 0., 1.]]
    rotation = accessor(motion, 'VEC4')
    image_data = b'not-a-png' if m.get('unsupported_image') else png(m.get('pixels'), m.get('filter', 0))
    image = data_view(image_data)
    material = {'pbrMetallicRoughness': {'baseColorTexture': {'index': 0}, 'baseColorFactor': [1., 1., 1., 1.]}, 'alphaMode': 'BLEND'}
    if m.get('material'): material['pbrMetallicRoughness']['baseColorFactor'][0] = .7
    j = {'asset': {'version': '2.0'}, 'buffers': [{'byteLength': len(binary)}], 'bufferViews': views, 'accessors': accessors,
         'meshes': [{'primitives': [{'attributes': attrs, 'indices': indices, 'material': 0}]}],
         'nodes': [{'name': 'rig', 'children': [1, 2]}, {'name': 'head'}, {'mesh': 0, 'skin': 0}],
         'skins': [{'joints': [1], 'inverseBindMatrices': ib}], 'scenes': [{'nodes': [0]}], 'scene': 0,
         'materials': [material], 'textures': [{'source': 0}], 'images': [{'bufferView': image, 'mimeType': 'image/png'}],
         'animations': [{'name': 'test', 'samplers': [{'input': time, 'output': rotation}], 'channels': [{'sampler': 0, 'target': {'node': 1, 'path': 'rotation'}}]}]}
    if m.get('sparse'): j['accessors'][0]['sparse'] = {}
    raw = json.dumps(j, separators=(',', ':')).encode(); raw += b' ' * (-len(raw) % 4)
    binary.extend(b'\0' * (-len(binary) % 4))
    payload = struct.pack('<III', 0x46546C67, 2, 28 + len(raw) + len(binary)) + struct.pack('<II', len(raw), 0x4E4F534A) + raw + struct.pack('<II', len(binary), 0x004E4942) + binary
    Path(path).write_bytes(payload)
    return Path(path)


class FakeMCP:
    def __init__(self): self.tools = {}
    def tool(self):
        def add(fn):
            self.tools[fn.__name__] = fn
            return fn
        return add


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.base = fixture(self.root / 'base.glb')
        self.reference = self.root / 'original.png'; self.reference.write_bytes(png())
        mcp = FakeMCP(); guard.register(mcp, self.root / 'state'); self.tools = mcp.tools
        self.contract = dict(baseline_glb=str(self.base), reference_images=[str(self.reference)],
                             edit_regions=[{'mesh': 0, 'primitive': 0, 'vertices': [2], 'attributes': ['POSITION', 'COLOR_0']}],
                             protected_features=[{'name': 'eyes', 'mesh': 0, 'primitive': 0, 'vertices': [0, 1]}],
                             image_edits=[{'image': 0, 'rectangles': [[8, 8, 2, 2]]}], objective='Repair only the synthetic nasal patch')
        self.gid = self.tools['create_asset_preservation_guard'](**self.contract)['guard_id']
    def tearDown(self): self.temp.cleanup()
    def check(self, mutations):
        return self.tools['validate_asset_preservation'](self.gid, str(fixture(self.root / 'candidate.glb', mutations)))
    def review(self, candidate, outcome='preserved'):
        views = [{'view': v, 'baseline_image': str(self.reference), 'candidate_image': str(self.reference)} for v in ('front', 'three_quarter', 'profile_left', 'profile_right')]
        return self.tools['record_asset_identity_review'](self.gid, str(candidate), outcome, 'codex', 'Synthetic protocol fixture, not a real visual approval', views)

    def test_unchanged_is_technical_only(self):
        r = self.check({}); self.assertTrue(r['technical_pass']); self.assertEqual(r['identity_status'], 'visual_review_required')
    def test_local_geometry_and_color_pass(self): self.assertTrue(self.check({'position': 2, 'nose_color': True})['technical_pass'])
    def test_body_and_silhouette_rejected(self):
        for i in (3, 4):
            with self.subTest(i=i): self.assertFalse(self.check({'position': i})['technical_pass'])
    def test_generic_eye_reveal_rejected(self):
        r = self.check({'eye_alpha': True}); self.assertIn('PROTECTED_FEATURE_CHANGED', [x['code'] for x in r['failures']])
    def test_rig_animation_uv_and_global_material_rejected(self):
        for key in ('bind', 'weights', 'animation', 'uv', 'material'):
            with self.subTest(key=key): self.assertFalse(self.check({key: True})['technical_pass'])
    def test_texture_local_pass_and_global_fail(self):
        self.assertTrue(self.check({'pixels': [(8, 8, [180, 110, 80, 255])]})['technical_pass'])
        self.assertFalse(self.check({'pixels': [(14, 14, [180, 110, 80, 255])]})['technical_pass'])
    def test_feature_texture_guard_uses_top_left_uv(self):
        contract = copy.deepcopy(self.contract); contract['image_edits'][0]['rectangles'] = [[0, 0, 16, 16]]
        self.gid = self.tools['create_asset_preservation_guard'](**contract)['guard_id']
        self.assertIn('PROTECTED_FEATURE_TEXTURE_CHANGED', [f['code'] for f in self.check({'pixels': [(1, 1, [0, 0, 0, 255])]})['failures']])
        self.assertTrue(self.check({'pixels': [(1, 14, [0, 0, 0, 255])]})['technical_pass'])
    def test_png_all_filters_decode_equally(self):
        decoded = guard.decode_png(png())
        for mode in range(1, 5): self.assertEqual(decoded, guard.decode_png(png(mode=mode)))
    def test_corrupt_png_crc_rejected(self):
        b = bytearray(png()); b[-1] ^= 1
        with self.assertRaises(ValueError): guard.decode_png(bytes(b))
    def test_unsupported_pixels_fail_closed(self): self.assertFalse(self.check({'unsupported_image': True})['technical_pass'])
    def test_bad_region_and_overlap_rejected(self):
        for ids in ([0], [True], [2, 2], [99]):
            value = copy.deepcopy(self.contract); value['edit_regions'][0]['vertices'] = ids
            with self.subTest(ids=ids), self.assertRaises(ValueError): self.tools['create_asset_preservation_guard'](**value)
    def test_baseline_and_reference_drift_rejected(self):
        self.base.write_bytes(self.base.read_bytes() + b'x')
        with self.assertRaises(ValueError): self.check({})
    def test_reference_drift_rejected(self):
        self.reference.write_bytes(png([(0, 0, [0, 0, 0, 255])]))
        with self.assertRaises(ValueError): self.check({})
    def test_nonfinite_and_sparse_fail_closed(self):
        for value in ({'nan': True}, {'sparse': True}):
            with self.subTest(value=value), self.assertRaises(ValueError): self.check(value)
    def test_export_requires_preserved_review(self):
        candidate = fixture(self.root / 'candidate.glb', {'position': 2})
        for outcome in ('uncertain', 'regressed'):
            review = self.review(candidate, outcome)
            with self.subTest(outcome=outcome), self.assertRaises(ValueError):
                self.tools['export_asset_with_preservation_guard'](self.gid, str(candidate), review['review_id'], str(self.root / 'out.glb'))
        self.assertFalse((self.root / 'out.glb').exists())
    def test_pass_review_cannot_override_technical_violation(self):
        candidate = fixture(self.root / 'candidate.glb', {'eye_alpha': True}); review = self.review(candidate)
        with self.assertRaises(ValueError): self.tools['export_asset_with_preservation_guard'](self.gid, str(candidate), review['review_id'], str(self.root / 'out.glb'))
    def test_new_copy_only_and_original_unchanged(self):
        before = guard.digest(self.base.read_bytes()); candidate = fixture(self.root / 'candidate.glb', {'position': 2}); review = self.review(candidate)
        result = self.tools['export_asset_with_preservation_guard'](self.gid, str(candidate), review['review_id'], str(self.root / 'out.glb'))
        self.assertFalse(result['human_approval']); self.assertEqual(guard.digest(self.base.read_bytes()), before)
        self.assertEqual((self.root / 'out.glb').read_bytes(), candidate.read_bytes())
        with self.assertRaises(FileExistsError): self.tools['export_asset_with_preservation_guard'](self.gid, str(candidate), review['review_id'], str(self.root / 'out.glb'))
    def test_candidate_hash_drift_rejected(self):
        candidate = fixture(self.root / 'candidate.glb'); review = self.review(candidate); fixture(candidate, {'position': 2})
        with self.assertRaises(ValueError): self.tools['export_asset_with_preservation_guard'](self.gid, str(candidate), review['review_id'], str(self.root / 'out.glb'))
    def test_evidence_drift_rejected(self):
        candidate = fixture(self.root / 'candidate.glb'); review = self.review(candidate)
        # Separate evidence path avoids relying only on original reference drift.
        review_file = self.root / 'state/asset-preservation/reviews' / (review['review_id'] + '.json')
        evidence = self.root / 'evidence.png'; evidence.write_bytes(png())
        value = json.loads(review_file.read_text()); value['views'][0]['candidate_image']['path'] = str(evidence)
        review_file.write_text(json.dumps(value)); evidence.write_bytes(png([(1, 1, [0, 0, 0, 255])]))
        with self.assertRaises(ValueError): self.tools['export_asset_with_preservation_guard'](self.gid, str(candidate), review['review_id'], str(self.root / 'out.glb'))


if __name__ == '__main__': unittest.main()
