"""LEGO-style assembly manual (PDF) for HomeMade2F140 v2."""
import math, os, sys, time
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import FancyBboxPatch
import matplotlib.patheffects as pe
import mlib as M
import design as D

OUT_PDF = sys.argv[1] if len(sys.argv) > 1 else 'HomeMade2F140_manual.pdf'
LANG = 'en' if '--lang=en' in sys.argv else 'es'
from manual_i18n import EN


def tr(t):
    return EN.get(t, t) if LANG == 'en' else t

QUICK = '--quick' in sys.argv
I = M.build_items()
X, Y, Z = np.eye(3)
DARK = (0.12, 0.12, 0.14)


def keys(prefix, kinds=None):
    return [k for k, it in I.items() if k.startswith(prefix + ':') and (kinds is None or it.kind in kinds)]


def hw_explode(name, Db=None, Dn=22.0, skip_nut=False):
    """Default explode offsets for one fastener stack: bolt back along its axis, nut/washers forward."""
    out = {}
    b = I[name + ':bolt']
    a = b.axis
    L = float(np.dot(b.tipw - b.entry, a))
    Db = Db if Db is not None else L + 14.0
    out[name + ':bolt'] = -a * Db
    for k in keys(name):
        it = I[k]
        if it.kind == 'bolt':
            continue
        t = float(np.dot(it.anchor - b.entry, a))
        if it.kind == 'nut':
            if not skip_nut:
                out[k] = a * Dn
        elif k.endswith(':hw') or t < 1.0:
            out[k] = -a * (Db * 0.45)
        elif t > L - 6.0:
            out[k] = a * (Dn * 0.55)
        else:
            out[k] = a * (6.0 if it.side > 0 else -6.0)
    return out


def both(name):
    return [name, name + '_R']


# ---------------------------------------------------------------- groups of already-assembled items
STACK = ['Flange', 'Cam', 'D435', 'SpA', 'SpB'] + sum([keys(f'HW_M6x75_Flange{i}') for i in range(4)], []) \
    + sum([keys(f'HW_M3x8_Camera{i}') for i in range(2)], []) + [f'HW_M3x12_Base{i}:nut0' for i in range(4)]
BOX = ['Box'] + [f'HW_M3x12_Tower{i}:nut0' for i in range(4)] \
    + sum([[f'HW_M3x12_Base{i}:bolt', f'HW_M3x12_Base{i}:hw'] for i in range(4)], [])
DRIVE = ['Servo', 'Horn', 'Crank', 'Rod'] + keys('HW_M3x16_PinC')
EARS = sum([keys(f'HW_M3x16_ServoEar{i}') for i in range(4)], [])
TOWER0 = ['Tower', 'OK_L', 'OK_R'] + keys('HW_M3x30_PivotO_L') + keys('HW_M3x30_PivotO_R')
IKS = ['IK_L', 'IK_R', 'HW_M3x12_PinK:nut0'] + keys('HW_M3x45_PivotI_L') + keys('HW_M3x45_PivotI_R')
OFS = ['OF_L', 'OF_R'] + sum([keys(n) for n in both('HW_M3x30_J') + both('HW_M3x30_J2')], [])
IFS = ['IF_L', 'IF_R'] + sum([keys(n) for n in both('HW_M3x30_P1') + both('HW_M3x30_P2')], [])
TIPS = ['FT_L', 'FT_R'] + sum([keys(n) for n in both('HW_M3x16_Pad0') + both('HW_M3x16_Pad1')], [])
TOWERSET = TOWER0 + IKS + OFS + IFS + TIPS
TOWERBOLTS = sum([[f'HW_M3x12_Tower{i}:bolt', f'HW_M3x12_Tower{i}:hw'] for i in range(4)], [])
KPIN = [k for k in keys('HW_M3x12_PinK') if not k.endswith('nut0')]


def off(keys_, v):
    return {k: np.asarray(v, float) for k in keys_}


