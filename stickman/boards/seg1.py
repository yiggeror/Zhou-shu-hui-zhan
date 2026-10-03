"""Storyboard, segment 1 (shots 0-6, frames 73-298): key frames as stick figures.
Each panel: (shot, original frame, story, staging, draw function)."""
import math
import numpy as np
import skia
from engine.canvas import Frame, col, paint, poly_path, smooth_path
from engine.camera import W, H
from engine import fx
from engine import stick2d as st
from engine.stick2d import Pose, P
from engine.roto import screen_cam, lift
from engine.theme import T as THEME

PAPER, INK = st.PAPER, st.INK


def paper(fr):
    fr.b.clear(col(PAPER))


def pencil(fr, pts, a=0.6, w=2.5, closed=False):
    fr.b.drawPath(poly_path([P(p) for p in pts], closed=closed), paint(THEME['env_edge'], a, stroke=w))


def flame(fr, at, pal, size, seed, frm=None, rise=0.5, t=0.6, z=2.0):
    """a burning fist for a still: the flame is simulated up to time t with the fist held at `at`
    (and the forearm toward `frm`), so it has its full shape"""
    cs = screen_cam().at(0.0)
    A = lift(P(at), z)
    B = lift(P(frm), z) if frm is not None else None
    f = fx.Flame(lambda tt: A, pal, size=size, rise=rise, life=0.26, src2=(lambda tt: B) if B is not None else None,
                 seg=(0.6, 1.0), seed=seed, trail=0.3)
    fx.render_flames(fr, cs, [f], t)


