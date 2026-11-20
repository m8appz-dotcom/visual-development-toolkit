"""Detached per-job supervisor; cancel only the child it launched."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

folder = Path(sys.argv[1]).resolve(strict=True)
spec = json.loads((folder / 'spec.json').read_text(encoding='utf-8'))


def write(value):
    value.update(job_id=folder.name, updated=time.time(), worker_pid=os.getpid())
    target = folder / 'status.json'
    temp = folder / (uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(value), encoding='utf-8')
    for attempt in range(20):
        try:
            os.replace(temp, target)
            return
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(.025)


proc = None
try:
    if (folder / 'cancel.json').exists():
        write({'status': 'cancelled', 'child_started': False})
        sys.exit(0)
    entry = folder / 'entry.py'
    entry.write_text('import runpy\nrunpy.run_path(' + repr(str(Path(__file__).resolve().with_name('blender_runner.py'))) +
                     ',init_globals={"SPEC_PATH":' + repr(str(folder / 'spec.json')) + '})\n', encoding='utf-8')
    args = [spec['binary'], '--background', '--factory-startup', '--disable-autoexec', '--threads', '2']
    if spec['blend_file']:
        args.append(spec['blend_file'])
    args.extend(['--python-exit-code', '1', '--python', str(entry)])
    start = time.monotonic()
    with (folder / 'stdout.log').open('wb') as out, (folder / 'stderr.log').open('wb') as err:
        proc = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                creationflags=subprocess.CREATE_NO_WINDOW, close_fds=True)
        write({'status': 'running', 'pid': proc.pid, 'started': time.time()})
        terminal = None
        while proc.poll() is None:
            if (folder / 'cancel.json').exists():
                terminal = 'cancelled'
                break
            if time.monotonic() - start > spec['timeout_seconds']:
                terminal = 'timed_out'
                break
            time.sleep(.1)
        if terminal:
            proc.kill()
        rc = proc.wait(10)
    result_file = folder / 'result.json'
    result = json.loads(result_file.read_text(encoding='utf-8')) if result_file.exists() else {}
    status = terminal or ('succeeded' if rc == 0 and result.get('status') == 'ok' else 'failed')
    write({'status': status, 'pid': proc.pid, 'returncode': rc, 'seconds': time.monotonic() - start})
except SystemExit:
    raise
except BaseException as ex:
    if proc is not None and proc.poll() is None:
        proc.kill()
        proc.wait(10)
    write({'status': 'failed', 'error': str(ex)})
