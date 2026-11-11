import math, random, subprocess, sys
BG="#f5f2ec"; INK="#4a4542"; LINE="#6e655e"; SUB="#7d746d"
BUN="#cfae8c"; BUN_D="#b48f6c"; MIST="#bccbd6"; WINE="#8e5f57"; STICK="#c4a07c"

def bun(cx, base, w, h, seed, cid):
    x0,x1=cx-w/2,cx+w/2; top=base-h
    d=(f"M{x0+6},{base} C{x0-6},{base-h*0.5} {cx-w*0.40},{top} {cx},{top} "
       f"C{cx+w*0.40},{top} {x1+6},{base-h*0.5} {x1-6},{base} Q{cx},{base+h*0.28} {x0+6},{base} Z")
    s=[f'<clipPath id="{cid}"><path d="{d}"/></clipPath>',
       f'<path d="{d}" fill="{BUN}" stroke="{LINE}" stroke-width="2.2"/>']
    # baked swirl seen from slightly above
    sx,sy=cx+w*0.02, top+h*0.36
    pts=[]
    for i in range(240):
        t=i/239; a=t*2.3*2*math.pi; r=5+t*w*0.40
        pts.append((sx+r*math.cos(a), sy+r*0.30*math.sin(a)))
    p="M"+" L".join(f"{x:.1f},{y:.1f}" for x,y in pts)
    s.append(f'<g clip-path="url(#{cid})"><path d="{p}" fill="none" stroke="{BUN_D}" stroke-width="5" stroke-linecap="round"/>'
             f'<path d="{p}" fill="none" stroke="{LINE}" stroke-width="1.4" transform="translate(0,3)" opacity="0.55"/></g>')
    # soft highlight
    s.append(f'<ellipse cx="{cx-w*0.18}" cy="{top+h*0.2}" rx="{w*0.12}" ry="{h*0.06}" fill="#fff" opacity="0.35" clip-path="url(#{cid})"/>')
    # pearl sugar only on the top surface
    rnd=random.Random(seed)
    for _ in range(22):
        a=rnd.uniform(0,2*math.pi); r=rnd.uniform(0,1)**0.6
        x=sx+r*w*0.34*math.cos(a); y=sy+r*w*0.34*0.30*math.sin(a)
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.3" fill="#fbfaf7" stroke="{LINE}" stroke-width="0.8"/>')
    return "\n".join(s)

def fika():
    s=[]
    cx=500; py=600  # plate surface centre
    s.append(f'<line x1="300" y1="664" x2="700" y2="664" stroke="{LINE}" stroke-width="1.6" opacity="0.6"/>')
    s.append(f'<ellipse cx="{cx}" cy="663" rx="170" ry="6" fill="#e6dfd6"/>')
    # plate: underside, rim, well
    s.append(f'<ellipse cx="{cx}" cy="{py+12}" rx="215" ry="50" fill="#e9e6e1" stroke="{LINE}" stroke-width="2"/>')
    s.append(f'<ellipse cx="{cx}" cy="{py}" rx="215" ry="50" fill="#fbfaf7" stroke="{LINE}" stroke-width="2.2"/>')
    s.append(f'<ellipse cx="{cx}" cy="{py+4}" rx="150" ry="32" fill="none" stroke="{MIST}" stroke-width="2.4"/>')
    # two cinnamon buns resting in the plate well (bases inside the well)
    s.append(f'<ellipse cx="452" cy="600" rx="78" ry="13" fill="#d9d2c8"/>')
    s.append(bun(452, 598, 160, 70, 1, "b1"))
    s.append(f'<ellipse cx="562" cy="622" rx="78" ry="13" fill="#d9d2c8"/>')
    s.append(bun(562, 620, 160, 70, 2, "b2"))
    return "\n".join(s)

def star(cx, cy, r, sy):
    pts=[]
    for i in range(16):
        a=i*math.pi/8 - math.pi/2; rr=r if i%2==0 else r*0.42
        pts.append(f"{cx+rr*math.cos(a):.1f},{cy+rr*sy*math.sin(a):.1f}")
    seeds="".join(f'<ellipse cx="{cx+r*0.62*math.cos(i*math.pi/4-math.pi/2):.1f}" cy="{cy+r*0.62*sy*math.sin(i*math.pi/4-math.pi/2):.1f}" rx="2.6" ry="{2.6*sy+0.6:.1f}" fill="{LINE}"/>' for i in range(8))
    return f'<polygon points="{" ".join(pts)}" fill="{STICK}" stroke="{LINE}" stroke-width="1.4"/>{seeds}<circle cx="{cx}" cy="{cy}" r="2.4" fill="{LINE}"/>'

