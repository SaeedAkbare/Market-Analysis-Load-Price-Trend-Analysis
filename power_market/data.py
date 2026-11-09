"""Explicit interval ingestion; raw XML retains resolution and source units."""
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET
import pandas as pd
import requests

ZONE = '10Y1001A1001A82H'
BORDERS = {'AT':'10YAT-APG------L','BE':'10YBE----------2','CH':'10YCH-SWISSGRIDZ',
           'CZ':'10YCZ-CEPS-----N','DK1':'10YDK-1--------W','DK2':'10YDK-2--------M',
           'FR':'10YFR-RTE------C','NL':'10YNL----------L','NO2':'10YNO-2--------T',
           'PL':'10YPL-AREA-----S','SE4':'10Y1001A1001A47J'}
START = pd.Timestamp('2024-01-01', tz='Europe/Berlin')
END = pd.Timestamp('2025-01-01', tz='Europe/Berlin')

def parse_xml(raw, unit):
    root = ET.fromstring(raw)
    for element in root.iter():
        element.tag = element.tag.split('}')[-1]
    rows = []
    for ts in root.findall('.//TimeSeries'):
        actual = ts.findtext('price_Measure_Unit.name') or ts.findtext('quantity_Measure_Unit.name')
        if actual != unit or (unit == 'MWH' and ts.findtext('currency_Unit.name') != 'EUR'):
            raise ValueError('Unexpected units/currency')
        if ts.findtext('curveType') not in (None, 'A01'):
            raise ValueError('Unsupported curve type; explicit interval review required')
        for period in ts.findall('Period'):
            step = {'PT15M':15, 'PT30M':30, 'PT60M':60}.get(period.findtext('resolution'))
            if step is None:
                raise ValueError('Unsupported resolution')
            start = pd.Timestamp(period.findtext('timeInterval/start'))
            end = pd.Timestamp(period.findtext('timeInterval/end'))
            if start.tzinfo is None or end.tzinfo is None:
                raise ValueError('Timezone missing')
            for point in period.findall('Point'):
                t = start + pd.Timedelta(minutes=step*(int(point.findtext('position'))-1))
                if t < start or t + pd.Timedelta(minutes=step) > end:
                    raise ValueError('Point outside period')
                rows.append((t, step, float(point.findtext('price.amount') or point.findtext('quantity'))))
    if not rows:
        raise ValueError('No observations returned')
    return pd.DataFrame(rows, columns=['start','minutes','value'])

def align(frame, start=START, end=END):
    """Expand explicit intervals to quarter hours; never fill across missing intervals."""
    frame = frame.drop_duplicates().sort_values('start')
    values = {}
    for row in frame.itertuples():
        if not pd.notna(row.value) or row.minutes not in (15,30,60):
            raise ValueError('Invalid observation')
        t = pd.Timestamp(row.start)
        if t.tzinfo is None or t.minute % 15 or t.second or t.microsecond:
            raise ValueError('Invalid timestamp')
        for stamp in pd.date_range(t, periods=row.minutes//15, freq='15min').tz_convert('UTC'):
            if stamp in values:
                raise ValueError('Conflicting duplicate or overlapping interval')
            values[stamp] = row.value
    index = pd.date_range(start.tz_convert('UTC'), end.tz_convert('UTC'), freq='15min', inclusive='left')
    return pd.Series(values, dtype=float).reindex(index)

def specifications():
    yield 'price', 'MWH', dict(documentType='A44', in_Domain=ZONE, out_Domain=ZONE)
    yield 'demand', 'MAW', dict(documentType='A65', processType='A16', outBiddingZone_Domain=ZONE)
    for name, code in [('solar','B16'),('wind_offshore','B18'),('wind_onshore','B19')]:
        yield name, 'MAW', dict(documentType='A75', processType='A16', in_Domain=ZONE, psrType=code)
    for name, zone in BORDERS.items():
        for direction, source, target in [('import',zone,ZONE),('export',ZONE,zone)]:
            yield f'{name}_{direction}', 'MAW', dict(documentType='A11', out_Domain=source, in_Domain=target)

def retrieve(folder='data/raw'):
    key = os.environ.get('ENTSOE_API_KEY')
    if not key:
        raise RuntimeError('Set ENTSOE_API_KEY; no empirical analysis has been produced.')
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    result = {}
    months = pd.date_range(START, END, freq='MS')
    for name, unit, params in specifications():
        chunks = []
        for a,b in zip(months[:-1],months[1:]):
            path = folder / f'{name}_{a:%Y%m}.xml'
            query = dict(params, periodStart=a.tz_convert('UTC').strftime('%Y%m%d%H%M'), periodEnd=b.tz_convert('UTC').strftime('%Y%m%d%H%M'))
            if not path.exists():
                try:
                    response = requests.get('https://web-api.tp.entsoe.eu/api', params=dict(query,securityToken=key), timeout=90)
                except requests.RequestException:
                    raise RuntimeError(f'Request failed for {name}; credentials omitted') from None
                if response.status_code != 200:
                    raise RuntimeError(f'HTTP {response.status_code} for {name}; response URL suppressed')
                parse_xml(response.content, unit)
                path.write_bytes(response.content)
                path.with_suffix('.json').write_text(json.dumps(dict(query=query, unit=unit, retrieved_utc=pd.Timestamp.now(tz='UTC').isoformat(), sha256=hashlib.sha256(response.content).hexdigest()), indent=2))
            chunks.append(parse_xml(path.read_bytes(), unit))
        result[name] = align(pd.concat(chunks, ignore_index=True))
    return pd.DataFrame(result)
