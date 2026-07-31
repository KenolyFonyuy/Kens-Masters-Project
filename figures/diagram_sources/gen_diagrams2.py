import os
from graphviz import Digraph
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
OUT="/tmp/diagrams"; os.makedirs(OUT, exist_ok=True)
NODE=dict(shape="box",style="filled",fillcolor="white",color="black",fontname="Helvetica",fontcolor="black",fontsize="13")
GA=dict(bgcolor="white",fontname="Helvetica",fontsize="13",color="black")
ED=dict(color="black",fontname="Helvetica",fontcolor="black",fontsize="11")
def newdg(n,rd="TB"):
    g=Digraph(n); g.attr(rankdir=rd,**GA); g.attr("node",**NODE); g.attr("edge",**ED); return g
def render(g,n): g.render(filename=n,directory=OUT,format="pdf",cleanup=True); print("ok",n)

# 8. Use-case diagram
g=newdg("uc","LR")
g.attr("node", shape="ellipse")
actors=[("admin","System\nAdministrator"),("owner","Farm Owner"),("mgr","Farm Manager"),
        ("worker","Farm Worker"),("vet","Veterinary\nConsultant"),("device","IoT Edge\nDevice")]
for a,l in actors: g.node(a,l,shape="box")
uc=["Manage users & roles","Manage farms/pens/batches","Record chick entries",
    "Log mortality","Record feeding","Record health & treatments","Manage inventory",
    "Record expenses & sales","Submit sensor readings","Submit vision results",
    "View dashboards","Acknowledge & resolve alerts","Generate reports"]
for i,u in enumerate(uc): g.node(f"u{i}",u,shape="ellipse")
def link(a,idxs):
    for i in idxs: g.edge(a,f"u{i}")
link("admin",[0,1,11,12]); link("owner",[1,2,7,10,11,12]); link("mgr",[1,2,3,4,5,6,7,10,11,12])
link("worker",[2,3,4,5,10]); link("vet",[5,10,11]); link("device",[8,9])
render(g,"usecase_diagram")

# 9. Class diagram (domain model, UML style records)
g=newdg("cls"); g.attr("node",shape="record")
def cls(name,attrs): return "{"+name+"|"+"\\l".join(attrs)+"\\l}"
g.node("User",cls("User",["+username","+role","+email","+is_active"]))
g.node("Farm",cls("Farm",["+name","+location","+owner"]))
g.node("Pen",cls("Pen",["+code","+capacity"]))
g.node("Batch",cls("Batch",["+code","+breed","+start_date","+initial_qty"]))
g.node("MortalityRecord",cls("MortalityRecord",["+date","+count","+cause"]))
g.node("FeedRecord",cls("FeedRecord",["+date","+feed_type","+qty_kg"]))
g.node("HealthRecord",cls("HealthRecord",["+date","+observation","+treatment"]))
g.node("Device",cls("Device",["+uuid","+token","+pen","+last_seen"]))
g.node("SensorReading",cls("SensorReading",["+ts","+temp","+humidity","+gas","+level"]))
g.node("VisionResult",cls("VisionResult",["+ts","+class","+confidence"]))
g.node("Alert",cls("Alert",["+ts","+type","+severity","+status"]))
for a,b,l in [("Farm","Pen","1..*"),("Pen","Batch","1..*"),("Batch","MortalityRecord","1..*"),
   ("Batch","FeedRecord","1..*"),("Batch","HealthRecord","1..*"),("Pen","Device","1"),
   ("Device","SensorReading","1..*"),("Device","VisionResult","1..*"),
   ("SensorReading","Alert","0..*"),("VisionResult","Alert","0..*"),("User","Farm","manages")]:
    g.edge(a,b,label=l, arrowhead="vee")
render(g,"class_diagram")

# 10. Activity diagram (alert handling)
g=newdg("act")
g.node("s","start",shape="circle"); g.node("e","end",shape="doublecircle")
acts=[("cap","Capture sensor &\nvision data"),("eval","Evaluate risk"),
      ("d","Risk detected?","diamond"),("gen","Generate alert"),
      ("auto","Trigger fan/heater"),("notify","Notify users"),
      ("ack","User acknowledges"),("act2","Corrective action taken"),
      ("res","Resolve & log outcome")]
