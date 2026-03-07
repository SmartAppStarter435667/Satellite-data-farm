import os, ee, json, time
from datetime import datetime, timedelta
from google import genai

# 認証
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
        s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(roi).filterDate(datetime.now() - timedelta(days=90), datetime.now()).sort('CLOUDY_PIXEL_PERCENTAGE').first()
        l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(roi).filterDate(datetime.now() - timedelta(days=90), datetime.now()).sort('CLOUD_COVER').first()

        img_url = s2.getThumbURL({'bands':['B4','B3','B2'], 'min':0, 'max':4000, 'dimensions':600, 'format':'png'})
        stats = s2.multiply(1).reduceRegion(ee.Reducer.mean(), roi, 30).getInfo()
        
        ndvi = (stats['B8'] - stats['B4']) / (stats['B8'] + stats['B4'])
        ndwi = (stats['B3'] - stats['B8']) / (stats['B3'] + stats['B8'])
        cloud = s2.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()
        
        temp_k = l8.select('ST_B10').reduceRegion(ee.Reducer.mean(), roi, 30).getInfo().get('ST_B10', 0)
        lst_c = (temp_k * 0.00341802 + 149.0) - 273.15 if temp_k else 0

        # AI分析（指数関数的バックオフ：エラー時に待機時間を倍にする）
        ai_text = "分析データ収集中..."
        for attempt in range(3):
            try:
                prompt = f"{lat},{lon}の植生指数{ndvi:.2f}, 地表温度{lst_c:.1f}度。現在の農作物の状況を短く一言で。"
                response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
                ai_text = response.text
                break
            except Exception:
                time.sleep(20 * (attempt + 1)) # 20秒, 40秒... と待機

        return {"img": img_url, "ndvi": round(ndvi, 3), "ndwi": round(ndwi, 3), "temp": round(lst_c, 1), "cloud": round(cloud, 1), "ai": ai_text, "date": s2.date().format('YYYY-MM-DD').getInfo()}
    except: return None

def main():
    results = []
    for p in PREFECTURES:
        print(f"Processing {p['name']}...")
        data = get_satellite_data(p['lat'], p['lon'])
        if data: results.append({**p, **data})
        time.sleep(10) # 1件ごとに10秒待機してQuotaを節約
    
    os.makedirs("frontend/src", exist_ok=True)
    with open("frontend/src/data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__": main()
