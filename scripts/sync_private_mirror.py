"""Mirror public project branches/tags to a verified private GitHub repository."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess


def repository(value):
    match = re.fullmatch(r'https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?', value)
    if not match:
        raise argparse.ArgumentTypeError('Use a credential-free https://github.com/OWNER/REPO URL')
    return match.group(1).removesuffix('.git')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public', type=repository, default='https://github.com/87jbzyzr9h-gif/Quantum-Chat.git')
    parser.add_argument('--private', type=repository, default='https://github.com/87jbzyzr9h-gif/Quantum-Chat-Private.git')
    parser.add_argument('--directory', type=Path, default=Path('work/private-mirror.git'))
    parser.add_argument('--gh', default='gh', help='GitHub CLI executable')
    parser.add_argument('--apply', action='store_true', help='Perform mirror push; default is dry-run')
    args = parser.parse_args()
    if args.public == args.private:
        parser.error('Source and destination must differ')
    for repo, expected_private in [(args.public, False), (args.private, True)]:
        info = json.loads(subprocess.check_output([args.gh, 'repo', 'view', repo,
                                                  '--json', 'nameWithOwner,isPrivate'], text=True))
        if info['isPrivate'] != expected_private:
            parser.error(f'Repository visibility does not match its role: {repo}')
    args.directory.parent.mkdir(parents=True, exist_ok=True)
    if not args.directory.exists():
        subprocess.run(['git', 'init', '--bare', str(args.directory)], check=True)
    git = ['git', f'--git-dir={args.directory}', '-c', 'credential.helper=', '-c',
           f'credential.helper=!{shlex.quote(args.gh)} auth git-credential']
    env = {**os.environ, 'GIT_TERMINAL_PROMPT': '0'}
    def run(arguments, capture=False):
        return subprocess.run(git+arguments, env=env, text=True, check=True,
                              capture_output=capture)
    bare = run(['rev-parse', '--is-bare-repository'], True).stdout.strip()
    if bare != 'true':
        parser.error('Mirror directory must be a dedicated bare repository')
    source = f'https://github.com/{args.public}.git'
    destination = f'https://github.com/{args.private}.git'
    run(['fetch', '--prune', source, '+refs/heads/*:refs/heads/*', '+refs/tags/*:refs/tags/*'])
    refs = run(['for-each-ref', '--format=%(refname)'], True).stdout.splitlines()
    if not refs or any(not ref.startswith(('refs/heads/', 'refs/tags/')) for ref in refs):
        parser.error('Mirror contains unexpected refs; use a fresh directory')
    run(['push', '--mirror', '--dry-run', destination])
    if args.apply:
        run(['push', '--mirror', destination])
        def remote_refs(url):
            return dict(line.split()[::-1] for line in run(['ls-remote', '--heads', '--tags', url], True).stdout.splitlines()
                        if not line.split()[1].endswith('^{}'))
        assert remote_refs(source) == remote_refs(destination), 'Remote branch/tag verification failed'
        print('Verified: public and private branches/tags match.')
    else:
        print('Dry-run only. Re-run with --apply to update/delete destination refs to match the source.')


if __name__ == '__main__':
    main()
