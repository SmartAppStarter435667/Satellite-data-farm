import os, ee, json, time
from datetime import datetime, timedelta
from google import genai
from google.genai import types

# 1. 認証設定
EE_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")
with open("service_account.json", "w") as f: f.write(EE_JSON)
ee.Initialize(ee.ServiceAccountCredentials("your-account", "service_account.json"))

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PREFECTURES = [
    {"id": "hokkaido", "name": "北海道", "lat": 43.06, "lon": 141.35},
    {"id": "saga", "name": "佐賀県", "lat": 33.26, "lon": 130.30},
    {"id": "tokyo", "name": "東京都", "lat": 35.68, "lon": 139.69}
]

def get_satellite_data(lat, lon):
    try:
        roi = ee.Geometry.Point([lon, lat]).buffer(5000).bounds()
        # Sentinel-2 (RGB, NDVI, NDWI, Cloud)
        s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(roi).filterDate(datetime.now() - timedelta(days=90), datetime.now()).sort('CLOUDY_PIXEL_PERCENTAGE').first()
        # Landsat 8 (Temperature)
        l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(roi).filterDate(datetime.now() - timedelta(days=90), datetime.now()).sort('CLOUD_COVER').first()

        img_url = s2.getThumbURL({'bands':['B4','B3','B2'], 'min':0, 'max':4000, 'dimensions':600, 'format':'png'})
        stats = s2.multiply(1).reduceRegion(ee.Reducer.mean(), roi, 30).getInfo()
        
        ndvi = (stats['B8'] - stats['B4']) / (stats['B8'] + stats['B4'])
        ndwi = (stats['B3'] - stats['B8']) / (stats['B3'] + stats['B8'])
        cloud = s2.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()
        
        temp_k = l8.select('ST_B10').reduceRegion(ee.Reducer.mean(), roi, 30).getInfo().get('ST_B10', 0)
        lst_c = (temp_k * 0.00341802 + 149.0) - 273.15 if temp_k else 0

        # AI生成 (Gemini) - 失敗してもデータは残すようにtry-exceptを入れる
        ai_text = "AI分析中..."
        try:
            prompt = f"{datetime.now().date()}時点の{lat},{lon}の衛星データ：NDVI {ndvi:.2f}, 温度 {lst_c:.1f}度。農業への影響を30文字で分析して。"
            response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            ai_text = response.text
        except:
            time.sleep(10) # 制限時は待機

        return {"img": img_url, "ndvi": round(ndvi, 3), "ndwi": round(ndwi, 3), "temp": round(lst_c, 1), "cloud": round(cloud, 1), "ai": ai_text, "date": s2.date().format('YYYY-MM-DD').getInfo()}
    except: return None

def main():
    results = []
    for p in PREFECTURES:
        print(f"Processing {p['name']}...")
        data = get_satellite_data(p['lat'], p['lon'])
        if data: results.append({**p, **data})
        [span_1](start_span)time.sleep(5) # Quota制限対策で長めに待機[span_1](end_span)
    
    os.makedirs("frontend/src", exist_ok=True)
    with open("frontend/src/data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__": main()
