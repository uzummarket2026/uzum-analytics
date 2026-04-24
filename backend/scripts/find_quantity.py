import json

with open('uzum_openapi.json', encoding='utf-8') as f:
    data = json.load(f)

print("=== Qoldiq (Stock) maydonlari topildi: ===")
schemas = data.get('components', {}).get('schemas', {})
for s_name, s_data in schemas.items():
    props = s_data.get('properties', {})
    q_fields = [p for p in props if 'quantity' in p.lower()]
    if q_fields:
        print(f"Sxema: {s_name}")
        for f in q_fields:
            desc = props[f].get('description', 'Tavsif yo\'q')
            print(f"  - {f}: {desc}")
