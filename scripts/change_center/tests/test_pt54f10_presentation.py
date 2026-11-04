"""PT54-F10: source-controlled TEST presentation labels and HTTP access."""
from __future__ import annotations

import copy
import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pt54f9_core import Invalid
from pt54f9_server import ChangeServer
from pt54f10_settings import DEFAULTS, RELATIVE, read, save


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo'
        p = self.repo / RELATIVE
        p.parent.mkdir(parents=True)
        self.original = {'schema_version': 1, 'revision': 0, 'labels': DEFAULTS.copy()}
        p.write_text(json.dumps(self.original), encoding='utf-8')
        self.backups = Path(self.temp.name) / 'asset-library' / 'presentation-backups'

    def test_roundtrip_backup_and_revision(self):
        self.assertEqual(read(self.repo), self.original)
        next_values = DEFAULTS | {'overview_heading': 'About this system'}
        result = save(self.repo, self.backups, {'expected_revision': 0, 'labels': next_values})
        self.assertEqual(result['document']['revision'], 1)
        self.assertEqual(result['changed'], ['overview_heading'])
        self.assertEqual(json.loads(Path(result['backup']).read_text()), self.original)
        self.assertEqual(read(self.repo)['labels']['overview_heading'], 'About this system')
        with self.assertRaisesRegex(Invalid, 'Refresh'):
            save(self.repo, self.backups, {'expected_revision': 0, 'labels': DEFAULTS})

    def test_reject_unsafe_labels_and_unexpected_fields(self):
        for invalid in ('', ' ', '<script>alert(1)</script>', 'a'*81, 'line\nreturn', '\x00'):
            labels = DEFAULTS | {'fitting_type_label': invalid}
            with self.subTest(invalid=repr(invalid)), self.assertRaises(Invalid):
                save(self.repo, self.backups, {'expected_revision': 0, 'labels': labels})
        labels=DEFAULTS | {'price':'$1'}
        with self.assertRaises(Invalid):save(self.repo, self.backups, {'expected_revision':0,'labels':labels})
        with self.assertRaisesRegex(Invalid, 'No changes'):
            save(self.repo, self.backups, {'expected_revision':0,'labels':DEFAULTS})
        self.assertEqual(len(list(self.backups.glob('*'))) if self.backups.exists() else 0, 0)

    def test_reject_symlinked_config(self):
        target=self.repo / RELATIVE
        target.unlink()
        other=self.repo/'other.json'
        other.write_text('{}')
        target.symlink_to(other)
        with self.assertRaisesRegex(Invalid, 'symlink'):
            read(self.repo)

    def test_http_save_and_no_cross_origin(self):
        server=ChangeServer(('127.0.0.1',0),Path(self.temp.name)/'changes',repo=self.repo)
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        self.addCleanup(server.server_close)
        self.addCleanup(lambda:(server.shutdown(),worker.join(3)))
        port=server.server_port
        def send(method,path,payload=None,headers=None):
            c=http.client.HTTPConnection('127.0.0.1',port,timeout=3)
            raw=None if payload is None else json.dumps(payload).encode()
            h={'Host':f'127.0.0.1:{port}',**(headers or {})}
            c.request(method,path,body=raw,headers=h)
            r=c.getresponse();b=json.loads(r.read());status=r.status;c.close();return status,b
        status,state=send('GET','/api/presentation')
        self.assertEqual(status,200)
        self.assertEqual(len(state['specs']),len(DEFAULTS))
        self.assertEqual(state['document'],self.original)
        payload={'expected_revision':0,'labels':DEFAULTS | {'tank_size_label':'TANK CAPACITY'}}
        self.assertEqual(send('POST','/api/presentation/save',payload)[0],403)
        headers={'Origin':f'http://127.0.0.1:{port}','X-PT54-CSRF':server.csrf,
                 'Content-Type':'application/json'}
        self.assertEqual(send('POST','/api/presentation/save',payload,headers)[0],200)
        self.assertEqual(read(self.repo)['labels']['tank_size_label'],'TANK CAPACITY')
        self.assertEqual(send('POST','/api/presentation/save',payload,headers)[0],400)