for t in acts:
    if len(t)==3: g.node(t[0],t[1],shape="diamond")
    else: g.node(t[0],t[1])
g.edge("s","cap");g.edge("cap","eval");g.edge("eval","d")
g.edge("d","gen",label="yes");g.edge("d","cap",label="no",style="dashed",constraint="false")
g.edge("gen","auto");g.edge("auto","notify");g.edge("notify","ack");g.edge("ack","act2")
g.edge("act2","res");g.edge("res","e")
render(g,"activity_diagram")

# 13. Component diagram
g=newdg("comp","LR"); g.attr("node",shape="component")
g.node("sense","Sensing &\nActuation")
g.node("edge","Edge Runtime\n(Python service)")
g.node("infer","Inference Engine\n(TFLite/ONNX)")
g.node("buffer","Local Buffer\n(SQLite)")
g.node("apicl","REST Client")
g.node("apis","Django REST API")
g.node("core","Farm Mgmt Core\n(Django apps)")
g.node("dbc","ORM / DB Layer")
g.node("db","PostgreSQL",shape="cylinder")
g.node("ui","Web UI\n(Bootstrap)")
for a,b in [("sense","edge"),("edge","infer"),("edge","buffer"),("edge","apicl"),
   ("apicl","apis"),("apis","core"),("core","dbc"),("dbc","db"),("core","ui")]:
    g.edge(a,b)
render(g,"component_diagram")

# 14. Deployment diagram
g=newdg("dep")
with g.subgraph(name="cluster_farm") as c:
    c.attr(label="Poultry house (edge site)",style="dashed",color="black",fontname="Helvetica")
    c.node("pi","<<device>>\nRaspberry Pi 4/5",shape="box3d")
    c.node("sensors","<<device>>\nSensors & relays",shape="box3d")
    c.edge("sensors","pi")
with g.subgraph(name="cluster_cloud") as c:
    c.attr(label="Server (VPS / on-prem)",style="dashed",color="black",fontname="Helvetica")
    c.node("ng","<<container>>\nNginx")
    c.node("gu","<<container>>\nGunicorn + Django")
    c.node("pg","<<database>>\nPostgreSQL",shape="cylinder")
    c.edge("ng","gu"); c.edge("gu","pg")
g.node("client","<<device>>\nBrowser (PC/phone)",shape="box3d")
g.edge("pi","ng",label="HTTPS REST")
g.edge("client","ng",label="HTTPS")
render(g,"deployment_diagram")

# 15. Alert state diagram
g=newdg("st","LR"); g.attr("node",shape="box",style="rounded,filled",fillcolor="white")
g.node("N","NORMAL"); g.node("W","WARNING"); g.node("C","CRITICAL")
g.node("A","ACKNOWLEDGED"); g.node("R","RESOLVED")
g.edge("N","W",label="threshold breach"); g.edge("W","C",label="worsens")
g.edge("C","W",label="improves"); g.edge("W","N",label="clears (hysteresis)")
g.edge("W","A",label="user ack"); g.edge("C","A",label="user ack")
g.edge("A","R",label="corrective action"); g.edge("R","N",label="condition normal")
render(g,"alert_state_diagram")

# 16. ERD
g=newdg("erd","LR"); g.attr("node",shape="record")
def ent(n,fields): return "{"+n+"|"+"\\l".join(fields)+"\\l}"
g.node("farm",ent("FARM",["PK id","name","location","owner_id FK"]))
g.node("pen",ent("PEN",["PK id","farm_id FK","code","capacity"]))
g.node("batch",ent("BATCH",["PK id","pen_id FK","code","breed","start_date","initial_qty"]))
g.node("mort",ent("MORTALITY",["PK id","batch_id FK","date","count","cause"]))
g.node("feed",ent("FEED",["PK id","batch_id FK","date","feed_type","qty_kg"]))
g.node("health",ent("HEALTH",["PK id","batch_id FK","date","observation","treatment"]))
g.node("dev",ent("DEVICE",["PK id","pen_id FK","uuid","token","last_seen"]))
g.node("sr",ent("SENSOR_READING",["PK id","device_id FK","ts","temp","humidity","gas","level"]))
g.node("vr",ent("VISION_RESULT",["PK id","device_id FK","ts","class","confidence"]))
g.node("alert",ent("ALERT",["PK id","device_id FK","ts","type","severity","status"]))
g.node("user",ent("USER",["PK id","username","role","email"]))
for a,b in [("user","farm"),("farm","pen"),("pen","batch"),("batch","mort"),
  ("batch","feed"),("batch","health"),("pen","dev"),("dev","sr"),("dev","vr"),("dev","alert")]:
    g.edge(a,b,arrowhead="crow")
