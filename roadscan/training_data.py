"""Explicit, revision-bound human approval and local YOLO dataset export."""
import hashlib
import json
import re
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image
from sqlalchemy import Column, String, ForeignKey, Text
from .core import BASE, Report, Audit, annotation_revision
from .review import validate_detections

CLASSES = ['D00', 'D10', 'D20', 'D40', 'OTHER']
ELIGIBLE = {'Confirmed', 'Assigned', 'Resolved'}


class TrainingApproval(BASE):
    __tablename__ = 'training_approvals'
    report_id = Column(String, ForeignKey('reports.id'), primary_key=True)
    revision = Column(String, nullable=False)
    split = Column(String, nullable=False)
    capture_group = Column(String, nullable=False)
    reviewer = Column(String, nullable=False)
    approved_at = Column(String, nullable=False)
    negative_confirmed = Column(String, nullable=False)


def current_approval(session, report):
    item = session.get(TrainingApproval, report.id)
    valid = bool(item and report.status in ELIGIBLE and item.revision == annotation_revision(report))
    return {'approved': valid, 'stale': bool(item and not valid),
            'revision': annotation_revision(report),
            'split': item.split if item else 'train', 'capture_group': item.capture_group if item else '',
            'reviewer': item.reviewer if valid else None, 'approved_at': item.approved_at if valid else None,
            'negative_confirmed': bool(item and item.negative_confirmed == 'yes'),
            'eligible': report.status in ELIGIBLE, 'weights_changed': False}


def approve(session, report, *, revision, split, capture_group, rights_confirmed, negative_confirmed, actor):
    if report.status not in ELIGIBLE:
        raise ValueError('Confirm and save the human review before approving training data')
    if revision != annotation_revision(report):
        raise ValueError('The report changed. Reload and check the current annotations')
    if not rights_confirmed:
        raise ValueError('Confirm permission to use this image for training or evaluation')
    if split not in {'train', 'val', 'test'} or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', capture_group):
        raise ValueError('Use a capture group with letters, numbers, hyphens or underscores')
    if not json.loads(report.detections) and not negative_confirmed:
        raise ValueError('Explicitly confirm an empty image as a reviewed negative example')
    for other, approval in session.query(Report, TrainingApproval).join(TrainingApproval, Report.id == TrainingApproval.report_id).all():
        if other.id == report.id or not current_approval(session, other)['approved']:
            continue
        if approval.capture_group == capture_group and approval.split != split:
            raise ValueError('All images from one capture group must stay in the same split')
        if other.image_sha == report.image_sha:
            raise ValueError('This exact image is already approved. Keep one reviewed copy to prevent leakage')
    item = session.get(TrainingApproval, report.id) or TrainingApproval(report_id=report.id)
    item.revision = revision; item.split = split; item.capture_group = capture_group; item.reviewer = actor
    item.approved_at = datetime.now(timezone.utc).isoformat()
    item.negative_confirmed = 'yes' if negative_confirmed else 'no'
    session.add(item)
    session.add(Audit(report_id=report.id, actor=actor, action='approve_training', details=json.dumps({
        'revision': revision, 'split': split, 'capture_group': capture_group,
        'negative_confirmed': negative_confirmed, 'rights_confirmed': True, 'weights_changed': False})))
    session.commit()
    return current_approval(session, report)


def training_summary(session):
    counts = {'train': 0, 'val': 0, 'test': 0}; stale = 0
    for report, item in session.query(Report, TrainingApproval).join(TrainingApproval, Report.id == TrainingApproval.report_id).all():
        if current_approval(session, report)['approved']: counts[item.split] += 1
        else: stale += 1
    return {'counts': counts, 'approved': sum(counts.values()), 'stale': stale, 'weights_changed': False}


