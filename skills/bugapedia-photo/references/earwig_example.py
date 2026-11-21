"""Worked reference, not an identification template. Prints the editable JSON."""
import json
from math import cos, sin, pi

sources = {
    "photo":["Jack Kelly Clark, UC IPM · Adult male on fruit","https://ipm.ucanr.edu/PMG/F/I-DM-FAUR-AD.005.html"],
    "uf":["University of Florida · European earwig","https://ask.ifas.ufl.edu/publication/IN875"],
    "gut":["NC State · Insect digestive system","https://genent.cals.ncsu.edu/bug-bytes/digestive-system/"],
    "air":["NC State · Insect respiratory system","https://genent.cals.ncsu.edu/bug-bytes/respiratory-system/"],
    "heart":["NC State · Insect circulatory system","https://genent.cals.ncsu.edu/bug-bytes/circulatory-system/"],
    "nerve":["NC State · Insect nervous system","https://genent.cals.ncsu.edu/nervous/"],
}
parts, controls, tracks, spread = [], {}, {}, {}
ex = "exterior"
observed = "Visible in the reference photograph"
inferred = "Comparative reconstruction"
reference = "Species reference"
def egg(c,p,r):
    return {"kind":"ellipsoid","center":p,"radii":r,"color":c}
def tube(c,points,radii):
    return {"kind":"tube","color":c,"points":points,"radii":radii}
def shell(c, sections):
    rings = [[[x+w*cos(2*pi*k/24),y+h*sin(2*pi*k/24),z] for k in range(24)] for x,y,z,w,h in sections]
    return {"kind":"loft","color":c,"rings":rings}
def part(key,name,term,system,parent,pivot,shapes,source,evidence,short,detail,offset):
    parts.append(dict(id=key,name=name,term=term,system=system,parent=parent,pivot=pivot,shapes=shapes,
                      source=source,evidence=evidence,short=short,detail=detail))
    spread[key]=offset
def pose(t, y=0, z=0, x=0, shift=None):
    return [t,[x,y,z],shift or [0,0,0]]

part("thorax","Chest","Thorax",ex,None,[0,0,-2.9],
     [shell("#56352a",[(0,.05,-4.5,.68,.36),(0,.09,-4.3,1,.48),(0,.1,-2.2,1.17,.5),(0,0,-1.1,.98,.43)])],
     "uf",reference,"All six legs meet the body here.","Three thoracic segments carry the legs. The wing-bearing segments lie behind the front shield.",[0,0,-.8])
part("head","Head","Head capsule",ex,"thorax",[0,.12,-4.38],
     [shell("#4a271d",[(0,.1,-6.16,.32,.2),(0,.18,-5.85,.71,.39),(0,.2,-5.18,.9,.47),(0,.15,-4.52,.65,.35)])],
     "photo",observed,"Look for the dark head between the two feelers.","The broad capsule narrows toward the mouth. Some of its front edge is obscured against the fruit.",[0,.9,-2.7])
part("shield","Front shield","Pronotum",ex,"thorax",[0,.45,-3.9],
     [shell("#886248",[(0,.47,-4.42,.76,.12),(0,.49,-4.22,1.02,.2),(0,.52,-3.35,1.06,.19),(0,.46,-3.16,.94,.1)])],
     "photo",observed,"This shield sits right behind the head.","Its pale sides contrast with the darker midline and wing covers.",[0,2,-1])
for j in range(8):
    z = -.85+j*.78
    width = 1.07+.23*sin((j+1)*pi/9)-max(0,j-4)*.105
    key=f"plate_{j+1}"
    part(key,f"Abdominal plate {j+1}","Abdominal cuticle",ex,"thorax",[0,.09,z],
         [shell(("#392322","#402825")[j%2],[(0,0,z-.45,width*.86,.40),(0,.05,z-.31,width,.51),
                                    (0,.08,z+.24,width*1.02,.48),(0,.10,z+.41,width*.96,.40)])],
         "photo",observed,"A dark band protects this stretch of belly.","The stepped, overlapping plates model the bands exposed behind the short forewings. The visible divisions are simplified.",[0,1.25+.20*j,(j-2)*.58])
