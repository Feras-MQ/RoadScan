"""Replacement CLI: local DINOv2 crop comparison, FAISS and GPS filtering."""
import argparse,json
from pathlib import Path
from roadscan.duplicate_finder import DuplicateFinder

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('query','gallery','checkpoint','cache','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--radius',type=float,default=50);p.add_argument('--threshold',type=float,default=.8)
    a=p.parse_args()
    if a.output.exists():p.error('Output exists; choose a new file')
    result=DuplicateFinder(a.checkpoint,a.cache).search(json.loads(a.query.read_text()),json.loads(a.gallery.read_text()),a.radius,a.threshold)
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
if __name__=='__main__':main()
