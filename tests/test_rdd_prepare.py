import io
import zipfile
from PIL import Image
import pytest
from roadscan.rdd_prepare import convert_voc, prepare_dataset
from roadscan.rdd_prepare import sha256_file

def annotation(box='<xmin>2</xmin><ymin>1</ymin><xmax>8</xmax><ymax>5</ymax>'):
    return f'<annotation><size><width>10</width><height>6</height></size><object><name>D40</name><bndbox>{box}</bndbox></object></annotation>'.encode()

def archive(root, country, color):
    output=io.BytesIO()
    Image.new('RGB',(10,6),color).save(output,format='JPEG')
    with zipfile.ZipFile(root/(country+'.zip'),'w') as z:
        z.writestr(country+'/train/images/a.jpg',output.getvalue())
        xml=annotation()
        objects=xml[xml.index(b'<object>'):xml.index(b'</object>')+len(b'</object>')]
        xml=xml.replace(b'</annotation>', b''.join(objects.replace(b'D40',cls.encode()) for cls in ('D00','D10','D20'))+b'</annotation>')
        z.writestr(country+'/train/annotations/xmls/a.xml',xml)
        z.writestr(country+'/test/images/unlabeled.jpg',b'not training data')

def test_conversion_preserves_class_and_extents():
    labels,ignored=convert_voc(annotation(),10,6)
    assert labels == [(3,0.5,0.5,0.6,4/6)]
    assert not ignored
    with pytest.raises(ValueError,match='outside'):
        convert_voc(annotation('<xmin>-1</xmin><ymin>1</ymin><xmax>8</xmax><ymax>5</ymax>'),10,6)
    with pytest.raises(ValueError,match='entity'):
        convert_voc(b'<!DOCTYPE x>'+annotation(),10,6)

def test_country_split_provenance_and_test_isolation(tmp_path):
    source=tmp_path/'source';source.mkdir()
    for country,color in [('India','red'),('Czech','blue'),('US','green')]: archive(source,country,color)
    output=tmp_path/'prepared'
    result=prepare_dataset(source,output,{'India':('train',1),'Czech':('val',1),'US':('heldout',1)})
    assert result['training_audit']['image_counts'] == {'train':1,'val':1}
    assert len(result['records']) == 3
    for record in result['records']:
        for kind in ('image','label'):
            assert sha256_file(output/record[kind]) == record[kind+'_sha256']
        assert b'\r\n' not in (output/record['label']).read_bytes()
    assert not (output/'training/test').exists()
    assert len(list((output/'heldout/images').glob('*.jpg'))) == 1
    assert not list(output.rglob('unlabeled.jpg'))
    with pytest.raises(ValueError,match='overwrite'): prepare_dataset(source,output)

def test_duplicate_country_image_rejected(tmp_path):
    archive(tmp_path,'India','red');archive(tmp_path,'Czech','red')
    with pytest.raises(RuntimeError,match='across'):
        prepare_dataset(tmp_path,tmp_path/'output',{'India':('train',1),'Czech':('val',1)})
