"""Prepare a frozen YOLO subset from local, licensed RDD2022 country ZIPs.

Never reads the live RoadScan database or uploads data. Original challenge
test images lack labels and are not used. A labeled country is held out instead.
"""
import argparse
from collections import Counter
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image
from .detector_train import CLASSES, inspect_dataset

DEFAULT_PLAN = {
    'India': ('train', 6200), 'China_MotorBike': ('train', 1800),
    'Czech': ('val', 1000), 'United_States': ('heldout', 1000),
}
SOURCE = {
    'doi': '10.6084/m9.figshare.21431547.v1',
    'url': 'https://figshare.com/articles/dataset/21431547',
    'license': 'CC BY 4.0',
    'attribution': 'Deeksha Arya, Hiroya Maeda, Sanjay Kumar Ghosh, Durga Toshniwal, Yoshihide Sekimoto (RDD2022)',
}

def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()

def convert_voc(xml, width, height):
    """Retain source numeric xyxy extents; reject malformed/out-of-image boxes."""
    if b'<!DOCTYPE' in xml.upper() or b'<!ENTITY' in xml.upper():
        raise ValueError('XML entity declarations are not permitted')
    root = ET.fromstring(xml)
    if int(root.findtext('size/width', '0')) != width or int(root.findtext('size/height', '0')) != height:
        raise ValueError('Annotation size differs from image')
    labels, ignored = [], Counter()
    for obj in root.findall('object'):
        name = obj.findtext('name', '').strip()
        if name not in CLASSES:
            ignored[name] += 1
            continue
        box = obj.find('bndbox')
        if box is None:
            raise ValueError('Missing bounding box')
        values = [float(box.findtext(k, 'nan')) for k in ('xmin', 'ymin', 'xmax', 'ymax')]
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Nonfinite bounding box')
        x1, y1, x2, y2 = values
        if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
            raise ValueError('Bounding box outside image')
        labels.append((CLASSES.index(name), (x1+x2)/(2*width), (y1+y2)/(2*height),
                       (x2-x1)/width, (y2-y1)/height))
    return labels, ignored

