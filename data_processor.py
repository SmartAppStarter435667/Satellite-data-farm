import os, ee, json, time
from datetime import datetime, timedelta
from google import genai

# 1. 認証
EE_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")
with open("service_account.json", "w") as f: f.write(EE_JSON)
ee.Initialize(ee.ServiceAccountCredentials("your-account", "service_account.json"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 47都道府県の代表座標（一部抜粋、実際には全県分を辞書化）
PREF_COORDS = [
    {"id": "hokkaido", "name": "北海道", "lat": 43.06, "lon": 141.35},
    {"id": "saga", "name": "佐賀県", "lat": 33.26, "lon": 130.30},
    {"id": "tokyo", "name": "東京都", "lat": 35.68, "lon": 139.69},
    # ここに47都道府県の全リストを定義
]

def get_pro_data(lat, lon):
    try:
        roi = ee.Geometry.Point([lon, lat]).buffer(3000).bounds()
        
        # Landsat 8/9 (高解像度・温度)
        ls_img = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").filterBounds(roi).sort('CLOUD_COVER').first()
        
        # ひまわり8号 (リアルタイム・気象)
        himawari = ee.ImageCollection("JAXA/GCOM-C/L3/LAND/LST/V1").filterBounds(roi).sort('system:time_start', False).first()

        img_url = ls_img.getThumbURL({'bands':['SR_B4','SR_B3','SR_B2'], 'min':0, 'max':20000, 'dimensions':800, 'format':'png'})
        stats = ls_img.reduceRegion(ee.Reducer.mean(), roi, 30).getInfo()
        
        ndvi = (stats['SR_B5'] - stats['SR_B4']) / (stats['SR_B5'] + stats['SR_B4'])
        lst_c = (stats.get('ST_B10', 0) * 0.00341802 + 149.0) - 273.15
        
        # 日付フォーマット修正
        obs_date = ls_img.date().format('YYYY年MM月DD日').getInfo()

        # B2B向けAI分析
        ai_text = "解析中..."
        try:
            prompt = f"衛星観測レポート：{obs_date}時点。植生指数{ndvi:.2f}, 温度{lst_c:.1f}度。プロの農業コンサルタントとして、今後の作業指示を25文字以内で出力して。"
            response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
            ai_text = response.text
        except: time.sleep(10)

        return {
            "img": img_url, "ndvi": round(ndvi, 3), "temp": round(lst_c, 1),
            "ai": ai_text, "date": obs_date, "sat": "Landsat 8/9 & Himawari"
        }
    except: return None

def main():
    results = {"japan": [], "overseas": []}
    # 日本47都道府県
    for p in PREF_COORDS:
        res = get_pro_data(p['lat'], p['lon'])
        if res: results["japan"].append({**p, **res})
        time.sleep(3)
    
    with open("frontend/src/data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__": main()
