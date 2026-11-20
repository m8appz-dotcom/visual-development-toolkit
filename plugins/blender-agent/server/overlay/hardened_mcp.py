"""Local overlay for the pinned Blender Lab MCP; upstream files stay intact."""
from __future__ import annotations

import asyncio
import base64
import contextvars
import functools
import contextlib
import importlib
import json
import os
from pathlib import Path
import pkgutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid

BASE = Path(os.environ.get('CODEX_BLENDER_HOME', r'D:\CodexTools\blender-mcp')).resolve()
STATE = BASE / 'hardening-state'
STATE.mkdir(parents=True, exist_ok=True)
SOURCE = Path(__file__).resolve().parent
BUNDLE = Path(os.environ.get('BLENDER_MCP_BUNDLE', str(Path(os.environ['APPDATA']) / 'Claude/Claude Extensions/ant.dir.gh.blender.blender-mcp')))
BLENDER = Path(os.environ.get('BLENDER_PATH', r'D:\CodexTools\Blender\5.2.1-S04\runtime\blender-5.2.1-windows-x64\blender.exe')).resolve()
sys.path.insert(0, str(BUNDLE))
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent

_selected = 'background-default'
_endpoint = contextvars.ContextVar('blender_endpoint', default=9877)
_registry_lock = threading.RLock()


@contextlib.contextmanager
def registry_guard():
    import msvcrt
    with _registry_lock, (STATE / 'registry.lock').open('a+b') as lock:
        lock.seek(0)
        if not lock.read(1):
            lock.write(b'0')
            lock.flush()
        for attempt in range(100):
            lock.seek(0)
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if attempt == 99:
                    raise
                time.sleep(.05)
        try:
            yield
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


