"""Build a deterministic source + results ZIP, optionally including a finished PPTX."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--results', type=Path, required=True, help='project output directory')
    p.add_argument('--out', type=Path, default=Path('submission.zip'))
    p.add_argument('--ppt', type=Path, help='team-reviewed presentation .pptx to include')
    a = p.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    if not (a.results/'simulation'/'manifest.json').is_file():
        p.error('--results must contain simulation/manifest.json from lastmile-project')
    if a.out.exists():
        p.error('ZIP already exists; choose a new output filename')
    if a.ppt and (not a.ppt.is_file() or a.ppt.suffix.lower() != '.pptx'):
        p.error('--ppt must be an existing .pptx')
    files = {}
    for item in ['src', 'tests', 'docs', '.github', 'README.md', 'TEAM_HANDOFF.md', 'pyproject.toml', 'requirements.txt']:
        path = root/item
        for f in sorted(path.rglob('*')) if path.is_dir() else [path]:
            if f.is_file() and '__pycache__' not in f.parts and f.suffix != '.pyc':
                files['project/'+str(f.relative_to(root))] = f.read_bytes()
    for f in sorted(a.results.rglob('*')):
        if f.is_file() and f.resolve() != a.out.resolve():
            files['results/'+str(f.relative_to(a.results))] = f.read_bytes()
    if a.ppt:
        files['presentation/'+a.ppt.name] = a.ppt.read_bytes()
    files['PACKAGE_MANIFEST.json'] = json.dumps({'presentation_included': bool(a.ppt),
        'note': 'Add team-reviewed PPTX with --ppt for final course submission.',
        'sha256': {k: hashlib.sha256(v).hexdigest() for k,v in files.items()}}, indent=2).encode()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(a.out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, content in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, content)
    print(a.out)

if __name__ == '__main__':
    main()
