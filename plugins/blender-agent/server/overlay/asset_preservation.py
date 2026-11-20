"""Read-only GLB regression checks and an opt-in, fail-closed delivery route.

This is an artifact guard, not a Python sandbox or an automatic likeness judge.
No Blender scene access; no third-party dependencies; originals are never written.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import struct
import uuid
import zlib

MAX_FILE = 512 * 1024 * 1024
MAX_PIXELS = 16 * 1024 * 1024
COMPONENTS = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
WIDTHS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT2': 4, 'MAT3': 9, 'MAT4': 16}
EDITABLE = {'POSITION', 'NORMAL', 'TANGENT', 'TEXCOORD_0', 'TEXCOORD_1', 'TEXCOORD_2', 'TEXCOORD_3', 'COLOR_0', 'COLOR_1'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_file(path, suffixes=None):
    p = Path(path).resolve(strict=True)
    if not p.is_file() or (suffixes and p.suffix.lower() not in suffixes):
        raise ValueError('Unsupported file type')
    if p.stat().st_size > MAX_FILE:
        raise ValueError('File exceeds 512 MiB guard budget')
    return p, p.read_bytes()


class GLB:
    def __init__(self, path):
        self.path, data = read_file(path, {'.glb'})
        self.sha = digest(data)
        if len(data) < 28 or struct.unpack_from('<III', data) != (0x46546C67, 2, len(data)):
            raise ValueError('Invalid GLB header or length')
        chunks = []
        off = 12
        while off < len(data):
            if off + 8 > len(data):
                raise ValueError('Truncated GLB chunk')
            size, kind = struct.unpack_from('<II', data, off)
            if size % 4 or off + 8 + size > len(data):
                raise ValueError('Invalid GLB chunk extent')
            chunks.append((kind, data[off + 8:off + 8 + size]))
            off += size + 8
        if len(chunks) != 2 or chunks[0][0] != 0x4E4F534A or chunks[1][0] != 0x004E4942:
            raise ValueError('Guard supports one JSON and one embedded BIN chunk')
        self.j = json.loads(chunks[0][1])
        self.bin = chunks[1][1]
        if self.j.get('asset', {}).get('version') != '2.0':
            raise ValueError('Expected glTF asset version 2.0')
        if self.j.get('extensionsRequired'):
            raise ValueError('Required GLB extensions need a dedicated verified decoder')
        buffers = self.j.get('buffers', [])
        if len(buffers) != 1 or 'uri' in buffers[0] or buffers[0]['byteLength'] > len(self.bin):
            raise ValueError('External or invalid GLB buffers are not supported')
        self.bin = self.bin[:buffers[0]['byteLength']]
        for image in self.j.get('images', []):
            if 'bufferView' not in image or 'uri' in image:
                raise ValueError('External images are not covered by this guard')

    def view(self, index):
        v = self.j['bufferViews'][index]
        start, size = v.get('byteOffset', 0), v['byteLength']
        if v.get('buffer', 0) != 0 or min(start, size) < 0 or start + size > len(self.bin):
            raise ValueError('Invalid bufferView')
        return v, self.bin[start:start + size]

    def accessor(self, index):
        a = self.j['accessors'][index]
        if 'sparse' in a or 'bufferView' not in a:
            raise ValueError('Sparse or implicit accessors require a dedicated decoder')
        v, data = self.view(a['bufferView'])
        width = COMPONENTS[a['componentType']] * WIDTHS[a['type']]
        count, off, stride = a['count'], a.get('byteOffset', 0), v.get('byteStride', width)
        if not isinstance(count, int) or count < 0 or count > 2_000_000 or off < 0 or stride < width:
            raise ValueError('Invalid accessor layout')
        end = off + (count - 1) * stride + width if count else off
        if end > len(data):
            raise ValueError('Accessor exceeds bufferView')
        rows = [data[off + i * stride:off + i * stride + width] for i in range(count)]
        if a['componentType'] == 5126 and any(not math.isfinite(f[0]) for row in rows for f in struct.iter_unpack('<f', row)):
            raise ValueError('Non-finite accessor value')
        layout = (a['componentType'], a['type'], bool(a.get('normalized', False)), count)
        return layout, rows

    def primitive(self, mesh, primitive):
        if type(mesh) is not int or type(primitive) is not int or min(mesh, primitive) < 0:
            raise ValueError('Invalid mesh/primitive index')
        return self.j['meshes'][mesh]['primitives'][primitive]

    def image(self, index):
        return self.view(self.j['images'][index]['bufferView'])[1]


def decode_png(data):
    """Bounded PNG RGB/RGBA8 decoder. Unsupported changes fail, never silently pass."""
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('Changed textures must be embedded non-interlaced RGB/RGBA8 PNG')
    off, packed, profile, header, ended = 8, bytearray(), [], None, False
    while off < len(data):
        if off + 12 > len(data):
            raise ValueError('Truncated PNG')
        n = struct.unpack_from('>I', data, off)[0]
        kind, value = data[off + 4:off + 8], data[off + 8:off + 8 + n]
        if off + n + 12 > len(data) or zlib.crc32(kind + value) & 0xFFFFFFFF != struct.unpack_from('>I', data, off + 8 + n)[0]:
            raise ValueError('Invalid PNG chunk or CRC')
        if kind == b'IHDR':
            if header is not None or n != 13:
                raise ValueError('Invalid PNG header')
            header = struct.unpack('>IIBBBBB', value)
        elif kind == b'IDAT':
            packed.extend(value)
        elif kind in (b'gAMA', b'sRGB', b'iCCP', b'cHRM', b'tRNS'):
            profile.append((kind.decode(), digest(value)))
        elif kind in (b'acTL', b'fcTL', b'fdAT'):
            raise ValueError('Animated PNG is not supported')
        elif kind == b'IEND':
            ended = True
            break
        elif kind[:1].isupper():
            raise ValueError('Unsupported critical PNG chunk')
        off += n + 12
    if not header or not ended:
        raise ValueError('Incomplete PNG')
    w, h, depth, color, compression, filtering, interlace = header
    if not 0 < w * h <= MAX_PIXELS or min(w, h) <= 0 or depth != 8 or color not in (2, 6) or any((compression, filtering, interlace)):
        raise ValueError('PNG exceeds budget or uses unsupported encoding')
    channels = 3 if color == 2 else 4
    size = (w * channels + 1) * h
    dec = zlib.decompressobj()
    raw = dec.decompress(bytes(packed), size + 1)
    if len(raw) != size or not dec.eof or dec.unconsumed_tail or dec.unused_data:
        raise ValueError('PNG decoded size mismatch')
    rows, prev, stride = [], bytearray(w * channels), w * channels
    for y in range(h):
        mode = raw[y * (stride + 1)]
        row = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if mode not in range(5):
            raise ValueError('Invalid PNG filter')
        for x in range(stride) if mode else ():
            left = row[x - channels] if x >= channels else 0
            up, corner = prev[x], prev[x - channels] if x >= channels else 0
            if mode == 1:
                predict = left
            elif mode == 2:
                predict = up
            elif mode == 3:
                predict = (left + up) // 2
            else:
                p = left + up - corner
                predict = min(((abs(p - left), 0, left), (abs(p - up), 1, up), (abs(p - corner), 2, corner)))[2]
            row[x] = (row[x] + predict) & 255
        rows.append(bytes(row))
        prev = row
    return w, h, channels, tuple(profile), rows


def rectangles(value, w, h):
    if len(value) > 128:
        raise ValueError('At most 128 image rectangles')
    out = []
    for r in value:
        if len(r) != 4 or any(type(n) is not int for n in r):
            raise ValueError('Rectangle must be integer [x,y,width,height], origin top-left')
        x, y, rw, rh = r
        if min(x, y) < 0 or min(rw, rh) <= 0 or x + rw > w or y + rh > h:
            raise ValueError('Image rectangle out of bounds')
        out.append((x, y, rw, rh))
    return out


def changed_outside(a, b, allowed):
    w, h, channels, profile, ra = a
    if a[:4] != b[:4]:
        return True
    rb = b[4]
    for y in range(h):
        intervals = sorted((x, x + rw) for x, yy, rw, rh in allowed if yy <= y < yy + rh)
        end = 0
        for lo, hi in intervals + [(w, w)]:
            if lo > end and ra[y][end * channels:lo * channels] != rb[y][end * channels:lo * channels]:
                return True
            end = max(end, hi)
    return False


def validate_regions(glb, regions, editable=False):
    if not isinstance(regions, list) or len(regions) > 128:
        raise ValueError('Expected at most 128 regions')
    checked = []
    for region in regions:
        allowed_keys = {'mesh', 'primitive', 'vertices', 'attributes'} if editable else {'name', 'mesh', 'primitive', 'vertices'}
        if set(region) - allowed_keys:
            raise ValueError('Unknown region field')
        p = glb.primitive(region['mesh'], region['primitive'])
        count = glb.j['accessors'][p['attributes']['POSITION']]['count']
        ids = region['vertices']
        if not ids or len(ids) > count or any(type(i) is not int or i < 0 or i >= count for i in ids) or len(set(ids)) != len(ids):
            raise ValueError('Invalid or duplicate region vertex IDs')
        if editable:
            attrs = region.get('attributes', [])
            if not attrs or set(attrs) - EDITABLE or set(attrs) - set(p['attributes']):
                raise ValueError('Unsupported editable attribute; skin weights/joints stay protected')
        elif not isinstance(region.get('name'), str) or not region['name'].strip():
            raise ValueError('Protected feature requires a name')
        checked.append(region)
    return checked


def check_artifact(base, candidate, contract):
    failures, changes = [], []
    def fail(code, **details):
        if len(failures) < 100:
            failures.append({'code': code, **details})
    for key in ('nodes', 'scenes', 'scene', 'materials', 'textures', 'samplers', 'extensionsUsed', 'extensionsRequired', 'extensions'):
        if base.j.get(key) != candidate.j.get(key):
            fail('PROTECTED_DOCUMENT_CHANGED', field=key)
    for key in ('cameras', 'skins'):
        aa, bb = base.j.get(key, []), candidate.j.get(key, [])
        if key == 'skins':
            def skin_signature(g, s):
                return {k: v for k, v in s.items() if k != 'inverseBindMatrices'}, g.accessor(s['inverseBindMatrices']) if 'inverseBindMatrices' in s else None
            aa = [skin_signature(base, s) for s in aa]
            bb = [skin_signature(candidate, s) for s in bb]
        if aa != bb:
            fail('RIG_OR_CAMERA_CHANGED', field=key)
    def animation_signature(g):
        return [{**a, 'samplers': [{**s, 'input': g.accessor(s['input']), 'output': g.accessor(s['output'])} for s in a['samplers']]} for a in g.j.get('animations', [])]
    if animation_signature(base) != animation_signature(candidate):
        fail('ANIMATION_CHANGED')
    meshes, cm = base.j.get('meshes', []), candidate.j.get('meshes', [])
    if len(meshes) != len(cm):
        fail('MESH_STRUCTURE_CHANGED')
    for mi, mesh in enumerate(meshes):
        if mi >= len(cm):
            continue
        if {k: v for k, v in mesh.items() if k != 'primitives'} != {k: v for k, v in cm[mi].items() if k != 'primitives'}:
            fail('MESH_METADATA_CHANGED', mesh=mi)
        if len(mesh['primitives']) != len(cm[mi]['primitives']):
            fail('PRIMITIVE_STRUCTURE_CHANGED', mesh=mi)
        for pi, p in enumerate(mesh['primitives']):
            if pi >= len(cm[mi]['primitives']):
                continue
            q = cm[mi]['primitives'][pi]
            for key in ('mode', 'material', 'extensions', 'extras'):
                if p.get(key) != q.get(key):
                    fail('PRIMITIVE_METADATA_CHANGED', mesh=mi, primitive=pi, field=key)
            if ('indices' in p) != ('indices' in q) or ('indices' in p and base.accessor(p['indices']) != candidate.accessor(q['indices'])):
                fail('TOPOLOGY_CHANGED', mesh=mi, primitive=pi)
            if set(p['attributes']) != set(q['attributes']):
                fail('ATTRIBUTE_SET_CHANGED', mesh=mi, primitive=pi)
            for attr, ai in p['attributes'].items():
                if attr not in q['attributes']:
                    continue
                la, va = base.accessor(ai)
                lb, vb = candidate.accessor(q['attributes'][attr])
                if la != lb:
                    fail('ATTRIBUTE_LAYOUT_CHANGED', mesh=mi, primitive=pi, attribute=attr)
                    continue
                changed = {i for i, (x, y) in enumerate(zip(va, vb)) if x != y}
                if not changed:
                    continue
                changes.append({'mesh': mi, 'primitive': pi, 'attribute': attr, 'changed_vertices': len(changed)})
                allowed = set()
                for r in contract['edit_regions']:
                    if r['mesh'] == mi and r['primitive'] == pi and attr in r['attributes']:
                        allowed.update(r['vertices'])
                outside = changed - allowed
                if outside:
                    fail('ATTRIBUTE_OUTSIDE_EDIT_REGION', mesh=mi, primitive=pi, attribute=attr, count=len(outside), first_vertices=sorted(outside)[:8])
                for r in contract['protected_features']:
                    if r['mesh'] == mi and r['primitive'] == pi and changed.intersection(r['vertices']):
                        fail('PROTECTED_FEATURE_CHANGED', feature=r['name'], attribute=attr)
            ta, tb = p.get('targets', []), q.get('targets', [])
            if len(ta) != len(tb) or any(set(x) != set(y) or any(base.accessor(x[k]) != candidate.accessor(y[k]) for k in x) for x, y in zip(ta, tb)):
                fail('MORPH_TARGET_CHANGED', mesh=mi, primitive=pi)
    images, ci = base.j.get('images', []), candidate.j.get('images', [])
    if len(images) != len(ci):
        fail('IMAGE_SET_CHANGED')
    for ii in range(min(len(images), len(ci))):
        if images[ii].get('mimeType') != ci[ii].get('mimeType'):
            fail('IMAGE_ENCODING_METADATA_CHANGED', image=ii)
        old, new = base.image(ii), candidate.image(ii)
        if old == new:
            continue
        changes.append({'image': ii, 'encoded_bytes_changed': True})
        regions = [r for r in contract['image_edits'] if r['image'] == ii]
        if not regions:
            fail('IMAGE_CHANGED_WITHOUT_PIXEL_REGION', image=ii)
            continue
        try:
            da, db = decode_png(old), decode_png(new)
            rects = rectangles([v for r in regions for v in r['rectangles']], da[0], da[1])
            if changed_outside(da, db, rects):
                fail('IMAGE_CHANGED_OUTSIDE_PIXEL_REGION', image=ii)
            # Protect the UV bounding rectangle of each feature in each used image.
            for feature in contract['protected_features']:
                p = base.primitive(feature['mesh'], feature['primitive'])
                mat = base.j.get('materials', [])[p.get('material', 0)] if base.j.get('materials') else {}
                slots = list(mat.get('pbrMetallicRoughness', {}).values()) + list(mat.values())
                for slot in slots:
                    if not isinstance(slot, dict) or 'index' not in slot:
                        continue
                    texture = base.j['textures'][slot['index']]
                    if texture.get('source') != ii:
                        continue
                    uvkey = 'TEXCOORD_' + str(slot.get('texCoord', 0))
                    if slot.get('extensions') or uvkey not in p['attributes']:
                        fail('FEATURE_TEXTURE_MAPPING_UNVERIFIED', feature=feature['name'])
                        continue
                    layout, uvs = base.accessor(p['attributes'][uvkey])
                    if layout[:2] != (5126, 'VEC2'):
                        fail('FEATURE_TEXTURE_MAPPING_UNVERIFIED', feature=feature['name'])
                        continue
                    points = [struct.unpack('<ff', uvs[i]) for i in feature['vertices']]
                    if any(not (0 <= u <= 1 and 0 <= v <= 1) for u, v in points):
                        fail('FEATURE_TEXTURE_MAPPING_UNVERIFIED', feature=feature['name'])
                        continue
                    w, h, ch = da[:3]
                    x0, x1 = max(0, int(min(u for u, _ in points) * w) - 2), min(w, int(max(u for u, _ in points) * w) + 3)
                    # glTF UV (0,0) is the image's TOP-LEFT, unlike Blender UV UI.
                    y0, y1 = max(0, int(min(v for _, v in points) * h) - 2), min(h, int(max(v for _, v in points) * h) + 3)
                    if da[:4] != db[:4] or any(da[4][y][x0 * ch:x1 * ch] != db[4][y][x0 * ch:x1 * ch] for y in range(y0, y1)):
                        fail('PROTECTED_FEATURE_TEXTURE_CHANGED', feature=feature['name'], image=ii)
        except (ValueError, KeyError, IndexError, struct.error, zlib.error) as ex:
            fail('PIXEL_DIFF_UNVERIFIED', image=ii, reason=str(ex))
    return {'technical_pass': not failures, 'failures': failures, 'changes': changes,
            'identity_status': 'visual_review_required',
            'limits': ['Stable-topology embedded GLB only; unsupported changes fail closed',
                       'A technical pass is not a likeness verdict',
                       'Feature texture protection uses UV bounding rectangles, not semantic recognition',
                       'Arbitrary scripts and other export paths are outside this opt-in guard']}


def register(mcp, state_dir):
    home = Path(state_dir) / 'asset-preservation'

    def store(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8') as f:
            json.dump(value, f, indent=2, ensure_ascii=False)

    def load_id(value, kind):
        if len(value) != 32 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('Invalid preservation identifier')
        return json.loads((home / kind / (value + '.json')).read_text(encoding='utf-8'))

    def validate(guard, candidate_path):
        baseline, candidate = GLB(guard['baseline']), GLB(candidate_path)
        if baseline.sha != guard['baseline_sha256']:
            raise ValueError('Baseline changed since guard creation')
        for reference in guard['references']:
            if digest(read_file(reference['path'])[1]) != reference['sha256']:
                raise ValueError('Original reference changed since guard creation')
        report = check_artifact(baseline, candidate, guard)
        return {**report, 'guard_id': guard['guard_id'], 'baseline_sha256': baseline.sha,
                'candidate': str(candidate.path), 'candidate_sha256': candidate.sha}

    @mcp.tool()
    def get_asset_preservation_capabilities() -> dict:
        """Describe the local GLB guard and its limits; does not access or modify Blender scenes."""
        return {'status': 'ok', 'version': '1.0.0', 'format': 'embedded GLB2, stable topology',
                'checks': ['outside-ROI vertex attributes including opacity', 'protected features and texture UV footprints',
                           'rig/bind/weights', 'animation samples', 'global materials', 'outside-ROI PNG pixels'],
                'changed_png_limit_pixels': MAX_PIXELS, 'automatic_likeness_judge': False,
                'enforcement': 'Only export_asset_with_preservation_guard gates delivery; arbitrary Python/other exporters are not intercepted'}

    @mcp.tool()
    def create_asset_preservation_guard(baseline_glb: str, reference_images: list[str], edit_regions: list[dict], protected_features: list[dict], image_edits: list[dict], objective: str) -> dict:
        """Freeze the preferred base and original references. Declare exact editable vertices/attributes and top-left PNG pixel rectangles. No model writes."""
        base = GLB(baseline_glb)
        if not objective.strip() or not 1 <= len(reference_images) <= 16:
            raise ValueError('Objective and 1–16 original reference images required')
        refs = []
        for name in reference_images:
            p, data = read_file(name, {'.png', '.jpg', '.jpeg', '.webp'})
            refs.append({'path': str(p), 'sha256': digest(data)})
        edits = validate_regions(base, edit_regions, True)
        features = validate_regions(base, protected_features)
        for feature in features:
            for edit in edits:
                if (feature['mesh'], feature['primitive']) == (edit['mesh'], edit['primitive']) and set(feature['vertices']).intersection(edit['vertices']):
                    raise ValueError('Editable region overlaps protected feature ' + feature['name'])
        if len(image_edits) > 32:
            raise ValueError('At most 32 texture edits')
        for edit in image_edits:
            if set(edit) != {'image', 'rectangles'} or type(edit['image']) is not int or edit['image'] < 0:
                raise ValueError('Image edit requires image index and rectangles')
            png = decode_png(base.image(edit['image']))
            if not edit['rectangles']:
                raise ValueError('Empty image edit region')
            rectangles(edit['rectangles'], png[0], png[1])
        value = {'schema': 'blender-asset-preservation/1', 'guard_id': uuid.uuid4().hex,
                 'baseline': str(base.path), 'baseline_sha256': base.sha, 'references': refs,
                 'edit_regions': edits, 'protected_features': features, 'image_edits': image_edits, 'objective': objective}
        store(home / 'guards' / (value['guard_id'] + '.json'), value)
        return {'status': 'ok', 'guard_id': value['guard_id'], 'baseline_sha256': base.sha,
                'identity_status': 'visual_review_required', 'model_written': False}

    @mcp.tool()
    def validate_asset_preservation(guard_id: str, candidate_glb: str) -> dict:
        """Compare a candidate against its frozen base and allowed regions. Reads artifacts only; technical pass never approves likeness."""
        return {'status': 'ok', **validate(load_id(guard_id, 'guards'), candidate_glb), 'model_written': False}

    @mcp.tool()
    def record_asset_identity_review(guard_id: str, candidate_glb: str, outcome: str, evaluator: str, observations: str, views: list[dict]) -> dict:
        """Record a Codex/external visual attestation after viewing original/base/candidate. Not human approval or automatic proof of likeness."""
        if outcome not in ('preserved', 'regressed', 'uncertain') or evaluator not in ('codex', 'external') or len(observations.strip()) < 10:
            raise ValueError('Explicit visual outcome, evaluator and observations required')
        required = {'front', 'three_quarter', 'profile_left', 'profile_right'}
        if len(views) > 12 or {v.get('view') for v in views} != required:
            raise ValueError('Front, three-quarter and both profiles required')
        evidence = []
        for view in views:
            if set(view) != {'view', 'baseline_image', 'candidate_image'}:
                raise ValueError('Each view requires baseline_image and candidate_image')
            row = {'view': view['view']}
            for key in ('baseline_image', 'candidate_image'):
                p, data = read_file(view[key], {'.png', '.jpg', '.jpeg', '.webp'})
                row[key] = {'path': str(p), 'sha256': digest(data)}
            evidence.append(row)
        report = validate(load_id(guard_id, 'guards'), candidate_glb)
        value = {'review_id': uuid.uuid4().hex, 'guard_id': guard_id, 'candidate_sha256': report['candidate_sha256'],
                 'outcome': outcome, 'evaluator': evaluator, 'observations': observations, 'views': evidence,
                 'attestation_only': True, 'human_approval': False}
        store(home / 'reviews' / (value['review_id'] + '.json'), value)
        return {'status': 'ok', **value, 'technical_pass': report['technical_pass'], 'model_written': False}

    @mcp.tool()
    def export_asset_with_preservation_guard(guard_id: str, candidate_glb: str, review_id: str, output_glb: str) -> dict:
        """Copy to a NEW GLB only after technical pass and hash-bound preserved-identity attestation. Never overwrites or claims human approval."""
        report = validate(load_id(guard_id, 'guards'), candidate_glb)
        review = load_id(review_id, 'reviews')
        if not report['technical_pass']:
            raise ValueError('Preservation violations block guarded export')
        if review['guard_id'] != guard_id or review['candidate_sha256'] != report['candidate_sha256'] or review['outcome'] != 'preserved':
            raise ValueError('Missing, stale, uncertain or regressed identity review blocks guarded export')
        for view in review['views']:
            for key in ('baseline_image', 'candidate_image'):
                if digest(read_file(view[key]['path'])[1]) != view[key]['sha256']:
                    raise ValueError('Visual evidence changed after review')
        out = Path(output_glb).resolve()
        if out.suffix.lower() != '.glb' or not out.parent.is_dir():
            raise ValueError('Output must be a NEW GLB in an existing directory')
        source, payload = read_file(candidate_glb, {'.glb'})
        if digest(payload) != report['candidate_sha256']:
            raise ValueError('Candidate changed during validation')
        with out.open('xb') as f:
            f.write(payload)
        return {'status': 'ok', 'output': str(out), 'sha256': report['candidate_sha256'],
                'technical_pass': True, 'identity_status': 'preserved_attestation_recorded', 'human_approval': False,
                'source_unchanged': True}
