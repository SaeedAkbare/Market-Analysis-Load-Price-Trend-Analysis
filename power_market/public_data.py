"""Token-free Energy-Charts v2 retrieval with explicit metadata validation."""
import hashlib
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from .data import align, START, END

BASE = 'https://api.energy-charts.info/v2/'
BORDERS = ['austria','belgium','czech_republic','denmark','france','luxembourg',
           'netherlands','norway','poland','sweden','switzerland']

def download(endpoint, params, folder):
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    identity = hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:16]
    path = folder / f'{endpoint}_{identity}.json'
    meta = path.with_suffix('.meta.json')
    if path.exists() and meta.exists():
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != json.loads(meta.read_text())['sha256']:
            raise ValueError('Cache hash mismatch')
        return json.loads(raw)
    for attempt in range(4):
        response = requests.get(BASE+endpoint, params=params, timeout=120)
        if response.status_code not in (429, 502, 503, 504):
            response.raise_for_status(); break
        delay = float(response.headers.get('Retry-After', 30))
        if delay > 60 or attempt == 3:
            raise RuntimeError(f'Source busy; retry after {delay} seconds')
        time.sleep(max(0,delay))
    payload = response.json()
    if payload.get('endpoint') != endpoint:
        raise ValueError('Unexpected API response')
    raw = response.content
    path.write_bytes(raw)
    meta.write_text(json.dumps(dict(url=response.url, retrieved_utc=pd.Timestamp.now(tz='UTC').isoformat(),
        sha256=hashlib.sha256(raw).hexdigest(), license=payload.get('license'),
        metadata={k:v for k,v in payload.items() if k!='data'}), indent=2), encoding='utf-8')
    return payload

def parse(payload, endpoint, unit, mapping, start=START, end=END):
    if payload.get('schema_version') != '2.0' or payload.get('endpoint') != endpoint:
        raise ValueError('Unsupported schema/endpoint')
    if payload.get('unit') != unit or payload.get('timezone') != 'Europe/Berlin':
        raise ValueError('Unexpected units/timezone')
    if payload.get('country') != 'de' or (endpoint=='price' and payload.get('bidding_zone')!='DE-LU'):
        raise ValueError('Unexpected geography')
    step = payload.get('interval_minutes')
    if step not in (15,30,60):
        raise ValueError('Mixed or unsupported resolution; split request at the transition')
    series = {s['id']:s for s in payload['series']}
    if not set(mapping).issubset(series):
        raise ValueError('Required series missing')
    result = {}
    for source,target in mapping.items():
        if series[source].get('unit',unit) != unit:
            raise ValueError('Unexpected series unit')
        rows=[]
        for record in payload['data']:
            t=pd.Timestamp(record['timestamp'])
            if t.tzinfo is None:
                raise ValueError('Naive timestamp')
            value=record['values'].get(source)
            if value is None:
                continue  # explicit null remains a gap in the canonical grid
            if not np.isfinite(value):
                raise ValueError('Nonfinite value')
            rows.append((t,step,float(value)*(1000 if unit=='GW' else 1)))
        result[target]=align(pd.DataFrame(rows,columns=['start','minutes','value']),start,end)
    return pd.DataFrame(result)

def retrieve(folder='data/energy_charts'):
    period=dict(start='2024-01-01',end='2024-12-31')
    price=download('price',dict(period,bzn='DE-LU'),folder)
    power=download('public_power',dict(period,country='de'),folder)
    flows=download('cbpf',dict(period,country='de'),folder)
    if flows.get('attributes',{}).get('sign_convention') != 'positive = import, negative = export':
        raise ValueError('Unrecognised physical-flow sign convention')
    p=parse(price,'price','EUR / MWh',{'day_ahead_price':'price'})
    g=parse(power,'public_power','MW',{'load':'demand','wind_onshore':'wind_onshore','wind_offshore':'wind_offshore','solar':'solar'})
    f=parse(flows,'cbpf','GW',{s:s for s in BORDERS+['sum']})
    # Provider values are rounded to 0.001 GW per border; allow rounding only.
    total=f[BORDERS].sum(axis=1,min_count=len(BORDERS))
    valid=total.notna() & f['sum'].notna()
    if (total[valid]-f.loc[valid,'sum']).abs().gt(12).any():
        raise ValueError('Border total disagrees with provider sum')
    result=pd.concat([p,g],axis=1)
    for border in BORDERS:
        result[border+'_import']=f[border].clip(lower=0)
        result[border+'_export']=(-f[border]).clip(lower=0)
    return result