def radial(i, pts, d, inward=False):
    s = np.array(pts[i], float)
    u = s / np.linalg.norm(s)
    return np.array([u[0], u[1], 0.0]) * d * (-1 if inward else 1)


def arm_dir(side):
    v = np.subtract(D.J, D.O)
    v = v / np.linalg.norm(v)
    return np.array([0.0, v[0] if side == 'L' else -v[0], v[1]])


STEPS = []


def step(title, context, new, view, notes=(), focus=None, arrows=None, label_parts=None, hide=(), repeat=1):
    STEPS.append(dict(title=title, context=list(context), new=new, view=view, notes=list(notes), focus=focus,
                      arrows=arrows, label_parts=label_parts or {}, hide=set(hide), repeat=repeat))


# ---------------------------------------------------------------- the build
base_nuts = {f'HW_M3x12_Base{i}:nut0': radial(i, D.BASE_SCREWS, 24) for i in range(4)}
step('Tuercas en el espaciador B', [], dict({'SpB': np.zeros(3)}, **base_nuts), (-35, 28),
     ['Mete una tuerca nyloc en cada ranura lateral hasta que quede centrada con el agujero.'])

step('Camera mount sobre la brida del robot', ['Flange'], {'Cam': Z * 40}, (-55, 24),
     ['El brazo de la camara apunta hacia +X (el lado donde ira la biela roja).',
      'Opcional: pasador de 6 mm en el agujero de centrado.'], focus=['Flange', 'Cam'])

step('Espaciadores A y B', ['Flange', 'Cam'],
     dict({'SpA': Z * 40}, **off(['SpB'] + list(base_nuts), Z * 85)), (-55, 24),
     ['El bloque saliente de ambos espaciadores va hacia el brazo de la camara.'],
     focus=['Cam', 'SpA', 'SpB'], label_parts={'SpB': 'Espaciador B (paso 1)'}, hide=list(base_nuts))

m6 = sum([keys(f'HW_M6x75_Flange{i}') for i in range(4)], [])
step('4 tornillos M6 a la brida', ['Flange', 'Cam', 'SpA', 'SpB'] + list(base_nuts), off(m6, Z * 95), (-55, 30),
     ['Aprieta en cruz. La cabeza queda hundida en el espaciador B.'], focus=['Cam', 'SpA', 'SpB'] + m6)

cam_hw = sum([keys(f'HW_M3x8_Camera{i}') for i in range(2)], [])
step('Camara RealSense D435i', ['Flange', 'Cam', 'SpA', 'SpB'] + m6 + list(base_nuts),
     dict({'D435': Z * 35}, **{k: -Z * 22 for k in cam_hw}), (-25, 12),
     ['Los 2 tornillos entran por debajo del camera mount.'], focus=['D435', 'Cam'] + cam_hw)

tower_nuts = {f'HW_M3x12_Tower{i}:nut0': radial(i, D.TOWER_SCREWS, 20, inward=True) for i in range(4)}
step('Tuercas en la caja', [], dict({'Box': np.zeros(3)}, **tower_nuts), (-60, 58),
     ['Una tuerca nyloc en cada columna de las esquinas, por la ranura interior.'])

step('Caja sobre el espaciador B', STACK, off(['Box'] + list(tower_nuts), Z * 50), (-55, 25),
     ['La pared con el hueco de cable (-X) va del lado opuesto a la camara.'], focus=['SpB', 'Box'],
     label_parts={'Box': 'Caja (paso 6)'}, hide=list(tower_nuts))

base_bolts = sum([[f'HW_M3x12_Base{i}:bolt', f'HW_M3x12_Base{i}:hw'] for i in range(4)], [])
step('Tornillos de la caja', STACK + ['Box'] + list(tower_nuts),
     dict({f'HW_M3x12_Base{i}:bolt': Z * 34 for i in range(4)}, **{f'HW_M3x12_Base{i}:hw': Z * 16 for i in range(4)}),
     (-60, 62), ['Desde dentro de la caja, antes de meter el servo.'], focus=['Box'])

