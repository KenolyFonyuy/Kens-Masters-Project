import os
from graphviz import Digraph, Graph
OUT = "/tmp/diagrams"
os.makedirs(OUT, exist_ok=True)

# ---- monochrome StarUML-like defaults ----
NODE = dict(shape="box", style="filled", fillcolor="white", color="black",
            fontname="Helvetica", fontcolor="black", fontsize="13")
GRAPHA = dict(bgcolor="white", fontname="Helvetica", fontsize="13", color="black")
EDGE = dict(color="black", fontname="Helvetica", fontcolor="black", fontsize="11")

def newdg(name, rankdir="TB"):
    g = Digraph(name)
    g.attr(rankdir=rankdir, **GRAPHA)
    g.attr("node", **NODE)
    g.attr("edge", **EDGE)
    return g

def render(g, name):
    g.render(filename=name, directory=OUT, format="pdf", cleanup=True)
    print("rendered", name)

# 1. Iterative development lifecycle
g = newdg("iter")
g.attr(rankdir="LR")
for n,l in [("p","Planning &\nRequirements"),("d","Design"),("b","Build /\nImplement"),
            ("t","Test &\nEvaluate"),("e","Evaluate vs.\nacceptance criteria")]:
    g.node(n,l)
g.edge("p","d"); g.edge("d","b"); g.edge("b","t"); g.edge("t","e")
g.edge("e","p", label="feedback / refine", constraint="false", style="dashed")
g.node("rel","Increment\naccepted &\nintegrated", shape="box", style="filled,bold", fillcolor="white")
g.edge("e","rel", label="exit criterion met")
render(g,"iterative_lifecycle")

# 2. Complete system workflow
g = newdg("wf")
seq = [("s","Sensors read\n(DHT22, MQ135+ADC)"),
       ("cam","Webcam captures\nframe"),
       ("val","Raspberry Pi validates\n& filters input"),
       ("inf","TFLite/YOLO\ninference"),
       ("eval","Evaluate environmental\n& visual risk"),
       ("act","Actuate fan/heater\n(hysteresis)"),
       ("buf","Buffer locally\n(SQLite)"),
       ("api","POST to Django\nREST API"),
       ("db","PostgreSQL\nstores records"),
       ("dash","Dashboards &\nalerts updated"),
       ("user","User acknowledges\n& resolves alert")]
for n,l in seq: g.node(n,l)
for i in range(len(seq)-1): g.edge(seq[i][0], seq[i+1][0])
g.edge("buf","api", label="on reconnect", style="dashed")
render(g,"system_workflow")

# 3. Hardware architecture
g = newdg("hw")
g.node("pi","Raspberry Pi 4/5\n(edge controller)", shape="box3d")
g.node("dht","DHT22\nTemp/Humidity")
g.node("mq","MQ135\nGas/ammonia risk")
g.node("adc","MCP3008 / ADS1115\nADC")
g.node("cam","USB webcam /\nPi camera")
g.node("relay","2-channel\nrelay module")
g.node("fan","Ventilation fan")
g.node("heat","Heater / heat lamp")
g.node("psu","5V regulated PSU\n+ mains isolation")
g.edge("dht","pi", label="1-wire GPIO")
g.edge("mq","adc", label="analogue")
g.edge("adc","pi", label="SPI / I2C")
g.edge("cam","pi", label="USB / CSI")
g.edge("pi","relay", label="GPIO")
g.edge("relay","fan", label="switched mains")
g.edge("relay","heat", label="switched mains")
g.edge("psu","pi")
render(g,"hardware_architecture")

# 4. Sensor acquisition workflow
g = newdg("sa")
nodes=[("init","Initialise sensors\n& warm-up gas sensor"),
 ("read","Read DHT22 & ADC\nat sampling interval"),
 ("stamp","Timestamp + device/pen ID"),
 ("valid","Range / plausibility check"),
 ("filt","Moving-median filter\n& outlier rejection"),
 ("miss","Handle missing /\nNaN values"),
 ("log","Append to local log"),
 ("send","Queue for REST transmission")]
