"""Version diagnostics never execute plasmashell or activate a bus service."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest import mock

import test_controller as fixtures

theme = fixtures.theme
PACKAGE = '/nix/store/' + 'a' * 32 + '-plasma-workspace-6.6.6'


class RuntimeVersionTests(unittest.TestCase):
    def setUp(self):
        self.runner = mock.Mock(return_value=types.SimpleNamespace(stdout='123\n'))
        self.backend = theme.Backend({'DBUS_SESSION_BUS_ADDRESS': 'unix:path=/test-only-bus'}, self.runner)

    def probe(self, executable=PACKAGE + '/bin/.plasmashell-wrapped', uid=None):
        with mock.patch.object(Path, 'stat', return_value=types.SimpleNamespace(st_uid=os.getuid() if uid is None else uid)), \
                mock.patch.object(os, 'readlink', return_value=executable):
            return self.backend.running_plasma()

    def test_running_process_wins_over_path_without_executing_binary(self):
        self.backend.env['PATH'] = '/different-generation/bin'
        self.assertEqual(self.probe()['version'], '6.6.6')
        self.runner.assert_called_once()
        command = self.runner.call_args.args[0]
        self.assertEqual(command[1], 'org.freedesktop.DBus')
        self.assertEqual(command[-2:], ['org.freedesktop.DBus.GetConnectionUnixProcessID', 'org.kde.plasmashell'])
        self.assertEqual(self.runner.call_args.kwargs['timeout'], 2)
        self.assertNotIn('--version', command)

    def test_offline_does_not_call_any_tool(self):
        self.backend.env.clear()
        self.assertIsNone(self.probe()['version'])
        self.runner.assert_not_called()

    def test_missing_tool_service_or_timeout_is_unknown(self):
        for error in (FileNotFoundError(), subprocess.TimeoutExpired('qdbus', 2),
                      subprocess.CalledProcessError(1, 'qdbus')):
            with self.subTest(error=type(error).__name__):
                self.runner.side_effect = error
                self.assertIsNone(self.probe()['version'])

    def test_bad_pid_foreign_owner_non_nix_and_deleted_process_are_unknown(self):
        for pid in ('', '0', '-1', '123 extra', '../../123'):
            with self.subTest(pid=pid):
                self.runner.return_value.stdout = pid
                self.assertIsNone(self.probe()['version'])
        self.runner.return_value.stdout = '123'
        self.assertIsNone(self.probe(uid=os.getuid() + 1)['version'])
        for executable in ('/usr/bin/plasmashell', PACKAGE + '/bin/plasmashell (deleted)',
                           PACKAGE + '/bin/other'):
            self.assertIsNone(self.probe(executable)['version'])
        with mock.patch.object(Path, 'stat', side_effect=FileNotFoundError()):
            self.assertIsNone(self.backend.running_plasma()['version'])


class ResourceVersionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.controller = theme.Controller(self.root / 'share', {'HOME': str(self.root), 'PATH': '/missing'})
        self.manifest = self.root / 'share/doc/kaltsit-theme/lockscreen-rendering.json'

    def put(self, value):
        self.manifest.parent.mkdir(parents=True, exist_ok=True)
        self.manifest.write_text(value)

    def test_missing_old_malformed_and_partial_metadata_remain_unknown(self):
        for data in (None, '{}', '{broken', 'null', '[]',
                     '{"plasma_desktop_version":"6.6.6"}',
                     '{"plasma_desktop_version":666,"plasma_workspace_version":{}}'):
            with self.subTest(data=data):
                if data is not None:
                    self.put(data)
                with mock.patch.object(self.controller.backend, 'running_plasma', return_value={'version': '6.6.6'}):
                    self.assertEqual(self.controller.status()['lockscreen_resources']['match'], 'unknown')
        self.assertFalse(self.controller.state_dir.exists())

    def test_match_mismatch_and_no_session_have_no_filesystem_effects(self):
        self.put(json.dumps({'plasma_desktop_version': '6.6.6', 'plasma_workspace_version': '6.6.6'}))
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        for running, expected in (('6.6.6', True), ('6.7.0', False), (None, 'unknown')):
            with mock.patch.object(self.controller.backend, 'running_plasma', return_value={'version': running}):
                result = self.controller.status()['lockscreen_resources']
                self.assertEqual(result['match'], expected)
                self.assertEqual('hint' in result, expected is False)
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)
        self.assertFalse(self.controller.state_dir.exists())

    def test_both_package_versions_must_match(self):
        self.put(json.dumps({'plasma_desktop_version': '6.7.0', 'plasma_workspace_version': '6.6.6'}))
        with mock.patch.object(self.controller.backend, 'running_plasma', return_value={'version': '6.6.6'}):
            self.assertIs(self.controller.status()['lockscreen_resources']['match'], False)
