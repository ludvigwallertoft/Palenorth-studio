from PIL import Image, ImageDraw, ImageFont
import zipfile, os, subprocess
W="/home/claude/work/fika/"; P="/home/claude/palenorth-secrets/products/b-glogg-and-fika/"
specs=[("1_Ratio_2x3","Ratio_2x3_7200x10800px"),("2_Ratio_3x4","Ratio_3x4_5400x7200px"),("3_Ratio_4x5","Ratio_4x5_4800x6000px"),("4_Size_11x14","Size_11x14_3300x4200px"),("5_ISO_A_Sizes","ISO_A_Sizes_7016x9933px")]
os.makedirs(W+"zips",exist_ok=True)
for zname,suf in specs:
    zp=W+f"zips/Glogg_and_Fika_{zname}.zip"
    with zipfile.ZipFile(zp,"w",zipfile.ZIP_DEFLATED) as z:
        for n in ("Glogg","Fika"):
            jp=W+f"Glogg_and_Fika_{n}_{suf}_300dpi.jpg"
            Image.open(W+f"out_{n}_{suf}.png").convert("RGB").save(jp,quality=92,dpi=(300,300)); z.write(jp,os.path.basename(jp)); os.remove(jp)
for n,slug in (("Glogg","glogg"),("Fika","fika")):
    Image.open(W+f"out_{n}_Ratio_2x3_7200x10800px.png").convert("RGB").resize((1000,1500),Image.LANCZOS).save(f"/home/claude/palenorth-studio/art-previews/b-glogg-and-fika-{slug}.jpg",quality=92)
im=Image.open(P+"03_what_you_get.jpg").convert("RGB")
for n,x0 in (("Glogg",410),("Fika",1030)):
    im.paste(Image.open(W+f"out_{n}_Ratio_2x3_7200x10800px.png").convert("RGB").resize((560,840),Image.LANCZOS),(x0,435))
im.save(W+"03_what_you_get.jpg",quality=92)
im=Image.open(P+"04_detail.jpg").convert("RGB"); bg=im.getpixel((50,50))
g=Image.open(W+"out_Glogg_Ratio_2x3_7200x10800px.png").convert("RGB")
im.paste(g.crop((1800,4560,5400,8160)).resize((1500,1500),Image.LANCZOS),(250,191))
d=ImageDraw.Draw(im); d.rectangle([150,1700,1850,1900],fill=bg)
f=ImageFont.truetype("/home/claude/palenorth-studio/fonts/Lora-Italic-Variable.ttf",38)
t="Clean line work · close-up of the 24x36 in file"; w=d.textlength(t,font=f)
d.text(((2000-w)/2,1752),t,font=f,fill=(90,84,80)); im.save(W+"04_detail.jpg",quality=92)
for room,n,out in (("r08-12486417.jpg","Glogg","01_cover_room.jpg"),("r09-5978718.jpg","Fika","02_second_room.jpg")):
    subprocess.run(["python3","/home/claude/palenorth-studio/tools/compose.py","--room",room,"--art",W+f"out_{n}_Ratio_2x3_7200x10800px.png","--out",W+out,"--etsy"],check=True)
ims=[Image.open(W+f).resize((500,500)) for f in ('01_cover_room.jpg','02_second_room.jpg','03_what_you_get.jpg','04_detail.jpg')]
s=Image.new('RGB',(1000,1000))
for i,m in enumerate(ims): s.paste(m,((i%2)*500,(i//2)*500))
s.save(W+'review.jpg')
