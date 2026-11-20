"""Update plugin branding only, without renaming the REA analysis engine."""
import argparse, hashlib, json, os, pathlib, shutil, socket, subprocess, time

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

parser = argparse.ArgumentParser()
parser.add_argument('--host', required=True)
parser.add_argument('roots', nargs='+')
args = parser.parse_args()
assert socket.gethostname().lower() == args.host.lower(), 'Unexpected host'
results = []
for root_arg in args.roots:
    root = pathlib.Path(root_arg).resolve()
    source = root / 'plugins/game-modding-toolkit'
    manifest = source / '.codex-plugin/plugin.json'
    original = manifest.read_bytes()
    data = json.loads(original.decode('utf-8-sig'))
    assert data['name'] == 'game-modding-toolkit'
    assert data['interface']['displayName'] in ('REA', 'SAM')
    runtime = source / 'mcp.json'
    runtime_hash = sha(runtime)
    backup = root / 'plugin-maintenance/rename-sam' / str(time.time_ns())
    backup.mkdir(parents=True)
    (backup / 'plugin.json').write_bytes(original)
    data['interface']['displayName'] = 'SAM'
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert sha(runtime) == runtime_hash
    results.append({'host': socket.gethostname(), 'source': str(source), 'version': data['version'],
                    'displayName': 'SAM', 'backup': str(backup), 'runtime_sha256': runtime_hash})
codex = shutil.which('codex.cmd') or shutil.which('codex')
assert codex, 'Codex executable missing'
refresh = subprocess.run([codex, 'plugin', 'add', 'game-modding-toolkit@modding-lab', '--json'],
                         capture_output=True, text=True, timeout=90,
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
assert refresh.returncode == 0, refresh.stderr
installed = json.loads(refresh.stdout)
cache = pathlib.Path(installed['installedPath'])
actual = json.loads((cache / '.codex-plugin/plugin.json').read_text(encoding='utf-8-sig'))
assert actual['interface']['displayName'] == 'SAM', actual
assert actual['name'] == 'game-modding-toolkit'
assert any(sha(cache / 'mcp.json') == r['runtime_sha256'] for r in results)
receipt = {'host': socket.gethostname(), 'sources': results, 'installed': str(cache),
           'installed_name': actual['interface']['displayName'], 'version': actual['version'],
           'runtime_preserved': True}
for r in results:
    (pathlib.Path(r['backup']) / 'receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
