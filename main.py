from fastapi import FastAPI, Body
import subprocess
import os
import json

app = FastAPI()

@app.get("/auth")
async def auth():
    # Sandbox（test.salesforce.com）へのデバイスログインを開始
    # --instance-url を指定しているので、Sandboxでも確実に動作します
    result = subprocess.run(
        ["sf", "org", "login", "device", "--instance-url", "https://test.salesforce.com", "--json"],
        capture_output=True, text=True
    )
    # 後の処理で扱いやすいよう、文字列(stdout)を辞書形式にパースして返すとAIが読みやすくなります
    try:
        output_data = json.loads(result.stdout)
    except:
        output_data = result.stdout
        
    return {"status": "auth_requested", "output": output_data}

@app.post("/deploy")
async def deploy(
    apex_code: str = Body(..., embed=True), 
    class_name: str = Body(..., embed=True),
    sf_username: str = Body(..., embed=True)
):
    # 1. Salesforce用のフォルダ構造を作成
    os.makedirs("force-app/main/default/classes", exist_ok=True)
    
    # 2. Apexファイルを保存
    with open(f"force-app/main/default/classes/{class_name}.cls", "w") as f:
        f.write(apex_code)
    
    # 3. メタデータファイルを自動作成
    with open(f"force-app/main/default/classes/{class_name}.cls-meta.xml", "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?><ApexClass xmlns="http://soap.sforce.com/2006/04/metadata"><apiVersion>60.0</apiVersion><status>Active</status></ApexClass>')

    # 4. デプロイ実行
    result = subprocess.run(
        ["sf", "project", "deploy", "start", "--target-org", sf_username, "--json"],
        capture_output=True, text=True
    )
    
    try:
        output_data = json.loads(result.stdout)
    except:
        output_data = result.stdout

    return {"status": "finished", "output": output_data}
