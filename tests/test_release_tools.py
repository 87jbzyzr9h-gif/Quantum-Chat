import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def mirror_module():
    spec = importlib.util.spec_from_file_location('mirror_helper', ROOT/'scripts/sync_private_mirror.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MirrorSafetyTests(unittest.TestCase):
    def test_credential_free_github_urls_only(self):
        helper = mirror_module()
        for url in ['https://github.com/owner/repository', 'https://github.com/owner/repository.git']:
            self.assertEqual(helper.repository(url), 'owner/repository')
        for bad in ['https://token@github.com/owner/repo', 'https://example.com/owner/repo',
                    'https://github.com/owner/repo?token=secret', 'git@github.com:owner/repo']:
            with self.assertRaises(Exception):
                helper.repository(bad)

    def test_refuses_identical_source_destination_before_network(self):
        helper = mirror_module()
        args = ['sync', '--public', 'https://github.com/a/repo', '--private', 'https://github.com/a/repo']
        with patch('sys.argv', args), patch.object(helper.subprocess, 'check_output') as network:
            with self.assertRaises(SystemExit):
                helper.main()
        network.assert_not_called()

    def test_refuses_public_destination_before_any_git_mutation(self):
        helper = mirror_module()
        with patch('sys.argv', ['sync']), patch.object(helper.subprocess, 'check_output',
                side_effect=[b'{"isPrivate": false}', b'{"isPrivate": false}']), patch.object(helper.subprocess, 'run') as git:
            with self.assertRaises(SystemExit):
                helper.main()
        git.assert_not_called()


if __name__ == '__main__':
    unittest.main()
