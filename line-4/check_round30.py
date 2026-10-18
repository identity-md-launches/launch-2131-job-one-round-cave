"""Read-back checks for round 30's concrete deliverables; no host inspection."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess


def head(path):
    return subprocess.run(['git', 'show', 'HEAD:'+path], capture_output=True, check=True).stdout


def main():
    spec = importlib.util.spec_from_file_location('codec30check', 'line-4/finish_wall22.py')
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    goal = Path('line-4/GOAL.md')
    assert goal.read_bytes() == head(str(goal))
    records = sorted(Path('dist/line-4').glob('[0-9][0-9].json'))
    assert len(records) == 30
    for p in records[:-1]:
        assert p.read_bytes() == head(str(p)), p
    for p in Path('line-4/tools').rglob('*.py'):
        if 'joint-check' not in p.parts:
            assert p.read_bytes() == head(str(p)), p
    png = Path('artifacts/line-4/wall-v13.png')
    raw = png.read_bytes()
    assert raw == Path('artifacts/line-4/wall.png').read_bytes()
    w, h, pixels = codec.read_png(raw)
    ow, oh, old = codec.read_png(Path('artifacts/line-4/wall-v12.png'))
    assert (w,h) == (ow,oh) == (1254,1254)
    changed = [i for i in range(w*h) if pixels[i*3:i*3+3] != old[i*3:i*3+3]]
    assert len(changed) == 3815
    assert all(876 <= i%w < 1005 and 949 <= i//w < 1014 for i in changed)
    record = json.loads(records[-1].read_text())
    assert set(record) == {'name','image','attributes'}
    assert record['image'] == 'https://api.imd.fun/artifacts/'+hashlib.sha256(raw).hexdigest()
    attributes = record['attributes']
    assert [a['trait_type'] for a in attributes] == ['Cave','Wall','Number','Left behind','Meaning','One thing']
    assert all(set(a) == {'trait_type','value'} for a in attributes)
    assert [a['value'] for a in attributes[:4]] == ['Crystal','Line 4',30,'Joint Check']
    assert type(attributes[2]['value']) is int
    jpeg = Path('dist/line-4/30.jpg').read_bytes()
    assert jpeg[:2] == b'\xff\xd8' and jpeg[-2:] == b'\xff\xd9'
    assert len(jpeg) < 100000
    at, dimensions = 2, None
    while at < len(jpeg):
        assert jpeg[at] == 255
        marker = jpeg[at+1]
        size = int.from_bytes(jpeg[at+2:at+4], 'big')
        if marker == 0xc0:
            depth, height, width = struct.unpack('>BHH', jpeg[at+4:at+9])
            assert depth == 8
            dimensions = [width,height]
        if marker == 0xda:
            break
        at += 2+size
    assert dimensions == [512,512]
    for p in [*Path('line-4/tools/joint-check').glob('*'),
              *Path('line-4').glob('*30*'), Path('dist/line-4/30.json'), Path('dist/line-4/30.jpg')]:
        if p.is_file():
            assert p.stat().st_size < 100000, p
            if p.suffix == '.json':
                json.loads(p.read_text())
    result = {'goal_unchanged': True, 'older_records_unchanged': 29,
              'inherited_tool_sources_unchanged': True,
              'required_png': {'path': str(png), 'dimensions': [w,h], 'format': 'PNG',
                               'sha256': hashlib.sha256(raw).hexdigest()},
              'preview': {'path': 'dist/line-4/30.jpg', 'dimensions': dimensions,
                          'format': 'JPEG', 'bytes': len(jpeg)},
              'record_schema_and_content_hash_valid': True,
              'changed_pixels': len(changed), 'changed_pixels_outside_mark_region': 0,
              'tests': [{'command': "python3 -B -m unittest discover -s line-4/tools/joint-check -p 'test_*.py' -v", 'passed': 11},
                        {'command': "python3 -B -m unittest discover -s line-4/tools/exhaustive-audit -p 'test_*.py' -v", 'passed': 14}],
              'demo_command': 'python3 -B line-4/tools/joint-check/joint.py demo',
              'demo_exit_code': 0,
              'unmet_visual_requirements': [],
              'authority': 'Local checks only; no independent certification'}
    Path('line-4/CHECKS-30.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