step('Manivela + biela (en la mesa)', [], dict({'Crank': np.zeros(3), 'Rod': X * 16}, **hw_explode('HW_M3x16_PinC')),
     (-60, 20), ['Aprieta la tuerca solo hasta quitar el juego: la biela debe girar libre.'],
     focus=['Crank', 'Rod'] + keys('HW_M3x16_PinC'))

step('Horn y manivela al servo', [],
     dict({'Servo': np.zeros(3), 'Horn': X * 16}, **off(['Crank', 'Rod'] + keys('HW_M3x16_PinC'), X * 34)),
     (-60, 22),
     ['1) Taladra la manivela usando el horn metalico como plantilla.',
      '2) Lleva el servo a su centro (1500 us).',
      '3) Monta el horn con la manivela hacia -Y (como en el dibujo) y la biela vertical.'],
     label_parts={'Crank': 'Manivela + biela (paso 9)'}, hide=['Rod'] + keys('HW_M3x16_PinC'))

step('Servo dentro de la caja', STACK + BOX, off(DRIVE, Z * 70), (-60, 32),
     ['Baja el servo desde arriba: las orejas apoyan en la mampara interior.'], focus=['Box'] + DRIVE,
     label_parts={'Servo': 'Servo + manivela (paso 10)'}, hide=DRIVE[1:])

ear_off = {}
for i in range(4):
    ear_off.update(hw_explode(f'HW_M3x16_ServoEar{i}', Db=26, Dn=16))
step('Tornillos del servo', STACK + BOX + DRIVE, ear_off, (-62, 62),
     ['Cabeza del lado de la mampara (+X), tuerca del lado de la oreja del servo.'], focus=['Servo'] + EARS)

step('Outer knuckles en la torre (en la mesa)', [], {'Tower': np.zeros(3), 'OK_L': -Y * 45, 'OK_R': Y * 45}, (-60, 22),
     ['OuterKnuckle_L va del lado -Y (lado de la biela). L y R NO son intercambiables.',
      'Engrana ambos con los dedos en posicion abierta (simetricos).'])

ok_hw = dict(**hw_explode('HW_M3x30_PivotO_L', Db=40), **hw_explode('HW_M3x30_PivotO_R', Db=40))
step('Pivotes de los outer knuckles', ['Tower', 'OK_L', 'OK_R'], ok_hw, (-60, 22),
     ['Izquierdo: cabeza hundida en la cara +X. Derecho: cabeza hundida en la cara -X.'],
     focus=['Tower', 'OK_L', 'OK_R'] + list(ok_hw))

step('Tuerca en la oreja (en la mesa)', [], {'IK_L': np.zeros(3), 'HW_M3x12_PinK:nut0': X * 18}, (-35, 25),
     ['Solo el inner knuckle que va del lado -Y usa la oreja. Mete la tuerca hasta el fondo del hexagono.'],
     focus=['IK_L', 'HW_M3x12_PinK:nut0'])

step('Inner knuckles', TOWER0, off(['IK_L', 'HW_M3x12_PinK:nut0'], Z * 45) | off(['IK_R'], Z * 45), (-60, 22),
     ['Los brazos abrazan la torre por fuera. La oreja con tuerca queda del lado -Y, cara +X.'],
     hide=['HW_M3x12_PinK:nut0'])

ik_hw = dict(**hw_explode('HW_M3x45_PivotI_L', Db=58), **hw_explode('HW_M3x45_PivotI_R', Db=58))
step('Pivotes de los inner knuckles', TOWER0 + ['IK_L', 'IK_R', 'HW_M3x12_PinK:nut0'], ik_hw, (-60, 22),
     ['Orden: brazo - arandela - pared - ranura del engrane - pared - arandela - brazo.'],
     focus=['Tower', 'IK_L', 'IK_R'] + list(ik_hw))

step('Outer fingers', TOWER0 + IKS, {'OF_L': arm_dir('L') * 40, 'OF_R': arm_dir('R') * 40}, (-60, 20),
     ['La horquilla del outer finger abraza el brazo amarillo.'])

