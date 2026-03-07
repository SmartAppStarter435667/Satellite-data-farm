import os
import ee
from google import genai
from datetime import datetime, timedelta

# 1. 認証設定
EE_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")
with open("service_account.json", "w") as f:
    f.write(EE_JSON)

ee.Initialize(ee.ServiceAccountCredentials("your-service-account@project.iam.gserviceaccount.com", "service_account.json"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 2. 監視地点リスト (ここを増やすだけで無限にページが作れます)
LOCATIONS = [
    {"id": "saga", "name": "佐賀 (日本)", "coords": [130.2, 33.2, 130.3, 33.3]},
    {"id": "hokkaido", "name": "十勝平野 (日本)", "coords": [143.0, 42.8, 143.2, 43.0]},
    {"id": "california", "name": "カリフォルニア (米国)", "coords": [-121.0, 37.0, -120.5, 37.5]},
    {"id": "nile", "name": "ナイルデルタ (エジプト)", "coords": [31.0, 30.5, 31.5, 31.0]}
]

def get_satellite_data(coords):
    """GEEから画像URLと解析値を取得"""
    roi = ee.Geometry.Rectangle(coords)
    # 最新の雲が少ない画像を取得
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterBounds(roi) \
        .filterDate(datetime.now() - timedelta(days=30), datetime.now()) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10)) \
        .median()

    # NDVI計算
    ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')
    ndvi_val = ndvi.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=30).getInfo().get('NDVI', 0)
    
    # 【修正ポイント】PNG出力用にRGBバンド(B4, B3, B2)のみを選択
    vis_params = {
        'bands': ['B4', 'B3', 'B2'],
        'min': 0,
        'max': 3000,
        'dimensions': 600,
        'format': 'png'
    }
    img_url = s2.select(['B4', 'B3', 'B2']).getThumbURL(vis_params)
    
    return {"ndvi": ndvi_val, "img_url": img_url}

def generate_html(title, content, menu, filename):
    """記事風レイアウトのHTML生成"""
    html = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} | Satellite Portal</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
        <style>
            body {{ display: grid; grid-template-columns: 250px 1fr; gap: 20px; background: #0b1021; color: #e2e8f0; }}
            nav {{ background: #161b22; padding: 20px; height: 100vh; position: sticky; top: 0; }}
            .card {{ background: #1c2128; border-radius: 12px; padding: 25px; margin-bottom: 30px; border: 1px solid #30363d; }}
            .sat-img {{ width: 100%; border-radius: 8px; box-shadow: 0 0 20px rgba(0,240,255,0.2); }}
            h1, h2, h3 {{ color: #00f0ff; }}
            .nav-link {{ display: block; padding: 10px; color: #8b949e; text-decoration: none; border-bottom: 1px solid #30363d; }}
            .nav-link:hover {{ color: #00f0ff; background: #21262d; }}
        </style>
    </head>
    <body>
        <nav>
            <h3>MENU</h3>
            {menu}
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
    
    # メニュー作成
    menu_html = "".join([f'<a href="{loc["id"]}.html" class="nav-link">📍 {loc["name"]}</a>' for loc in LOCATIONS])
    menu_html = '<a href="index.html" class="nav-link">🏠 Top Page</a>' + menu_html
    
    summary_list = []
    for loc in LOCATIONS:
        print(f"Processing {loc['name']}...")
        data = get_satellite_data(loc['coords'])
        
        # AIによる記事生成
        prompt = f"場所:{loc['name']}、NDVI値:{data['ndvi']:.2f}。この地域の植生状況と農業への影響を、専門家として解説するブログ記事をHTML形式で作成して。"
        ai_article = client.models.generate_content(model='gemini-2.0-flash', contents=prompt).text
        
        content = f"""
        <div class="card">
            <h2>最新衛星画像分析</h2>
            <img src="{data['img_url']}" class="sat-img">
            <p>※Sentinel-2による真カラー合成画像</p>
        </div>
        <div class="card">
            {ai_article}
        </div>
        """
        generate_html(loc['name'], content, menu_html, f"{loc['id']}.html")
        summary_list.append(f"<li><a href='{loc['id']}.html'>{loc['name']}</a>: NDVI {data['ndvi']:.2f}</li>")

    # インデックス（トップ）ページ生成
    top_content = f"<h2>🌏 監視中エリア一覧</h2><div class='card'><ul>{''.join(summary_list)}</ul></div>"
    generate_html("衛星データ・グローバルポータル", top_content, menu_html, "index.html")

if __name__ == "__main__":
    main()
