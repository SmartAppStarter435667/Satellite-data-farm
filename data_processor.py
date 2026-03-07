import os, ee, json, time
from datetime import datetime, timedelta
from google import genai

# 1. 認証
EE_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")
with open("service_account.json", "w") as f: f.write(EE_JSON)
ee.Initialize(ee.ServiceAccountCredentials("your-account", "service_account.json"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 地点データ (47都道府県の座標をここへ追加)
LOCATIONS = {
    "japan": [
        {"id": "hokkaido", "name": "北海道", "lat": 43.06, "lon": 141.35},
        {"id": "saga", "name": "佐賀県", "lat": 33.26, "lon": 130.30},
        {"id": "tokyo", "name": "東京都", "lat": 35.68, "lon": 139.69},
        # 他の県も同様に追加
    ],
    "overseas": [
        {"id": "california", "name": "カリフォルニア (農場地帯)", "lat": 36.77, "lon": -119.41},
        {"id": "vietnam", "name": "ベトナム (メコンデルタ)", "lat": 10.03, "lon": 105.78}
    ]
}

def get_data(lat, lon):
    try:
        roi = ee.Geometry.Point([lon, lat]).buffer(3000).bounds()
        # Landsat 8/9 データの取得
        img = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
            .filterBounds(roi) \
            .filterDate(datetime.now() - timedelta(days=180), datetime.now()) \
            .sort('CLOUD_COVER') \
            .first()

        img_url = img.getThumbURL({'bands':['SR_B4','SR_B3','SR_B2'], 'min':0, 'max':20000, 'dimensions':800, 'format':'png'})
        stats = img.reduceRegion(ee.Reducer.mean(), roi, 30).getInfo()
        
        # 指標計算
        ndvi = (stats['SR_B5'] - stats['SR_B4']) / (stats['SR_B5'] + stats['SR_B4'])
        ndwi = (stats['SR_B3'] - stats['SR_B5']) / (stats['SR_B3'] + stats['SR_B5'])
        lst_c = (stats.get('ST_B10', 0) * 0.00341802 + 149.0) - 273.15
        cloud = img.get('CLOUD_COVER').getInfo()
        date_str = img.date().format('YYYY年MM月DD日').getInfo() # 日付フォーマット修正

        # 農業B2B向けAI分析
        ai_text = "分析中..."
        try:
            prompt = f"Landsatデータ分析：植生指数{ndvi:.2f}, 地表温度{lst_c:.1f}度。この農地の生育状況と今後のリスクを、専門家として農家にアドバイスして（30文字以内）。"
            response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            ai_text = response.text
        except: time.sleep(10)

        return {
            "img": img_url, "ndvi": round(ndvi, 3), "ndwi": round(ndwi, 3),
            "temp": round(lst_c, 1), "cloud": round(cloud, 1), 
            "ai": ai_text, "date": date_str, "sat": "Landsat 8/9"
        }
    except: return None

def main():
    final = {"japan": [], "overseas": []}
    for cat in ["japan", "overseas"]:
        for loc in LOCATIONS[cat]:
            res = get_data(loc['lat'], loc['lon'])
            if res: final[cat].append({**loc, **res})
            time.sleep(5)
    
    os.makedirs("frontend/src", exist_ok=True)
    with open("frontend/src/data.json", "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

if __name__ == "__main__": main()
