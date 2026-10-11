# -*- coding: utf-8 -*-
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

with open('scratch/generated_index.py', 'r', encoding='utf-8') as f:
    new_index_html = f.read().strip()

start_marker = 'INDEX_HTML = """'
end_marker = '"""\n\n\n@app.get("/")'

# Check if markers exist
start_idx = content.find(start_marker)
if start_idx == -1:
    raise Exception("Could not find start marker: " + start_marker)

end_idx = content.find(end_marker, start_idx)
if end_idx == -1:
    raise Exception("Could not find end marker: " + end_marker)

# Replace INDEX_HTML
new_content = content[:start_idx] + new_index_html + "\n\n\n"

# Now let's handle the @app.get("/") route and add Cache-Control headers
rest = content[end_idx + len('"""\n\n\n'):]

old_route = '''@app.get("/")
def index():
    return Response(INDEX_HTML.replace("__APP_NAME__", APP_NAME), mimetype="text/html")'''

new_route = '''@app.get("/")
def index():
    resp = Response(INDEX_HTML.replace("__APP_NAME__", APP_NAME), mimetype="text/html")
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp'''

if old_route in rest:
    rest = rest.replace(old_route, new_route, 1)
else:
    print("Notice: old_route string format didn't match exactly, checking...")

new_content += rest

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Successfully replaced INDEX_HTML and updated index() route in app.py")
