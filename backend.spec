# Build with pyinstaller backend.spec on Windows only.
from PyInstaller.utils.hooks import collect_submodules
hiddenimports=collect_submodules('uvicorn') + collect_submodules('roadscan')
a=Analysis(['roadscan/desktop_server.py'],pathex=['.'],binaries=[],datas=[('static','static'),('frontend/dist','frontend/dist')],hiddenimports=hiddenimports,hookspath=[],hooksconfig={},runtime_hooks=[],excludes=[],noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,a.binaries,a.datas,[],name='roadscan-backend',debug=False,strip=False,upx=False,console=False)