of_hw = {}
for n in both('HW_M3x30_J') + both('HW_M3x30_J2'):
    of_hw.update(hw_explode(n, Db=40))
step('Union outer knuckle - outer finger', TOWER0 + IKS + ['OF_L', 'OF_R'], of_hw, (-60, 20),
     ['2 tornillos por lado: esta union es rigida, aprieta firme.'])

step('Inner fingers', TOWER0 + IKS + OFS, {'IF_L': np.array([0, 30, 12.0]), 'IF_R': np.array([0, -30, 12.0])}, (-60, 20),
     ['Entran en las horquillas del outer finger (azul) y del inner knuckle (verde).'])

if_hw = {}
for n in both('HW_M3x30_P1') + both('HW_M3x30_P2'):
    if_hw.update(hw_explode(n, Db=40))
step('Pivotes de los inner fingers', TOWER0 + IKS + OFS + ['IF_L', 'IF_R'], if_hw, (-60, 20),
     ['Aprieta hasta quitar el juego; los dedos deben moverse suaves.'])

pad_nuts = {k: (-Y if k.find('_R') < 0 else Y) * 16 for n in both('HW_M3x16_Pad0') + both('HW_M3x16_Pad1')
            for k in keys(n, ('nut',))}
pad_nuts_L = {k: v for k, v in pad_nuts.items() if '_R' not in k}
step('Tuercas en las puntas (en la mesa)', [], dict({'FT_L': np.zeros(3)}, **pad_nuts_L), (-115, 15),
     ['2 tuercas en los hexagonos de la cara trasera de cada punta.', 'Repite con la otra punta.'],
     focus=['FT_L'] + list(pad_nuts_L), repeat=2)

tip_off = dict(**off(['FT_L'] + [k for k in pad_nuts if '_R' not in k], Y * 28),
               **off(['FT_R'] + [k for k in pad_nuts if '_R' in k], -Y * 28))
for n in both('HW_M3x16_Pad0') + both('HW_M3x16_Pad1'):
    tip_off.update({k: v for k, v in hw_explode(n, Db=30).items() if not k.endswith('nut0')})
step('Puntas en los inner fingers', TOWER0 + IKS + OFS + IFS, tip_off, (-60, 20),
     ['Tornillos desde la cara exterior del inner finger.'],
     hide=list(pad_nuts))

step('Torre sobre la caja', STACK + BOX + DRIVE + EARS, off(TOWERSET, Z * 75), (-58, 18),
     ['Pasa la biela roja por la ranura de la placa de la torre.'], focus=['Box', 'Tower', 'IK_L', 'IK_R', 'Rod'],
     label_parts={'Tower': 'Torre con dedos (pasos 13-23)'}, hide=TOWERSET[1:])

step('Tornillos de la torre', STACK + BOX + DRIVE + EARS + TOWERSET,
     dict({f'HW_M3x12_Tower{i}:bolt': Z * 30 for i in range(4)}, **{f'HW_M3x12_Tower{i}:hw': Z * 14 for i in range(4)}),
     (-60, 48), [], focus=['Box', 'Tower'])

k_off = {k: v for k, v in hw_explode('HW_M3x12_PinK', Db=28).items() if not k.endswith('nut0')}
step('Biela a la oreja', STACK + BOX + DRIVE + EARS + TOWERSET + TOWERBOLTS, k_off, (-45, 15),
     ['Mueve los dedos a mano hasta alinear el agujero de la biela con la tuerca de la oreja.',
      'Apretar solo hasta quitar el juego.'], focus=['Rod', 'IK_L'] + KPIN)

ALL = STACK + BOX + DRIVE + EARS + TOWERSET + TOWERBOLTS + KPIN


