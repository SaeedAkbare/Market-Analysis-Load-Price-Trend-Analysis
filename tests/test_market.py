import pandas as pd
import pytest
from power_market.data import align, parse_xml
from power_market.analysis import daily, fundamentals, episodes

def test_alignment():
    a=pd.Timestamp('2024-01-01',tz='UTC')
    raw=pd.DataFrame({'start':[a,a+pd.Timedelta(hours=1)],'minutes':[30,60],'value':[20,40]})
    s=align(raw,a,a+pd.Timedelta(hours=2))
    assert s.iloc[2:4].isna().all()
    assert s.sum()*.25==50
    assert align(pd.concat([raw,raw]),a,a+pd.Timedelta(hours=2)).equals(s)
    with pytest.raises(ValueError): align(pd.concat([raw,raw.assign(value=99)]),a,a+pd.Timedelta(hours=2))

@pytest.mark.parametrize('date,hours',[('2024-03-31',23),('2024-10-27',25)])
def test_dst(date,hours):
    a=pd.Timestamp(date,tz='Europe/Berlin'); b=a+pd.DateOffset(days=1)
    idx=pd.date_range(a,b,freq='15min',inclusive='left').tz_convert('UTC')
    x=pd.DataFrame({'price':-1.0},index=idx)
    assert len(x)==hours*4
    assert daily(x).negative_hours.iloc[0]==hours
    x.iloc[0,0]=float('nan')
    assert pd.isna(daily(x).spread.iloc[0])

def test_calculations():
    idx=pd.date_range('2024-01-01',periods=96,freq='15min',tz='Europe/Berlin').tz_convert('UTC')
    x=pd.DataFrame(dict(price=[-10,-5]+[20]*94,demand=100,wind_onshore=20,wind_offshore=10,solar=15,FR_import=9,FR_export=3),index=idx)
    f=fundamentals(x)
    assert (f.residual_load==55).all()
    assert (f.net_import==6).all()
    assert daily(f).spread.iloc[0]==30
    assert daily(f).negative_hours.iloc[0]==.5
    assert episodes(x.price).observed_hours.tolist()==[.5]

def test_units():
    xml='<root><TimeSeries><quantity_Measure_Unit.name>MAW</quantity_Measure_Unit.name><Period><timeInterval><start>2024-01-01T00:00Z</start><end>2024-01-01T01:00Z</end></timeInterval><resolution>PT15M</resolution><Point><position>2</position><quantity>50</quantity></Point></Period></TimeSeries></root>'
    assert parse_xml(xml,'MAW').iloc[0]['start']==pd.Timestamp('2024-01-01T00:15Z')
    with pytest.raises(ValueError): parse_xml(xml,'MWH')
    with pytest.raises(ValueError): parse_xml(xml.replace('PT15M','PT5M'),'MAW')

def test_resolution_change():
    a=pd.Timestamp('2024-01-01',tz='UTC')
    raw=pd.DataFrame({'start':[a,a+pd.Timedelta(hours=1)],'minutes':[60,15],'value':[-1,2]})
    s=align(raw,a,a+pd.Timedelta(minutes=75))
    assert s.tolist()==[-1,-1,-1,-1,2]
    assert episodes(s).observed_hours.tolist()==[1]
