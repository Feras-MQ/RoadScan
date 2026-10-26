"""Offline E5 ResNet18 / DINOv2 feature extraction; no network or weight downloads.

Only use trusted locally supplied checkpoints with appropriate rights. Torch checkpoints
can execute code during deserialization; never load untrusted checkpoint files.
"""
from pathlib import Path
import math

SUPPORTED = ('resnet18', 'dinov2_vits14')


def cosine_similarity(left, right):
    if not left or len(left) != len(right):
        raise ValueError('Feature vectors must be nonempty and equal-length')
    if any(not math.isfinite(float(x)) for x in (*left, *right)):
        raise ValueError('Feature vectors must be finite')
    nl = math.sqrt(sum(float(x)**2 for x in left))
    nr = math.sqrt(sum(float(x)**2 for x in right))
    if nl == 0 or nr == 0:
        raise ValueError('Zero-norm embedding')
    return max(-1.0, min(1.0, sum(float(x)*float(y) for x,y in zip(left,right))/(nl*nr)))


class OfflineEmbedder:
    """Local-only embedding extractor. No pretrained=True or torch.hub calls."""
    def __init__(self, method, checkpoint):
        if method not in SUPPORTED:
            raise ValueError(f'Unsupported method: {method}')
        path = Path(checkpoint)
        if not path.is_file():
            raise FileNotFoundError('Authorized local checkpoint not configured')
        try:
            import torch
            import torchvision.models as models
        except ImportError as exc:
            raise RuntimeError('Install compatible torch and torchvision offline') from exc
        self.torch = torch
        self.method = method
        if method == 'resnet18':
            model = models.resnet18(weights=None)
            state = torch.load(path, map_location='cpu', weights_only=True)
            if isinstance(state,dict) and 'state_dict' in state:state=state['state_dict']
            if 'fc.weight' in state:model.fc=torch.nn.Linear(model.fc.in_features,state['fc.weight'].shape[0])
            model.load_state_dict(state, strict=True)
            model.fc = torch.nn.Identity()
            self.model = model.eval()
            self.size = 224
        else:
            # DINOv2 architecture must be provided locally by an approved package.
            try:
                from dinov2.models.vision_transformer import vit_small
            except ImportError as exc:
                raise RuntimeError('Install an approved local DINOv2 source; no torch.hub downloads') from exc
            model = vit_small(patch_size=14, img_size=518, init_values=1.0, block_chunks=0)
            state = torch.load(path, map_location='cpu', weights_only=True)
            if isinstance(state, dict) and 'model' in state:
                state = state['model']
            model.load_state_dict(state, strict=True)
            self.model = model.eval()
            self.size = 518

    def encode(self, image_path, box=None):
        from PIL import Image
        import torchvision.transforms as transforms
        prep = transforms.Compose([
            transforms.Resize((self.size, self.size)),
            transforms.ToTensor(),
            transforms.Normalize((0.485,0.456,0.406),(0.229,0.224,0.225)),
        ])
        with Image.open(image_path) as image:
            image = image.convert('RGB')
            if box is not None:
                if len(box)!=4 or not all(math.isfinite(float(v)) for v in box):raise ValueError('Invalid crop')
                x1,y1,x2,y2=box
                if not (0<=x1<x2<=image.width and 0<=y1<y2<=image.height):raise ValueError('Crop outside image')
                image=image.crop((math.floor(x1),math.floor(y1),math.ceil(x2),math.ceil(y2)))
            tensor = prep(image).unsqueeze(0)
        with self.torch.inference_mode():
            result = self.model(tensor)
            if isinstance(result, dict):
                result = result.get('x_norm_clstoken')
            if result is None:
                raise RuntimeError('DINOv2 output did not include a class-token embedding')
            result = result.flatten().float()
            result = result / result.norm().clamp_min(1e-12)
            return result.tolist()