# ---------------------------------------------------------------- rendering helpers
def scene_for(keys_, offsets, q=0.0):
    sc, pts = [], {}
    for k in keys_:
        it = I[k]
        R, t = M.group_tf(it.group, q)
        o = offsets.get(k, np.zeros(3))
        tri = it.tris @ R.T + t + o
        sc.append((tri, it.color))
        if it.extra is not None:
            sc.append((it.extra @ R.T + t + o, DARK))
        pts[k] = tri.reshape(-1, 3)
    return sc, pts


def render_step(st, W=1500, H=1150):
    keys_ = st['context'] + [k for k in st['new'] if k not in st['context']]
    sc, pts = scene_for(keys_, st['new'])
    fkeys = (st['focus'] or keys_) + list(st['new'])
    fp = np.concatenate([pts[k] for k in fkeys if k in pts])
    cam = M.Camera(st['view'][0], st['view'][1], W, H, fp, margin=0.07, ss=1 if QUICK else 2)
    img = M.render(sc, cam)
    arrows = []
    for k, o in st['new'].items():
        o = np.asarray(o, float)
        if np.linalg.norm(o) < 1e-6 or k in st['hide']:
            continue
        it = I[k]
        if it.kind == 'bolt':
            a = it.axis
            L = float(np.dot(it.tipw - it.entry, a))
            tip_now = it.entry + a * L + o
            back = float(np.dot(it.entry - tip_now, a))      # distance still to travel
            s3, e3 = tip_now + a * 1.0, it.entry - a * 1.5
            if back < 4:
                s3, e3 = it.entry + o * 0.85, it.entry + o * 0.25
        elif it.kind in ('nut', 'washer'):
            s3, e3 = it.anchor + o * 0.80, it.anchor + o * 0.22
        else:
            s3, e3 = it.anchor + o * 0.62, it.anchor + o * 0.16
        (s2, e2), _ = cam.project(np.array([s3, e3]))
        if np.hypot(*(e2 - s2)) > 14:
            arrows.append((s2, e2))
    return img, arrows


def thumb(it, W=260, H=200):
    if it.kind == 'bolt':
        L = float(np.dot(it.tipw - it.entry, it.axis))
        head_d = 10.0 if 'M6' in it.label else 5.5
        tri, sock = M.bolt_mesh((0, 0, 0), (1, 0, 0), head_d, 6.0 if 'M6' in it.label else 3.0, 6.0 if 'M6' in it.label else 3.0, L)
        sc = [(tri, it.color), (sock, DARK)]
        view = (-80, 18)
    else:
        tri = it.tris - it.anchor
        sc = [(tri, it.color)]
        view = (-55, 28) if it.kind not in ('nut', 'washer') else (-60, 45)
        if it.kind in ('nut', 'washer'):
            a = it.axis
            if abs(a[2]) < 0.9:          # show nuts/washers lying flat
                Rm = M.view_matrix(0, 0)
                ax = a / np.linalg.norm(a)
                v = np.cross(ax, [0, 0, 1.0]); s = np.linalg.norm(v); c = ax[2]
                if s > 1e-9:
                    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
                    Rr = np.eye(3) + vx + vx @ vx * ((1 - c) / s ** 2)
                    sc = [(tri @ Rr.T, it.color)]
    pts = np.concatenate([s[0].reshape(-1, 3) for s in sc])
    cam = M.Camera(view[0], view[1], W, H, pts, margin=0.10, ss=1 if QUICK else 2)
    return M.render(sc, cam)


THUMBS = {}


def thumb_for(k):
    it = I[k]
    key = (it.kind, it.label) if it.kind in ('bolt', 'nut', 'washer') else it.key.split('_')[0] + it.kind
    if key not in THUMBS:
        THUMBS[key] = thumb(it)
    return THUMBS[key]


PRETTY = {'Tower': 'Torre', 'Box': 'Caja', 'SpA': 'Espaciador A', 'SpB': 'Espaciador B', 'Cam': 'Camera mount',
          'D435': 'RealSense D435i', 'Servo': 'Servo D5545GS', 'Horn': 'Horn metalico', 'Crank': 'Manivela',
          'Rod': 'Biela', 'OK': 'OuterKnuckle', 'OF': 'OuterFinger', 'IK': 'InnerKnuckle', 'IF': 'InnerFinger',
          'FT': 'Fingertip', 'Flange': 'Brida UR'}