for n,l in nodes: g.node(n,l)
for i in range(len(nodes)-1): g.edge(nodes[i][0],nodes[i+1][0])
g.edge("valid","read", label="invalid: retry", style="dashed", constraint="false")
render(g,"sensor_acquisition_workflow")

# 5. Environmental control algorithm (flowchart)
g = newdg("ctrl")
g.node("start","Read filtered\ntemp / humidity / gas", shape="ellipse")
g.node("crit","Any value in\nCRITICAL band?", shape="diamond")
g.node("warn","Any value in\nWARNING band?", shape="diamond")
g.node("hot","Temp high?", shape="diamond")
g.node("cold","Temp low?", shape="diamond")
g.node("fan","Enforce min-on/off,\nswitch FAN on", )
g.node("heater","Enforce min-on/off,\nswitch HEATER on")
g.node("alertC","Raise CRITICAL alert")
g.node("alertW","Raise WARNING alert")
g.node("normal","State NORMAL\n(respect hysteresis)")
g.node("end","Log state & actuator action", shape="ellipse")
g.edge("start","crit")
g.edge("crit","alertC", label="yes")
g.edge("crit","warn", label="no")
g.edge("alertC","hot")
g.edge("warn","alertW", label="yes")
g.edge("warn","normal", label="no")
g.edge("alertW","hot")
g.edge("hot","fan", label="yes")
g.edge("hot","cold", label="no")
g.edge("cold","heater", label="yes")
g.edge("cold","normal", label="no")
g.edge("fan","end"); g.edge("heater","end"); g.edge("normal","end")
render(g,"environmental_control_algorithm")

# 6. ML development pipeline
g = newdg("mlp"); g.attr(rankdir="LR")
nodes=[("acq","Acquire public\ndataset (RGB)"),
 ("local","Collect local\nGreenFarms images"),
 ("frame","Extract video\nframes"),
 ("clean","Remove duplicate /\ncorrupt images"),
 ("anno","Annotate &\nverify labels"),
 ("eda","Exploratory\ndata analysis"),
 ("aug","Augment"),
 ("split","Split train/val/test\n(no frame leakage)"),
 ("tl","Transfer learning\n(YOLO / EfficientNet)"),
 ("train","Iterative training\non Colab GPU"),
 ("tune","Hyperparameter\ntuning"),
 ("evalm","Evaluate\n(mAP, P, R, F1)"),
 ("exp","Export TFLite /\nONNX / NCNN")]
for n,l in nodes: g.node(n,l)
for i in range(len(nodes)-1): g.edge(nodes[i][0],nodes[i+1][0])
g.edge("evalm","tune", label="below target", style="dashed", constraint="false")
render(g,"ml_pipeline")

# 7. ML inference flow (on Pi)
g = newdg("mli")
nodes=[("cap","Capture frame"),
 ("pre","Preprocess\n(resize, normalise)"),
 ("skip","Frame-skip /\nrate control", "diamond"),
 ("model","Run quantised model"),
 ("conf","Confidence >\nthreshold?","diamond"),
 ("agg","Aggregate over\nN frames"),
 ("flag","Flag visible\nrisk class"),
 ("hum","Queue for human\nverification"),
 ("post","POST result via REST")]
for t in nodes:
    if len(t)==3: g.node(t[0],t[1],shape=t[2])
    else: g.node(t[0],t[1])
g.edge("cap","pre"); g.edge("pre","skip"); g.edge("skip","model", label="process")
g.edge("skip","cap", label="skip", style="dashed", constraint="false")
g.edge("model","conf"); g.edge("conf","agg", label="yes"); g.edge("conf","cap", label="no", style="dashed", constraint="false")
g.edge("agg","flag"); g.edge("flag","hum"); g.edge("hum","post")
render(g,"ml_inference_flow")
