import math, sys, itertools, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from design import *
import check2d as C
L=C.build_layers(C.instances())
def posed(q): return [(n,g,[(a,b,C.transform(s,g,q)) for a,b,s in lay]) for n,g,lay in L]
def layer_at(x,q):
    out=[]
    for n,g,lay in posed(q):
        for a,b,s in lay:
            if a<x<b: out.append((n,s))
    return out
def draw(ax,x,q,title):
    cols={}
    for n,s in layer_at(x,q):
        c=cols.setdefault(n.split('_')[0],plt.cm.tab20(len(cols)%20))
        for g in getattr(s,'geoms',[s]):
            if g.geom_type!='Polygon': continue
            xs,ys=g.exterior.xy; ax.fill(xs,ys,color=c,alpha=0.5,lw=0.3,ec='k')
            for h in g.interiors: hx,hy=h.xy; ax.fill(hx,hy,color='w',lw=0.3,ec='k')
    ax.set_aspect('equal'); ax.set_title(title,fontsize=8); ax.grid(True,lw=0.3)
if __name__=='__main__':
    xs=[0.0,8.0,15.0,22.0]; qs=[0.0,0.35,0.705]
    fig,axs=plt.subplots(len(qs),len(xs),figsize=(5*len(xs),6*len(qs)))
    for i,q in enumerate(qs):
        for j,x in enumerate(xs):
            draw(axs[i][j],x,q,f'x={x} q={q}'); axs[i][j].set_xlim(-110,110); axs[i][j].set_ylim(-5,240)
    plt.tight_layout(); plt.savefig('layers.png',dpi=55)
    # min distances
    def mind(n1,n2,q):
        A=[s for n,g,lay in posed(q) if n==n1 for a,b,s in lay if a<0<b or True]
        return None
    import shapely
    for q in (Q_OPEN_STOP,0,0.2,0.35,0.5,0.7,Q_CLOSE_STOP):
        P=posed(q); d={}
        get=lambda nm,x: [s for n,g,lay in P if n==nm for a,b,s in lay if a<x<b]
        gl=get('OuterKnuckle_L',0)[0]; gr=get('OuterKnuckle_R_R',0)[0]
        servo=get('Servo_D5545GS',0)[0]
        print(f'q={q:.3f} gearL-gearR {gl.distance(gr):.3f}  gearL-servo {gl.distance(servo):.2f} gearR-servo {gr.distance(servo):.2f}',
              ' padgap', round(-2*(p1_at(q)[0]+29.9),2))