def glogg():
    s=[]; cx=500
    top=505; bot=650; rx=84; ry=16
    s.append(f'<line x1="300" y1="688" x2="700" y2="688" stroke="{LINE}" stroke-width="1.6" opacity="0.6"/>')
    # saucer
    s.append(f'<ellipse cx="{cx}" cy="{bot+12}" rx="150" ry="24" fill="#e9e6e1" stroke="{LINE}" stroke-width="2"/>')
    s.append(f'<ellipse cx="{cx}" cy="{bot+4}" rx="150" ry="24" fill="#fbfaf7" stroke="{LINE}" stroke-width="2.2"/>')
    s.append(f'<ellipse cx="{cx}" cy="{bot+4}" rx="96" ry="14" fill="none" stroke="{MIST}" stroke-width="2"/>')
    # handle
    s.append(f'<path d="M{cx+rx-4},{top+28} C{cx+rx+56},{top+20} {cx+rx+60},{top+100} {cx+rx-6},{top+108}" fill="none" stroke="{LINE}" stroke-width="13" stroke-linecap="round"/>')
    s.append(f'<path d="M{cx+rx-4},{top+28} C{cx+rx+56},{top+20} {cx+rx+60},{top+100} {cx+rx-6},{top+108}" fill="none" stroke="#fbfaf7" stroke-width="8.5" stroke-linecap="round"/>')
    # body
    body=(f"M{cx-rx},{top} L{cx-rx+8},{bot-6} Q{cx},{bot+ry} {cx+rx-8},{bot-6} L{cx+rx},{top} Z")
    s.append(f'<path d="{body}" fill="#fbfaf7" stroke="{LINE}" stroke-width="2.2"/>')
    # nordic band following the curve
    b1,b2=top+56,top+76
    s.append(f'<path d="M{cx-rx+3.5},{b1} Q{cx},{b1+ry*1.6} {cx+rx-3.5},{b1} L{cx+rx-4.5},{b2} Q{cx},{b2+ry*1.6} {cx-rx+4.5},{b2} Z" fill="{MIST}" opacity="0.75"/>')
    for i in range(9):
        t=(i+0.5)/9; x=cx-rx+8+t*(2*rx-16); yc=b1+11+ry*1.6*2*t*(1-t)*0.95
        s.append(f'<path d="M{x-5},{yc-4} L{x},{yc+4} L{x+5},{yc-4}" fill="none" stroke="#f7f6f2" stroke-width="1.8"/>')
    # rim and glögg surface
    s.append(f'<ellipse cx="{cx}" cy="{top}" rx="{rx}" ry="{ry}" fill="#fbfaf7" stroke="{LINE}" stroke-width="2.2"/>')
    s.append(f'<ellipse cx="{cx}" cy="{top+3}" rx="{rx-9}" ry="{ry-5}" fill="{WINE}"/>')
    # star anise floating on the glögg
    s.append(star(cx-30, top+3, 22, 0.38))
    # cinnamon stick standing in the glögg, leaning on the back rim
    sx0,sy0=cx+22,top+4; sx1,sy1=cx+50,top-78
    ang=math.atan2(sy1-sy0,sx1-sx0); nx,ny=-math.sin(ang)*7,math.cos(ang)*7
    s.append(f'<polygon points="{sx0+nx},{sy0+ny} {sx1+nx},{sy1+ny} {sx1-nx},{sy1-ny} {sx0-nx},{sy0-ny}" fill="{STICK}" stroke="{LINE}" stroke-width="1.6"/>')
    s.append(f'<ellipse cx="{sx1}" cy="{sy1}" rx="7.4" ry="4" transform="rotate({math.degrees(ang)+90} {sx1} {sy1})" fill="#d4b796" stroke="{LINE}" stroke-width="1.4"/>')
    s.append(f'<line x1="{sx0+nx*0.2}" y1="{sy0+ny*0.2}" x2="{sx1+nx*0.2}" y2="{sy1+ny*0.2}" stroke="{LINE}" stroke-width="0.9" opacity="0.6"/>')
    # liquid line in front of the stick (stick goes into the drink)
    s.append(f'<path d="M{cx-rx+9},{top+3} A{rx-9},{ry-5} 0 0 0 {cx+rx-9},{top+3}" fill="none" stroke="{WINE}" stroke-width="3"/>')
    s.append(f'<path d="M{cx-rx},{top} A{rx},{ry} 0 0 0 {cx+rx},{top}" fill="none" stroke="{LINE}" stroke-width="2.2"/>')
    # steam
    for dx in (-30,0,30):
        s.append(f'<path d="M{cx+dx-14},{top-30} c-8,-12 8,-20 0,-32 c-8,-12 8,-20 0,-32" fill="none" stroke="{MIST}" stroke-width="2.6" stroke-linecap="round"/>')
    return "\n".join(s)

DESIGNS={"Glogg":("Glögg","in progress",glogg,1.36,688,760),"Fika":("Fika first,","presents later",fika,1.3,664,735)}

def svg(name, W, H):
    t1,t2,fn,sc,base,to=DESIGNS[name]
    h=1000*H/W
    oy=h*0.5-470  # block: titles ~ y 230-300, art ~ y 330-672
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 {h:.2f}" width="{W}" height="{H}">
<rect width="1000" height="{h:.2f}" fill="{BG}"/>
<g transform="translate(0,{oy:.2f})">
<text x="500" y="268" text-anchor="middle" font-family="Lora" font-size="86" fill="{INK}">{t1}</text>
<text x="500" y="326" text-anchor="middle" font-family="Lora" font-style="italic" font-size="38" fill="{SUB}">{t2}</text>
<g transform="translate(500,{to}) scale({sc}) translate(-500,-{base})">{fn()}</g>
</g></svg>'''

if __name__=="__main__":
    name,W,H,out=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),sys.argv[4]
    open(out+".svg","w").write(svg(name,W,H))
    subprocess.run(["rsvg-convert","-w",str(W),"-h",str(H),"-o",out+".png",out+".svg"],check=True)
