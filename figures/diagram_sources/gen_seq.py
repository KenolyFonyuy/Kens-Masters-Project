import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow
OUT="/tmp/diagrams"

def seqdiagram(fname, title, actors, messages):
    n=len(actors); fig_w=max(8, n*2.2)
    fig,ax=plt.subplots(figsize=(fig_w, 0.7*len(messages)+2.2))
    xs={a:i*(10/(n-1)) for i,a in enumerate(actors)}
    top=len(messages)+1.2; bottom=0.2
    for a in actors:
        x=xs[a]
        ax.add_patch(Rectangle((x-0.95,top),1.9,0.7,fill=False,ec="black",lw=1.2))
        ax.text(x,top+0.35,a,ha="center",va="center",fontsize=10,fontweight="bold")
        ax.plot([x,x],[bottom,top],color="black",lw=0.8,ls=(0,(4,3)))
    y=top-0.6
    for (src,dst,label,kind) in messages:
        x1,x2=xs[src],xs[dst]
        style="-|>"
        ls="--" if kind=="return" else "-"
        if x1==x2:
            ax.annotate("",xy=(x1+0.6,y-0.25),xytext=(x1+0.6,y),
                        arrowprops=dict(arrowstyle="-|>",color="black",lw=1.1))
            ax.plot([x1,x1+0.6,x1+0.6],[y,y,y-0.25],color="black",lw=1.1)
            ax.text(x1+0.7,y+0.05,label,ha="left",va="bottom",fontsize=8.5)
        else:
            ax.annotate("",xy=(x2,y),xytext=(x1,y),
                arrowprops=dict(arrowstyle=style,color="black",lw=1.1,ls=ls))
            ax.text((x1+x2)/2,y+0.06,label,ha="center",va="bottom",fontsize=8.5)
        y-=0.85
    ax.set_xlim(-1.4,11.4); ax.set_ylim(-0.2,top+1.1)
    ax.set_title(title,fontsize=12,fontweight="bold")
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(f"{OUT}/{fname}.pdf",format="pdf",bbox_inches="tight")
    plt.close(); print("ok",fname)

# 11. Sensor-data submission sequence
seqdiagram("sensor_submission_sequence",
 "Sensor-data submission sequence",
 ["Pi Runtime","Local Buffer","REST API","Auth","PostgreSQL","Dashboard"],
 [("Pi Runtime","Local Buffer","store reading (UUID, ts)","call"),
  ("Pi Runtime","REST API","POST /api/readings + token","call"),
  ("REST API","Auth","validate device token","call"),
  ("Auth","REST API","token valid","return"),
  ("REST API","PostgreSQL","insert (idempotent on UUID)","call"),
  ("PostgreSQL","REST API","201 / duplicate ignored","return"),
  ("REST API","Pi Runtime","201 Created (ack)","return"),
  ("Pi Runtime","Local Buffer","mark synced","call"),
  ("REST API","Dashboard","push updated reading","call")])

# 12. ML result submission sequence
seqdiagram("ml_result_submission_sequence",
 "Machine-learning result submission sequence",
 ["Pi Runtime","Inference","REST API","PostgreSQL","Alert Svc","User"],
 [("Pi Runtime","Inference","run model on frame","call"),
  ("Inference","Pi Runtime","class + confidence","return"),
  ("Pi Runtime","REST API","POST /api/vision + token","call"),
  ("REST API","PostgreSQL","store vision result","call"),
  ("PostgreSQL","REST API","ok","return"),
  ("REST API","Alert Svc","evaluate risk rules","call"),
  ("Alert Svc","PostgreSQL","create alert if risk","call"),
  ("Alert Svc","User","notify (dashboard)","call"),
  ("REST API","Pi Runtime","201 Created (ack)","return")])
print("DONE seq")
