import json, os

fpath = os.path.join('models', 'feature_names.json')
data = json.load(open(fpath))
print(f'feature_names.json: {len(data)} features')
print(data)

w = json.load(open(os.path.join('models', 'weights.json')))
print(f'weights: {w}')

for f in ['bpnn.pt', 'rf.pkl', 'xgb.json']:
    exists = os.path.exists(os.path.join('models', f))
    print(f'{f}: {"✅" if exists else "❌"}')
