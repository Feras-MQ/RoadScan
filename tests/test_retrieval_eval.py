from PIL import Image
import pytest
from roadscan.retrieval_eval import evaluate_retrieval, secure_image, read_manifest


def test_synthetic_ranked_retrieval(tmp_path):
    # SYNTHETIC software fixture, NOT empirical retrieval performance.
    for name, color in [('q.png','red'),('match.png','red'),('other.png','blue')]:
        Image.new('RGB',(32,32),color).save(tmp_path/name)
    queries = [{'image':'q.png','damage_id':'road-1'}]
    gallery = [{'image':'match.png','damage_id':'road-1'}, {'image':'other.png','damage_id':'road-2'}]
    result = evaluate_retrieval(queries,gallery,tmp_path)
    assert result['eligible_queries'] == 1
    assert result['recall_at_5'] == 1


def test_no_eligible_queries(tmp_path):
    Image.new('RGB',(32,32),'red').save(tmp_path/'q.png')
    result = evaluate_retrieval([{'image':'q.png','damage_id':'x'}], [{'image':'q.png','damage_id':'x'}],tmp_path)
    assert result['eligible_queries'] == 0 and result['recall_at_1'] is None


def test_rejects_escaping_paths(tmp_path):
    with pytest.raises(ValueError):
        secure_image(tmp_path,'../secret.jpg')


def test_split_filter(tmp_path):
    manifest = tmp_path/'m.csv'
    manifest.write_text('image,damage_id,split\na.png,x,validation\nb.png,y,test\n')
    assert len(read_manifest(manifest,'test')) == 1