def callout_groups(st):
    groups, order = {}, []
    for k in st['new']:
        if k in st['hide']:
            continue
        it = I[k]
        if k in st['label_parts']:
            g, name = 'sub_' + k, st['label_parts'][k]
        elif it.kind in ('bolt', 'nut', 'washer'):
            g = (it.kind, it.label)
            name = {'bolt': it.label.replace('x', ' x '), 'nut': 'Tuerca M3 nyloc', 'washer': 'Arandela M3'}[it.kind]
        elif k in ('OK_L', 'OK_R'):
            g, name = k, {'OK_L': 'OuterKnuckle_L', 'OK_R': 'OuterKnuckle_R'}[k]
        else:
            g, name = it.kind, PRETTY.get(it.kind, it.label)
        if g not in groups:
            groups[g] = [0, name, k]
            order.append(g)
        groups[g][0] += 1
    out = [tuple(groups[g]) for g in order]
    rank = {'bolt': 1, 'washer': 2, 'nut': 3}
    out.sort(key=lambda r: rank.get(I[r[2]].kind, 0))
    return out


# ---------------------------------------------------------------- pages
A4 = (11.69, 8.27)
LEGO_BLUE = '#d8ecf9'


def draw_arrows(ax, arrows):
    for s, e in arrows:
        ax.annotate('', xy=e, xytext=s, arrowprops=dict(arrowstyle='-|>', lw=3.0, color='#111111', mutation_scale=22,
                                                        shrinkA=0, shrinkB=0,
                                                        path_effects=[pe.Stroke(linewidth=6, foreground='white'), pe.Normal()]))


def page_step(pdf, n, st):
    img, arrows = render_step(st)
    fig = plt.figure(figsize=A4)
    ax = fig.add_axes([0.27, 0.02, 0.72, 0.96])
    ax.imshow((np.clip(img, 0, 1) * 255).astype(np.uint8))
    draw_arrows(ax, arrows)
    ax.set_xlim(0, img.shape[1]); ax.set_ylim(img.shape[0], 0)
    ax.axis('off')
    fig.text(0.03, 0.965, str(n), fontsize=54, fontweight='bold', va='top', color='#1a1a1a')
    import textwrap
    fig.text(0.03, 0.845, chr(10).join(textwrap.wrap(tr(st['title']), 30)), fontsize=12.5, fontweight='bold', va='top',
             color='#1a1a1a')
    groups = callout_groups(st)
    ncol = 2
    cw, ch = 0.115, 0.135
    rows = math.ceil(len(groups) / ncol)
    top = 0.77
    h = rows * ch + 0.02
    bax = fig.add_axes([0.02, top - h, 2 * cw + 0.01, h], zorder=-5)
    bax.add_patch(FancyBboxPatch((0.01, 0.01), 0.98, 0.98, boxstyle='round,pad=0.0,rounding_size=0.06',
                                 transform=bax.transAxes, facecolor=LEGO_BLUE, edgecolor='#7fb5d8', lw=1.5))
    bax.axis('off')
    for i, (cnt, name, k) in enumerate(groups):
        r, c = divmod(i, ncol)
        x0 = 0.025 + c * cw
        y0 = top - 0.01 - (r + 1) * ch
        tax = fig.add_axes([x0 + 0.005, y0 + 0.032, cw - 0.012, ch - 0.04], zorder=5)
        tim = thumb_for(k).copy()
        wm = (tim > 0.995).all(-1)
        tim[wm] = np.array([0xd8, 0xec, 0xf9]) / 255.0
        tax.imshow((np.clip(tim, 0, 1) * 255).astype(np.uint8)); tax.axis('off')
        fig.text(x0 + 0.006, y0 + 0.03, f'{cnt}x', fontsize=13, fontweight='bold', color='#111', zorder=50)
        fig.text(x0 + 0.006, y0 + 0.012, tr(name), fontsize=7.5, color='#222', zorder=50)
    y = top - h - 0.035
    for line in st['notes']:
        wl = textwrap.wrap(tr(line), 42)
        fig.text(0.025, y, chr(10).join(['- ' + wl[0]] + ['  ' + w for w in wl[1:]]), fontsize=8.8, va='top', color='#222',
                 linespacing=1.35)
        y -= 0.03 * len(wl) + 0.015
    if st.get('repeat', 1) > 1:
        fig.text(0.93, 0.08, f"x{st['repeat']}", fontsize=30, fontweight='bold', ha='center', va='center', color='#111',
                 bbox=dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor='#111', lw=2.5))
    fig.text(0.985, 0.012, f"HomeMade2F140 v2  |  {tr('paso')} {n}/{len(STEPS)}", fontsize=7, ha='right', color='#888')
    if '--png' in sys.argv:
        fig.savefig(f'preview_{n:02d}.png', dpi=70)
    pdf.savefig(fig); plt.close(fig)


