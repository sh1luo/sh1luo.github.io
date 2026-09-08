"""Regression checks for publishing failures and recoverable image backups."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import backup_external_images as images


class PublishingTests(unittest.TestCase):
    def run_publish(self, failure):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            git = path / 'git'
            git.write_text('''#!/bin/sh
if [ "$1" = '-c' ]; then shift 2; fi
printf '%s\\n' "$*" >> "$REVIEW_LOG"
case "$1" in
 branch) printf 'master\\n';;
 add) if [ "$FAILURE" = add ]; then exit 1; fi;;
 diff)
   case "$*" in
     *--quiet*) if [ "$FAILURE" = diff ]; then exit 2; else exit 1; fi;;
     *) if [ "$FAILURE" = list ]; then exit 1; fi;;
   esac;;
 commit) if [ "$FAILURE" = commit ]; then exit 1; fi;;
 push) if [ "$FAILURE" = push ]; then exit 1; fi;;
esac
''')
            git.chmod(0o755)
            env = dict(os.environ, PATH=directory + ':' + os.environ['PATH'], REVIEW_LOG=str(path / 'log'), FAILURE=failure)
            result = subprocess.run(['make', '-o', 'check', 'publish', "MESSAGE=writer's update"], cwd=ROOT, env=env, capture_output=True, text=True)
            return result, (path / 'log').read_text().splitlines()

    def test_failures_stop_publish(self):
        for failure in ['add', 'diff', 'list', 'commit']:
            with self.subTest(failure=failure):
                result, calls = self.run_publish(failure)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn('push origin master', calls)

    def test_push_failure_is_reported(self):
        result, _ = self.run_publish('push')
        self.assertNotEqual(result.returncode, 0)

    def test_success_preserves_literal_message(self):
        result, calls = self.run_publish('none')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("commit -m writer's update -- content backups", calls)
        self.assertEqual(calls[-1], 'push origin master')

    def test_failed_new_does_not_announce_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            hugo = Path(directory) / 'hugo'
            hugo.write_text('#!/bin/sh\nexit 1\n')
            hugo.chmod(0o755)
            result = subprocess.run(['make', '-o', 'check-hugo', 'new', f'HUGO={hugo}', 'NAME=example', 'SECTION=go'], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('已创建', result.stdout)


class BackupTests(unittest.TestCase):
    def response(self, data):
        response = io.BytesIO(data)
        response.status = 200
        response.headers = {'Content-Length': str(len(data))}
        return response

    def test_rejects_html_with_success_status(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(images, 'urlopen', return_value=self.response(b'<html>access denied</html>')):
                with self.assertRaisesRegex(ValueError, 'not a recognized image'):
                    images.download('https://example.com/image.png', Path(directory), 1, 0)
            self.assertEqual(list(Path(directory).rglob('*')), [])

    def test_download_verify_corruption_and_offline_restore(self):
        # A complete 1x1 PNG; no external network is used by these tests.
        import base64
        data = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1cAAAAASUVORK5CYII=')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            url = 'https://example.com/image.png'
            with patch.object(images, 'urlopen', return_value=self.response(data)):
                entry = images.download(url, path, 1, 0)
            self.assertEqual(entry['sha256'], hashlib.sha256(data).hexdigest())
            saved = images.verified_file(path, entry)
            self.assertIsNotNone(saved)
            (path / 'manifest.json').write_text(json.dumps({'version': 1, 'images': {url: entry}}))
            command = [sys.executable, str(ROOT / 'scripts/backup_external_images.py'), '--backup-dir', str(path), '--restore', url, '--output', str(path / 'restored.png')]
            restored = subprocess.run(command, capture_output=True)
            self.assertEqual(restored.returncode, 0, restored.stderr)
            self.assertEqual((path / 'restored.png').read_bytes(), data)
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            saved.write_bytes(b'corrupt')
            self.assertIsNone(images.verified_file(path, entry))

    def test_rerun_preserves_existing_copy_when_source_disappears(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            content = path / 'content'
            content.mkdir()
            url = 'https://example.com/image.png'
            (content / 'post.md').write_text(f'![example]({url})')
            saved = path / 'objects' / 'image.png'
            saved.parent.mkdir()
            saved.write_bytes(b'previously backed up image')
            entry = {'file': 'objects/image.png', 'sha256': hashlib.sha256(saved.read_bytes()).hexdigest()}
            manifest = {'version': 1, 'images': {url: entry}}
            with patch.object(images, 'urlopen', side_effect=OSError('offline')) as network:
                self.assertEqual(images.backup(content, path, manifest, 1, 1, 0), 0)
                network.assert_not_called()
            self.assertEqual(images.verified_file(path, entry), saved)

    def test_failed_download_keeps_successful_backups_and_failure_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            content = path / 'content'
            content.mkdir()
            good, bad = 'https://example.com/good.png', 'https://example.com/bad.png'
            (content / 'post.md').write_text(f'![good]({good})\n![bad]({bad})')
            def response(request, **kwargs):
                if request.full_url == bad:
                    raise OSError('source unavailable')
                return self.response(b'GIF89a' + bytes(20))
            manifest = {'version': 1, 'images': {}}
            with patch.object(images, 'urlopen', side_effect=response):
                self.assertEqual(images.backup(content, path, manifest, 1, 1, 0), 1)
            saved = json.loads((path / 'manifest.json').read_text())['images']
            self.assertIsNotNone(images.verified_file(path, saved[good]))
            self.assertIn('source unavailable', saved[bad]['lastError'])

    def test_verify_detects_new_unbacked_article_images(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            content = path / 'content'
            content.mkdir()
            (content / 'post.md').write_text('![new](https://example.com/new.png)')
            (path / 'manifest.json').write_text(json.dumps({'version': 1, 'images': {}}))
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/backup_external_images.py'), str(content), '--backup-dir', str(path), '--verify'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('https://example.com/new.png', result.stderr)


if __name__ == '__main__':
    unittest.main()
