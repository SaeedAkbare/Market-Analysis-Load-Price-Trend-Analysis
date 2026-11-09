"""Run with python -m power_market.run from the repository root."""
from pathlib import Path
import json
import pandas as pd
from .public_data import retrieve
from .analysis import fundamentals, daily, episodes

def run():
    out = Path('reports/results'); out.mkdir(parents=True, exist_ok=True)
    x = fundamentals(retrieve())
    coverage = x.notna().mean()
    coverage.to_csv(out/'coverage.csv', header=['fraction_observed'])
    if not coverage.eq(1).all():
        raise RuntimeError('Incomplete coverage: inspect reports/results/coverage.csv. No findings generated.')
    if (x.drop(columns=['price','residual_load','net_import']) < 0).any().any():
        raise ValueError('Negative physical quantity requires source review')
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    x.to_csv('data/processed/aligned.csv', index_label='utc')
    d = daily(x); d.index.name='Delivery date (Europe/Berlin)'; d.to_csv(out/'daily.csv')
    events = episodes(x.price); events.to_csv(out/'negative_episodes.csv', index=False)
    x[['price','residual_load','renewables','net_import']].corr(method='spearman').to_csv(out/'associations.csv')
    stats = dict(negative_hours=float(x.price.lt(0).sum()/4), negative_share=float(x.price.lt(0).mean()), mean_spread=float(d.spread.mean()), longest_observed_negative_run_hours=float(events.observed_hours.max()) if len(events) else 0)
    (out/'summary.json').write_text(json.dumps(stats, indent=2))
    cases = []
    for label, order in [('Largest spread',d.spread.sort_values(ascending=False)),('Most negative hours',d.negative_hours.sort_values(ascending=False)),('Highest mean residual load',d.residual_load.sort_values(ascending=False))]:
        date = next(t for t in order.index if t not in [c[1] for c in cases])
        cases.append((label,date))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'axes.spines.top':False,'axes.spines.right':False,'font.size':11,'figure.facecolor':'white','axes.prop_cycle':plt.cycler(color=['#176B87','#DB6B37','#476A46'])})
    def save(fig, name, title):
        fig.suptitle(title+' | 2024', fontsize=15, fontweight='bold')
        fig.text(.06,.015,'Energy-Charts / SMARD • DE-LU prices; German fundamentals • Jan–Dec 2024 • Europe/Berlin',fontsize=8)
        fig.tight_layout(rect=(0,.05,1,.94)); fig.savefig(out/f'{name}.png',dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(10,5)); ax.hist(x.price, bins=70, weights=[.25]*len(x)); ax.set(xlabel='Day-ahead price (EUR/MWh)',ylabel='Delivery hours'); save(fig,'01_distribution','Price distribution')
    local=x.tz_convert('Europe/Berlin'); local.index.name='Delivery time (Europe/Berlin)'
    fig,axes=plt.subplots(1,2,figsize=(11,5)); local.price.groupby(local.index.month).mean().plot(ax=axes[0],marker='o'); local.price.groupby(local.index.hour).mean().plot(ax=axes[1],marker='o'); axes[0].set(xlabel='Month',ylabel='Mean price (EUR/MWh)'); axes[1].set(xlabel='Local delivery hour',ylabel='Mean price (EUR/MWh)'); save(fig,'02_seasonality','Price seasonality')
    fig,axes=plt.subplots(2,1,figsize=(11,7)); d.spread.plot(ax=axes[0]); d.negative_hours.plot(ax=axes[1]); axes[0].set_ylabel('Daily spread (EUR/MWh)'); axes[1].set_ylabel('Negative-price hours'); save(fig,'03_spreads','Daily ranges and negative prices')
    fig,axes=plt.subplots(1,2,figsize=(11,5))
    for ax,col in zip(axes,['residual_load','renewables']):
        h=ax.hexbin(x[col]/1000,x.price,gridsize=40,mincnt=1,cmap='viridis'); fig.colorbar(h,ax=ax,label='Quarter-hour observations'); ax.set(xlabel=('Wind + solar' if col=='renewables' else 'Residual load')+' (GW)',ylabel='Price (EUR/MWh)')
    save(fig,'04_fundamentals','Physical fundamentals and prices')
    fig,ax=plt.subplots(figsize=(10,5)); groups=[x.loc[x.price<0,'net_import']/1000,x.loc[x.price>=0,'net_import']/1000]; ax.boxplot(groups,tick_labels=['Negative price','Nonnegative price'],showfliers=False); ax.set_ylabel('Net imports (GW; positive inward)'); save(fig,'05_flows','Physical flow conditions')
    fig,axes=plt.subplots(3,1,figsize=(11,9))
    text=['# European Power Market Fundamentals — market report','', 'DE-LU prices with German fundamentals and German physical border flows, full calendar 2024. Descriptive associations, not causal effects. Luxembourg is a German physical border here, not an external border of the DE-LU bidding zone.', '',f'Negative prices: {stats["negative_hours"]:.2f} hours ({stats["negative_share"]:.2%}). Mean daily spread: {stats["mean_spread"]:.2f} EUR/MWh.', '', '## Selected market days']
    association=x[['price','residual_load','renewables','net_import']].corr(method='spearman')['price']
    text[5:5]=['## Relationships',f'Price Spearman association: residual load {association.residual_load:.3f}; wind plus solar {association.renewables:.3f}; net imports {association.net_import:.3f}. Higher residual load coincided with higher prices, while more wind and solar coincided with lower prices. Imports also coincided with higher prices; this is consistent with multiple market responses and does not show that imports caused higher prices. Seasonal and hourly patterns are not controlled here.','']
    for ax,(label,date) in zip(axes,cases):
        day=local.loc[str(date.date())]; day.price.plot(ax=ax); ax.set_title(f'{label}: {date:%Y-%m-%d}'); ax.set_ylabel('EUR/MWh')
        row=d.loc[date]; text += ['',f'**{label}, {date:%Y-%m-%d}:** spread {row.spread:.2f} EUR/MWh; negative prices {row.negative_hours:.2f} hours; mean residual load {row.residual_load/1000:.2f} GW; renewables {row.renewables/1000:.2f} GW; net imports {row.net_import/1000:.2f} GW. Selection is mechanical and retrospective.']
    save(fig,'06_cases','Unusual delivery days')
    text += ['', '## Decision relevance and limits', 'Negative-price exposure matters for renewable capture revenues; daily ranges help screen flexibility opportunities but are not achievable storage profit. Efficiency, capacity, cycling costs and dispatch constraints are absent. Actual generation and physical flows occur after the auction and cannot establish an actionable forecast. Physical flows differ from commercial schedules and include loop flows. Weather, outages, fuel and carbon prices, and neighbouring price differentials remain omitted. No causal or hedge recommendation follows from these associations. Negative episodes touching sample boundaries are censored.', '', 'Source: ENTSO-E Transparency Platform; retrieval timestamps and hashes in data/raw/*.json.']
    text[-1]='Source: Energy-Charts.info (Fraunhofer ISE); DE-LU prices from Bundesnetzagentur | SMARD.de. CC BY 4.0 per retrieved responses. Retrieval timestamps, units and hashes: data/energy_charts/*.meta.json. Derived analysis changes the source data through alignment and aggregation.'
    (out/'market-report.md').write_text('\n'.join(text),encoding='utf-8')
    (out/'provenance.json').write_text(json.dumps([json.loads(p.read_text(encoding='utf-8')) for p in sorted(Path('data/energy_charts').glob('*.meta.json'))],indent=2),encoding='utf-8')
    return x,d

if __name__ == '__main__':
    run()
