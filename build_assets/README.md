# Optional offline build asset

The portable release includes the official `dinov2_vits14_pretrain.pth` here.
The source-only release omits it; the detector-enabled build downloads it from Meta and checks its recorded SHA-256.
This backbone was pretrained by Meta, not by the RoadScan team.
