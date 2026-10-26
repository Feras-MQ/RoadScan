import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('prepare_local_env', Path(__file__).parents[1] / 'tools/prepare_local_env.py')
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class LocalEnvironmentTests(unittest.TestCase):
    def test_fresh_cpu_setup_and_existing_settings_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            setup.prepare(root)
            original = (root / '.env').read_bytes()
            self.assertTrue(b'ROADSCAN_WITH_DETECTOR=1\n' in original)
            self.assertGreater(len(original.splitlines()[0].split(b'=', 1)[1]), 30)
            setup.prepare(root)
            self.assertEqual((root / '.env').read_bytes(), original)

    def test_invalid_model_never_creates_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'models').mkdir()
            weights = root / 'models/roadscan_best.pt'
            weights.write_bytes(b'synthetic checkpoint bytes, not a model')
            for digest, confidence in [('wrong', 0.25), (hashlib.sha256(weights.read_bytes()).hexdigest(), float('nan'))]:
                (root / 'models/roadscan_model.json').write_text(json.dumps({'sha256': digest, 'confidence': confidence}))
                with self.assertRaises(ValueError):
                    setup.prepare(root)
                self.assertFalse((root / '.env').exists())

    def test_verified_model_record_is_configured(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'models').mkdir()
            weights = root / 'models/roadscan_best.pt'
            weights.write_bytes(b'synthetic checkpoint bytes, not a model')
            digest = hashlib.sha256(weights.read_bytes()).hexdigest()
            (root / 'models/roadscan_model.json').write_text(json.dumps({'sha256': digest, 'confidence': 0.3}))
            setup.prepare(root)
            self.assertIn(f'ROADSCAN_YOLO_SHA256={digest}', (root / '.env').read_text())


if __name__ == '__main__':
    unittest.main()
