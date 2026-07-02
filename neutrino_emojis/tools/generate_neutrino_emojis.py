#!/usr/bin/env python3
"""
Generate the Neutrino Emojis package.
Original deterministic SVG/PNG geometry. No third-party emoji artwork.
SPDX-License-Identifier: CC0-1.0
"""
from __future__ import annotations
import argparse, csv, hashlib, html, json, math, os, shutil, tarfile, zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

PKG = "neutrino_emojis"
CANVAS = 128
BASE_RENDER = 256
SCALE = BASE_RENDER // CANVAS
SIZES = [16, 32, 64, 128]

THEMES: Dict[str, Dict[str, str]] = {
    "classic_yellow": {"face":"#FFD85A","shadow":"#F4B94A","outline":"#3A2C20","feature":"#2D2118","accent":"#E94B66","accent2":"#FFFFFF","tear":"#5EC8FF","tongue":"#FF6B8A","blush":"#FF8C99","mask":"#EAF6F8","metal":"#8E9BAA","bg":"#FFFFFF"},
    "neutrino_blue": {"face":"#83D7FF","shadow":"#43A6E8","outline":"#13314A","feature":"#0B2032","accent":"#00E0FF","accent2":"#F4FEFF","tear":"#C9F6FF","tongue":"#FF7AA8","blush":"#74E6FF","mask":"#DFF8FF","metal":"#6D8FAA","bg":"#F6FBFF"},
    "graphite_dark": {"face":"#515E6B","shadow":"#303943","outline":"#E8EDF2","feature":"#F5F7FA","accent":"#9FD6FF","accent2":"#0D1218","tear":"#71C8FF","tongue":"#FF87A8","blush":"#B1A0FF","mask":"#DDE5EC","metal":"#B8C2CC","bg":"#151A20"},
    "forest_mint": {"face":"#A8F0BF","shadow":"#58C983","outline":"#163B24","feature":"#0F2A19","accent":"#1FCE7A","accent2":"#F7FFF8","tear":"#85DBFF","tongue":"#FF7E93","blush":"#72E0A0","mask":"#ECFFF3","metal":"#6C9C7C","bg":"#FAFFFB"},
    "royal_purple": {"face":"#C7A8FF","shadow":"#8B68D8","outline":"#2C1E4A","feature":"#211536","accent":"#FF72D2","accent2":"#FFF8FE","tear":"#93D9FF","tongue":"#FF6FB5","blush":"#FF9EE8","mask":"#F7EDFF","metal":"#A89DBB","bg":"#FCFAFF"},
    "solar_gold": {"face":"#FFC647","shadow":"#E88A24","outline":"#4B2A08","feature":"#2C1703","accent":"#FF6A00","accent2":"#FFF8E7","tear":"#59BFFF","tongue":"#FF4F7E","blush":"#FF9468","mask":"#FFF7E8","metal":"#AA8860","bg":"#FFFDF5"},
    "candy_pink": {"face":"#FFB7D5","shadow":"#F079B1","outline":"#5A1B37","feature":"#341020","accent":"#FF2E9E","accent2":"#FFF7FB","tear":"#6ACBFF","tongue":"#E92575","blush":"#FF6FBC","mask":"#FFF2F8","metal":"#BB8AA4","bg":"#FFF8FC"},
    "aqua_cyan": {"face":"#6FF2E5","shadow":"#27BFB6","outline":"#063E3D","feature":"#052928","accent":"#009DFF","accent2":"#F4FFFF","tear":"#B9F7FF","tongue":"#FF6F91","blush":"#5CCCE9","mask":"#E8FFFF","metal":"#5B9BA0","bg":"#F5FFFF"},
    "lava_orange": {"face":"#FF8759","shadow":"#D94B2E","outline":"#4A140A","feature":"#2D0B05","accent":"#FFD34D","accent2":"#FFF5ED","tear":"#4DBEFF","tongue":"#FF4078","blush":"#FFB36B","mask":"#FFF0E6","metal":"#A47C6A","bg":"#FFF8F3"},
    "mono_ink": {"face":"#F2F2F2","shadow":"#C7C7C7","outline":"#161616","feature":"#111111","accent":"#444444","accent2":"#FFFFFF","tear":"#A8A8A8","tongue":"#6A6A6A","blush":"#B8B8B8","mask":"#FAFAFA","metal":"#888888","bg":"#FFFFFF"},
}