def export_dataset(session, storage):
    rows = [(report, item) for report, item in session.query(Report, TrainingApproval)
            .join(TrainingApproval, Report.id == TrainingApproval.report_id).order_by(Report.id).all()
            if current_approval(session, report)['approved']]
    if not rows: raise ValueError('Approve at least one reviewed example first')
    if len(rows) > 1000: raise ValueError('Export supports up to 1000 examples per local package')
    handle = tempfile.NamedTemporaryFile(prefix='roadscan-reviewed-', suffix='.zip', delete=False)
    path = Path(handle.name); handle.close()
    manifest = {'format': 1, 'created_at': datetime.now(timezone.utc).isoformat(), 'classes': CLASSES,
                'weights_changed': False, 'split_policy': 'Human-assigned capture groups; no automatic random split', 'examples': []}
    total = 0; hashes = set(); groups = {}
    try:
        with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
            for report, item in rows:
                image = Path(storage)/Path(report.image_ref).name
                total += image.stat().st_size
                if total > 512*1024*1024: raise ValueError('Dataset exceeds the 512 MB local export limit')
                with image.open('rb') as stream: digest = hashlib.file_digest(stream, 'sha256').hexdigest()
                if digest != report.image_sha: raise ValueError('An approved image changed on disk; review it again')
                if digest in hashes: raise ValueError('Duplicate approved image; revoke one approval before exporting')
                if item.capture_group in groups and groups[item.capture_group] != item.split:
                    raise ValueError('Capture group crosses splits; correct approvals before exporting')
                hashes.add(digest); groups[item.capture_group] = item.split
                with Image.open(image) as decoded: width, height = decoded.size
                boxes = validate_detections(json.loads(report.detections), width, height)
                if not boxes and item.negative_confirmed != 'yes': raise ValueError('Empty labels require negative confirmation')
                name = digest
                lines = []
                for d in boxes:
                    x1, y1, x2, y2 = d['box']
                    lines.append(f"{CLASSES.index(d['class_id'])} {(x1+x2)/2/width:.8f} {(y1+y2)/2/height:.8f} {(x2-x1)/width:.8f} {(y2-y1)/height:.8f}")
                archive.write(image, f'images/{item.split}/{name}.jpg')
                archive.writestr(f'labels/{item.split}/{name}.txt', '\n'.join(lines)+('\n' if lines else ''))
                original = json.loads(report.source_metadata or '{}').get('initial_prediction', {})
                manifest['examples'].append({'report_id': report.id, 'image_sha256': digest, 'revision': item.revision,
                    'split': item.split, 'capture_group': item.capture_group, 'reviewer': item.reviewer,
                    'approved_at': item.approved_at, 'width': width, 'height': height, 'detections': boxes,
                    'reviewed_negative': not boxes, 'initial_model_version': original.get('model_version', report.model_version)})
            for split in ('train', 'val', 'test'):
                archive.writestr(f'images/{split}/', b''); archive.writestr(f'labels/{split}/', b'')
            # Omitting path makes an absolute data.yaml resolve images relative
            # to its own folder rather than Ultralytics' global datasets folder.
            archive.writestr('data.yaml', 'train: images/train\nval: images/val\ntest: images/test\nnames:\n'+''.join(f'  {i}: {c}\n' for i, c in enumerate(CLASSES)))
            archive.writestr('manifest.json', json.dumps(manifest, indent=2, ensure_ascii=False))
            archive.writestr('START-HERE.txt', 'REVIEWED ROADSCAN DATA\n1. Keep capture groups together. Reserve val and test images before training.\n2. Add representative original training data; never train on val/test.\n3. Fine-tune a candidate in an appropriate training environment.\n4. Measure per-class AP, missed defects and latency on protected test data.\n5. Import the new checkpoint into RoadScan only after evaluation.\n\nSaving reviews or exporting this ZIP DOES NOT change model weights. Empty label files are explicitly reviewed negatives.\nClasses: 0 D00, 1 D10, 2 D20, 3 D40, 4 OTHER. Remap external datasets explicitly.\nImages and reviewer identifiers are private workspace data. Store and share this export appropriately.\nNo training is launched and no data is sent to a cloud service by RoadScan.\n')
        return path, manifest
    except Exception:
        path.unlink(missing_ok=True)
        raise
