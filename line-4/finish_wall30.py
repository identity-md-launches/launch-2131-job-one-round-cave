"""One-shot preservation of image-generated Joint Check pigment only."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    codec = load('png30', 'finish_wall22.py')
    preview = load('jpeg30', 'preview_jpeg27.py')
    ancestor = Path('artifacts/line-4/wall.png')
    output = Path('artifacts/line-4/wall-v13.png')
    assert not Path('dist/line-4/30.json').exists(), 'one-shot helper'
    oldhash = hashlib.sha256(ancestor.read_bytes()).hexdigest()
    width, height, original = codec.read_png(ancestor)
    dw, dh, draft = codec.read_png(output)
    assert (width, height) == (dw, dh) == (1254, 1254)
    final = original[:]
    # Two image-generated stones and a U-shaped charcoal cradle, on bare rock.
    # Soft geometric masks exclude all generated background elsewhere.
    for y in range(949, 1014):
        for x in range(876, 1005):
            stones = max(0, min(1, (19-math.hypot(x-919, y-973))/2,
                                  1))
            stones = max(stones, max(0, min(1, (19-math.hypot(x-960, y-974))/2)))
            ellipse = math.sqrt(((x-940)/58)**2 + ((y-959)/48)**2)
            bowl = max(0, min(1, (0.09-abs(ellipse-1))*25)) if y >= 959 else 0
            alpha = max(stones, bowl)
            if alpha:
                at = (y*width+x)*3
                for c in range(3):
                    final[at+c] = round(original[at+c]*(1-alpha)+draft[at+c]*alpha)
    changed = [i for i in range(width*height)
               if final[i*3:i*3+3] != original[i*3:i*3+3]]
    assert changed and all(876 <= i%width < 1005 and 949 <= i//width < 1014 for i in changed)
    sha = codec.write_png(output, width, height, final)
    assert codec.read_png(output)[2] == final
    jpeg = preview.encode(preview.resize(final, width, height), 512, 512, quality=40)
    assert len(jpeg) < 100000
    Path('dist/line-4/30.jpg').write_bytes(jpeg)
    ancestor.write_bytes(output.read_bytes())
    evidence = {'ancestor_sha256': oldhash, 'wall_sha256': sha,
                'dimensions': [width, height], 'format': 'PNG', 'mode': 'RGB',
                'changed_pixels': len(changed), 'changed_pixels_outside_mark_region': 0,
                'mark_region_xyxy': [876,949,1005,1014],
                'method': 'Only image-generated pigment within feathered stone and bowl masks retained; every other pixel equals the ancestor.',
                'preview': {'path': 'dist/line-4/30.jpg', 'format': 'JPEG',
                            'dimensions': [512,512], 'bytes': len(jpeg)},
                'unmet_visual_requirements': []}
    Path('line-4/IMAGE-30.json').write_text(json.dumps(evidence, indent=2)+'\n')
    record = {'name': 'A Place Together', 'image': 'https://api.imd.fun/artifacts/'+sha,
              'attributes': [{'trait_type': 'Cave', 'value': 'Crystal'},
                             {'trait_type': 'Wall', 'value': 'Line 4'},
                             {'trait_type': 'Number', 'value': 30},
                             {'trait_type': 'Left behind', 'value': 'Joint Check'},
                             {'trait_type': 'Meaning', 'value': 'Two ochre stones in one charcoal cradle ask whether choices can fit together.'},
                             {'trait_type': 'One thing', 'value': 'Finite offline dependency resolution'}]}
    Path('dist/line-4/30.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