for side,sign in (("left",-1),("right",1)):
    side_name=side.capitalize()
    def keyed(name): return side+"_"+name
    def mx(x,y,z): return [sign*x,y,z]
    def add(name,label,term,parent,pivot,shapes,source,evidence,short,detail,offset):
        part(keyed(name),side_name+" "+label,term,ex,parent,pivot,shapes,source,evidence,short,detail,offset)
    add("eye","eye","Compound eye","head",mx(.77,.26,-5.56),[egg("#23191c",mx(.75,.31,-5.55),[.24,.23,.30])],
        "uf",reference,"This eye samples light from many directions.","The rounded surface stands in for the many facets of a compound eye.",mx(1.5,.8,-.2))
    points=[mx(x,y,z) for x,y,z in [(0.49,.23,-5.95),(.89,.31,-6.55),(1.38,.46,-7.15),(1.94,.62,-7.84),(2.55,.65,-8.46),(3.19,.81,-9.02)]]
    shapes=[tube("#8e613a",points,[.11,.09,.075,.061,.051,.035])]
    for a,b in zip(points,points[1:]):
        for t in (.15,.60):
            q=[u+t*(v-u) for u,v in zip(a,b)]
            shapes.append(egg("#a77d53",q,[.078,.076,.094]))
    add("antenna","feeler","Antenna","head",points[0],shapes,"photo",observed,"The long feeler reaches past the head.",
        "The tapered, jointed form follows the visible outline. Small joints are grouped as one movable feeler.",mx(1.4,1.1,-1.9))
    tracks[keyed("antenna")]=[pose(0),pose(.55,sign*19,sign*5),pose(1.1,-sign*10),pose(1.65,sign*15),pose(2),pose(5),pose(6,sign*9),pose(7)]
    add("jaw","jaw","Mandible","head",mx(.29,.01,-5.96),
        [tube("#714c32",[mx(.29,.01,-5.96),mx(.4,-.02,-6.2),mx(.18,-.05,-6.37)],[.14,.12,.034])],
        "uf",reference,"A pair of jaws grips and chews food.","The mouth is tucked beneath the front of the head. The tooth shape here is illustrative.",mx(.8,-.8,-1.3))
    wing_z=[(-3.25,.46,.34,.10),(-2.99,.53,.48,.20),(-2.0,.59,.55,.20),(-1.32,.52,.52,.13)]
    add("cover","short wing cover","Tegmen","thorax",mx(.68,.51,-3.22),
        [shell("#61483d",[(sign*x,.47,z,w,h) for z,x,w,h in wing_z])],
        "photo",observed,"The short forewing covers the folded flight wing.","Both covers end well before the rear of the abdomen, leaving its dark bands visible.",mx(1.4,2.2,-.8))
    controls[keyed("cover")]={"open":"Lift wing cover","close":"Lower wing cover","angles":[-32,sign*17,sign*37]}
    add("wing","folded hindwing","Membranous hindwing","thorax",mx(.62,.37,-3.01),
        [shell("#bb9563",[(sign*.55,.37,-3.05,.33,.065),(sign*.56,.38,-2.55,.42,.072),(sign*.51,.39,-1.38,.37,.05)])],
        "uf",reference,"The thin flight wing folds beneath the cover.","The folded packet is shown in its resting position. Its internal crease pattern is simplified.",mx(1.7,1.3,.3))
    for j,(base_z,mid_z,end_z) in enumerate([(-3.97,-4.56,-5.01),(-3.04,-2.97,-3.35),(-2.19,-1.20,-.43)]):
        limb=["front","middle","hind"][j]
        pts=[mx(.74,-.02,base_z),mx(1.13,.02,base_z-.1),mx(1.93,.20,mid_z),mx(2.52,-.36,end_z),mx(2.78,-.52,end_z-.22),mx(3.05,-.55,end_z-.28)]
        add(limb+"_leg",limb+" leg","Thoracic walking leg","thorax",pts[0],
            [tube("#bc905b",pts,[.18,.22,.16,.105,.07,.032]),egg("#d0a571",pts[2],[.15,.14,.14])],
            "photo",observed,"The pale jointed leg plants a foot on the surface.","Follow the thicker thigh outward to the slimmer shin and foot. The segments move together around the hip in this teaching gait.",mx(1.5,-1,j-1))
        frames=[pose(0),pose(2)]
        for n in range(1,13):
            phase=n*pi/2+(j+(1 if sign<0 else 0))*pi
            frames.append(pose(2+n*.22,sign*14*sin(phase),sign*9*max(0,sin(phase))))
        frames += [pose(5),pose(7)]
        tracks[keyed(limb+"_leg")]=frames
    pinc=[mx(x,y,z) for x,y,z in [(.6,.13,4.91),(.83,.17,5.4),(1.17,.21,5.97),(1.42,.30,6.58),(1.40,.36,7.13),(1.13,.38,7.58),(.63,.40,7.85),(.26,.41,7.88)]]
    add("forceps","pincer","Forceps-like cercus","plate_8",pinc[0],
        [tube("#38251f",pinc,[.26,.25,.205,.176,.15,.118,.075,.027]),
         tube("#513527",[pinc[2],mx(.95,.23,6.13)],[.12,.025])],
        "photo",observed,"Drag this curved pincer to open it.","These paired appendages are at the rear of the abdomen. The inward curve is particularly pronounced in this photographed male.",mx(1.45,.35,2.45))
    controls[keyed("forceps")]={"open":"Open pincer","close":"Close pincer","angles":[0,sign*32,0]}
    tracks[keyed("forceps")]=[pose(0),pose(5),pose(5.55,sign*32),pose(6.18,sign*32),pose(6.48,-sign*3),pose(7)]
