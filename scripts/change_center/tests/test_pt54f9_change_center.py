"""Tests for TEST-only request register, approvals, persistence, and HTTP boundary."""
from __future__ import annotations

import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pt54f9_core import Invalid, create, edit, export_approved, fresh, load, transition, write
from pt54f9_server import ChangeServer


INPUT = {'title': 'Fix gallery caption', 'category': 'caption', 'family': 'refine',
         'reference': 'Refine 1.5 · gallery 2', 'before': 'Treatment tank',
         'after': 'Refine tank', 'notes': 'Client prefers more specific language',
         'acceptance': 'Caption displayed on selected TEST gallery'}


class CoreTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'change-center'

    def test_empty_and_create(self):
        self.assertEqual(load(self.root), fresh())
        doc = fresh()
        first = create(doc, INPUT)
        self.assertEqual(first['id'], 'CR-00001')
        self.assertEqual(first['status'], 'draft')
        self.assertEqual(doc['revision'], 1)
        write(self.root, doc)
        self.assertEqual(load(self.root), doc)
        self.assertEqual(create(doc, dict(INPUT, title='Second'))['id'], 'CR-00002')

    def test_edit_approval_reopen_and_backups(self):
        doc=fresh()
        row=create(doc, INPUT)
        write(self.root, doc)
        newer=edit(doc, dict(INPUT, id=row['id'], expected_version=1, after='Corrected label'))
        self.assertEqual(newer['version'], 2)
        write(self.root, doc)
        self.assertEqual(len(list((self.root / 'backups').glob('*.json'))), 1)
        transition(doc, {'id':row['id'], 'expected_version':2, 'status':'in_review'})
        with self.assertRaisesRegex(Invalid, 'typing APPROVE'):
            transition(doc, {'id':row['id'], 'expected_version':3, 'status':'approved',
                             'reviewer':'Reviewer', 'confirmation':'YES'})
        approved=transition(doc, {'id':row['id'], 'expected_version':3, 'status':'approved',
                                  'reviewer':'Reviewer', 'confirmation':'APPROVE CR-00001'})
        self.assertEqual(approved['status'], 'approved')
        with self.assertRaisesRegex(Invalid, 'Reopen'):
            edit(doc, dict(INPUT,id=row['id'],expected_version=4))
        receipt=export_approved(self.root,doc)
        self.assertEqual(receipt['count'],1)
        self.assertIn('approved_requests',Path(receipt['file']).read_text())
        transition(doc, {'id':row['id'], 'expected_version':4, 'status':'in_review'})
        self.assertIsNone(row['approved_utc'])
        with self.assertRaisesRegex(Invalid, 'No approved'):
            export_approved(self.root,doc)

    def test_reject_bad_values_stale_edits_and_transitions(self):
        doc=fresh()
        row=create(doc, INPUT)
        for bad in ({**INPUT,'family':'unknown'}, {**INPUT, 'title':'x'*121},
                    {**INPUT, 'title':''}, {**INPUT,'category':'shell'}):
            with self.assertRaises(Invalid): create(doc,bad)
        with self.assertRaisesRegex(Invalid, 'Invalid transition'):
            transition(doc,{'id':row['id'],'expected_version':1,'status':'approved'})
        with self.assertRaisesRegex(Invalid, 'Refresh'):
            edit(doc,{**INPUT,'id':row['id'],'expected_version':0})

    def test_symlink_rejected(self):
        bad=Path(self.tmp.name)/'link'
        bad.symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(Invalid, 'Symlinked'):
            load(bad)

    def test_symlinked_parent_rejected(self):
        other = Path(self.tmp.name) / 'actual-parent'
        other.mkdir()
        alias = Path(self.tmp.name) / 'link-parent'
        alias.symlink_to(other, target_is_directory=True)
        with self.assertRaisesRegex(Invalid, 'Symlinked'):
            load(alias / 'changes')

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS system alias regression')
    def test_macos_var_folders_allowed_but_user_symlinks_rejected(self):
        # macOS maps /var to /private/var; tempfile commonly uses /var/folders.
        self.assertEqual(Path('/var').resolve(), Path('/private/var'))
        self.assertEqual(load(self.root), fresh())
        other = Path(self.tmp.name) / 'normal-dir'
        other.mkdir()
        alias = Path(self.tmp.name) / 'user-symlink'
        alias.symlink_to(other, target_is_directory=True)
        with self.assertRaisesRegex(Invalid, 'Symlinked'):
            load(alias / 'changes')


class HTTPTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.server=ChangeServer(('127.0.0.1',0), Path(self.tmp.name)/'changes')
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)
        self.port=self.server.server_port

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def request(self,method,path,payload=None,csrf=True,host=True,origin=True):
        c=http.client.HTTPConnection('127.0.0.1',self.port,timeout=3)
        headers={'Host':f'127.0.0.1:{self.port}' if host else 'evil.example'}
        body=None
        if method=='POST':
            body=json.dumps(payload or {}).encode()
            headers.update({'Content-Type':'application/json',
                            'Origin':f'http://127.0.0.1:{self.port}' if origin else 'https://evil.example',
                            'X-PT54-CSRF':self.server.csrf if csrf else 'wrong'})
        c.request(method,path,body=body,headers=headers)
        r=c.getresponse()
        data=r.read()
        out=(r.status,json.loads(data) if r.getheader('Content-Type','').startswith('application/json') else data)
        c.close()
        return out

    def test_browser_flow(self):
        code, page=self.request('GET','/')
        self.assertEqual(code,200)
        self.assertIn(b'Client Change Center',page)
        code, state=self.request('GET','/api/state')
        self.assertEqual((code,state['register']['requests']),(200,[]))
        code, result=self.request('POST','/api/create',INPUT)
        self.assertEqual(code,200)
        rid=result['request']['id']
        code, result=self.request('POST','/api/status',{'id':rid,'expected_version':1,'status':'in_review'})
        self.assertEqual(code,200)
        code, result=self.request('POST','/api/status',{'id':rid,'expected_version':2,'status':'approved',
                                             'reviewer':'Client', 'confirmation':'APPROVE '+rid})
        self.assertEqual(code,200)
        code, export=self.request('POST','/api/export',{})
        self.assertEqual(code,200)
        self.assertEqual(export['export']['count'],1)
        self.assertTrue(Path(export['export']['file']).exists())
        code, state=self.request('GET','/api/state')
        self.assertEqual(state['register']['requests'][0]['status'],'approved')

    def test_http_security(self):
        self.assertEqual(self.request('POST','/api/create',INPUT,csrf=False)[0],403)
        self.assertEqual(self.request('POST','/api/create',INPUT,origin=False)[0],403)
        self.assertEqual(self.request('GET','/api/state',host=False)[0],403)
        self.assertEqual(self.request('GET','/../secret')[0],404)
        self.assertEqual(self.request('POST','/api/edit',INPUT)[0],400)
        self.assertEqual(self.request('POST','/api/create',dict(INPUT,title='<img src=x>'))[0],200)
        self.assertEqual(self.request('GET','/api/state')[0],200)


if __name__ == '__main__':
    unittest.main()
