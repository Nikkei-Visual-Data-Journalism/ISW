import requests
import json
import pandas as pd
import geopandas as gpd
from datetime import datetime, timedelta

urls = [
    'https://services5.arcgis.com/SaBe5HMtmnbqSWlu/arcgis/rest/services/VIEW_RussiaCoTinUkraine_V3/FeatureServer/49/',
    'https://services5.arcgis.com/SaBe5HMtmnbqSWlu/arcgis/rest/services/MDS_AssessedRussianAdvanceInUkraine_view/FeatureServer/49/',
    'https://services5.arcgis.com/SaBe5HMtmnbqSWlu/arcgis/rest/services/VIEW_ClaimedRussianTerritoryinUkraine_V2/FeatureServer/49/',
    'https://services5.arcgis.com/SaBe5HMtmnbqSWlu/arcgis/rest/services/VIEW_ClaimedUkrainianCounteroffensives_V2/FeatureServer/51/'
]

query = 'query?f=geoJSON&maxRecordCountFactor=4&resultOffset=0&resultRecordCount=8000&where=1%3D1&orderByFields=OBJECTID&outFields=OBJECTID&resultType=tile'\
'&spatialRel=esriSpatialRelIntersects&geometryType=esriGeometryEnvelope&defaultSR=102100'

isw = pd.DataFrame()
for url in urls:
  data = requests.get(url+query).json()
  json_string = json.dumps(data)
  gdf = gpd.read_file(json_string)
  gdf['layer'] = url.split('/FeatureServer')[0].split('services/')[1]
  isw = pd.concat([isw,gdf],ignore_index=True)

isw = isw.drop(['OBJECTID'],axis=1)

isw.to_file('data/'+(datetime.today() - timedelta(days=1)).strftime(format='%Y%m%d')+'.geojson',index=False)

dic = {
    'VIEW_RussiaCoTinUkraine_V3':'ロシア軍支配エリア',
    'MDS_AssessedRussianAdvanceInUkraine_view':'ロシア軍侵攻エリア',
    'VIEW_ClaimedRussianTerritoryinUkraine_V2':'ロシア軍侵攻エリア',
    'VIEW_ClaimedUkrainianCounteroffensives_V2':'ウクライナ軍反撃エリア'
}

isw.layer = isw.layer.map(dic)

ukraine = gpd.read_file('https://github.com/Nikkei-Visual-Data-Journalism/ISW/raw/main/Ukraine.geojson')

interactive = pd.concat([ukraine,isw],ignore_index=True)

interactive.reindex(['geometry','layer'],axis=1).to_file('interactive.geojson',index=False)

data = json.loads(open('interactive.geojson').read())

table = pd.DataFrame(data['features'])

table['layer'] = [x['layer'] for x in table.properties]

table = table[['geometry', 'layer']]

table.geometry = [str(x).replace("'",'"') for x in table.geometry]

table.to_csv('interactive.csv',index=False)

static = isw.dissolve(by='layer').reindex(['ロシア軍支配エリア','ロシア軍侵攻エリア','ウクライナ軍反撃エリア']).reset_index()

countries = gpd.read_file('https://github.com/Nikkei-Visual-Data-Journalism/ISW/raw/main/map.geojson')

static = pd.concat([countries,static],ignore_index=True)

static.reindex(['geometry','layer'],axis=1).to_file('static.geojson',index=False)

data = json.loads(open('static.geojson').read())

table = pd.DataFrame(data['features'])

table['layer'] = [x['layer'] for x in table.properties]

table = table[['geometry', 'layer']]

table.geometry = [str(x).replace("'",'"') for x in table.geometry]

table.to_csv('static.csv',index=False)