BASES: List[Tuple[str, str, str, str, List[str]]] = [
    ("smiley","joy","dot","smile",["happy","smile"]),("smile","joy","soft","smile",["happy","friendly"]),("grin","joy","dot","grin",["teeth","happy"]),("wide_grin","joy","oval","wide_grin",["big","teeth"]),("beaming","joy","arc","wide_grin",["beaming","happy"]),
    ("laugh","joy","arc","laugh",["laugh","open-mouth"]),("rofl","joy","squint","laugh",["rolling","laugh"]),("joy_tears","joy","squint","laugh",["tears","laugh"]),("wink","joy","wink","smile",["wink","playful"]),("wink_tongue","playful","wink","tongue",["wink","tongue"]),
    ("tongue_out","playful","dot","tongue",["tongue","silly"]),("silly","playful","uneven","tongue",["silly","fun"]),("zany","playful","zany","tongue",["zany","wild"]),("blush","affection","arc","smile",["blush","warm"]),("shy","affection","downcast","small_smile",["shy","gentle"]),
    ("relieved","calm","closed","small_smile",["relieved","peaceful"]),("content","calm","closed","smile",["content","calm"]),("heart_eyes","affection","heart","smile",["love","heart"]),("star_eyes","affection","star","smile",["star","excited"]),("kiss","affection","soft","kiss",["kiss","love"]),
    ("kiss_wink","affection","wink","kiss",["kiss","wink"]),("cool","attitude","sunglasses","smirk",["cool","sunglasses"]),("nerd","attitude","glasses","grin",["nerd","glasses"]),("monocle","thought","monocle","flat",["monocle","inspect"]),("thinking","thought","raised","thinking",["thinking","hmm"]),
    ("confused","thought","uneven","confused",["confused","question"]),("raised_brow","thought","raised","flat",["skeptical","brow"]),("neutral","neutral","dot","flat",["neutral","plain"]),("expressionless","neutral","flat","flat",["expressionless","deadpan"]),("meh","neutral","half","meh",["meh","unimpressed"]),
    ("unamused","neutral","side","meh",["unamused","side-eye"]),("sad","sadness","downcast","frown",["sad","frown"]),("frown","sadness","dot","frown",["frown","unhappy"]),("cry","sadness","downcast","frown",["cry","tear"]),("sob","sadness","closed","open_frown",["sob","crying"]),
    ("worried","sadness","worried","small_frown",["worried","concern"]),("anxious_sweat","sadness","worried","flat",["anxious","sweat"]),("surprised","surprise","wide","small_o",["surprised","wow"]),("astonished","surprise","wide","open_o",["astonished","shock"]),("scream","surprise","wide","scream",["scream","fear"]),
    ("angry","anger","angry","frown",["angry","mad"]),("rage","anger","rage","open_frown",["rage","furious"]),("pouting","anger","angry","pout",["pout","annoyed"]),("sleepy","sleep","sleepy","small_smile",["sleepy","zzz"]),("yawn","sleep","closed","yawn",["yawn","tired"]),
    ("sick","health","sick","wavy",["sick","ill"]),("nauseated","health","nauseated","wavy",["nauseated","green"]),("dizzy","health","spiral","small_o",["dizzy","spiral"]),("party","fun","arc","laugh",["party","celebrate"]),("pleading","sadness","pleading","small_frown",["pleading","cute"]),
]
MODS: List[Tuple[str, str, List[str]]] = [
    ("plain","base expression only",[]),("soft_shadow","extra soft drop shadow",["depth"]),("sparkle","sparkle accent",["sparkle"]),("left_sweat","left-side sweat drop",["sweat"]),("right_tear","right-side tear drop",["tear"]),
    ("cheek_blush","cheek blush marks",["blush"]),("halo","halo ring",["angel"]),("tiny_horns","small horns",["mischief"]),("party_hat","party hat",["party"]),("sunglasses_badge","small sunglasses badge",["badge","cool"]),
    ("monocle_badge","small monocle badge",["badge","inspect"]),("medical_mask","medical mask overlay",["mask","health"]),("thermometer","thermometer accent",["fever"]),("headphones","headphones overlay",["audio"]),("crown","small crown",["royal"]),
    ("cap","baseball cap",["cap"]),("heart_badge","small heart badge",["love","badge"]),("question_badge","question badge",["question","badge"]),("exclamation_badge","exclamation badge",["alert","badge"]),("neutrino_orbit","Neutrino orbit mark",["neutrino","orbit"]),
]

@dataclass(frozen=True)
class Spec:
    index:int; uid:str; name:str; base:str; modifier:str; category:str; eye:str; mouth:str; description:str; tags:List[str]

def build_specs(limit: Optional[int]=None)->List[Spec]:
    out=[]; i=0
    for base,cat,eye,mouth,tags in BASES:
        for mod,desc,mtags in MODS:
            i+=1
            name=f"{base}_{mod}".lower()
            out.append(Spec(i, f"NE{i:04d}", name, base, mod, cat, eye, mouth, f"Original Neutrino emoji: {base.replace('_',' ')} with {desc}.", list(dict.fromkeys([cat]+tags+mtags))))
            if limit and len(out)>=limit: return out
    return out

def rgba(h:str,a:int=255):
    h=h.lstrip('#'); return (int(h[:2],16),int(h[2:4],16),int(h[4:6],16),a)
def sc(v:float)->int: return int(round(v*SCALE))
def box(b): return tuple(sc(x) for x in b)
def pts(ps): return [(sc(x),sc(y)) for x,y in ps]

def ellipse(d,b,fill,outline=None,width=1): d.ellipse(box(b), fill=rgba(fill) if isinstance(fill,str) else fill, outline=rgba(outline) if outline else None, width=sc(width) if outline else 1)
def rect(d,b,fill,outline=None,width=1,r=0):
    if r: d.rounded_rectangle(box(b), radius=sc(r), fill=rgba(fill), outline=rgba(outline) if outline else None, width=sc(width) if outline else 1)
    else: d.rectangle(box(b), fill=rgba(fill), outline=rgba(outline) if outline else None, width=sc(width) if outline else 1)
def line(d,ps,fill,width=4): d.line(pts(ps), fill=rgba(fill), width=sc(width), joint="curve")
def arc(d,b,start,end,fill,width=4): d.arc(box(b), start=start, end=end, fill=rgba(fill), width=sc(width))
def poly(d,ps,fill,outline=None,width=1):
    ps=list(ps); d.polygon(pts(ps), fill=rgba(fill));
    if outline: d.line(pts(ps+[ps[0]]), fill=rgba(outline), width=sc(width), joint="curve")

def heart(cx,cy,s):
    a=[]
    for i in range(36):
        t=2*math.pi*i/36; x=16*math.sin(t)**3; y=-(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t)); a.append((cx+x*s/32,cy+y*s/32))
    return a
def star(cx,cy,r1,r2,n=5,rot=-90): return [(cx+(r1 if i%2==0 else r2)*math.cos(math.radians(rot+i*180/n)), cy+(r1 if i%2==0 else r2)*math.sin(math.radians(rot+i*180/n))) for i in range(n*2)]
def drop(cx,cy,s): return [(cx,cy-s),(cx+s*.7,cy-s*.1),(cx+s*.38,cy+s*.75),(cx,cy+s),(cx-s*.38,cy+s*.75),(cx-s*.7,cy-s*.1)]

def get_font(sz:int):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]:
        if os.path.exists(p): return ImageFont.truetype(p, sz*SCALE)
    return ImageFont.load_default()