def wall_drawers(fr, dx=0.0):
    TL, TR, BR, BL = (30, 8), (102, -5), (102, 93), (30, 78)
    lerp = lambda a, b, u: (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
    sh = lambda p: (p[0] + dx, p[1])
    for i in range(5):
        u = i / 4
        pencil(fr, [sh(lerp(TL, TR, u * 0.98)), sh(lerp(BL, BR, u * 0.98))], 0.7)
    for j in range(6):
        v = j / 5
        pencil(fr, [sh(lerp(TL, BL, v)), sh(lerp(TR, BR, v))], 0.7)
    for i in range(4):
        for j in range(5):
            u, v = (i + 0.5) / 4, (j + 0.3) / 5
            top = lerp(lerp(TL, TR, u), lerp(BL, BR, u), v)
            pencil(fr, [sh((top[0] - 2.2, top[1])), sh((top[0] + 2.2, top[1] - 0.6))], 0.85, 3.0)


# ---------------------------------------------------------------------------------- panels
def p0a(fr):
    """the punch is launched at us: Gojo lunges toward the lens, the burning fist already
    big in front of him, the other fist pulled back to the hip"""
    paper(fr)
    pose = Pose(head_at=(53, 30), head_r=6, face=0.05, brow=0.9, mouth='grit', glow=1.3, torso=-4,
                uar=-40, k_uar=0.55, far=-25, k_far=0.45, hand_r='fist', hk_r=2.6,
                ual=55, fal=-20, k_fal=0.8, hand_l='fist', thl=30, shl=10, thr=-35, k_thr=0.8, shr=-20, front=('r_arm',))
    J = st.draw(fr, pose, st.GOJO)
    u = np.array([W / 100, H / 100])
    flame(fr, tuple(J['Wr'] / u), 'cyan', 0.07, 3, frm=tuple(J['Er'] / u), rise=0.45)


def p0b(fr):
    """the fist reaches the lens: huge, wrapped in cyan fire, filling the middle; his head and
    glowing eyes above it, the other fist cocked at his side"""
    paper(fr)
    pose = Pose(head_at=(55, 12), head_r=9, face=0.05, brow=1.0, mouth='grit', glow=1.6, torso=-3,
                uar=-45, k_uar=0.8, far=-20, k_far=0.6, hand_r='fist', hk_r=6.0,
                ual=70, k_ual=1.3, fal=-10, k_fal=0.9, hand_l='fist', hk_l=1.4, hide=('l_leg', 'r_leg'), front=('r_arm',))
    J = st.draw(fr, pose, st.GOJO)
    u = np.array([W / 100, H / 100])
    flame(fr, tuple(J['Wr'] / u + np.array([0, 6])), 'cyan', 0.13, 3, frm=tuple(J['Er'] / u), rise=0.35)


def p1(fr):
    """Sukuna answers in kind: the red fist at the lens, his face beside it - four eyes, a grin"""
    paper(fr)
    pose = Pose(head_at=(67, 30), head_r=11, face=-0.35, brow=0.7, mouth='smile', glow=1.4, torso=4,
                ual=-60, k_ual=0.9, fal=-35, k_fal=0.6, hand_l='fist', hk_l=5.4,
                uar=75, k_uar=1.2, far=-15, k_far=0.9, hand_r='fist', hk_r=1.6, hide=('l_leg', 'r_leg'), front=('l_arm',))
    J = st.draw(fr, pose, st.SUKUNA)
    u = np.array([W / 100, H / 100])
    flame(fr, tuple(J['Wl'] / u + np.array([0, 3])), 'red', 0.15, 4, frm=tuple(J['El'] / u), rise=0.75)


def _cross(fr, k=1.0, c=(50, 50)):
    """top view of the clinch: Gojo (left) hooks his left arm over Sukuna's head and holds his
    right fist back low, burning cyan; Sukuna (right) swings his red fist in over the top and
    reaches down with the other hand"""
    sc = lambda p: (c[0] + (p[0] - c[0]) * k, c[1] + (p[1] - c[1]) * k)
    hk = 7.5 * k
    g = Pose(head_at=sc((42, 52)), head_r=hk, back=True, top=True, torso=-135, head=-135, k_torso=0.45,
             ual=137, k_ual=1.6, fal=42, k_fal=1.0, hand_l='fist',
             uar=-31, k_uar=1.6, far=-40, k_far=1.4, hand_r='fist', hk_r=1.5,
             thl=-120, shl=-130, k_thl=0.6, k_shl=0.6, thr=-150, shr=-160, k_thr=0.6, k_shr=0.6, front=('r_arm', 'l_arm'))
    s = Pose(head_at=sc((60, 47)), head_r=hk, back=True, top=True, torso=108, head=108, k_torso=0.45,
             uar=-160, k_uar=1.4, far=-170, k_far=1.3, hand_r='fist', hk_r=1.5,
             ual=-33, k_ual=1.6, fal=-25, k_fal=1.4, hand_l='open', hk_l=1.4,
             thl=70, shl=80, k_thl=0.6, k_shl=0.6, thr=110, shr=100, k_thr=0.6, k_shr=0.6, front=('r_arm', 'l_arm'))
    return g, s


def p2a(fr):
    """straight down on them, locked together: both charging a punch at point-blank range"""
    paper(fr)
    pencil(fr, [(-5, 35), (105, 35)], 0.45)
    pencil(fr, [(-5, 66), (105, 66)], 0.45)
    g, s = _cross(fr)
    Jg = st.draw(fr, g, st.GOJO)
    Js = st.draw(fr, s, st.SUKUNA)
    u = np.array([W / 100, H / 100])
    flame(fr, tuple(Jg['Wr'] / u), 'cyan', 0.09, 7, frm=tuple(Jg['Er'] / u), rise=0.3)
    flame(fr, tuple(Js['Wr'] / u), 'red', 0.09, 8, frm=tuple(Js['Er'] / u), rise=0.3)


def p2b(fr):
    """the camera shoots up and away: the two of them small in the middle of the street"""
    paper(fr)
    c = (50, 50)
    for y in (35, 66):
        pencil(fr, [(-5, c[1] + (y - c[1]) * 0.33), (105, c[1] + (y - c[1]) * 0.33)], 0.45)
    g, s = _cross(fr, 0.33)
    Jg = st.draw(fr, g, st.GOJO)
    Js = st.draw(fr, s, st.SUKUNA)
    u = np.array([W / 100, H / 100])
    flame(fr, tuple(Jg['Wr'] / u), 'cyan', 0.025, 7, frm=tuple(Jg['Er'] / u), rise=0.1)
    flame(fr, tuple(Js['Wr'] / u), 'red', 0.025, 8, frm=tuple(Js['Er'] / u), rise=0.1)


def p3(fr):
    from films.r_open import S3
    s3 = S3()
    s3.draw(fr, 139 / 24 - S3.t0)


def p4(fr):
    """before the battle: Ijichi's back in the foreground; Gojo sits hunched on a gurney among
    the body drawers, eyes down; Shoko smokes and watches him"""
    paper(fr)
    wall_drawers(fr)
    gojo = Pose(head_at=(45, 41), head_r=5.5, face=-0.15, head=-22, eyes='narrow', glow=0.3, mouth='flat', torso=-14, k_torso=1.3,
                uar=-20, far=2, k_uar=1.45, k_far=1.45, hand_r='flat', hd_r=-95, ual=22, fal=4, k_ual=1.45, k_fal=1.45,
                hand_l='flat', hd_l=95, hide=('l_leg', 'r_leg'), front=('r_arm', 'l_arm'))
    st.draw(fr, gojo, st.GOJO)
    top = [P((27, 80)), P((70, 86)), P((74, 78)), P((35, 75))]
    fr.b.drawPath(poly_path(top + [P((74, 100)), P((27, 100))][:0], closed=True), paint(PAPER, 1.0))
    fr.b.drawPath(poly_path([P((27, 80)), P((70, 86)), P((70, 100)), P((27, 100))], closed=True), paint(PAPER, 1.0))
    for q in ([(27, 80), (70, 86), (74, 78), (35, 75), (27, 80)], [(29, 82), (29, 100)], [(66, 87), (66, 100)], [(30, 92), (66, 96)]):
        pencil(fr, q, 0.85, 3.0)
    shoko = Pose(head_at=(89, 40), head_r=4.2, face=-0.6, eyes='narrow', mouth='flat', torso=-3,
                 uar=-55, far=172, hand_r='two', ual=8, fal=-65, hand_l='flat', thl=4, shl=2, thr=-3, shr=-1, front=('r_arm',))
    J = st.draw(fr, shoko, st.SHOKO)
    hnd = J['Wr']
    cig = hnd + np.array([-28, -6])
    fr.b.drawLine(float(hnd[0]), float(hnd[1]), float(cig[0]), float(cig[1]), paint(PAPER, 1.0, stroke=5))
    smoke = [(cig[0] + 9 * math.sin(i * 0.9) * i / 7, cig[1] - 12 - i * 26) for i in range(8)]
    fr.b.drawPath(smooth_path(smoke), paint(THEME['env_edge'], 0.6, stroke=3))
    ij = Pose(head_at=(17, 2), head_r=10, back=True, torso=1, ual=-8, fal=-4, uar=8, far=4, hand_l='fist', hand_r='fist',
              thl=-4, shl=-2, thr=4, shr=2, k_w=1.5)
    J = st.draw(fr, ij, st.IJICHI)
    bag = J['Wl']
    fr.b.drawRect(skia.Rect(float(bag[0] - 70), float(bag[1] + 10), float(bag[0] + 10), float(bag[1] + 70)), paint(INK, 1.0))


def p5(fr):
    """his face, close: the eyes lift and the blue light comes up in them - he has decided"""
    paper(fr)
    pencil(fr, [(4, 100), (8, 12), (15, 10), (21, 100)], 0.4, 3.0)
    g = Pose(head_at=(55, 46), head_r=40, head=16, face=0.08, eyes='narrow', glow=1.6, brow=0.45, mouth='flat',
             hide=('torso', 'l_arm', 'r_arm', 'l_leg', 'r_leg'), eye_k=0.8)
    st.draw(fr, g, st.GOJO)


def p6(fr):
    """the three who will hold the ritual for him: Gakuganji with the guitar case on his back,
    Gojo in the middle, head lowered, Utahime glancing at him"""
    paper(fr)
    for x in (2, 6, 10, 13):
        pencil(fr, [(x, 58), (x, 100)], 0.3, 2.0)
    gk = Pose(head_at=(14, 47), head_r=7.5, face=0.25, head=10, eyes='narrow', mouth='none', torso=6,
              ual=-10, fal=-5, uar=10, far=6, hide=('l_leg', 'r_leg'), k_w=1.1)
    fr.b.drawPath(smooth_path([P((16, 21)), P((26, 15)), P((32, 92)), P((21, 100)), P((16, 21))], closed=True), paint(INK, 1.0))
    st.draw(fr, gk, st.GAKUGANJI)
    ut = Pose(head_at=(83, 38), head_r=6, face=-0.5, eyes='open', brow=-0.5, mouth='flat', torso=-4,
              ual=-8, fal=-4, uar=8, far=4, hide=('l_leg', 'r_leg'))
    st.draw(fr, ut, st.UTAHIME)
    g = Pose(head_at=(43, 32), head_r=12, face=-0.25, head=8, eyes='narrow', glow=0.9, brow=0.3, mouth='flat', torso=-2,
             ual=-8, fal=-6, uar=8, far=6, hide=('l_leg', 'r_leg'), k_w=1.1)
    st.draw(fr, g, st.GOJO)


PANELS = [
    (0, 75, '镜头 0　3.0–3.8 秒', '开场第一拳。五条先出手：拳头裹着青色咒力，从暗处朝观众直直打过来。"最强"在宣告自己来了。',
     '五条正面冲向镜头：出拳的手臂朝镜头伸过来（缩短），拳头已经比头还大，另一只拳收在腰侧；咬牙、眉头压低。', p0a),
    (0, 82, '', '', '拳头到了镜头前：巨大的拳头裹着青焰占满中央，头和发光的眼睛在上方，另一只拳在身侧蓄着。', p0b),
    (1, 101, '镜头 1　3.8–4.5 秒', '宿傩回敬同样的一拳，红色咒力。和上一镜左右镜像：两人势均力敌。',
     '红色火焰拳头占满中央，宿傩的脸从拳头右后方露出来：四只红眼、嘴角带笑，从容又挑衅。', p1),
    (2, 116, '镜头 2　4.5–5.3 秒', '两人已经贴身缠在一起：从正上方往下看，五条一只手勾住宿傩的头，另一只拳压在下方蓄着青焰；宿傩的红拳从上方抡过来，另一只手往下抓。两人都在近距离蓄力，下一拳就要砸下去——开战。',
     '俯视：两颗头挨在一起，五条的手臂从上面勾过宿傩，青焰拳在左下；宿傩的红焰拳在上方抡起，空手伸向右下。', p2a),
    (2, 125, '', '', '最后镜头急速升高，两人缩成画面中央的一小团。', p2b),
    (3, 139, '镜头 3　5.3–6.2 秒', '片名：在黑白碎片里一个字一个字砸下来，然后被碎片切碎。', '保留原版节奏（130、132、134、136 帧各落一个字）。', p3),
    (4, 175, '镜头 4　6.2–9.1 秒', '决战之前的安静时刻。镜头从伊地知（前景、背对、戴眼镜、提包）背后横移出来：五条低着头、双手撑在停尸间的推床上，家入硝子在旁边抽着烟看着他。气氛沉重。',
     '三人的位置和原版一致；五条弓着背俯在推床上，双手撑着床沿、低着头（腿被推床挡住）；硝子一手夹烟在嘴边，烟往上飘；前景的伊地知只露出背影。', p4),
    (5, 230, '镜头 5　8.8–11.2 秒', '五条的脸部特写：眼皮半垂，眼里慢慢亮起青光——他已经下定决心。',
     '大头特写，头微微歪着；眼睛半睁、青光渐亮，眉头略压，嘴抿成一条线。', p5),
    (6, 282, '镜头 6　10.5–12.4 秒', '要为五条做增幅仪式的三个人一起出发：乐岩寺背着吉他盒，五条在中间低着头，歌姬侧过脸看着他。',
     '半身三人并排，五条最大最靠前；歌姬眉头微皱，带点担心。', p6),
]