# Internal volumes are placed between the dorsal and ventral cuticle.
def organ(key,name,term,system,pivot,shapes,source,short,detail,offset):
    part(key,name,term,system,"thorax",pivot,shapes,source,inferred,short,detail,offset)
organ("gut","Digestive tract","Alimentary canal","digestive",[0,.04,0],
      [tube("#b08866",[[0,.03,-5.94],[0,.02,-4.6],[.10,.07,-3.2],[.07,.03,-1.5],[-.14,.03,-.2],[.09,0,1.3],[.16,0,2.4],[0,.03,4.77]],[.07,.13,.22,.26,.32,.29,.18,.11])],
      "gut","Food passes through this long tube.","The widened middle region represents digestion and absorption. Its exact course beneath the plates is inferred.",[-2,-.4,1])
organ("dorsal_vessel","Heart tube","Dorsal vessel","circulatory",[0,.31,1],
      [tube("#b87673",[[0,.25,-4.6],[0,.30,-2],[0,.31,.8],[0,.31,2.6],[0,.30,4.5]],[.05,.07,.10,.11,.09])],
      "heart","This tube moves the insect’s circulating fluid forward.","It runs near the back wall above the gut. Its color is a teaching approximation.",[1,2,1.4])
organ("nerve_cord","Belly nerve cord","Ventral nerve cord","nervous",[0,-.25,0],
      [tube("#d7bc83",[[0,-.20,-4.9],[0,-.27,-3.2],[0,-.27,-1],[0,-.26,1.8],[0,-.23,4.25]],[.05,.055,.06,.052,.046])]+
      [egg("#cdb382",[0,-.25,z],[.13,.075,.18]) for z in [-3.8,-2.85,-1.95,-.4,1.2,2.8,4.1]],
      "nerve","Signals travel along the underside of the body.","The swellings represent ganglia. Their spacing illustrates the general insect arrangement.",[0,-1.7,1.5])