def center_text(d,txt,cx,cy,sz,fill):
    f=get_font(sz); bb=d.textbbox((0,0),txt,font=f); d.text((sc(cx)-(bb[2]-bb[0])//2, sc(cy)-(bb[3]-bb[1])//2-sc(1)), txt, fill=rgba(fill), font=f)

def draw_pre(d,mod,th):
    c=th['outline']; a=th['accent']
    if mod=='halo': ellipse(d,(37,2,91,17),a,c,3); ellipse(d,(42,5,86,14),th['bg'])
    elif mod=='tiny_horns': poly(d,[(27,23),(38,3),(47,31)],a,c,3); poly(d,[(81,31),(90,3),(101,23)],a,c,3)
    elif mod=='party_hat': poly(d,[(70,19),(101,0),(104,41)],a,c,3); line(d,[(76,16),(100,32)],th['accent2'],3); poly(d,star(101,0,6,3),th['accent2'],c,1.5)
    elif mod=='crown': poly(d,[(36,22),(45,5),(58,22),(64,5),(72,22),(84,5),(93,22),(91,38),(38,38)],'#FFD34D',c,3); ellipse(d,(60,11,68,19),a)
    elif mod=='cap': rect(d,(28,17,90,40),a,c,3,12); poly(d,[(76,33),(112,34),(84,45)],a,c,3); line(d,[(37,28),(80,28)],th['accent2'],2)

def draw_face(d,th,soft_shadow=False, sick_green=False):
    if soft_shadow: ellipse(d,(17,18,116,119),(0,0,0,70))
    ellipse(d,(14,13,114,116), th['shadow'])
    ellipse(d,(10,8,118,116), '#98D45F' if sick_green else th['face'], th['outline'],5)
    # small specular mark kept subtle and consistent
    ellipse(d,(28,19,63,35), th['accent2'])

def draw_eyes(d,s:Spec,th):
    c=th['feature']; e=s.eye
    if e in ('angry','rage'): line(d,[(35,41),(53,49)],c,4); line(d,[(75,49),(93,41)],c,4)
    if e in ('worried','pleading'): line(d,[(34,43),(52,37)],c,3); line(d,[(76,37),(94,43)],c,3)
    if e=='raised': line(d,[(34,38),(52,34)],c,3); line(d,[(76,44),(94,44)],c,3)
    if e in ('dot','soft','raised','worried','angry','rage','nauseated','sick'):
        ellipse(d,(35,45,48,58),c); ellipse(d,(80,45,93,58),c)
        if e=='sick': rect(d,(28,26,100,35),th['accent'],th['outline'],2,7)
    elif e=='oval': ellipse(d,(34,43,49,61),c); ellipse(d,(79,43,94,61),c)
    elif e in ('arc','closed'): arc(d,(31,41,53,62),200,340,c,5); arc(d,(75,41,97,62),200,340,c,5)
    elif e=='squint': line(d,[(33,47),(48,58),(54,47)],c,4); line(d,[(75,47),(84,58),(97,47)],c,4)
    elif e=='wink': arc(d,(30,43,54,62),200,340,c,5); ellipse(d,(80,45,93,58),c)
    elif e=='uneven': ellipse(d,(35,45,48,58),c); arc(d,(75,43,98,62),200,340,c,4)
    elif e=='zany': ellipse(d,(31,41,52,62),th['accent2'],c,3); ellipse(d,(39,49,47,57),c); ellipse(d,(77,43,97,63),th['accent2'],c,3); ellipse(d,(79,45,87,53),c)
    elif e=='downcast': arc(d,(31,47,55,66),200,340,c,4); arc(d,(73,47,97,66),200,340,c,4)
    elif e=='heart': poly(d,heart(42,52,22),'#F54767',th['outline'],2); poly(d,heart(86,52,22),'#F54767',th['outline'],2)
    elif e=='star': poly(d,star(42,52,12,5),'#FFE35C',th['outline'],2); poly(d,star(86,52,12,5),'#FFE35C',th['outline'],2)
    elif e=='sunglasses': rect(d,(29,41,56,58),'#111111',th['outline'],3,5); rect(d,(72,41,99,58),'#111111',th['outline'],3,5); line(d,[(56,49),(72,49)],th['outline'],3); line(d,[(34,45),(50,45)],'#FFFFFF',2); line(d,[(77,45),(93,45)],'#FFFFFF',2)
    elif e=='glasses': ellipse(d,(29,40,58,66),th['accent2'],c,4); ellipse(d,(70,40,99,66),th['accent2'],c,4); line(d,[(58,53),(70,53)],c,3); ellipse(d,(40,50,47,57),c); ellipse(d,(81,50,88,57),c)
    elif e=='monocle': ellipse(d,(34,45,47,58),c); ellipse(d,(70,36,101,67),th['accent2'],c,4); ellipse(d,(82,49,90,57),c); line(d,[(95,63),(105,76)],c,3)
    elif e=='flat': line(d,[(33,52),(52,52)],c,4); line(d,[(76,52),(95,52)],c,4)
    elif e=='half': arc(d,(31,43,55,62),0,180,c,4); arc(d,(73,43,97,62),0,180,c,4)
    elif e=='side': ellipse(d,(33,45,52,60),th['accent2'],c,3); ellipse(d,(75,45,94,60),th['accent2'],c,3); ellipse(d,(35,50,43,58),c); ellipse(d,(77,50,85,58),c)
    elif e=='wide': ellipse(d,(31,39,55,63),th['accent2'],c,4); ellipse(d,(73,39,97,63),th['accent2'],c,4); ellipse(d,(40,48,48,56),c); ellipse(d,(82,48,90,56),c)
    elif e=='sleepy': arc(d,(30,45,55,63),200,340,c,4); arc(d,(73,45,98,63),200,340,c,4); center_text(d,'Z',96,30,12,th['accent']); center_text(d,'z',106,18,9,th['accent'])
    elif e=='spiral':
        for cx in [42,86]:
            ps=[]
            for i in range(26):
                a=i*.75; r=1+i*.35; ps.append((cx+math.cos(a)*r,52+math.sin(a)*r))
            line(d,ps,c,3)
    elif e=='pleading': ellipse(d,(29,37,57,68),th['accent2'],c,4); ellipse(d,(71,37,99,68),th['accent2'],c,4); ellipse(d,(39,51,47,61),c); ellipse(d,(81,51,89,61),c); ellipse(d,(36,44,41,49),'#FFFFFF'); ellipse(d,(78,44,83,49),'#FFFFFF')
    else: ellipse(d,(35,45,48,58),c); ellipse(d,(80,45,93,58),c)

def draw_mouth(d,s:Spec,th):
    c=th['feature']; m=s.mouth
    if m=='smile': arc(d,(36,58,92,101),20,160,c,5)
    elif m=='small_smile': arc(d,(46,64,82,92),20,160,c,4)
    elif m=='smirk': arc(d,(45,65,92,93),20,150,c,4)
    elif m=='grin': rect(d,(39,68,89,91),'#FFFFFF',c,4,9); line(d,[(39,79),(89,79)],c,2)
    elif m=='wide_grin': rect(d,(32,66,96,96),'#FFFFFF',c,4,10); line(d,[(34,81),(94,81)],c,2); line(d,[(50,67),(50,95)],c,1.5); line(d,[(78,67),(78,95)],c,1.5)
    elif m=='laugh': ellipse(d,(36,63,92,104),c); rect(d,(41,65,87,77),'#FFFFFF',None,1,4); ellipse(d,(46,85,82,106),th['tongue'])
    elif m=='tongue': ellipse(d,(41,66,87,101),c); rect(d,(45,66,83,76),'#FFFFFF',None,1,4); ellipse(d,(52,80,76,108),th['tongue'],c,2); line(d,[(64,82),(64,102)],'#D84363',2)
    elif m=='kiss': ellipse(d,(56,70,72,86),c); ellipse(d,(45,63,57,75),th['accent'])
    elif m=='flat': line(d,[(47,78),(81,78)],c,5)
    elif m=='thinking': arc(d,(48,70,86,95),190,330,c,4); ellipse(d,(87,85,98,96),c)
    elif m=='confused': line(d,[(45,80),(57,75),(70,82),(84,76)],c,4)
    elif m=='meh': line(d,[(47,81),(83,76)],c,4)
    elif m=='frown': arc(d,(39,76,89,108),200,340,c,5)
    elif m=='small_frown': arc(d,(47,78,81,98),200,340,c,4)
    elif m=='open_frown': ellipse(d,(45,72,83,100),c); ellipse(d,(53,82,75,101),th['tongue'])
    elif m=='small_o': ellipse(d,(55,70,73,88),c)
    elif m=='open_o': ellipse(d,(49,66,79,98),c); ellipse(d,(57,75,71,89),th['face'])
    elif m=='scream': ellipse(d,(48,64,80,108),c)
    elif m=='pout': ellipse(d,(50,74,78,91),c)
    elif m=='yawn': ellipse(d,(43,65,85,104),c); ellipse(d,(53,76,75,96),th['shadow'])
    elif m=='wavy': line(d,[(42,82),(50,76),(58,82),(66,76),(74,82),(84,76)],c,4)
    else: arc(d,(36,58,92,101),20,160,c,5)

def draw_post(d,s:Spec,th):
    mod=s.modifier; c=th['outline']; a=th['accent']; feat=th['feature']
    if s.base=='joy_tears': poly(d,drop(29,67,9),th['tear'],c,1.5); poly(d,drop(99,67,9),th['tear'],c,1.5)
    elif s.base=='cry': poly(d,drop(94,70,11),th['tear'],c,1.5)
    elif s.base=='sob': line(d,[(36,58),(36,82)],th['tear'],5); line(d,[(90,58),(90,82)],th['tear'],5)
    elif s.base=='anxious_sweat': poly(d,drop(94,33,10),th['tear'],c,1.5)
    elif s.base in ('blush','shy','pleading') and mod!='cheek_blush': ellipse(d,(23,66,42,77),th['blush']); ellipse(d,(86,66,105,77),th['blush'])
    if mod=='sparkle': poly(d,star(102,27,12,5),a,c,2); poly(d,star(24,92,7,3),a,c,1.5)
    elif mod=='left_sweat': poly(d,drop(27,39,12),th['tear'],c,1.5)
    elif mod=='right_tear': poly(d,drop(93,69,14),th['tear'],c,1.5)
    elif mod=='cheek_blush': ellipse(d,(23,66,43,78),th['blush']); ellipse(d,(85,66,105,78),th['blush'])
    elif mod=='sunglasses_badge': ellipse(d,(90,88,124,122),a,c,3); rect(d,(96,100,107,108),'#111111',None,1,2); rect(d,(110,100,121,108),'#111111',None,1,2); line(d,[(107,104),(110,104)],'#111111',2)
    elif mod=='monocle_badge': ellipse(d,(90,88,124,122),th['accent2'],c,3); ellipse(d,(99,96,116,113),th['accent2'],feat,3); line(d,[(114,111),(121,118)],feat,2)
    elif mod=='medical_mask': rect(d,(29,65,99,97),th['mask'],c,3,9); line(d,[(34,73),(94,73)],th['metal'],2); line(d,[(35,84),(93,84)],th['metal'],2); line(d,[(28,75),(16,68)],c,2); line(d,[(100,75),(112,68)],c,2)
    elif mod=='thermometer': line(d,[(93,63),(108,93)],c,8); line(d,[(93,63),(108,93)],th['accent2'],5); ellipse(d,(101,88,119,106),a,c,3); line(d,[(97,70),(102,69)],c,2)
    elif mod=='headphones': arc(d,(25,23,103,94),190,350,c,5); rect(d,(17,56,32,84),c,None,1,6); rect(d,(96,56,111,84),c,None,1,6); rect(d,(20,60,30,80),a,None,1,5); rect(d,(98,60,108,80),a,None,1,5)
    elif mod=='heart_badge': ellipse(d,(90,88,124,122),th['accent2'],c,3); poly(d,heart(107,106,21),'#F54767')
    elif mod=='question_badge': ellipse(d,(90,88,124,122),a,c,3); center_text(d,'?',107,104,22,th['accent2'])
    elif mod=='exclamation_badge': ellipse(d,(90,88,124,122),a,c,3); line(d,[(107,96),(107,108)],th['accent2'],5); ellipse(d,(104,112,110,118),th['accent2'])
    elif mod=='neutrino_orbit': arc(d,(15,31,113,97),315,140,a,3); arc(d,(15,31,113,97),135,320,a,3); ellipse(d,(94,32,104,42),th['accent2'],c,2)

def render(spec:Spec, th:Dict[str,str], size:int)->Image.Image:
    img=Image.new('RGBA',(BASE_RENDER,BASE_RENDER),(0,0,0,0)); d=ImageDraw.Draw(img)
    draw_pre(d,spec.modifier,th)
    draw_face(d, th, spec.modifier=='soft_shadow', spec.base in ('nauseated',))
    draw_eyes(d,spec,th); draw_mouth(d,spec,th); draw_post(d,spec,th)
    if size!=BASE_RENDER: img=img.resize((size,size), Image.Resampling.LANCZOS)
    return img

class SVG:
    def __init__(self): self.p=[]
    def add(self,x): self.p.append(x)
    def ellipse(self,cx,cy,rx,ry,fill,stroke=None,sw=1,op=None): self.add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '')+(f' opacity="{op}"' if op is not None else '')+'/>' )
    def circle(self,cx,cy,r,fill,stroke=None,sw=1,op=None): self.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '')+(f' opacity="{op}"' if op is not None else '')+'/>' )
    def rect(self,x,y,w,h,fill,stroke=None,sw=1,rx=0): self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"'+(f' rx="{rx}" ry="{rx}"' if rx else '')+(f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '')+'/>' )
    def line(self,ps,stroke,sw=4):
        if len(ps)==2: self.add(f'<line x1="{ps[0][0]}" y1="{ps[0][1]}" x2="{ps[1][0]}" y2="{ps[1][1]}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"/>')
        else: self.add(f'<polyline points="{' '.join(f'{round(x,2)},{round(y,2)}' for x,y in ps)}" fill="none" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')
    def poly(self,ps,fill,stroke=None,sw=1): self.add(f'<polygon points="{' '.join(f'{round(x,2)},{round(y,2)}' for x,y in ps)}" fill="{fill}"'+(f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"' if stroke else '')+'/>' )
    def path(self,d,stroke,sw=4,fill='none'): self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')
    def text(self,t,x,y,sz,fill): self.add(f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{sz}" font-weight="700" text-anchor="middle" dominant-baseline="central" fill="{fill}">{html.escape(t)}</text>')
    def xml(self,title,desc): return f'<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128" role="img" aria-labelledby="title desc">\n<title id="title">{html.escape(title)}</title>\n<desc id="desc">{html.escape(desc)}</desc>\n'+'\n'.join(self.p)+'\n</svg>\n'

def svgarc(s,x1,y1,cx,cy,x2,y2,stroke,sw=4): s.path(f'M {x1} {y1} Q {cx} {cy} {x2} {y2}',stroke,sw)

def svg_icon(sp:Spec, th:Dict[str,str])->str:
    s=SVG(); c=th['feature']; o=th['outline']; a=th['accent']
    if sp.modifier=='soft_shadow': s.ellipse(67,69,49,50,'#000000',op=.22)
    # draw simple pre-mods for vector masters
    if sp.modifier=='halo': s.ellipse(64,9,27,7,a,o,3); s.ellipse(64,9,22,4,th['bg'])
    elif sp.modifier=='tiny_horns': s.poly([(27,23),(38,3),(47,31)],a,o,3); s.poly([(81,31),(90,3),(101,23)],a,o,3)
    elif sp.modifier=='party_hat': s.poly([(70,19),(101,0),(104,41)],a,o,3); s.line([(76,16),(100,32)],th['accent2'],3)
    elif sp.modifier=='crown': s.poly([(36,22),(45,5),(58,22),(64,5),(72,22),(84,5),(93,22),(91,38),(38,38)],'#FFD34D',o,3)
    elif sp.modifier=='cap': s.rect(28,17,62,23,a,o,3,12); s.poly([(76,33),(112,34),(84,45)],a,o,3)
    s.ellipse(64,65,50,52,th['shadow']); s.ellipse(64,62,54,54,'#98D45F' if sp.base=='nauseated' else th['face'],o,5); s.ellipse(45.5,27,17.5,8,th['accent2'],op=.45)
    # eyes: simplified but editable
    e=sp.eye
    if e in ('dot','soft','raised','worried','angry','rage','sick','nauseated'): s.circle(41.5,51.5,6.5,c); s.circle(86.5,51.5,6.5,c)
    elif e=='oval': s.ellipse(41.5,52,7.5,9,c); s.ellipse(86.5,52,7.5,9,c)
    elif e in ('arc','closed','sleepy'): svgarc(s,33,52,42,61,53,52,c,5); svgarc(s,75,52,86,61,97,52,c,5); (s.text('Z',96,30,12,a) if e=='sleepy' else None)
    elif e=='squint': s.line([(33,47),(48,58),(54,47)],c,4); s.line([(75,47),(84,58),(97,47)],c,4)
    elif e=='wink': svgarc(s,32,53,42,61,54,53,c,5); s.circle(86.5,51.5,6.5,c)
    elif e in ('uneven',): s.circle(41.5,51.5,6.5,c); svgarc(s,77,53,86,61,98,53,c,4)
    elif e=='zany': s.circle(42,52,11,th['accent2'],c,3); s.circle(84,53,10,th['accent2'],c,3); s.circle(43,53,4,c); s.circle(83,49,4,c)
    elif e=='downcast': svgarc(s,33,58,42,66,54,58,c,4); svgarc(s,75,58,86,66,97,58,c,4)
    elif e=='heart': s.poly(heart(42,52,22),'#F54767',o,2); s.poly(heart(86,52,22),'#F54767',o,2)
    elif e=='star': s.poly(star(42,52,12,5),'#FFE35C',o,2); s.poly(star(86,52,12,5),'#FFE35C',o,2)
    elif e=='sunglasses': s.rect(29,41,27,17,'#111111',o,3,5); s.rect(72,41,27,17,'#111111',o,3,5); s.line([(56,49),(72,49)],o,3)
    elif e=='glasses': s.ellipse(43.5,53,14.5,13,th['accent2'],c,4); s.ellipse(84.5,53,14.5,13,th['accent2'],c,4); s.line([(58,53),(70,53)],c,3); s.circle(43.5,53.5,3.5,c); s.circle(84.5,53.5,3.5,c)
    elif e=='monocle': s.circle(41,51.5,6.5,c); s.ellipse(85.5,51.5,15.5,15.5,th['accent2'],c,4); s.circle(86,53,4,c); s.line([(95,63),(105,76)],c,3)
    elif e=='flat': s.line([(33,52),(52,52)],c,4); s.line([(76,52),(95,52)],c,4)
    elif e=='half': s.line([(33,50),(52,50)],c,4); s.line([(76,50),(95,50)],c,4)
    elif e=='side': s.ellipse(42.5,52.5,9.5,7.5,th['accent2'],c,3); s.ellipse(84.5,52.5,9.5,7.5,th['accent2'],c,3); s.circle(39,54,4,c); s.circle(81,54,4,c)
    elif e=='wide': s.circle(43,51,12,th['accent2'],c,4); s.circle(85,51,12,th['accent2'],c,4); s.circle(44,52,4,c); s.circle(86,52,4,c)
    elif e=='spiral':
        for cx in [42,86]: s.line([(round(cx+math.cos(i*.75)*(1+i*.35),1), round(52+math.sin(i*.75)*(1+i*.35),1)) for i in range(26)],c,3)
    elif e=='pleading': s.ellipse(43,52.5,14,15.5,th['accent2'],c,4); s.ellipse(85,52.5,14,15.5,th['accent2'],c,4); s.circle(43,56,4,c); s.circle(85,56,4,c)
    # mouth
    m=sp.mouth
    if m=='smile': svgarc(s,38,76,64,101,90,76,c,5)
    elif m=='small_smile': svgarc(s,48,77,64,92,80,77,c,4)
    elif m=='smirk': svgarc(s,47,79,67,92,91,76,c,4)
    elif m=='grin': s.rect(39,68,50,23,'#FFFFFF',c,4,9); s.line([(39,79),(89,79)],c,2)
    elif m=='wide_grin': s.rect(32,66,64,30,'#FFFFFF',c,4,10); s.line([(34,81),(94,81)],c,2); s.line([(50,67),(50,95)],c,1.5); s.line([(78,67),(78,95)],c,1.5)
    elif m=='laugh': s.ellipse(64,83.5,28,20.5,c); s.rect(41,65,46,12,'#FFFFFF',rx=4); s.ellipse(64,95,18,10,th['tongue'])
    elif m=='tongue': s.ellipse(64,83.5,23,17.5,c); s.rect(45,66,38,10,'#FFFFFF',rx=4); s.ellipse(64,94,12,14,th['tongue'],c,2)
    elif m=='kiss': s.circle(64,78,8,c); s.circle(51,69,6,a)
    elif m=='flat': s.line([(47,78),(81,78)],c,5)
    elif m=='thinking': svgarc(s,50,81,65,94,85,82,c,4); s.circle(92,91,5,c)
    elif m=='confused': s.line([(45,80),(57,75),(70,82),(84,76)],c,4)
    elif m=='meh': s.line([(47,81),(83,76)],c,4)
    elif m=='frown': svgarc(s,40,91,64,71,88,91,c,5)
    elif m=='small_frown': svgarc(s,48,91,64,77,80,91,c,4)
    elif m=='open_frown': s.ellipse(64,86,19,14,c); s.ellipse(64,91,11,9,th['tongue'])
    elif m=='small_o': s.circle(64,79,9,c)
    elif m=='open_o': s.circle(64,82,16,c); s.circle(64,82,7,th['face'])
    elif m=='scream': s.ellipse(64,86,16,22,c)
    elif m=='pout': s.ellipse(64,82.5,14,8.5,c)
    elif m=='yawn': s.ellipse(64,84.5,21,19.5,c); s.ellipse(64,86,11,10,th['shadow'])
    elif m=='wavy': s.line([(42,82),(50,76),(58,82),(66,76),(74,82),(84,76)],c,4)
    # simplified base tears and post modifiers
    if sp.base=='joy_tears': s.poly(drop(29,67,9),th['tear'],o,1.5); s.poly(drop(99,67,9),th['tear'],o,1.5)
    elif sp.base=='cry': s.poly(drop(94,70,11),th['tear'],o,1.5)
    elif sp.base=='sob': s.line([(36,58),(36,82)],th['tear'],5); s.line([(90,58),(90,82)],th['tear'],5)
    if sp.modifier=='sparkle': s.poly(star(102,27,12,5),a,o,2); s.poly(star(24,92,7,3),a,o,1.5)
    elif sp.modifier=='left_sweat': s.poly(drop(27,39,12),th['tear'],o,1.5)
    elif sp.modifier=='right_tear': s.poly(drop(93,69,14),th['tear'],o,1.5)
    elif sp.modifier=='cheek_blush': s.ellipse(33,72,10,6,th['blush']); s.ellipse(95,72,10,6,th['blush'])
    elif sp.modifier=='medical_mask': s.rect(29,65,70,32,th['mask'],o,3,9); s.line([(34,73),(94,73)],th['metal'],2); s.line([(35,84),(93,84)],th['metal'],2)
    elif sp.modifier=='heart_badge': s.circle(107,105,17,th['accent2'],o,3); s.poly(heart(107,106,21),'#F54767')
    elif sp.modifier=='question_badge': s.circle(107,105,17,a,o,3); s.text('?',107,104,22,th['accent2'])
    elif sp.modifier=='exclamation_badge': s.circle(107,105,17,a,o,3); s.line([(107,96),(107,108)],th['accent2'],5); s.circle(107,115,3,th['accent2'])
    elif sp.modifier=='neutrino_orbit': s.path('M 18 74 C 38 31 95 25 111 54',a,3); s.path('M 17 57 C 45 100 93 104 111 73',a,3); s.circle(99,37,5,th['accent2'],o,2)
    elif sp.modifier=='thermometer': s.line([(93,63),(108,93)],o,8); s.line([(93,63),(108,93)],th['accent2'],5); s.circle(110,97,9,a,o,3)
    elif sp.modifier=='headphones': s.path('M 27 64 C 28 25 100 25 101 64',o,5); s.rect(17,56,15,28,o,rx=6); s.rect(96,56,15,28,o,rx=6)
    elif sp.modifier=='sunglasses_badge': s.circle(107,105,17,a,o,3); s.rect(96,100,11,8,'#111111',rx=2); s.rect(110,100,11,8,'#111111',rx=2)
    elif sp.modifier=='monocle_badge': s.circle(107,105,17,th['accent2'],o,3); s.circle(107,105,8,th['accent2'],c,3)
    return s.xml(sp.name,sp.description)

def write(p:Path,txt:str): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(txt,encoding='utf-8')
def sha(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def write_docs(root:Path,specs:List[Spec]):
    write(root/'LICENSE.md',"""# License\n\nNeutrino Emojis is released under a CC0-1.0-style public-domain dedication.\n\nTo the extent possible under law, the generator author dedicates all copyright and neighboring rights in the original generated artwork, manifests, previews, and generator code in this package to the public domain worldwide.\n\nYou may copy, modify, distribute, and use these files, including for commercial purposes, without asking permission.\n\nNo third-party emoji artwork is included. The package is provided as-is, without warranty of any kind. This file is not legal advice.\n""")
    write(root/'NOTICE.md',"""# Notice\n\nPackage: neutrino_emojis\nPurpose: Original emoji icon pack for the Neutrino Project.\n\nNo third-party emoji artwork was imported, copied, traced, or embedded. The icons are generated from deterministic geometric primitives in `tools/generate_neutrino_emojis.py`. Fonts are not bundled.\n""")
    write(root/'README.md',f"""# Neutrino Emojis\n\n`neutrino_emojis` is an original, normalized emoji icon pack for the Neutrino Project.\n\nIt contains {len(specs)} generated emoji-style icons, {len(THEMES)} color themes, and PNG exports in {', '.join(map(str,SIZES))} pixel sizes. Artwork is generated from original vector geometry rather than copied from third-party emoji projects.\n\n## Contents\n\n- {len(specs)} master SVG files in `svg/master/`\n- {len(specs)*len(THEMES)} themed SVG files in `svg/<theme>/`\n- {len(specs)*len(THEMES)*len(SIZES)} PNG files in `png/<theme>/<size>/`\n- `manifest.json` and `manifest.csv`\n- `include/neutrino_emojis.h`\n- `preview/index.html` and contact sheets\n- `tools/generate_neutrino_emojis.py`\n\n## Themes\n\n{chr(10).join('- `'+t+'`' for t in THEMES)}\n\n## Regenerate\n\n```bash\npython3 tools/generate_neutrino_emojis.py --out /path/to/neutrino_emojis --clean\n```\n\n## Layout\n\n```text\nneutrino_emojis/\n  LICENSE.md\n  NOTICE.md\n  README.md\n  themes.json\n  manifest.json\n  manifest.csv\n  generation_report.json\n  include/neutrino_emojis.h\n  svg/master/\n  svg/<theme>/\n  png/<theme>/16/\n  png/<theme>/32/\n  png/<theme>/64/\n  png/<theme>/128/\n  preview/\n  tools/\n```\n""")
    write(root/'themes.json',json.dumps(THEMES,indent=2))
    names=',\n'.join(f'    "{x.name}"' for x in specs); cats=',\n'.join(f'    "{x.category}"' for x in specs); themes=',\n'.join(f'    "{x}"' for x in THEMES)
    write(root/'include'/'neutrino_emojis.h',f"""/* Neutrino Emojis registry - SPDX-License-Identifier: CC0-1.0 */\n#ifndef NEUTRINO_EMOJIS_H\n#define NEUTRINO_EMOJIS_H\n#ifdef __cplusplus\nextern \"C\" {{\n#endif\n#define NEUTRINO_EMOJI_COUNT {len(specs)}\n#define NEUTRINO_EMOJI_THEME_COUNT {len(THEMES)}\n#define NEUTRINO_EMOJI_SIZE_COUNT {len(SIZES)}\nstatic const int NEUTRINO_EMOJI_SIZES[NEUTRINO_EMOJI_SIZE_COUNT] = {{{', '.join(map(str,SIZES))}}};\nstatic const char* const NEUTRINO_EMOJI_THEMES[NEUTRINO_EMOJI_THEME_COUNT] = {{\n{themes}\n}};\nstatic const char* const NEUTRINO_EMOJI_NAMES[NEUTRINO_EMOJI_COUNT] = {{\n{names}\n}};\nstatic const char* const NEUTRINO_EMOJI_CATEGORIES[NEUTRINO_EMOJI_COUNT] = {{\n{cats}\n}};\n#ifdef __cplusplus\n}}\n#endif\n#endif\n""")

def write_manifest(root:Path,specs:List[Spec]):
    rows=[]
    for s in specs:
        rows.append({"index":s.index,"uid":s.uid,"name":s.name,"category":s.category,"base":s.base,"modifier":s.modifier,"description":s.description,"tags":s.tags,"svg_master":f"svg/master/{s.name}.svg","svg_themed_pattern":f"svg/{{theme}}/{s.name}.svg","png_pattern":f"png/{{theme}}/{{size}}/{s.name}.png","sizes":SIZES,"themes":list(THEMES.keys())})
    write(root/'manifest.json',json.dumps(rows,indent=2))
    with (root/'manifest.csv').open('w',encoding='utf-8',newline='') as f:
        fields=list(rows[0].keys()); w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows:
            rr=dict(r); rr['tags']='|'.join(rr['tags']); rr['sizes']='|'.join(map(str,rr['sizes'])); rr['themes']='|'.join(rr['themes']); w.writerow(rr)

def copy_generator(root:Path):
    src=Path(__file__).resolve(); dst=root/'tools'/'generate_neutrino_emojis.py'; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst); dst.chmod(0o755)

def generate(root:Path,specs:List[Spec],no_png=False):
    mt=THEMES['classic_yellow']
    for sp in specs: write(root/'svg'/'master'/f'{sp.name}.svg', svg_icon(sp,mt))
    for tn,th in THEMES.items():
        tdir=root/'svg'/tn; tdir.mkdir(parents=True,exist_ok=True)
        for sp in specs: write(tdir/f'{sp.name}.svg', svg_icon(sp,th))
    if no_png: return
    for tn,th in THEMES.items():
        print(f'Rendering PNG theme {tn} ({len(specs)} icons x {len(SIZES)} sizes)...', flush=True)
        for z in SIZES: (root/'png'/tn/str(z)).mkdir(parents=True,exist_ok=True)
        for sp in specs:
            base=render(sp,th,BASE_RENDER)
            for z in SIZES:
                im=base.resize((z,z), Image.Resampling.LANCZOS)
                im.save(root/'png'/tn/str(z)/f'{sp.name}.png', 'PNG', compress_level=1)

def contact(root:Path,specs:List[Spec],theme:str):
    cols=40; size=64; cell=76; rows=math.ceil(len(specs)/cols); bg=rgba(THEMES[theme]['bg'])
    img=Image.new('RGBA',(cols*cell+12,rows*cell+12),bg)
    for i,sp in enumerate(specs):
        p=root/'png'/theme/str(size)/f'{sp.name}.png'; im=Image.open(p).convert('RGBA') if p.exists() else render(sp,THEMES[theme],size)
        img.alpha_composite(im,(6+(i%cols)*cell+6,6+(i//cols)*cell+6))
    out=root/'preview'/f'contact_sheet_{theme}.png'; out.parent.mkdir(parents=True,exist_ok=True); img.save(out,'PNG',compress_level=1)

def preview(root:Path,specs:List[Spec]):
    for t in THEMES: contact(root,specs,t)
    links=''.join(f'<li><a href="contact_sheet_{html.escape(t)}.png">{html.escape(t)}</a></li>' for t in THEMES)
    cards=''.join(f'<div class="card"><img src="../png/classic_yellow/64/{html.escape(s.name)}.png"><span>{html.escape(s.name)}</span></div>' for s in specs[:200])
    write(root/'preview'/'index.html',f"""<!doctype html><html><head><meta charset='utf-8'><title>Neutrino Emojis Preview</title><style>body{{font-family:system-ui,sans-serif;margin:24px;background:#f7f7f7;color:#222}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px}}.card{{background:white;border:1px solid #ddd;border-radius:10px;padding:10px;text-align:center;min-height:100px}}.card img{{width:64px;height:64px;display:block;margin:0 auto 8px}}.card span{{font-size:12px;word-break:break-word}}</style></head><body><h1>Neutrino Emojis</h1><p>{len(specs)} original generated emoji icons, {len(THEMES)} themes, sizes {', '.join(map(str,SIZES))}.</p><h2>Contact sheets</h2><ul>{links}</ul><h2>Sample: first 200 classic_yellow icons</h2><div class='grid'>{cards}</div></body></html>""")

def counts(root:Path):
    d={'total_files':0,'png_files':0,'svg_files':0}
    for p in root.rglob('*'):
        if p.is_file():
            d['total_files']+=1
            if p.suffix.lower()=='.png': d['png_files']+=1
            elif p.suffix.lower()=='.svg': d['svg_files']+=1
    return d

def package(root:Path):
    parent=root.parent; zp=parent/f'{root.name}.zip'; tp=parent/f'{root.name}.tar.gz'
    if zp.exists(): zp.unlink()
    if tp.exists(): tp.unlink()
    print(f'Creating {zp}...',flush=True)
    with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for p in sorted(root.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(parent))
    print(f'Creating {tp}...',flush=True)
    with tarfile.open(tp,'w:gz',compresslevel=1) as t: t.add(root,arcname=root.name)
    write(parent/f'{root.name}_archive_checksums.txt', f'SHA256  {sha(zp)}  {zp.name}\nSHA256  {sha(tp)}  {tp.name}\n')
    return zp,tp

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default=f'/mnt/data/{PKG}'); ap.add_argument('--clean',action='store_true'); ap.add_argument('--limit',type=int); ap.add_argument('--no-png',action='store_true'); ap.add_argument('--no-package',action='store_true')
    a=ap.parse_args(); root=Path(a.out)
    if a.clean and root.exists(): shutil.rmtree(root)
    root.mkdir(parents=True,exist_ok=True)
    specs=build_specs(a.limit)
    copy_generator(root); write_docs(root,specs); write_manifest(root,specs); generate(root,specs,a.no_png)
    if not a.no_png: print('Creating preview contact sheets...',flush=True); preview(root,specs)
    report={'package':PKG,'icon_count':len(specs),'theme_count':len(THEMES),'themes':list(THEMES.keys()),'sizes':SIZES,'expected_png_files':0 if a.no_png else len(specs)*len(THEMES)*len(SIZES),'expected_themed_svg_files':len(specs)*len(THEMES),'expected_master_svg_files':len(specs),'generation_mode':'original deterministic geometry; no third-party emoji artwork'}
    report.update(counts(root)); write(root/'generation_report.json',json.dumps(report,indent=2))
    if not a.no_package:
        zp,tp=package(root); report.update({'zip_path':str(zp),'zip_size_bytes':zp.stat().st_size,'zip_sha256':sha(zp),'tar_gz_path':str(tp),'tar_gz_size_bytes':tp.stat().st_size,'tar_gz_sha256':sha(tp)}); write(root/'generation_report.json',json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__': main()
