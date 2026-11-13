#!/usr/bin/env python3
"""Data Transfer Guard: read-only, exact CSV update verification (stdlib only)."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import sys

VERSION = '0.1.0'


class Invalid(Exception):
    def __init__(self, code, **location):
        self.code, self.location = code, location


def digest(data):
    return hashlib.sha256(data).hexdigest()


def unique_object(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise Invalid('DUPLICATE_POLICY_FIELD')
        result[k] = v
    return result


def load_policy(raw):
    try:
        p = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object,
                       parse_constant=lambda _: (_ for _ in ()).throw(Invalid('INVALID_POLICY')))
    except (ValueError, UnicodeError, RecursionError):
        raise Invalid('INVALID_POLICY') from None
    fields = {'schema_version', 'key_column', 'allowed_update_columns',
              'allow_added_rows', 'allow_removed_rows'}
    if type(p) is not dict or set(p) != fields:
        raise Invalid('INVALID_POLICY_FIELDS')
    if p['schema_version'] != 'dtg-policy-v1':
        raise Invalid('INVALID_POLICY_VERSION')
    key, allowed = p['key_column'], p['allowed_update_columns']
    if type(key) is not str or not key.strip():
        raise Invalid('INVALID_KEY_COLUMN')
    if (type(allowed) is not list or any(type(c) is not str or not c.strip() for c in allowed)
            or len(set(allowed)) != len(allowed) or key in allowed):
        raise Invalid('INVALID_ALLOWED_COLUMNS')
    if any(type(p[k]) is not bool for k in ('allow_added_rows', 'allow_removed_rows')):
        raise Invalid('INVALID_ROW_POLICY')
    return p


def validate_quotes(text):
    """Reject permissive csv.reader cases: quote inside bare field, junk after quote."""
    state = 'start'
    for ch in text:
        if state == 'quoted':
            if ch == '"':
                state = 'closed'
        elif state == 'closed':
            if ch == '"':
                state = 'quoted'
            elif ch == ',':
                state = 'start'
            elif ch in '\r\n':
                state = 'start'
            else:
                raise Invalid('CSV_PARSE_ERROR')
        elif state == 'start':
            if ch == '"':
                state = 'quoted'
            elif ch not in ',\r\n':
                state = 'bare'
        elif ch == '"':
            raise Invalid('CSV_PARSE_ERROR')
        elif ch in ',\r\n':
            state = 'start'
    if state == 'quoted':
        raise Invalid('CSV_PARSE_ERROR')


def load_csv(raw, policy):
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeError:
        raise Invalid('INVALID_UTF8') from None
    if '\x00' in text:
        raise Invalid('NUL_BYTE')
    validate_quotes(text)
    try:
        rows = list(csv.reader(io.StringIO(text, newline=''), strict=True))
    except (csv.Error, ValueError):
        raise Invalid('CSV_PARSE_ERROR') from None
    if not rows:
        raise Invalid('MISSING_HEADER')
    header = rows[0]
    if not header or any(not c.strip() for c in header):
        raise Invalid('EMPTY_HEADER')
    if len(set(header)) != len(header):
        raise Invalid('DUPLICATE_HEADER')
    if policy['key_column'] not in header:
        raise Invalid('MISSING_KEY_COLUMN')
    for col in policy['allowed_update_columns']:
        if col not in header:
            raise Invalid('UNKNOWN_ALLOWED_COLUMN', column=col)
    indexed = {}
    for line, row in enumerate(rows[1:], 2):
        if len(row) != len(header):
            raise Invalid('COLUMN_COUNT_MISMATCH', record=line)
        data = dict(zip(header, row))
        key = data[policy['key_column']]
        if not key.strip():
            raise Invalid('EMPTY_KEY', record=line)
        if key in indexed:
            raise Invalid('DUPLICATE_KEY', record=line, first_record=indexed[key][0])
        indexed[key] = (line, data)
    return header, indexed


def verify(before, after, policy_path, *, show_keys=False):
    report = {'schema_version': 'dtg-report-v1', 'tool_version': VERSION,
              'status': 'INVALID_INPUT', 'exit_code': 2, 'inspection_complete': False,
              'row_counts': {'before': None, 'after': None}, 'matched_rows': None,
              'detection_count': 0, 'counts_by_code': {}, 'violations': [],
              'sha256': {'before': None, 'after': None, 'policy': None},
              'key_display': 'plain' if show_keys else 'suppressed',
              'environment': {'python': platform.python_version(), 'platform': platform.platform()}}
    def add(code, **location):
        report['violations'].append({'code': code, **location})
    blobs = {}
    for name, path in [('before', before), ('after', after), ('policy', policy_path)]:
        try:
            blobs[name] = Path(path).read_bytes()
            report['sha256'][name] = digest(blobs[name])
        except OSError:
            add('READ_ERROR', input=name)
    p = None
    if 'policy' in blobs:
        try:
            p = load_policy(blobs['policy'])
        except Invalid as exc:
            add(exc.code, input='policy', **exc.location)
    parsed = {}
    if p is not None:
        for name in ('before', 'after'):
            if name not in blobs:
                continue
            try:
                parsed[name] = load_csv(blobs[name], p)
                report['row_counts'][name] = len(parsed[name][1])
            except Invalid as exc:
                add(exc.code, input=name, **exc.location)
    if not report['violations'] and len(parsed) == 2:
        bh, b = parsed['before']; ah, a = parsed['after']
        report['matched_rows'] = len(b.keys() & a.keys())
        if set(bh) != set(ah):
            add('SCHEMA_MISMATCH')
        else:
            if not p['allow_removed_rows']:
                for key in sorted(b.keys() - a.keys()):
                    add('MISSING_ROW', key=key if show_keys else None, record=b[key][0], input='before')
            if not p['allow_added_rows']:
                for key in sorted(a.keys() - b.keys()):
                    add('UNEXPECTED_ROW', key=key if show_keys else None, record=a[key][0], input='after')
            for key in sorted(b.keys() & a.keys()):
                for col in bh:
                    if col not in p['allowed_update_columns'] and b[key][1][col] != a[key][1][col]:
                        add('UNAUTHORIZED_CHANGE', column=col, key=key if show_keys else None,
                            before_record=b[key][0], after_record=a[key][0])
        report['inspection_complete'] = True
        report['status'] = 'FAIL' if report['violations'] else 'PASS'
        report['exit_code'] = 1 if report['violations'] else 0
    report['detection_count'] = len(report['violations'])
    report['counts_by_code'] = dict(sorted(Counter(v['code'] for v in report['violations']).items()))
    return report


def emit_error(code):
    # If a report destination is unsafe/unavailable, JSON goes to stderr only.
    report = {'schema_version': 'dtg-report-v1', 'tool_version': VERSION,
              'status': 'INVALID_INPUT', 'exit_code': 2, 'inspection_complete': False,
              'row_counts': {'before': None, 'after': None}, 'matched_rows': None,
              'detection_count': 1, 'counts_by_code': {code: 1},
              'violations': [{'code': code}],
              'sha256': {'before': None, 'after': None, 'policy': None},
              'key_display': 'suppressed',
              'environment': {'python': platform.python_version(), 'platform': platform.platform()}}
    print(json.dumps(report, ensure_ascii=True), file=sys.stderr)
    return 2


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    v = sub.add_parser('verify')
    for name in ('before', 'after', 'policy', 'out'):
        v.add_argument('--' + name, required=True, type=Path)
    v.add_argument('--show-keys', action='store_true', help='Include raw IDs (may be personal data)')
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        if exc.code:
            return emit_error('INVALID_ARGUMENTS')
        return 0
    inputs = [args.before, args.after, args.policy]
    try:
        if any(args.out.resolve() == p.resolve() for p in inputs):
            return emit_error('OUTPUT_IS_INPUT')
        # Exclusive creation rejects existing files, symlinks and hardlink aliases.
        fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except (OSError, ValueError, RuntimeError):
        return emit_error('OUTPUT_UNAVAILABLE')
    try:
        report = verify(args.before, args.after, args.policy, show_keys=args.show_keys)
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            fd = None
            json.dump(report, f, ensure_ascii=True, indent=2)
            f.write('\n')
        return report['exit_code']
    except (OSError, ValueError, RecursionError):
        return emit_error('INSPECTION_OR_REPORT_ERROR')
    finally:
        if fd is not None:
            os.close(fd)


if __name__ == '__main__':
    raise SystemExit(main())
