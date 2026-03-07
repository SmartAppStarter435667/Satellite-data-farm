import os
import ee
from google import genai
from datetime import datetime, timedelta

# 認証設定 (前回の設定を継承)
EE_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")
with open("service_account.json", "w") as f:
    f.write(EE_JSON)
ee.Initialize(ee.ServiceAccountCredentials("your-service-account@project.iam.gserviceaccount.com", "service_account.json"))

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 解析対象リスト（ここを増やすだけで世界中に対応可能）
LOCATIONS = [
    {"id": "saga", "name": "佐賀 (日本)", "coords": [130.2, 33.2, 130.3, 33.3]},
    {"id": "tokyo", "name": "東京 (日本)", "coords": [139.7, 35.6, 139.8, 35.7]},
    {"id": "amazon", "name": "アマゾン (ブラジル)", "coords": [-62.0, -10.0, -61.5, -9.5]},
    {"id": "sahara", "name": "サハラ砂漠 (アフリカ)", "coords": [20.0, 25.0, 21.0, 26.0]}
]

def get_satellite_data(coords, location_id):
    """GEEから画像URLとNDVI数値を取得"""
    roi = ee.Geometry.Rectangle(coords)
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(roi).filterDate('2024-01-01', '2024-03-01').filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)).median()
    
    # NDVI計算
    ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')
    ndvi_val = ndvi.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=30).getInfo().get('NDVI', 0)
    
    # 画像URL生成 (サムネイルとして表示可能)
    vis_params = {'bands': ['B4', 'B3', 'B2'], 'min': 0, 'max': 3000}
    img_url = s2.getThumbURL({'params': vis_params, 'dimensions': 512, 'format': 'png'})
    
    return {"ndvi": ndvi_val, "img_url": img_url}

def generate_html_page(title, content, menu_html, filename):
    """共通テンプレートを使用したHTML生成"""
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} | Satellite Portal</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
        <style>
            body {{ display: flex; margin: 0; background: #0b1021; color: #e2e8f0; }}
            nav {{ width: 250px; background: #161b22; height: 100vh; padding: 20px; position: fixed; border-right: 1px solid #30363d; }}
            main {{ margin-left: 280px; padding: 40px; width: 100%; }}
            .card {{ background: #1c2128; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
            .sat-img {{ width: 100%; border-radius: 8px; border: 1px solid #444; }}
            .nav-link {{ display: block; padding: 10px; color: #58a6ff; text-decoration: none; }}
            .nav-link:hover {{ background: #21262d; }}
        </style>
    </head>
    <body>
        <nav>
            <h2>🛰️ Satellite Menu</h2>
            {menu_html}
        </nav>
        <main>
            <h1>{title}</h1>
            {content}
        </main>
    </body>
    </html>
    """
    with open(f"public/{filename}", "w", encoding="utf-8") as f:
        f.write(html)

def main():
    os.makedirs("public", exist_ok=True)
    
    # 共通メニューの作成
    menu_items = ['<a href="index.html" class="nav-link">🏠 ホーム</a>']
    for loc in LOCATIONS:
        menu_items.append(f'<a href="{loc["id"]}.html" class="nav-link">📍 {loc["name"]}</a>')
    menu_html = "\n".join(menu_items)
    
    # 各ページの生成
    summaries = []
    for loc in LOCATIONS:
        print(f"Processing {loc['name']}...")
        data = get_satellite_data(loc['coords'], loc['id'])
        
        # AIによる地域別記事生成
        prompt = f"場所:{loc['name']} の衛星データNDVI値:{data['ndvi']:.2f}。この場所の環境状況を専門的に解説する短い記事をHTML形式で作成して。"
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        
        content = f"""
        <div class="card">
            <h3>最新の衛星画像</h3>
            <img src="{data['img_url']}" class="sat-img" alt="Satellite view">
        </div>
        <div class="card">
            <h3>解析データ</h3>
            <p>NDVI（植生指標）: <strong>{data['ndvi']:.4f}</strong></p>
            {response.text}
        </div>
        """
        generate_html_page(loc['name'], content, menu_html, f"{loc['id']}.html")
        summaries.append(f"<li>{loc['name']}: NDVI {data['ndvi']:.2f}</li>")

    # ホームページの生成
    home_content = f"""
    <div class="card">
        <h2>🌏 全球・日本全国 監視状況</h2>
        <p>現在、以下の地点をリアルタイム監視中です。</p>
        <ul>{"".join(summaries)}</ul>
    </div>
    """
    generate_html_page("衛星データ総合ポータル", home_content, menu_html, "index.html")

if __name__ == "__main__":
    main()
