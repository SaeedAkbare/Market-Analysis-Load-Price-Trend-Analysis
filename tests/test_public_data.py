import copy
import pandas as pd
import pytest
from power_market.public_data import parse

def payload():
    return dict(schema_version='2.0',endpoint='cbpf',country='de',timezone='Europe/Berlin',unit='GW',interval_minutes=15,
        series=[{'id':'france'}],data=[{'timestamp':'2024-10-27T02:00:00+02:00','values':{'france':1.5}},
        {'timestamp':'2024-10-27T02:00:00+01:00','values':{'france':None}}])

def test_units_nulls_and_repeated_local_hour():
    a=pd.Timestamp('2024-10-27T00:00Z'); b=a+pd.Timedelta(hours=2)
    x=parse(payload(),'cbpf','GW',{'france':'flow'},a,b)
    assert x.iloc[0,0]==1500
    assert x.iloc[1:,0].isna().all()
    p=payload(); p['data'][1]['values']['france']=-2
    x=parse(p,'cbpf','GW',{'france':'flow'},a,b)
    assert x.iloc[4,0]==-2000

@pytest.mark.parametrize('key,value',[('unit','MW'),('country','lu'),('interval_minutes',None),('schema_version','3.0')])
def test_metadata_rejected(key,value):
    p=payload(); p[key]=value
    with pytest.raises(ValueError): parse(p,'cbpf','GW',{'france':'flow'})

def test_conflicting_duplicate():
    p=payload(); row=copy.deepcopy(p['data'][0]); row['values']['france']=9; p['data'].append(row)
    with pytest.raises(ValueError): parse(p,'cbpf','GW',{'france':'flow'})
