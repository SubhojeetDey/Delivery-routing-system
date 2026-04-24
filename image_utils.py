from io import BytesIO
from PIL import Image,ImageOps
import os
from pathlib import Path
import uuid
from datetime import datetime,timezone

import qrcode
import os
from pathlib import Path

QR_DIR = Path(os.path.join(os.getcwd(),"media/qr"))
DIR = Path("/qr")
QR_DIR.mkdir(parents=True, exist_ok=True)



def generate_qr(consignment_id: str):
    qr = qrcode.make(consignment_id)
    filename = f"{consignment_id}{str(uuid.uuid4())}.png"
    file_path = QR_DIR / filename
    qr.save(file_path)

    return str(str(DIR/filename))

PROFILE_PIC_DIR = Path(os.path.join(os.getcwd(),"media/img/consignments"))
PROFILE_PIC_DIR.mkdir(parents=True,exist_ok=True)

max_file_size = 5*1024*1024
def upload_image(file:bytes):
    with Image.open(BytesIO(file)) as original:
        img = ImageOps.exif_transpose(original)
        img = ImageOps.fit(img,(300,300),method=Image.Resampling.LANCZOS)
        if img.mode in ("RGBA","LA","P"):
            img.convert("RGB")
        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = PROFILE_PIC_DIR/filename
        PROFILE_PIC_DIR.mkdir(parents=True,exist_ok=True)
        img.save(filepath,"JPEG",quality=85,optimize=True)
    return filename

def delete_profile_pic(filename:str|None):
    if filename is None:
        return
    filepath = PROFILE_PIC_DIR/filename
    if filepath.exists():
        filepath.unlink()