def atomic(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    for attempt in range(20):
        try:
            os.replace(temp, path)
            return
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(.025)


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def failure(code: str, message: str, **details) -> dict:
    return {'status': 'error', 'error': {'code': code, 'message': message, **details}}


class ExecutionFailure(RuntimeError):
    def __init__(self, response):
        self.response = response
        super().__init__(response['error']['message'])


def rpc(code: str, port: int | None = None, timeout: float = 15, strict_json: bool = False) -> dict:
    port = port or _endpoint.get()
    request = json.dumps({'type': 'execute', 'code': code, 'strict_json': strict_json}).encode() + b'\0'
    with socket.create_connection(('127.0.0.1', port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(request)
        buf = bytearray()
        while b'\0' not in buf:
            chunk = sock.recv(65536)
            if not chunk:
                raise ConnectionError('Blender closed the connection before returning a complete response')
            buf.extend(chunk)
            if len(buf) > 64 * 1024 * 1024:
                raise ValueError('Blender response exceeds 64 MiB; return a summary or file path')
    return json.loads(buf.split(b'\0', 1)[0])


PROBE = """import bpy,os
result={'pid':os.getpid(),'binary':bpy.app.binary_path,'version':bpy.app.version_string,
'build':bpy.app.build_hash.decode(),'background':bpy.app.background,'filepath':bpy.data.filepath,
'dirty':bpy.data.is_dirty,'owner':bpy.app.driver_namespace.get('codex_mcp_session')}
"""


def registry() -> dict:
    file = STATE / 'sessions.json'
    return read(file) if file.exists() else {'background-default': {'port': 9877, 'owned': False}}


def session_info(session_id: str, timeout: float = 10) -> dict:
    item = registry().get(session_id)
    if not item:
        raise ValueError('Unknown Blender session: ' + session_id)
    response = rpc(PROBE, item['port'], timeout=timeout)
    if response.get('status') != 'ok':
        raise RuntimeError(str(response))
    info = response['result']
    if os.path.normcase(os.path.realpath(info['binary'])) != os.path.normcase(str(BLENDER)):
        raise RuntimeError('Session executable does not match the configured Blender binary')
    if item.get('pid') and item['pid'] != info['pid']:
        raise RuntimeError('Session PID changed; register it again before selecting it')
    return {'session_id': session_id, **item, **info}


def launch_detached(argv: list[str]) -> int:
    """WMI parent prevents MCP client cleanup from killing durable local jobs."""
    command = subprocess.list2cmdline(argv)
    literal = "'" + command.replace("'", "''") + "'"
    script = ("$ErrorActionPreference='Stop';$s=New-CimInstance Win32_ProcessStartup -ClientOnly -Property @{ShowWindow=[uint16]0};"
              "Invoke-CimMethod Win32_Process -MethodName Create -Arguments @{CommandLine=" + literal +
              ";ProcessStartupInformation=$s} | Select-Object ProcessId,ReturnValue | ConvertTo-Json -Compress")
    encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
    p = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
                       capture_output=True, text=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW,
                       stdin=subprocess.DEVNULL)
    if p.returncode:
        raise RuntimeError(p.stderr)
    value = json.loads(p.stdout)
    if value['ReturnValue']:
        raise RuntimeError('Hidden process launch failed: ' + str(value))
    return value['ProcessId']


def command(blend_file: str, script: Path) -> list[str]:
    args = [str(BLENDER), '--background', '--factory-startup', '--disable-autoexec', '--threads', '2']
    if blend_file:
        file = Path(blend_file).resolve(strict=True)
        if file.suffix.lower() != '.blend':
            raise ValueError('Expected an existing .blend file')
        args.append(str(file))
    return [*args, '--python-exit-code', '1', '--python', str(script)]


def run_cli(blend_file: str, code: str, timeout: float = 120) -> dict:
    """No Python expression/JSON markers on argv or stdout; bounded hidden child."""
    run_id = uuid.uuid4().hex
    folder = STATE / 'cli' / run_id
    folder.mkdir(parents=True)
    spec = {'code': code, 'result_path': str(folder / 'result.json'), 'state_dir': str(folder),
            'addon_root': str(BASE / 'official-addon'), 'progress_path': str(folder / 'progress.json')}
    atomic(folder / 'spec.json', spec)
    script = folder / 'entry.py'
    script.write_text('import runpy\nrunpy.run_path(' + repr(str(SOURCE / 'blender_runner.py')) +
                      ',init_globals={"SPEC_PATH":' + repr(str(folder / 'spec.json')) + '})\n', encoding='utf-8')
    start = time.monotonic()
    argv = command(blend_file, script)
    atomic(folder / 'invocation.json', {'argv': argv, 'timeout': timeout})
    with (folder / 'stdout.log').open('wb') as out, (folder / 'stderr.log').open('wb') as err:
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                creationflags=subprocess.CREATE_NO_WINDOW, close_fds=True)
        try:
            rc = proc.wait(timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(10)
            return failure('CLI_TIMEOUT', f'Blender CLI exceeded {timeout:g} seconds', run_id=run_id,
                           logs=str(folder), process_cancelled=True)
    if not (folder / 'result.json').exists():
        return failure('CLI_NO_RESULT', 'Blender exited without a result', run_id=run_id,
                       returncode=rc, logs=str(folder))
    response = read(folder / 'result.json')
    if rc and response.get('status') == 'ok':
        return failure('CLI_PROCESS_FAILED', 'Blender failed after producing a result', returncode=rc, logs=str(folder))
    response['execution'] = {'run_id': run_id, 'seconds': time.monotonic() - start, 'returncode': rc, 'logs': str(folder)}
    return response


def patch_upstream() -> None:
    from blmcp.tools_helpers import connection, blender_cli
    connection.send_code = lambda code, strict_json: rpc(code, strict_json=strict_json, timeout=300)
    def cli_compatible(blend_file, code, timeout=120):
        value = run_cli(blend_file, code, timeout)
        if value.get('status') == 'error':
            raise ExecutionFailure(value)
        return value['result']
    blender_cli.run_blender_cli = cli_compatible
    blender_cli.send_code = connection.send_code


def error_in(value):
    if not isinstance(value, dict):
        return None
    if value.get('status') in ('error', 'failed'):
        return value
    nested = value.get('result')
    if isinstance(nested, dict) and nested.get('status') in ('error', 'failed'):
        return nested
    return None


class HardenedMCP(FastMCP):
    async def call_tool(self, name, arguments):
        try:
            info = registry().get(_selected)
            if not info:
                raise ValueError('Selected session is no longer registered')
            token = _endpoint.set(info['port'])
            try:
                # Upstream synchronous tools otherwise block all status/cancel requests.
                tool = self._tool_manager.get_tool(name)
                if tool and not tool.is_async:
                    raw = await asyncio.to_thread(self._run_sync, name, arguments)
                else:
                    raw = await super().call_tool(name, arguments)
            finally:
                _endpoint.reset(token)
            structured = raw.structuredContent if isinstance(raw, CallToolResult) else (raw[1] if isinstance(raw, tuple) and len(raw) == 2 else (raw if isinstance(raw, dict) else None))
            if structured is None and isinstance(raw, list) and len(raw) == 1 and isinstance(raw[0], TextContent):
                try:
                    structured = json.loads(raw[0].text)
                except (ValueError, TypeError):
                    pass
            error = error_in(structured)
            if error:
                detail = error.get('error', {})
                detail = detail if isinstance(detail, dict) else {'message': str(detail)}
                result = failure(detail.get('code', 'BLENDER_OPERATION_FAILED'), detail.get('message') or error.get('message') or 'Blender operation failed', tool=name, original=structured)
                return CallToolResult(isError=True, structuredContent=result, content=[TextContent(type='text', text=json.dumps(result))])
            return raw
        except Exception as ex:
            cause = ex
            while cause is not None and not isinstance(cause, ExecutionFailure):
                cause = cause.__cause__
            if isinstance(cause, ExecutionFailure):
                result = {**cause.response, 'tool': name}
            else:
                result = failure('MCP_EXECUTION_FAILED', str(ex), tool=name, exception_type=type(ex).__name__)
            return CallToolResult(isError=True, structuredContent=result, content=[TextContent(type='text', text=json.dumps(result))])

    def _run_sync(self, name, arguments):
        # Function argument validation and output conversion remain in the SDK.
        return asyncio.run(self._tool_manager.call_tool(name, arguments, context=None, convert_result=True))


def job_path(job_id: str) -> Path:
    if len(job_id) != 32 or any(c not in '0123456789abcdef' for c in job_id):
        raise ValueError('Invalid job ID')
    path = STATE / 'jobs' / job_id
    if not (path / 'spec.json').exists():
        raise ValueError('Unknown job ID')
    return path


def register_extra(mcp):
    def render_image(output_path, thumbnail):
        output = Path(output_path)
        formats = {'.png':'PNG','.jpg':'JPEG','.jpeg':'JPEG','.exr':'OPEN_EXR','.tif':'TIFF','.tiff':'TIFF','.webp':'WEBP','.bmp':'BMP'}
        if not output.is_absolute() or output.suffix.lower() not in formats or output.exists():
            raise ValueError('Render output must be a new absolute image path with a supported extension')
        output.parent.mkdir(parents=True,exist_ok=True)
        stage = output.with_name('.' + output.stem + '-' + uuid.uuid4().hex + output.suffix)
        options = {'output':str(stage),'format':formats[output.suffix.lower()],'thumbnail':thumbnail}
        code = 'OPTIONS='+repr(options)+'\n'+(SOURCE/'render_image.py').read_text(encoding='utf-8')
        value = rpc(code,timeout=300)
        if error_in(value):
            return value
        if not stage.is_file() or stage.stat().st_size==0:
            return failure('RENDER_NO_FILE','Blender did not write the expected image')
        os.link(stage,output)
        stage.unlink()
        return {'status':'ok','filepath':str(output),'bytes':output.stat().st_size,'render':value['result']}

    @mcp.tool()
    def render_thumbnail_to_path(output_path: str) -> dict[str,object]:
        """Render a preview up to 320 pixels to a NEW absolute image path; restore render settings afterwards."""
        return render_image(output_path,True)

    @mcp.tool()
    def render_viewport_to_path(output_path: str) -> dict[str,object]:
        """Render the scene camera with current settings to a NEW absolute image path; this is a final render, not a viewport screenshot."""
        return render_image(output_path,False)

    @mcp.tool()
    def get_blender_capabilities() -> dict:
        """Return selected runtime identity and supported modes; no scene modifications."""
        info = session_info(_selected)
        return {'status': 'ok', 'session': info, 'capabilities': {'python': True, 'isolated_cli': True,
                'durable_jobs': True, 'cancel_owned_job': True, 'checkpoint_restart': True,
                'copy_transaction': True, 'scene_checkpoints': True, 'interactive_ui': not info['background']},
                'limits': ['Checkpoints cover Blender scene data, not external file/network effects',
                           'Restart uses an explicit checkpoint or original input, not instruction-level continuation']}

    @mcp.tool()
    def list_blender_sessions() -> dict:
        """List registered loopback sessions with live identity checks."""
        items = []
        for session_id in registry():
            try:
                items.append({'status': 'ok', **session_info(session_id)})
            except Exception as ex:
                items.append({'status': 'unavailable', 'session_id': session_id, 'message': str(ex)})
        return {'status': 'ok', 'selected': _selected, 'sessions': items}

    @mcp.tool()
    def register_blender_session(session_id: str, port: int) -> dict:
        """Register an already running Blender bridge on loopback; validates binary and PID."""
        if not session_id or len(session_id) > 80 or not 1024 <= port <= 65535:
            raise ValueError('Invalid session ID or loopback port')
        value = rpc(PROBE, port, timeout=3)
        if value.get('status') != 'ok':
            raise RuntimeError(str(value))
        with registry_guard():
            data = registry()
            if session_id in data:
                raise ValueError('Session ID already exists')
            data[session_id] = {'port': port, 'pid': value['result']['pid'], 'owned': False}
            # Validate executable before registering.
            if os.path.normcase(os.path.realpath(value['result']['binary'])) != os.path.normcase(str(BLENDER)):
                raise ValueError('Unexpected Blender executable')
            atomic(STATE / 'sessions.json', data)
        return {'status': 'ok', 'session': session_info(session_id)}

    @mcp.tool()
    def select_blender_session(session_id: str) -> dict:
        """Select a live validated session for this MCP server connection; does not open files."""
        global _selected
        info = session_info(session_id)
        _selected = session_id
        return {'status': 'ok', 'session': info}

    @mcp.tool()
    def start_blender_session(session_id: str, background: bool = True) -> dict:
        """Start an isolated factory session; GUI mode starts hidden without touching existing windows."""
        if not session_id or len(session_id) > 80:
            raise ValueError('Invalid session ID')
        with registry_guard():
            data = registry()
            if session_id in data:
                raise ValueError('Session ID already exists')
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            folder = STATE / 'sessions' / uuid.uuid4().hex
            folder.mkdir(parents=True)
            atomic(folder / 'spec.json', {'session_id': session_id, 'port': port, 'background': background,
                   'addon_root': str(BASE / 'official-addon'), 'log': str(folder / 'blender.log')})
            entry = folder / 'entry.py'
            entry.write_text('import runpy\nrunpy.run_path(' + repr(str(SOURCE / 'session_bootstrap.py')) +
                             ',init_globals={"SPEC_PATH":' + repr(str(folder / 'spec.json')) + '})', encoding='utf-8')
            args = [str(BLENDER), '--factory-startup', '--disable-autoexec', '--threads', '2']
            if background:
                args.append('--background')
            args.extend(['--python', str(entry)])
            pid = launch_detached(args)
            data[session_id] = {'port': port, 'pid': pid, 'owned': True, 'entry': str(entry), 'log': str(folder / 'blender.log')}
            atomic(STATE / 'sessions.json', data)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            try:
                info = session_info(session_id, timeout=1)
                if not background:
                    # First script execution can precede window/GPU initialization.
                    time.sleep(.5)
                    info = session_info(session_id, timeout=5)
                return {'status': 'ok', 'session': info}
            except (OSError, RuntimeError):
                time.sleep(.25)
        return failure('SESSION_START_TIMEOUT', 'Session did not become ready within the startup budget', session_id=session_id, pid=pid, log=str(folder / 'blender.log'))

    @mcp.tool()
    def close_blender_session(session_id: str) -> dict:
        """Close only a clean isolated session created by this overlay; refuses existing user sessions and unsaved edits."""
        global _selected
        info = session_info(session_id)
        if not info.get('owned') or session_id == 'background-default':
            raise ValueError('This session is not an isolated session owned by the overlay')
        if info['dirty']:
            raise ValueError('Save the isolated scene or create/restore a checkpoint before closing unsaved work')
        entry_literal = "'" + info['entry'].replace("'", "''") + "'"
        script = ("$ErrorActionPreference='Stop';$p=Get-CimInstance Win32_Process -Filter \"ProcessId=" + str(info['pid']) +
                  "\";if(-not $p -or -not $p.CommandLine.Contains(" + entry_literal + ")){throw 'Process identity changed'};"
                  "Invoke-CimMethod -InputObject $p -MethodName Terminate | Select-Object ReturnValue | ConvertTo-Json -Compress")
        encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
        done = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',encoded],
                              capture_output=True,text=True,timeout=15,creationflags=subprocess.CREATE_NO_WINDOW)
        if done.returncode or json.loads(done.stdout)['ReturnValue']:
            raise RuntimeError('Could not close owned session: ' + done.stderr)
        with registry_guard():
            items = registry()
            del items[session_id]
            atomic(STATE / 'sessions.json', items)
        if _selected == session_id:
            _selected = 'background-default'
        return {'status':'ok','closed_session_id':session_id,'pid':info['pid']}

    @mcp.tool()
    def start_blender_job(code: str, blend_file: str = '', timeout_seconds: int = 3600) -> dict:
        """Start a durable isolated Blender process. Use mcp_progress(value) and mcp_checkpoint() in code."""
        if not 1 <= timeout_seconds <= 86400:
            raise ValueError('Timeout must be between 1 and 86400 seconds')
        if blend_file:
            blend_file = str(Path(blend_file).resolve(strict=True))
        job_id = uuid.uuid4().hex
        folder = STATE / 'jobs' / job_id
        folder.mkdir(parents=True)
        atomic(folder / 'spec.json', {'code': code, 'blend_file': blend_file, 'timeout_seconds': timeout_seconds,
            'binary': str(BLENDER), 'addon_root': str(BASE / 'official-addon'), 'state_dir': str(folder),
            'result_path': str(folder / 'result.json'), 'progress_path': str(folder / 'progress.json')})
        atomic(folder / 'status.json', {'status': 'queued', 'job_id': job_id, 'created': time.time()})
        # The supervisor is standard-library-only. Windows WMI cannot launch some
        # venv redirectors; use the verified base interpreter for this helper.
        supervisor_python = Path(getattr(sys, '_base_executable', sys.executable)).resolve(strict=True)
        pid = launch_detached([str(supervisor_python), str(SOURCE / 'job_worker.py'), str(folder)])
        return {'status': 'ok', 'job_id': job_id, 'worker_pid': pid, 'state_dir': str(folder)}

    @mcp.tool()
    def get_blender_job(job_id: str) -> dict:
        """Read durable job state, result, progress, checkpoints and bounded logs."""
        folder = job_path(job_id)
        value = read(folder / 'status.json')
        for name in ('result', 'progress', 'checkpoint'):
            if (folder / (name + '.json')).exists():
                value[name] = read(folder / (name + '.json'))
        for name in ('stdout', 'stderr'):
            file = folder / (name + '.log')
            if file.exists():
                with file.open('rb') as stream:
                    stream.seek(max(0, file.stat().st_size - 8192))
                    value[name + '_tail'] = stream.read().decode('utf-8', errors='replace')
        return {'status': 'ok', 'job': value}

    @mcp.tool()
    def list_blender_jobs() -> dict:
        """List persisted job states without loading full results."""
        return {'status': 'ok', 'jobs': [read(p) for p in sorted((STATE / 'jobs').glob('*/status.json'))]}

    @mcp.tool()
    def cancel_blender_job(job_id: str) -> dict:
        """Cancel only this job's isolated child, preserving its logs/checkpoints."""
        folder = job_path(job_id)
        value = read(folder / 'status.json')
        if value['status'] in ('succeeded', 'failed', 'cancelled', 'timed_out'):
            return {'status': 'ok', 'job': value, 'cancel_requested': False}
        atomic(folder / 'cancel.json', {'requested': time.time()})
        return {'status': 'ok', 'job_id': job_id, 'cancel_requested': True}

    @mcp.tool()
    def restart_blender_job(job_id: str, use_checkpoint: bool = True) -> dict:
        """Start a new job from the latest explicit scene checkpoint, or original input; code restarts from its beginning."""
        folder = job_path(job_id)
        state = read(folder / 'status.json')
        if state['status'] not in ('succeeded', 'failed', 'cancelled', 'timed_out'):
            raise ValueError('Job must be terminal before restart')
        spec = read(folder / 'spec.json')
        source = spec['blend_file']
        if use_checkpoint:
            if not (folder / 'checkpoint.json').exists():
                raise ValueError('No explicit checkpoint is available')
            source = read(folder / 'checkpoint.json')['path']
        value = start_blender_job(spec['code'], source, spec['timeout_seconds'])
        value['restarted_from_job'] = job_id
        value['input_checkpoint'] = source
        return value

    @mcp.tool()
    def execute_blender_transaction(blend_file: str, code: str, output_path: str, checks_code: str = '') -> dict:
        """Edit an isolated copy; publish a NEW .blend only after code and assertions succeed. External effects are not rolled back."""
        source = Path(blend_file).resolve(strict=True)
        output = Path(output_path).resolve()
        if output.suffix.lower() != '.blend' or output.exists() or source == output:
            raise ValueError('Output must be a new .blend path, distinct from the input')
        output.parent.mkdir(parents=True, exist_ok=True)
        stage = output.with_name('.' + output.stem + '-' + uuid.uuid4().hex + '.blend')
        wrapped = code + '\n' + checks_code + '\nimport bpy\nbpy.ops.wm.save_as_mainfile(filepath=' + repr(str(stage)) + ',copy=True)\n'
        value = run_cli(str(source), wrapped)
        if value.get('status') == 'ok' and stage.is_file() and stage.stat().st_size > 0:
            # Hard-link publication is atomic and refuses an existing destination.
            os.link(stage, output)
            stage.unlink()
            return {'status': 'ok', 'output_path': str(output), 'bytes': output.stat().st_size, 'result': value['result'], 'execution': value['execution']}
        return failure('TRANSACTION_ABORTED', 'No output was published; the input scene was not modified by the transaction wrapper', original=value, staged_file=str(stage), external_effects_rolled_back=False)

    @mcp.tool()
    def create_scene_checkpoint() -> dict:
        """Save a copy of selected scene data. Does not change its current filepath."""
        checkpoint_id = uuid.uuid4().hex
        path = STATE / 'checkpoints' / (checkpoint_id + '.blend')
        path.parent.mkdir(parents=True, exist_ok=True)
        value = rpc('import bpy\noriginal=bpy.data.filepath\nbpy.ops.wm.save_as_mainfile(filepath=' + repr(str(path)) + ',copy=True)\nresult={"original_filepath":original,"checkpoint_path":' + repr(str(path)) + '}')
        if value.get('status') != 'ok':
            return value
        atomic(path.with_suffix('.json'), {'session': session_info(_selected), **value['result']})
        return {'status': 'ok', 'checkpoint_id': checkpoint_id, **value['result']}

    @mcp.tool()
    def restore_scene_checkpoint(checkpoint_id: str) -> dict:
        """Restore scene data from a checkpoint; current filepath becomes the checkpoint. Saves a pre-restore copy first."""
        if len(checkpoint_id) != 32 or any(c not in '0123456789abcdef' for c in checkpoint_id):
            raise ValueError('Invalid checkpoint ID')
        path = STATE / 'checkpoints' / (checkpoint_id + '.blend')
        meta = read(path.with_suffix('.json'))
        current = session_info(_selected)
        if meta['session']['pid'] != current['pid']:
            raise ValueError('Checkpoint belongs to a different Blender session')
        backup = create_scene_checkpoint()
        if backup.get('status') != 'ok':
            return backup
        value = rpc('import bpy\nbpy.ops.wm.open_mainfile(filepath=' + repr(str(path)) + ',load_ui=False,use_scripts=False)\nresult={"filepath":bpy.data.filepath,"objects":len(bpy.data.objects)}')
        value['pre_restore_checkpoint_id'] = backup['checkpoint_id']
        value['original_filepath'] = meta['original_filepath']
        return value

    @mcp.tool()
    def run_blender_operator(identifier: str, properties: dict | None = None, object_name: str = '', mode: str = '', area_type: str = '') -> dict:
        """Run one operator with validated context; restore selection/active/mode. Use copy transactions for data rollback."""
        if len(identifier.split('.')) != 2 or not all(p.isidentifier() for p in identifier.split('.')):
            raise ValueError('Operator must use module.name syntax')
        options = {'identifier': identifier, 'properties': properties or {}, 'object_name': object_name, 'mode': mode, 'area_type': area_type}
        script = (SOURCE / 'context_operator.py').read_text(encoding='utf-8')
        return rpc('OPTIONS=' + repr(options) + '\n' + script)


def build_server():
    patch_upstream()
    import yaml
    instructions = yaml.safe_load((BUNDLE / 'blmcp/data/prompts.yml').read_text(encoding='utf-8'))['initial_instructions']
    from agent_knowledge import STARTUP_NOTE, register as register_knowledge
    instructions = str(instructions) + STARTUP_NOTE
    mcp = HardenedMCP('blender-mcp', instructions=str(instructions) + '\nUse get_blender_capabilities before UI work. Use durable jobs for long work and copy transactions for reversible edits. Checkpoints do not roll back external effects.')
    import blmcp.tools as tools_pkg
    for _, name, _ in pkgutil.iter_modules(tools_pkg.__path__):
        if name.endswith('_toolcode') or name.startswith('_template_'):
            continue
        if name in ('render_thumbnail_to_path','render_viewport_to_path'):
            continue
        mod = importlib.import_module('blmcp.tools.' + name)
        if hasattr(mod, 'register'):
            mod.register(mcp)
    register_extra(mcp)
    register_knowledge(mcp)
    from asset_preservation import register as register_preservation
    register_preservation(mcp, state_dir=STATE)
    from retopology_tools import register as register_retopology
    register_retopology(mcp, rpc=rpc, session_info=session_info, state_dir=STATE)
    return mcp


if __name__ == '__main__':
    build_server().run(transport='stdio')

