import pytest
from roadscan.feature_embeddings import cosine_similarity, OfflineEmbedder

def test_cosine():
    assert cosine_similarity([1,0], [1,0]) == 1
    assert cosine_similarity([1,0], [0,1]) == 0
    assert cosine_similarity([1,0], [-1,0]) == -1

@pytest.mark.parametrize('left,right', [([], []), ([0,0],[1,0]), ([float('nan')],[1]), ([1],[1,2])])
def test_invalid_vectors(left,right):
    with pytest.raises(ValueError): cosine_similarity(left,right)

def test_no_missing_checkpoint_download(tmp_path):
    with pytest.raises(FileNotFoundError): OfflineEmbedder('resnet18',tmp_path/'absent.pt')

def test_unsupported_method(tmp_path):
    with pytest.raises(ValueError): OfflineEmbedder('unapproved',tmp_path/'absent.pt')
