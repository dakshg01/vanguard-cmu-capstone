"""Package/publish or download the full SQLite database using GitHub Releases.

python database_release.py package
python database_release.py publish  # requires authenticated GitHub CLI (gh)
python database_release.py download
"""
import argparse
from contextlib import closing
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parent
REPO = 'dakshg01/vanguard-cmu-capstone'
TAG = 'nport-data-v1'
PACKAGE = ROOT / '.tmp' / TAG
DATABASE = ROOT / 'output' / 'nport.sqlite'
CHUNK = 1024 ** 3


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def package():
    PACKAGE.mkdir(parents=True, exist_ok=True)
    snapshot = PACKAGE / 'snapshot.sqlite'
    # SQLite backup includes committed WAL content and provides a consistent snapshot.
    with closing(sqlite3.connect(DATABASE.as_uri() + '?mode=ro', uri=True)) as source:
        with closing(sqlite3.connect(snapshot)) as target:
            source.backup(target)
    manifest = {'database': 'nport.sqlite', 'size': snapshot.stat().st_size,
                'sha256': digest(snapshot), 'parts': []}
    with snapshot.open('rb') as source:
        for index in range((manifest['size'] + CHUNK - 1) // CHUNK):
            part = PACKAGE / f'nport.sqlite.part{index:03d}.gz'
            remaining = CHUNK
            with gzip.open(part, 'wb', compresslevel=1) as output:
                while remaining:
                    block = source.read(min(8 * 1024 ** 2, remaining))
                    if not block:
                        break
                    output.write(block)
                    remaining -= len(block)
            manifest['parts'].append({'name': part.name, 'size': part.stat().st_size,
                                      'sha256': digest(part)})
            print(f'Packaged {part.name}: {part.stat().st_size:,} bytes', flush=True)
    (PACKAGE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    snapshot.unlink()
    print(f'Package ready: {PACKAGE}', flush=True)


def gh(*args):
    subprocess.run(['gh', *args], check=True)


def publish():
    if not shutil.which('gh'):
        raise SystemExit('Install GitHub CLI and run gh auth login, then retry publish.')
    gh('auth', 'status')
    manifest = json.loads((PACKAGE / 'manifest.json').read_text())
    files = [PACKAGE / p['name'] for p in manifest['parts']]
    for path, part in zip(files, manifest['parts']):
        if digest(path) != part['sha256']:
            raise SystemExit(f'Checksum failed: {path}')
    # Keep the release a draft until every asset has uploaded successfully.
    existing = subprocess.run(['gh', 'release', 'view', TAG, '--repo', REPO,
                               '--json', 'isDraft'], capture_output=True, text=True)
    if existing.returncode == 0:
        if not json.loads(existing.stdout)['isDraft']:
            raise SystemExit('This release is already published; use a new version tag.')
    else:
        gh('release', 'create', TAG, '--repo', REPO, '--draft', '--title',
           'N-PORT SQLite database v1', '--notes',
           'Full SQLite snapshot. Clone the repository and run python database_release.py download. '
           'The download command verifies SHA-256 checksums and restores output/nport.sqlite.')
    gh('release', 'upload', TAG, '--repo', REPO,
       str(PACKAGE / 'manifest.json'), *map(str, files), '--clobber')
    remote = json.loads(subprocess.check_output(
        ['gh', 'release', 'view', TAG, '--repo', REPO, '--json', 'assets'], text=True))
    sizes = {asset['name']: asset['size'] for asset in remote['assets']}
    for path in [PACKAGE / 'manifest.json', *files]:
        if sizes.get(path.name) != path.stat().st_size:
            raise RuntimeError(f'Remote asset size mismatch: {path.name}')
    gh('release', 'edit', TAG, '--repo', REPO, '--draft=false')
    gh('release', 'view', TAG, '--repo', REPO)


def fetch(name, target):
    if shutil.which('gh'):
        gh('release', 'download', TAG, '--repo', REPO, '--pattern', name,
           '--dir', str(target.parent), '--clobber')
    else:
        url = f'https://github.com/{REPO}/releases/download/{TAG}/{name}'
        try:
            urllib.request.urlretrieve(url, target)
        except Exception as error:
            raise RuntimeError('Download failed. For a private repository, install GitHub '
                               'CLI and run gh auth login with an account that has access.') from error


def download():
    if DATABASE.exists():
        raise SystemExit(f'{DATABASE} already exists; move it aside before downloading.')
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    # Temporary files share the destination filesystem so the final rename is atomic.
    with tempfile.TemporaryDirectory(dir=DATABASE.parent, prefix='database-download-') as tmp:
        folder = Path(tmp)
        fetch('manifest.json', folder / 'manifest.json')
        manifest = json.loads((folder / 'manifest.json').read_text())
        result = folder / 'restored.sqlite'
        with result.open('wb') as output:
            for part in manifest['parts']:
                name = part['name']
                if Path(name).name != name or not name.startswith('nport.sqlite.part'):
                    raise ValueError('Invalid part name in manifest')
                path = folder / name
                fetch(name, path)
                if path.stat().st_size != part['size'] or digest(path) != part['sha256']:
                    raise ValueError(f'Checksum failed: {name}')
                with gzip.open(path, 'rb') as source:
                    shutil.copyfileobj(source, output, 8 * 1024 ** 2)
                path.unlink()
                print(f'Restored {name}', flush=True)
        if result.stat().st_size != manifest['size'] or digest(result) != manifest['sha256']:
            raise ValueError('Restored database checksum failed')
        with closing(sqlite3.connect(result.as_uri() + '?mode=ro', uri=True)) as connection:
            if connection.execute('PRAGMA quick_check').fetchone() != ('ok',):
                raise ValueError('SQLite integrity check failed')
        result.replace(DATABASE)
    print(f'Database ready: {DATABASE}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['package', 'publish', 'download'])
    args = parser.parse_args()
    globals()[args.action]()
