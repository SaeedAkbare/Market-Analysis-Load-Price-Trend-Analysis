import pandas as pd

def fundamentals(frame):
    x = frame.copy()
    x['wind'] = x[['wind_onshore','wind_offshore']].sum(axis=1, min_count=2)
    x['renewables'] = x['wind'] + x['solar']
    x['residual_load'] = x['demand'] - x['renewables']
    imports = x.filter(regex='_import$')
    exports = x.filter(regex='_export$')
    x['net_import'] = imports.sum(axis=1, min_count=len(imports.columns)) - exports.sum(axis=1, min_count=len(exports.columns))
    return x

def daily(frame):
    x = frame.tz_convert('Europe/Berlin')
    groups = x.resample('D')
    out = groups.mean()
    expected = pd.Series([int(((d + pd.DateOffset(days=1)).tz_convert('UTC')-d.tz_convert('UTC')).total_seconds()/900) for d in out.index], index=out.index)
    complete = groups['price'].count().eq(expected)
    out['spread'] = (groups['price'].max()-groups['price'].min()).where(complete)
    out['negative_hours'] = x['price'].lt(0).resample('D').sum().mul(.25).where(complete)
    out['price_complete'] = complete
    return out

def episodes(price):
    """Observed runs, including runs censored by sample boundaries or missing data."""
    rows = []
    active = None
    for t,v in price.items():
        if pd.notna(v) and v < 0:
            if active is None:
                active = [t,t,.25]
            elif t-active[1] == pd.Timedelta(minutes=15):
                active[1], active[2] = t, active[2]+.25
            else:
                rows.append(active); active = [t,t,.25]
        elif active is not None:
            rows.append(active); active = None
    if active is not None:
        rows.append(active)
    return pd.DataFrame(rows, columns=['start','last_interval_start','observed_hours'])
