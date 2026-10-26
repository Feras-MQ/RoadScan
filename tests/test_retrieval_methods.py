from pathlib import Path
import pytest
from roadscan.retrieval_eval import evaluate_retrieval

class FakeEmbedder:
    def __init__(self):
        self.calls = []
    def encode(self, path):
        self.calls.append(path)
        return {'q.jpg':[1.,0.], 'same.jpg':[1.,0.], 'other.jpg':[0.,1.]}[path.name]


def test_neural_ranking_with_injected_encoder(tmp_path):
    for name in ('q.jpg','same.jpg','other.jpg'):
        (tmp_path/name).write_bytes(b'fixture')
    queries = [{'image':'q.jpg','damage_id':'A'}]
    gallery = [{'image':'q.jpg','damage_id':'A'}, {'image':'other.jpg','damage_id':'B'},
               {'image':'same.jpg','damage_id':'A'}]
    encoder = FakeEmbedder()
    result = evaluate_retrieval(queries, gallery, tmp_path, method='resnet18', embedder=encoder)
    assert result['recall_at_1'] == result['recall_at_5'] == 1.0
    assert len(encoder.calls) == 3


def test_missing_checkpoint_fails_closed(tmp_path):
    with pytest.raises(ValueError, match='checkpoint'):
        evaluate_retrieval([], [], tmp_path, method='dinov2_vits14')


def test_unknown_method_rejected(tmp_path):
    with pytest.raises(ValueError, match='Unsupported'):
        evaluate_retrieval([], [], tmp_path, method='random')


def test_path_traversal_rejected_before_encoding(tmp_path):
    with pytest.raises(ValueError, match='outside'):
        evaluate_retrieval([], [{'image':'../outside.jpg','damage_id':'A'}], tmp_path,
                           method='resnet18', embedder=FakeEmbedder())
