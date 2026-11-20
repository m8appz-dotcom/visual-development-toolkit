"""Rename only toolkit presentation metadata; preserve IDs and MCP runtime."""
import argparse, hashlib, json, pathlib, shutil, socket, time

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rename(root, apply=False):
    root = pathlib.Path(root).resolve()
    source = root / 'plugins/game-modding-toolkit'
    manifest = source / '.codex-plugin/plugin.json'
    if not manifest.is_file():
        return {'root': str(root), 'status': 'not_installed'}
    data = json.loads(manifest.read_text(encoding='utf-8-sig'))
    assert data['name'] == 'game-modding-toolkit'
    before = data.get('interface', {}).get('displayName')
    assert before in ('Visual Development Toolkit', 'REA'), before
    runtime = source / 'mcp.json'
    runtime_hash = digest(runtime)
    if before == 'REA':
        return {'root': str(root), 'status': 'already_REA', 'version': data['version']}
    paths = [manifest]
    paths += [p for p in source.rglob('*.md') if '__pycache__' not in p.parts
              and 'Visual Development Toolkit' in p.read_text(encoding='utf-8-sig')]
    readme = root / 'README.md'
    if readme.is_file() and 'Visual Development Toolkit' in readme.read_text(encoding='utf-8-sig'):
        paths.append(readme)
    old_version = data['version']
    parts = old_version.split('.')
    assert len(parts) == 3 and all(p.isdecimal() for p in parts)
    new_version = old_version
    result = {'host': socket.gethostname(), 'root': str(root), 'source': str(source),
              'old_version': old_version, 'new_version': new_version,
              'files': [str(p.relative_to(root)) for p in paths],
              'mcp_sha256': runtime_hash, 'applied': apply}
    if not apply:
        return result
    backup = root / 'plugin-maintenance/rename-rea' / str(time.time_ns())
    backup.mkdir(parents=True)
    for path in paths:
        relative = path.relative_to(root)
        target = backup / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    for path in paths:
        text = path.read_text(encoding='utf-8-sig').replace('Visual Development Toolkit', 'REA')
        if path == manifest:
            parsed = json.loads(text)
            parsed['version'] = new_version
            text = json.dumps(parsed, ensure_ascii=False, indent=2) + '\n'
        path.write_text(text, encoding='utf-8')
    final = json.loads(manifest.read_text(encoding='utf-8'))
    assert final['name'] == 'game-modding-toolkit'
    assert final['interface']['displayName'] == 'REA'
    assert digest(runtime) == runtime_hash
    result.update(backup=str(backup), runtime_preserved=True)
    (backup / 'receipt.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('roots', nargs='+')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    print(json.dumps([rename(root, args.apply) for root in args.roots], indent=2))
