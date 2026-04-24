import json

with open('uzum_openapi.json', encoding='utf-8') as f:
    data = json.load(f)

paths = data.get('paths', {})
print(f"Jami endpointlar: {len(paths)}\n")
print("=== BARCHA ENDPOINTLAR ===")
for path in sorted(paths.keys()):
    methods = list(paths[path].keys())
    for method in methods:
        info = paths[path][method]
        summary = info.get('summary', '')
        print(f"  [{method.upper()}] {path} — {summary}")
