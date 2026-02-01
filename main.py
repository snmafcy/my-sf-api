from fastapi import FastAPI, Body
import subprocess
import os

app = FastAPI()

@app.post("/deploy")
async def deploy(
    apex_code: str = Body(..., embed=True), 
    class_name: str = Body(..., embed=True),
    sf_username: str = Body(..., embed=True)
):
    # 1. Salesforce用のフォルダ構造を作成
    os.makedirs("force-app/main/default/classes", exist_ok=True)
    
    # 2. Apexファイルを一時保存
    with open(f"force-app/main/default/classes/{class_name}.cls", "w") as f:
        f.write(apex_code)
    
    # 3. メタデータ（設定ファイル）も自動作成
    with open(f"force-app/main/default/classes/{class_name}.cls-meta.xml", "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?><ApexClass xmlns="http://soap.sforce.com/2006/04/metadata"><apiVersion>60.0</apiVersion><status>Active</status></ApexClass>')

    # 4. デプロイ実行 (CLIがサーバーに入っている前提)
    # 実際にはここで認証済み組織(sf_username)を指定します
    result = subprocess.run(
        ["sf", "project", "deploy", "start", "--target-org", sf_username, "--json"],
        capture_output=True, text=True
    )
    
    return {"status": "finished", "output": result.stdout}