organ("brain","Brain","Supraoesophageal ganglion","nervous",[0,.31,-5.35],
      [egg("#d8b978",[x,.31,-5.36],[.29,.15,.23]) for x in [-.16,.16]],
      "nerve","The brain receives signals from the eyes and feelers.","The paired lobes are inferred from insect anatomy and sit above the front of the gut.",[.9,1.6,-1.5])
for sign,side in [(-1,"left"),(1,"right")]:
    pts=[[sign*.72,.10,z] for z in [-3.8,-1,.8,2.4,4.3]]
    shapes=[tube("#c6b89c",pts,[.055,.075,.075,.06,.04])]
    for z in [-2.9,-.8,.8,2.2,3.6]:
        shapes.append(tube("#c6b89c",[[sign*.72,.1,z],[sign*.88,.1,z+.1],[sign*.96,.02,z+.2]],[.05,.035,.02]))
    organ(side+"_air",side.capitalize()+" air tubes","Tracheal trunk and branches","respiratory",pts[0],shapes,
          "air","Small tubes bring air directly to the tissues.","The branches mark a few representative paths. The photo cannot resolve their number or exact routing.",[sign*1.6,-.3,.7])

spec={
    "id":"earwig-study","name":"European earwig","scientific":"Forficula auricularia","stage":"Adult male",
    "lengthMm":12,"scaleNote":"12 mm illustrative body length, excluding forceps. The photograph has no scale.",
    "focus":"left_forceps","landmarks":["left_forceps","shield","right_antenna","left_front_leg"],
    "title":"How the earwig opens its pincers","overview":"Start at the curved tips behind the abdomen. Open one pincer, then follow the exposed bands forward to the short wing covers.",
    "dragHint":"Drag a rear pincer to open it","gestureGuide":"Drag a rear pincer or short wing cover upward to open it.",
    "view":{"radius":10.6,"target":[0,.1,-.4],"direction":[-.7,1.48,-.82],"floor":-.59},
    "systems":{k:{"name":n,"color":c} for k,n,c in [
        (ex,"Exterior","#785644"),("digestive","Digestion","#d7803a"),("respiratory","Breathing","#39a394"),
        ("circulatory","Circulation","#c95868"),("nervous","Nerves and senses","#956aba")]},
    "sources":sources,"parts":parts,"controls":controls,"spread":spread,
    "observation":{"identification":"The UC IPM photograph identifies an adult male European earwig. The model follows that identification.",
      "visible":"The picture shows curved rear forceps, exposed dark abdominal bands, pale walking legs and thin feelers.",
      "reconstructed":"The underside, concealed wings and internal organs use published anatomy. The motion timing is illustrative.",
      "unresolved":"Body size, individual internal geometry and the far-side details cannot be measured from this angle."},
    "fieldNotes":[{"topic":"Where to look","text":"Adults often shelter in dark, confined places by day and emerge at night.","source":"uf"},
      {"topic":"What it eats","text":"Earwigs can feed on plant material and on small animals. Fruit in a photograph gives context but cannot establish what the animal just ate.","source":"uf"},
      {"topic":"Young earwigs","text":"The female tends her eggs. The young resemble small adults and gain more developed wings as they mature.","source":"uf"}],
    "behavior":{"clip":"AN_Earwig_FieldSequence","duration":7,"frameScale":1.14,"sourceIds":["uf","photo"],
      "actions":[{"start":0,"name":"Sweep the feelers","note":"Follow one antenna as it samples the space ahead."},
        {"start":2,"name":"Step in place","note":"Watch alternating groups of legs swing through a slowed teaching gait."},
        {"start":5,"name":"Open and close the forceps","note":"Look at the gap between the curved tips as the two sides open and draw together."}],"tracks":tracks}}
if __name__=="__main__":
    print(json.dumps(spec,indent=2))