def page_cover(pdf):
    sc, pts = scene_for(ALL, {})
    cam = M.Camera(-55, 22, 1300, 1300, np.concatenate([pts[k] for k in ALL if k != 'Flange']), margin=0.04,
                   ss=1 if QUICK else 2)
    img = M.render(sc, cam)
    fig = plt.figure(figsize=A4)
    ax = fig.add_axes([0.42, 0.02, 0.56, 0.96]); ax.imshow(img); ax.axis('off')
    fig.text(0.05, 0.80, 'HomeMade2F140', fontsize=40, fontweight='bold', color='#1a1a1a')
    fig.text(0.05, 0.73, tr('Manual de ensamble'), fontsize=24, color='#333')
    lines = ['Gripper de 2 dedos con la cinematica del Robotiq 2F-140',
             'Servo DFRobot SER0062 (D5545GS)  -  version v2',
             '', '17 piezas impresas  -  36 tornillos M3  -  4 tornillos M6',
             '30 tuercas M3 nyloc  -  50 arandelas M3', '',
             'Herramientas: llave allen 2,5 mm y 5 mm,', 'llave de 5,5 mm para tuercas M3.', '',
             'Pasos 1-12: muneca y caja con el servo', 'Pasos 13-23: torre con los dedos (en la mesa)',
             'Pasos 24-26: union final']
    for i, l in enumerate(lines):
        fig.text(0.05, 0.64 - i * 0.04, tr(l), fontsize=12, color='#222')
    if '--png' in sys.argv:
        fig.savefig('preview_cover.png', dpi=70)
    pdf.savefig(fig); plt.close(fig)