def prepare_dataset(archives_dir, output_dir, plan=None, seed=20261010):
    plan = DEFAULT_PLAN if plan is None else plan
    if not plan or not any(split == 'train' for split, _ in plan.values()) or not any(split == 'val' for split, _ in plan.values()):
        raise ValueError('A country-disjoint train and validation plan is required')
    if any(split not in ('train', 'val', 'heldout') or count < 1 for split, count in plan.values()):
        raise ValueError('Invalid split or image limit')
    destination = Path(output_dir).resolve()
    if destination.exists():
        raise ValueError('Refusing to overwrite an existing dataset')
    archives = Path(archives_dir).resolve(strict=True)
    source_paths = {country: archives / (country + '.zip') for country in plan}
    for country, path in source_paths.items():
        if not re.fullmatch(r'[A-Za-z_]+', country) or path.is_symlink() or not path.is_file():
            raise ValueError('Missing or unsafe country archive')
    destination.mkdir(parents=True, exist_ok=False)
    records, rejected, seen = [], [], {}
    class_counts, negatives, ignored_counts, archive_hashes = {}, Counter(), Counter(), {}
    for country, (split, limit) in plan.items():
        path = source_paths[country]
        archive_hashes[country] = sha256_file(path)
        counts = Counter()
        accepted = 0
        with zipfile.ZipFile(path) as archive:
            members = {i.filename: i for i in archive.infolist()}
            if len(members) != len(archive.infolist()):
                raise ValueError('Duplicate archive member names')
            prefix = country + '/train/'
            candidates = [n for n in members if n.startswith(prefix + 'annotations/') and n.endswith('.xml')]
            candidates.sort(key=lambda name: hashlib.sha256(f'{seed}:{country}:{name}'.encode()).digest())
            for annotation in candidates:
                if accepted >= limit:
                    break
                stem = PurePosixPath(annotation).stem
                if not re.fullmatch(r'[A-Za-z0-9_-]+', stem):
                    raise ValueError('Unsafe annotation name')
                image_name = prefix + 'images/' + stem + '.jpg'
                try:
                    if image_name not in members or members[image_name].file_size > 20*1024*1024 or members[annotation].file_size > 512*1024:
                        raise ValueError('Missing or oversized image/annotation')
                    image_data, xml = archive.read(image_name), archive.read(annotation)
                    with Image.open(io.BytesIO(image_data)) as image:
                        width, height = image.size
                        if image.format != 'JPEG': raise ValueError('Expected JPEG image')
                        if image.getexif().get(274, 1) != 1:
                            raise ValueError('EXIF rotation requires separate label review')
                        image.load()
                    labels, ignored = convert_voc(xml, width, height)
                    digest = hashlib.sha256(image_data).hexdigest()
                    if digest in seen:
                        if seen[digest] != split:
                            raise RuntimeError('Exact duplicate across country splits')
                        raise ValueError('Exact duplicate within split')
                except (ValueError, OSError, ET.ParseError, zipfile.BadZipFile) as exc:
                    rejected.append({'country': country, 'annotation': annotation, 'reason': str(exc)})
                    continue
                seen[digest] = split
                relative_root = Path('heldout') if split == 'heldout' else Path('training') / split
                name = country + '-' + stem
                image_path = relative_root / 'images' / (name + '.jpg')
                label_path = relative_root / 'labels' / (name + '.txt')
                for relative in (image_path, label_path):
                    (destination / relative).parent.mkdir(parents=True, exist_ok=True)
                    if (destination / relative).exists(): raise ValueError('Duplicate output name')
                label_text = ''.join(f'{cls} {cx:.17g} {cy:.17g} {w:.17g} {h:.17g}\n' for cls,cx,cy,w,h in labels)
                (destination / image_path).write_bytes(image_data)
                (destination / label_path).write_text(label_text, encoding='utf-8', newline='\n')
                records.append({'country': country, 'split': split, 'source_image': image_name,
                    'source_annotation': annotation, 'image': image_path.as_posix(), 'label': label_path.as_posix(),
                    'image_sha256': digest, 'label_sha256': hashlib.sha256(label_text.encode()).hexdigest(),
                    'annotation_sha256': hashlib.sha256(xml).hexdigest(), 'boxes':len(labels), 'width':width, 'height':height})
                counts.update(CLASSES[label[0]] for label in labels)
                if not labels: negatives[country] += 1
                ignored_counts.update(ignored)
                accepted += 1
        if accepted != limit:
            raise ValueError(f'Insufficient valid images in {country}: {accepted}/{limit}; staged output retained for diagnosis')
        class_counts[country] = dict(counts)
    training = destination / 'training'
    # YAML paths are relative to the YAML directory and remain portable in ZIP exports.
    yaml = 'train: train/images\nval: val/images\nnames:\n' + ''.join(f'  {i}: {name}\n' for i,name in enumerate(CLASSES))
    (training / 'data.yaml').write_text(yaml, encoding='utf-8')
    audit = inspect_dataset(training)
    audit['root'] = 'training'
    for split in ('train', 'val'):
        coverage = Counter()
        for country, (country_split, _) in plan.items():
            if country_split == split:
                coverage.update(class_counts[country])
        if any(coverage[cls] == 0 for cls in CLASSES):
            raise ValueError(f'Missing target class in {split}; review staged dataset')
    manifest = {'source': SOURCE, 'seed': seed, 'country_plan':plan, 'class_order':list(CLASSES),
        'class_box_counts':class_counts, 'negative_image_counts':dict(negatives),
        'ignored_non_target_objects':dict(ignored_counts), 'source_archive_sha256':archive_hashes,
        'selection':'SHA256(seed:country:annotation path), ascending, first valid N',
        'box_policy':'Retain source numeric xyxy extents; no 1-based adjustment; invalid boxes reject whole image',
        'label_line_endings':'Canonical LF; hashes refer to stored UTF-8 file bytes',
        'leakage_policy':'Countries disjoint across splits; byte-identical images rejected across all splits. No sequence IDs supplied; visually audit near duplicates before training.',
        'original_unlabeled_test':'Excluded', 'training_audit':audit, 'records':records, 'rejected':rejected}
    (destination / 'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n', encoding='utf-8')
    return manifest

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archives-dir', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args(argv)
    try:
        manifest = prepare_dataset(args.archives_dir, args.output_dir)
        print(json.dumps({k:manifest[k] for k in ('country_plan','class_box_counts','negative_image_counts','ignored_non_target_objects')}))
    except (ValueError, OSError, RuntimeError, zipfile.BadZipFile) as exc:
        parser.error(str(exc))

if __name__ == '__main__':
    main()
