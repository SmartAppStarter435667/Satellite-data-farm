import os
from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, MimeType, BBox, CRS

# 設定
config = SHConfig()
config.sh_client_id = os.getenv("SH_CLIENT_ID")
config.sh_client_secret = os.getenv("SH_CLIENT_SECRET")

def build_site(image_url):
    """表示用のHTMLを自動生成する"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>農地 生育監視パネル</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
    </head>
    <body>
        <h1>🛰️ 衛星データ 生育監視レポート</h1>
        <p>最新の更新日: {os.popen('date').read()}</p>
        <hr>
        <section>
            <h2>最新のNDVI（植物元気度）マップ</h2>
            <img src="ndvi_latest.png" alt="NDVI Image" style="width:100%; max-width:512px; border:1px solid #ccc;">
            <p>※緑色が濃いほど植物が元気です。赤い部分は土壌が露出しているか、生育が遅れています。</p>
        </section>
        <footer>
            <p>© 2026 Satellite Monitoring Service</p>
        </footer>
    </body>
    </html>
    """
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

def main():
    # publicフォルダを作成
    os.makedirs("public", exist_ok=True)
    
    # 衛星画像取得（座標は適宜変更）
    target_bbox = [130.20, 33.20, 130.22, 33.22]
    # ... (前述の get_ndvi_image 処理を行い、public/ndvi_latest.png として保存) ...
    
    # HTML生成
    build_site("ndvi_latest.png")

if __name__ == "__main__":
    main()
