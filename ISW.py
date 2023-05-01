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

export = pd.DataFrame()
for i in range(len(layers)):
    data = requests.get(layers.url[i]+query).json()
    json_string = json.dumps(data)
    gdf = gpd.read_file(json_string)
    gdf['layer'] = layers.title[i]
    export = pd.concat([export,gdf.dissolve(by='layer')])

export = gpd.GeoDataFrame(export).drop(['OBJECTID'],axis=1)

export.index = export.index.map(
    {'Assess Russian Control':'ロシア軍支配エリア',
     'Claimed Ukrainian Counteroffensives':'ウクライナ軍反撃エリア',
     'Claimed Russian Territory in Ukraine':'ロシア軍侵攻エリア',
     'Assessed Russian Advance':'ロシア軍侵攻エリア'})

export.to_file('Ukraine.geojson')

export.to_file('data/'+(datetime.today() - timedelta(days=1)).strftime(format='%Y%m%d')+'.geojson')
