import os, ee, json, time
from datetime import datetime, timedelta
from google import genai

# 1. 認証設定
EE_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")
with open("service_account.json", "w") as f: f.write(EE_JSON)
ee.Initialize(ee.ServiceAccountCredentials("your-account", "service_account.json"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PREF_COORDS = [
    {"id": "hokkaido", "name": "北海道", "lat": 43.06, "lon": 141.35},
    {"id": "saga", "name": "佐賀県", "lat": 33.26, "lon": 130.30},
    {"id": "tokyo", "name": "東京都", "lat": 35.68, "lon": 139.69},
]

def get_comprehensive_data(lat, lon):
    try:
        roi = ee.Geometry.Point([lon, lat]).buffer(3000).bounds()
        
        # 1. Landsat 8/9 (高解像度・地表温度)
        ls = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(roi).sort('CLOUD_COVER').first()
        ls_url = ls.getThumbURL({'bands':['SR_B4','SR_B3','SR_B2'], 'min':0, 'max':20000, 'dimensions':600, 'format':'png'})
        ls_stats = ls.reduceRegion(ee.Reducer.mean(), roi, 30).getInfo()
        ndvi = (ls_stats['SR_B5'] - ls_stats['SR_B4']) / (ls_stats['SR_B5'] + ls_stats['SR_B4'])
        temp = (ls_stats.get('ST_B10', 0) * 0.00341802 + 149.0) - 273.15

        # 2. Sentinel-1 (レーダー衛星: 雲を透過)
        s1 = ee.ImageCollection('COPERNICUS/S1_GRD').filterBounds(roi).filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV')).sort('system:time_start', False).first()
        s1_url = s1.getThumbURL({'bands':['VV'], 'min':-25, 'max':0, 'dimensions':600, 'format':'png'})

        # 3. ひまわり (広域気象・日照)
        himawari = ee.ImageCollection("JAXA/GCOM-C/L3/LAND/LST/V1").filterBounds(roi).sort('system:time_start', False).first()
        himawari_date = himawari.date().format('YYYY-MM-DD').getInfo()

        # AI分析
        ai_text = "分析完了"
        try:
            prompt = f"農業レポート: 植生{ndvi:.2f}, 温度{temp:.1f}度。専門家として短く一言で。"
            ai_text = client.models.generate_content(model='gemini-2.0-flash', contents=prompt).text
        except: pass

        return {
            "images": {
                "visible": ls_url,       # Landsat
                "radar": s1_url          # Sentinel-1
            },
            "metrics": {
                "ndvi": round(ndvi, 3),  # Landsat 8/9
                "temp": round(temp, 1),  # Landsat 8/9
                "update": himawari_date  # Himawari 8/9
            },
            "ai": ai_text,
            "date": ls.date().format('YYYY年MM月DD日').getInfo()
        }
    except: return None

def main():
    results = {"japan": []}
    for p in PREF_COORDS:
        res = get_comprehensive_data(p['lat'], p['lon'])
        if res: results["japan"].append({**p, **res})
        time.sleep(5)
    
    with open("frontend/src/data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__": main()
