"""Prepare the existing MIT AnyBug viewer for opening a single local HTML file."""
import base64
import json
import posixpath
import re


def data_url(media, raw):
    return "data:"+media+";base64,"+base64.b64encode(raw).decode("ascii")


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError("Viewer interface has changed: " + old[:50])
    return source.replace(old,new)


def template(repo):
    def module_text(path):
        src = path.read_text()
        if path.name == "app.js":
            src = replace_once(src,'await json("./specimens/catalog.json")','[window.specimenData]')
            src = replace_once(src,'await json(base + "anatomy.json")','window.specimenData')
            src = replace_once(src,'base + specimen.model','document.getElementById("bug-model").textContent')
            src = src.replace('specimen.lengthMm + " mm body length"', '(specimen.scaleNote || specimen.lengthMm + " mm body length")')
        if path.name == "behavior-player.js":
            src = replace_once(src,'history.replaceState(history.state, "", url);','if (location.protocol !== "file:") history.replaceState(history.state, "", url);')
        if path.name == "app.js":
            src = replace_once(src,'showDialog("Field guide");', """
    const body = el("dialog-body");
    const guide = document.createDocumentFragment();
    const add = (tag,text) => {const node=document.createElement(tag); node.textContent=text; guide.append(node); return node;};
    if (specimen.observation) add("h3","About this reconstruction");
    for (const line of Object.values(specimen.observation || {})) add("p",line);
    for (const item of specimen.fieldNotes || []) {
      add("h3",item.topic);
      const paragraph=add("p",item.text+" ");
      const source=document.createElement("a");
      const [label,url]=specimen.sources[item.source];
      source.textContent=label; source.href=url; source.target="_blank"; source.rel="noopener noreferrer";
      paragraph.append(source);
    }
    body.prepend(guide);
    showDialog("Field guide");""")
            src = replace_once(src,'<span>Body length</span>', '<span>Model body length</span>')
        folder = path.parent.relative_to(repo).as_posix()
        def rewrite(m):
            dest = posixpath.normpath(posixpath.join(folder,m[2].split("?")[0]))
            return 'from "anybug/'+dest+'"'
        return re.sub(r"""\bfrom\s*(["'])(\.\.?/[^"']+)\1""",rewrite,src)
    paths = sorted([*(repo/"viewer").glob("*.js"),*(repo/"vendor/three").rglob("*.js")])
    modules = {"anybug/"+path.relative_to(repo).as_posix():data_url("text/javascript",module_text(path).encode()) for path in paths}
    # Alias three without duplicating its runtime in the HTML.
    modules["three"] = data_url("text/javascript", b'export * from "anybug/vendor/three/build/three.module.min.js";')
    html = (repo/"index.html").read_text()
    css = (repo/"viewer/style.css").read_text()
    css = re.sub(r'url\(\.\./vendor/fonts/([\w.-]+)\)',lambda m:"url("+data_url("font/woff2",(repo/"vendor/fonts"/m[1]).read_bytes())+")",css)
    html = html.replace("viewer/mark.svg",data_url("image/svg+xml",(repo/"viewer/mark.svg").read_bytes()))
    html = html.replace('href="./" aria-label="AnyBug home"', 'href="#" aria-label="Specimen home"')
    html = re.sub(r'<link rel="stylesheet"[^>]+>',lambda _: "<style>"+css+"</style>",html)
    html = re.sub(r'<script type="importmap">.*?</script>',lambda _:'<script type="importmap">'+json.dumps({"imports":modules})+'</script>',html,flags=re.S)
    scripts = ('<script id="bug-data" type="application/json">__ANYBUG_DATA__</script>'
               '<script id="bug-model" type="text/plain">__ANYBUG_MODEL__</script>'
               '<script>window.specimenData=JSON.parse(document.getElementById("bug-data").textContent);</script>'
               '<script type="module">import "anybug/viewer/app.js";</script>')
    html = replace_once(html,'<script type="module" src="viewer/app.js?v=3"></script>',scripts)
    notices = [repo/"LICENSE",repo/"vendor/three/LICENSE",*sorted((repo/"vendor/fonts").glob("*LICENSE.txt"))]
    from html import escape
    return html.replace('</body>', '<template id="licenses">'+escape("\n\n".join(p.read_text() for p in notices))+'</template></body>')


def render(manifest, glb, skill):
    packed = skill/"assets/viewer.html.gz"
    if packed.is_file():
        import gzip
        tpl = gzip.decompress(packed.read_bytes()).decode()
    else:
        tpl = template(skill.parent.parent)
    # Insert data last so literal placeholder strings in field notes stay inert.
    return tpl.replace("__ANYBUG_MODEL__",data_url("model/gltf-binary",glb)).replace(
        "__ANYBUG_DATA__",json.dumps(manifest,allow_nan=False).replace("<","\\u003c"))
