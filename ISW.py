import requests
import json
import pandas as pd
import geopandas as gpd
from datetime import datetime, timedelta

urls = [
    'https://services5.arcgis.com/SaBe5HMtmnbqSWlu/arcgis/rest/services/VIEW_RussiaCoTinUkraine_V3/FeatureServer/49?f=json',
    'https://services5.arcgis.com/SaBe5HMtmnbqSWlu/arcgis/rest/services/VIEW_ClaimedRussianTerritoryinUkraine_V2/FeatureServer/49?f=json',
    'https://services5.arcgis.com/SaBe5HMtmnbqSWlu/arcgis/rest/services/VIEW_Russian_controlled_Ukrainian_Territory_before_February_24_2022/FeatureServer/36?f=json',
    'https://services5.arcgis.com/SaBe5HMtmnbqSWlu/arcgis/rest/services/MDS_AssessedRussianAdvanceInUkraine_view/FeatureServer/49?f=json',
    'https://services5.arcgis.com/SaBe5HMtmnbqSWlu/arcgis/rest/services/VIEW_ClaimedUkrainianCounteroffensives_V2/FeatureServer/51?f=json',
    'https://services5.arcgis.com/SaBe5HMtmnbqSWlu/arcgis/rest/services/VIEW_Reported_Ukrainian_Partisan_Warfare_V2/FeatureServer/53?f=json'
]

list_ = []
for url in urls:
    dic = {}
    data = requests.get(url).json()
    dic['name'] = data['name']
    dic['lastEditDate'] = data['editingInfo']['lastEditDate']
    list_.append(dic)

df = pd.DataFrame(list_)

df.lastEditDate = pd.to_datetime(df.lastEditDate,unit='ms')

df.to_csv('lastEditDate.csv',index=False)

layers = pd.DataFrame(requests.get(
    'https://www.arcgis.com/sharing/rest/content/items/9f04944a2fe84edab9da31750c2b15eb/data?f=json'
).json()['operationalLayers'])

layers['layer'] = layers.url.str.extract('services/(.*)/FeatureServer')

query = '/query?f=geoJSON&maxRecordCountFactor=4&resultOffset=0&resultRecordCount=8000&where=1%3D1&orderByFields=OBJECTID&outFields=OBJECTID&resultType=tile&spatialRel=esriSpatialRelIntersects&geometryType=esriGeometryEnvelope&defaultSR=102100'

layers = layers[~layers.title.isin(
    ['Russian-controlled before February 24, 2022','Reported Ukrainian Partisan Warfare'])].reset_index(drop=True)

geojson = pd.DataFrame()
for i in range(len(layers)):
    data = requests.get(layers.url[i]+query).json()
    json_string = json.dumps(data)
    gdf = gpd.read_file(json_string)
    gdf['layer'] = layers.title[i]
    geojson = pd.concat([geojson,gdf])

geojson.layer = geojson.layer.map(
    {'Assess Russian Control':'ロシア軍支配エリア',
     'Claimed Ukrainian Counteroffensives':'ウクライナ軍反撃エリア',
     'Claimed Russian Territory in Ukraine':'ロシア軍侵攻エリア',
     'Assessed Russian Advance':'ロシア軍侵攻エリア'})

geojson = geojson.drop(['OBJECTID'],axis=1)

geojson.to_file('data/'+(datetime.today() - timedelta(days=1)).strftime(format='%Y%m%d')+'.geojson',index=False)

countries = gpd.read_file('https://github.com/Nikkei-Visual-Data-Journalism/ISW/raw/main/map.geojson')

dissolved = geojson.dissolve(by='layer').reset_index()

dissolved = pd.concat([countries,dissolved],ignore_index=True)

dissolved.reindex(['geometry','layer'],axis=1).to_file('dissolved.geojson',index=False)

ukraine = gpd.read_file('https://github.com/Nikkei-Visual-Data-Journalism/ISW/raw/main/Ukraine.geojson')

geojson = pd.concat([ukraine,geojson],ignore_index=True)

geojson.reindex(['geometry','layer'],axis=1).to_file('ISW.geojson',index=False)

data = json.loads(open('ISW.geojson').read())

isw = pd.DataFrame(data['features'])
isw = isw[['geometry', 'properties']]
isw = isw.rename(columns={'properties': 'layer'})
isw.layer = isw.layer.apply(lambda x: x['layer'])

isw.geometry = isw.geometry.apply(lambda x: str(x).replace("'", '"'))
isw.geometry = isw.geometry.apply(lambda x: '' if x=='None' else '')

isw.to_csv('ISW.csv', index=False)
