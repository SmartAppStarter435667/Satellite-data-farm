import os
import ee
from google import genai
from datetime import datetime, timedelta

# 1. 各種認証
EE_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")
with open("service_account.json", "w") as f:
    f.write(EE_JSON)

ee.Initialize(ee.ServiceAccountCredentials("your-service-account@project.iam.gserviceaccount.com", "service_account.json"))

def get_satellite_summary():
    """佐賀県エリアの最新NDVI平均値を取得"""
    roi = ee.Geometry.Rectangle([130.2, 33.2, 130.3, 33.3])
    today = datetime.now()
    last_week = today - timedelta(days=7)
    
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterBounds(roi) \
        .filterDate(last_week.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
        .median()

    ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')
    stats = ndvi.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=10).getInfo()
    return stats.get('NDVI', 0)

def generate_article(ndvi_value):
    """新しいSDKでAIに記事を書かせる"""
    # 新しいSDKの初期化
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    prompt = f"""
    あなたは農業衛星データ専門のライターです。
    佐賀県の農地で計測された最新のNDVI（植生指標）の値は「{ndvi_value:.2f}」でした。
    
    この数値を元に、地元の農家さんに向けて以下の構成でブログ記事を日本語で書いてください：
    1. キャッチーなタイトル
    2. 現在の農作物の健康状態の解説（0.2以下なら注意、0.5以上なら良好など）
    3. 農家への具体的なアドバイス
    4. 今後の展望
    
    HTMLの<div class="report-content">タグ形式で出力し、小見出しには<h3>タグを使用してください。
    """
    
    # 新しいSDKの生成メソッド (モデル名も最新の2.5-flash等に変更)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text

def main():
    ndvi_val = get_satellite_summary()
    article_html = generate_article(ndvi_val)
    
    # 人工衛星風ダークデザインのテンプレート
    template = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SATELLITE AGRI-DATA | 佐賀県</title>
        <style>
            :root {{
                --bg-color: #0b1021;
                --text-main: #e2e8f0;
                --accent-blue: #00f0ff;
                --accent-green: #39ff14;
                --panel-bg: rgba(16, 24, 43, 0.8);
                --border-color: #1e2d4a;
            }}
            body {{
                background-color: var(--bg-color);
                color: var(--text-main);
                font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', sans-serif;
                margin: 0;
                padding: 0;
                background-image: 
                    radial-gradient(circle at 15% 50%, rgba(0, 240, 255, 0.05), transparent 25%),
                    radial-gradient(circle at 85% 30%, rgba(57, 255, 20, 0.05), transparent 25%);
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                padding: 40px 20px;
            }}
            header {{
                text-align: center;
                margin-bottom: 40px;
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 20px;
            }}
            h1 {{
                font-size: 2em;
                color: var(--text-main);
                letter-spacing: 2px;
                margin: 0;
                text-transform: uppercase;
                text-shadow: 0 0 10px rgba(0, 240, 255, 0.3);
            }}
            .h1-accent {{ color: var(--accent-blue); }}
            .metadata {{
                display: flex;
                justify-content: space-between;
                font-size: 0.9em;
                color: #8fa0b3;
                margin-top: 10px;
            }}
            .data-panel {{
                background: var(--panel-bg);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(4px);
            }}
            .ndvi-score {{
                text-align: center;
                margin-bottom: 30px;
                padding: 20px;
                background: rgba(0,0,0,0.3);
                border-radius: 8px;
                border-left: 4px solid var(--accent-green);
            }}
            .ndvi-score span {{
                font-size: 2.5em;
                font-weight: bold;
                color: var(--accent-green);
                text-shadow: 0 0 15px rgba(57, 255, 20, 0.4);
            }}
            .report-content h3 {{
                color: var(--accent-blue);
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 8px;
                margin-top: 30px;
            }}
            footer {{
                text-align: center;
                margin-top: 50px;
                font-size: 0.8em;
                color: #64748b;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>SATELLITE <span class="h1-accent">AGRI-DATA</span></h1>
                <div class="metadata">
                    <span>Target Area: Saga, Japan</span>
                    <span>Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}</span>
                </div>
            </header>
            
            <main class="data-panel">
                <div class="ndvi-score">
                    <p>Latest NDVI Index</p>
                    <span>{ndvi_val:.3f}</span>
                </div>
                
                {article_html}
            </main>
            
            <footer>
                <p>Data Source: ESA Sentinel-2 | Processing: Google Earth Engine | AI Analysis: Gemini</p>
                <p>&copy; 2026 Space Agri-Solutions</p>
            </footer>
        </div>
    </body>
    </html>
    """
    
    os.makedirs("public", exist_ok=True)
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(template)

if __name__ == "__main__":
    main()