def page_inventory(pdf):
    fig = plt.figure(figsize=A4)
    fig.text(0.03, 0.94, tr('Inventario de piezas'), fontsize=26, fontweight='bold')
    printed = [('SpB', 1), ('SpA', 1), ('Cam', 1), ('Box', 1), ('Tower', 1), ('Crank', 1), ('Rod', 1), ('OK_L', 1),
               ('OK_R', 1), ('OF_L', 2), ('IK_L', 2), ('IF_L', 2), ('FT_L', 2)]
    names = {'OK_L': 'OuterKnuckle_L', 'OK_R': 'OuterKnuckle_R'}
    for i, (k, n) in enumerate(printed):
        r, c = divmod(i, 5)
        x0, y0 = 0.03 + c * 0.19, 0.66 - r * 0.25
        bax = fig.add_axes([x0, y0, 0.18, 0.22], zorder=-5)
        bax.add_patch(FancyBboxPatch((0.01, 0.01), 0.98, 0.98, boxstyle='round,pad=0.0,rounding_size=0.06',
                                     transform=bax.transAxes, facecolor=LEGO_BLUE, edgecolor='#7fb5d8'))
        bax.axis('off')
        tim = thumb_for(k).copy(); tim[(tim > 0.995).all(-1)] = np.array([0xd8, 0xec, 0xf9]) / 255.0
        tax = fig.add_axes([x0 + 0.01, y0 + 0.05, 0.16, 0.16], zorder=5); tax.imshow(tim); tax.axis('off')
        fig.text(x0 + 0.008, y0 + 0.028, f'{n}x', fontsize=14, fontweight='bold', zorder=50)
        fig.text(x0 + 0.05, y0 + 0.03, tr(names.get(k, PRETTY.get(I[k].kind, k))), fontsize=9, zorder=50)
    hw = ['6x M3 x 8', '9x M3 x 12', '9x M3 x 16', '10x M3 x 30', '2x M3 x 45', '4x M6 x 75',
          '30x tuerca M3 nyloc', '50x arandela M3 (7 x 0,5 mm)']
    fig.text(0.62, 0.355, tr('Tornilleria'), fontsize=14, fontweight='bold')
    for i, l in enumerate(hw):
        fig.text(0.62 + (i // 4) * 0.17, 0.31 - (i % 4) * 0.04, tr(l), fontsize=10.5)
    fig.text(0.03, 0.02, tr('STL: carpeta print/parts del repositorio (la cantidad esta en el nombre del archivo, _x2 = 2 piezas).'),
             fontsize=8, color='#555')
    if '--png' in sys.argv:
        fig.savefig('preview_inv.png', dpi=70)
    pdf.savefig(fig); plt.close(fig)


def page_final(pdf):
    fig = plt.figure(figsize=A4)
    fig.text(0.03, 0.93, tr('Listo!'), fontsize=40, fontweight='bold')
    for j, (q, txt) in enumerate(((0.0, 'Abierto: servo 0 deg -> 130,7 mm'), (0.7, 'Cerrado: servo +45,4 deg -> 2 mm'))):
        sc, pts = scene_for(ALL, {}, q=q)
        cam = M.Camera(-15, 8, 900, 1100, np.concatenate([pts[k] for k in ALL if k not in ('Flange', 'Cam', 'D435')]),
                       margin=0.05, ss=1 if QUICK else 2)
        img = M.render(sc, cam)
        ax = fig.add_axes([0.04 + j * 0.33, 0.06, 0.31, 0.82]); ax.imshow(img); ax.axis('off')
        fig.text(0.06 + j * 0.33, 0.06, tr(txt), fontsize=11, fontweight='bold')
    notes = ['Primera prueba:', '- Alimenta el servo a 6 V con limite de corriente.',
             '- Recorrido por software: 0 a +45,4 deg desde la', '  posicion de montaje (q = 0 ... 0,7 del simulador).',
             '- Relacion casi lineal: servo_deg = 64,8 x q.', '- Topes mecanicos en -2,0 y +45,7 deg.', '',
             'Si algo roza: revisa que los dos engranes', 'esten simetricos (paso 13) y que todas las',
             'tuercas de pivote giren libres.']
    for i, l in enumerate(notes):
        fig.text(0.70, 0.80 - i * 0.04, tr(l), fontsize=10.5, fontweight='bold' if i == 0 else 'normal')
    if '--png' in sys.argv:
        fig.savefig('preview_final.png', dpi=70)
    pdf.savefig(fig); plt.close(fig)


if __name__ == '__main__':
    t0 = time.time()
    only = [int(a) for a in sys.argv[2:] if a.isdigit()]
    with PdfPages(OUT_PDF) as pdf:
        if not only or '--pages' in sys.argv:
            page_cover(pdf); print('cover', round(time.time() - t0))
            page_inventory(pdf); print('inventory', round(time.time() - t0))
        for n, st in enumerate(STEPS, 1):
            if only and n not in only:
                continue
            page_step(pdf, n, st)
            print('step', n, st['title'], round(time.time() - t0))
        if not only or '--pages' in sys.argv:
            page_final(pdf)
        d = pdf.infodict()
        d['Title'] = tr('HomeMade2F140 v2 - Manual de ensamble')
    print('done', OUT_PDF, round(time.time() - t0), 's')
