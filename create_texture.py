import os
from PIL import Image, ImageFilter, ImageEnhance

# 1. Load base texture and Alec Douglas-Home photo
base_tex = Image.open('m:/TDS/3D-face-reconstruction/Map-COL.jpg').convert('RGB')
tw, th = base_tex.size # 1024 x 1024

alec_img = Image.open('m:/TDS/3D-face-reconstruction/alec_douglas_home.jpg').convert('RGB')
aw, ah = alec_img.size

# In alec_douglas_home.jpg:
# Center of eyes is around y=680, x=870
# Left eye (image right) ≈ (1010, 680), Right eye (image left) ≈ (730, 680) -> Eye distance ≈ 280 px
# Nose tip ≈ (870, 880)
# Mouth center ≈ (870, 990)
# Chin tip ≈ (870, 1150)
# Forehead top ≈ (870, 350)

# In Map-COL.jpg (note in image pixels, PIL y=0 is top, while glTF v=1 is top):
# glTF v=0.655 corresponds to PIL y = int((1.0 - 0.655) * 1024) = 353
# Eye level PIL y ≈ 353
# Left eye (u=0.633) -> PIL x = int(0.633 * 1024) = 648
# Right eye (u=0.376) -> PIL x = int(0.376 * 1024) = 385
# Eye distance in texture = 648 - 385 = 263 px
# Nose tip: PIL x ≈ 512, PIL y = int((1 - 0.613) * 1024) = 396
# Mouth: PIL x ≈ 512, PIL y = int((1 - 0.548) * 1024) = 463
# Chin: PIL x ≈ 500, PIL y = int((1 - 0.444) * 1024) = 569
# Forehead: PIL x ≈ 512, PIL y = int((1 - 0.767) * 1024) = 238

# Crop Alec Douglas-Home face region:
# Face box in original photo:
# x: from 480 to 1260 (width 780, centered at 870)
# y: from 180 to 1320 (height 1140, centered at 750)
face_box = (480, 180, 1260, 1320)
alec_face = alec_img.crop(face_box)

# We want the cropped face to map onto the texture:
# Texture target area:
# x: from 280 to 744 (width 464, centered at 512)
# y: from 150 to 650 (height 500)
target_w = 480
target_h = 520
alec_resized = alec_face.resize((target_w, target_h), Image.Resampling.LANCZOS)

# Create an elliptical feather mask so the photo seamlessly blends with the head skin
mask = Image.new('L', (target_w, target_h), 0)
mw, mh = mask.size
cx, cy = mw / 2.0, mh / 2.0
rx, ry = mw * 0.42, mh * 0.44

for y in range(mh):
    for x in range(mw):
        # Normalized distance from center
        dx = (x - cx) / rx
        dy = (y - cy) / ry
        dist = (dx*dx + dy*dy)**0.5
        if dist < 0.65:
            alpha = 255
        elif dist < 1.0:
            alpha = int(255 * (1.0 - (dist - 0.65) / 0.35))
        else:
            alpha = 0
        mask.putpixel((x, y), alpha)

mask = mask.filter(ImageFilter.GaussianBlur(radius=8))

# Paste onto base texture
dest_x = 512 - target_w // 2
dest_y = 155
base_tex.paste(alec_resized, (dest_x, dest_y), mask)

# Save result texture
base_tex.save('m:/TDS/3D-face-reconstruction/alec_blended_texture.jpg', quality=90)
print("Saved alec_blended_texture.jpg successfully!")