render(g,"erd")

# 17. Django application architecture
g=newdg("dj")
g.node("req","HTTP request",shape="ellipse")
for n,l in [("url","URL Router (urls.py)"),("mw","Middleware\n(auth, CSRF, sessions)"),
  ("view","Views / DRF\nViewSets"),("ser","Serializers &\nForms (validation)"),
  ("perm","Permissions /\nrole checks"),("model","Models (ORM)"),
  ("tmpl","Templates\n(Bootstrap)"),("db","PostgreSQL",)]:
    g.node(n,l, shape="cylinder" if n=="db" else "box")
g.edge("req","url");g.edge("url","mw");g.edge("mw","view");g.edge("view","perm")
g.edge("perm","ser");g.edge("ser","model");g.edge("model","db")
g.edge("view","tmpl",label="HTML"); g.edge("view","req",label="JSON / HTML",style="dashed",constraint="false")
render(g,"django_app_architecture")

# 18. REST API integration
g=newdg("api","LR")
g.node("pi","Raspberry Pi\nREST client",shape="box3d")
for n,l in [("auth","POST /api/auth\n(token)"),("read","POST /api/readings"),
  ("vis","POST /api/vision"),("hb","POST /api/heartbeat"),
  ("cfg","GET /api/config"),("alert","GET/PATCH /api/alerts")]:
    g.node(n,l)
g.node("srv","Django REST\nFramework",shape="box")
g.node("db","PostgreSQL",shape="cylinder")
for n in ["auth","read","vis","hb","cfg","alert"]:
    g.edge("pi",n); g.edge(n,"srv")
g.edge("srv","db")
render(g,"rest_api_integration")

# 19. Three-subsystem integration
g=newdg("tri")
with g.subgraph(name="cluster_iot") as c:
    c.attr(label="IoT subsystem",style="dashed",fontname="Helvetica")
    c.node("env","Environmental sensing\n& actuation")
with g.subgraph(name="cluster_ml") as c:
    c.attr(label="Machine-learning subsystem",style="dashed",fontname="Helvetica")
    c.node("cv","Computer-vision\ndistress detection")
with g.subgraph(name="cluster_web") as c:
    c.attr(label="Web subsystem",style="dashed",fontname="Helvetica")
    c.node("dj","Django farm-management\n& dashboards")
    c.node("pg","PostgreSQL",shape="cylinder")
    c.edge("dj","pg")
g.node("pi","Raspberry Pi edge runtime",shape="box3d")
g.edge("env","pi"); g.edge("cv","pi")
g.edge("pi","dj",label="REST / HTTPS")
g.edge("dj","pi",label="config / ack",style="dashed",constraint="false")
render(g,"three_subsystem_integration")

# 20. Overall system architecture (layered)
g=newdg("over")
g.node("perc","Perception: DHT22, MQ135+ADC, webcam")
g.node("edge","Edge: Raspberry Pi (validation, filtering,\nTFLite inference, control, buffering)")
g.node("comm","Communication: REST over HTTPS, token auth")
g.node("app","Application: Django + DRF, PostgreSQL,\nBootstrap dashboards, alerts, reports")
g.node("user","Users: owner, manager, worker, vet")
for a,b in [("perc","edge"),("edge","comm"),("comm","app"),("app","user")]:
    g.edge(a,b)
render(g,"overall_system_architecture")
print("DONE graphviz set 2")
