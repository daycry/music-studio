"""Fault injection owned by the eight native custody negative tests only.

No kernel errno is claimed. Receipts copy the supervisor's live state only;
process identities, signals, waits and release authorization stay native.
"""
import errno
import inspect
import json
import os
import runpy
import selectors
import sys
import time
from pathlib import Path

KEYS = {
    'CUSTODY_TEST_JOURNAL_ERRNO': ('journal', {'ENOSPC', 'EIO'}),
    'CUSTODY_TEST_GRACE_ENFILE': ('grace', {'create', 'register', 'select', 'close'}),
    'CUSTODY_TEST_FINAL_NOTIFY_ERROR': ('notify', {'ValueError'}),
    'CUSTODY_TEST_FINAL_GROUP_QUERY_ERROR': ('query', {'EIO'}),
}


def invocation(argv, environment):
    """Translate an exact fixture supervisor invocation, never arbitrary Python."""
    argv = list(argv)
    selected = [(k, environment[k]) for k in KEYS if k in environment]
    if len(selected) != 1 or len(argv) != 9 or argv[1] != '-B':
        raise ValueError('Exactly one native supervisor fault required')
    source = Path(argv[2]).resolve(strict=True)
    if source.name != 'custody_linux_supervisor.py' or argv[5] != 'silent':
        # argv: python -B supervisor live control mode root execution epoch
        raise ValueError('Fault bootstrap only supports the silent test supervisor')
    key, value = selected[0]
    kind, values = KEYS[key]
    if value not in values:
        raise ValueError('Unsupported injected fault')
    clean = {k: v for k, v in environment.items() if not k.startswith('CUSTODY_TEST_')}
    return [argv[0], '-B', str(Path(__file__).resolve()), str(source), kind, value] + argv[3:], clean


def launch():
    if len(sys.argv) != 10:
        raise ValueError('Explicit native fault bootstrap invocation required')
    source, kind, stage = sys.argv[1:4]
    source = str(Path(source).resolve(strict=True))
    if Path(source).name != 'custody_linux_supervisor.py' or sys.argv[6] != 'silent':
        raise ValueError('Invalid native test supervisor')
    if (kind, stage) not in {(k, v) for k, values in KEYS.values() for v in values}:
        raise ValueError('Invalid injected fault configuration')
    if any(k.startswith('CUSTODY_TEST_') for k in os.environ):
        raise ValueError('Fault selectors must not escape into workload environment')
    owner = os.getpid()
    root = Path(sys.argv[7])
    actual_dumps, actual_write = json.dumps, Path.write_text
    actual_getpgid, actual_selector = os.getpgid, selectors.DefaultSelector
    injected = False

    def frame(name):
        if os.getpid() != owner:
            return None
        current = inspect.currentframe().f_back
        while current:
            if current.f_code.co_filename == source and current.f_code.co_name == name:
                return current
            current = current.f_back
        return None

    def snapshot(record):
        # Serialization round-trip copies only observed live supervisor fields.
        return json.loads(actual_dumps(record))

    def receipt(name, values):
        actual_write(root / name, actual_dumps(dict(
            values, injected=True, injection_source='test_owned_stdlib_wrapper',
            supervisor_pid=owner, kernel_errno_claimed=False,
        )))

    def write_text(path, data, *args, **kwargs):
        nonlocal injected
        caller = frame('journal')
        if kind == 'journal' and caller and path == root / 'supervisor-journal.tmp':
            record = caller.f_locals['record']
            if record['registered']:
                if not injected:
                    injected = True
                    receipt('journal-fault-before.json', {'record': snapshot(record), 'errno': getattr(errno, stage)})
                    end = time.monotonic() + 6
                    while not (root / 'release-journal-fault').exists():
                        if time.monotonic() >= end:
                            raise TimeoutError('Native journal fault barrier not released')
                        time.sleep(0.001)
                raise OSError(getattr(errno, stage), 'Injected journal fault')
        return actual_write(path, data, *args, **kwargs)

    def dumps(value, *args, **kwargs):
        nonlocal injected
        if kind == 'notify' and frame('notify') and value.get('kind') == 'final':
            injected = True
            receipt('notify-fault.json', {'record': snapshot(value), 'error_type': 'ValueError'})
            raise ValueError('Injected final metadata serialization fault')
        return actual_dumps(value, *args, **kwargs)

    def getpgid(pid):
        nonlocal injected
        caller = frame('main')
        if kind == 'query' and caller and 'retained' in caller.f_locals:
            record = caller.f_locals['record']
            if not injected:
                injected = True
                receipt('group-query-fault.json', {'record': snapshot(record), 'retained_before_query': caller.f_locals['retained'], 'errno': errno.EIO})
            raise OSError(errno.EIO, 'Injected final group query fault')
        return actual_getpgid(pid)

    def grace_fault(selected):
        nonlocal injected
        caller = frame('cleanup_pause')
        if kind != 'grace' or stage != selected or injected or not caller:
            return
        record = caller.f_locals['record']
        if not record.get('term_sent') or record.get('kill_sent'):
            return
        injected = True
        receipt('grace-fault.json', {'stage': selected, 'errno': errno.ENFILE, 'actual_term_returned': record['term_sent'], 'record': snapshot(record)})
        raise OSError(errno.ENFILE, 'Injected grace selector fault')

    class FaultSelector(actual_selector):
        def __init__(self, *args, **kwargs):
            grace_fault('create')
            super().__init__(*args, **kwargs)

        def register(self, *args, **kwargs):
            grace_fault('register')
            return super().register(*args, **kwargs)

        def select(self, *args, **kwargs):
            grace_fault('select')
            return super().select(*args, **kwargs)

        def close(self):
            # Release the real selector FD even when its secondary close fails.
            result = super().close()
            grace_fault('close')
            return result

    Path.write_text, json.dumps = write_text, dumps
    os.getpgid, selectors.DefaultSelector = getpgid, FaultSelector
    sys.argv = [source] + sys.argv[4:]
    try:
        runpy.run_path(source, run_name='__main__')
    finally:
        Path.write_text, json.dumps = actual_write, actual_dumps
        os.getpgid, selectors.DefaultSelector = actual_getpgid, actual_selector


if __name__ == '__main__':
    launch()
