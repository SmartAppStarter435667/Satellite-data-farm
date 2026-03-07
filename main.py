import os
import ee
import google.generativeai as genai
from datetime import datetime, timedelta

# 1. 各種認証
# Earth Engineの認証 (GitHub SecretsからJSONを読み込む想定)
EE_JSON = os.getenv("EE_SERVICE_ACCOUNT_JSON")
with open("service_account.json", "w") as f:
    f.write(EE_JSON)

ee.Initialize(ee.ServiceAccountCredentials("your-service-account@project.iam.gserviceaccount.com", "service_account.json"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_satellite_summary():
    """佐賀県エリアの最新NDVI平均値を取得"""
    roi = ee.Geometry.Rectangle([130.2, 33.2, 130.3, 33.3])
    today = datetime.now()
    last_week = today - timedelta(days=7)
    
    # Sentinel-2のデータを取得
    s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED") \
        .filterBounds(roi) \
        .filterDate(last_week.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20)) \
        .median()

    # NDVI計算
    ndvi = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')
    stats = ndvi.reduceRegion(reducer=ee.Reducer.mean(), geometry=roi, scale=10).getInfo()
    return stats.get('NDVI', 0)

def generate_article(ndvi_value):
    """AIに記事を書かせる"""
    model = genai.GenerativeModel('gemini-1.5-flash') # 2.5や3.1があれば適宜変更
    prompt = f"""
    あなたは農業衛星データ専門のライターです。
    佐賀県の農地で計測された最新のNDVI（植生指標）の値は「{ndvi_value:.2f}」でした。
    
    この数値を元に、地元の農家さんに向けて以下の構成でブログ記事を日本語で書いてください：
    1. キャッチーなタイトル
    2. 現在の農作物の健康状態の解説（0.2以下なら注意、0.5以上なら良好など）
    3. 農家への具体的なアドバイス
    4. 今後の展望
    
    HTMLの<article>タグ形式で出力してください。
    """
    response = model.generate_content(prompt)
    return response.text

def main():
    # データ取得
    ndvi_val = get_satellite_summary()
    
    # 記事作成
    article_html = generate_article(ndvi_val)
    
    # 保存用のテンプレート作成 (index.htmlを更新)
    template = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8"><title>佐賀 衛星データ農業日報</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
    </head>
    <body>
        <h1>🛰️ 衛星データ × AI 農業レポート</h1>
        <p>更新日: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <hr>
        {article_html}
        <hr>
        <p><small>データ元: ESA Sentinel-2 / 解析: Google Earth Engine / 執筆: Gemini AI</small></p>
    </body>
    </html>
    """
    
    os.makedirs("public", exist_ok=True)
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(template)

if __name__ == "__main__":
    main()
