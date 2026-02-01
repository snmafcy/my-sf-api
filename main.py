from fastapi import FastAPI, Body
import subprocess
import os
import json
import shutil

app = FastAPI()

# 道具(sf)の優先順位：1.システムのパス 2.直接ダウンロードした場所
# main.py の get_sf_path を修正
def get_sf_path():
    # 上記ビルドコマンドで解凍される実行ファイルのフルパス
    return "/opt/render/project/src/sfdx/bin/sfdx"

@app.get("/auth")
async def auth():
    sf_path = get_sf_path()
    try:
        # 「全部入り」ならこのコマンドが確実に通ります
        result = subprocess.run(
            [sf_path, "force:auth:device:login", "--instanceurl", "https://test.salesforce.com", "--json"],
            capture_output=True, text=True, timeout=60
        )
        # (以下、結果をパースする処理)

@app.get("/auth")
async def auth():
    sf_path = get_sf_path()
    
    try:
        # 'org login device' の代わりに 'login device' (または旧式の呼び出し) を試行
        # 多くの環境で互換性がある形式に変更します
        result = subprocess.run(
            [sf_path, "login", "device", "--instance-url", "https://test.salesforce.com", "--json"],
            capture_output=True, text=True, timeout=30
        )
        
        # もし上記がダメならさらに旧式のコマンドを試すロジック
        if "is not a sf command" in result.stderr:
             result = subprocess.run(
                [sf_path, "force:auth:device:login", "--instanceurl", "https://test.salesforce.com", "--json"],
                capture_output=True, text=True, timeout=30
            )

        stdout_content = result.stdout.strip()
        if stdout_content:
            return {"status": "auth_requested", "output": json.loads(stdout_content)}
        else:
            return {"status": "error", "message": "出力が空です", "stderr": result.stderr}

    except Exception as e:
        return {"status": "critical_error", "message": str(e)}

@app.post("/deploy")
async def deploy(
    apex_code: str = Body(..., embed=True), 
    class_name: str = Body(..., embed=True),
    sf_username: str = Body(..., embed=True)
):
    sf_path = get_sf_path()
    
    # 1. Salesforceプロジェクトの最小構成を作成
    if not os.path.exists("sfdx-project.json"):
        with open("sfdx-project.json", "w") as f:
            json.dump({"packageDirectories": [{"path": "force-app", "default": True}], "sourceApiVersion": "60.0"}, f)

    os.makedirs("force-app/main/default/classes", exist_ok=True)
    
    # 2. ファイル書き出し
    with open(f"force-app/main/default/classes/{class_name}.cls", "w") as f:
        f.write(apex_code)
    with open(f"force-app/main/default/classes/{class_name}.cls-meta.xml", "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?><ApexClass xmlns="http://soap.sforce.com/2006/04/metadata"><apiVersion>60.0</apiVersion><status>Active</status></ApexClass>')

    # 3. デプロイ実行
    try:
        result = subprocess.run(
            [sf_path, "project", "deploy", "start", "--target-org", sf_username, "--json"],
            capture_output=True, text=True, timeout=60
        )
        output = json.loads(result.stdout) if result.stdout else result.stderr
        return {"status": "finished", "output": output}
    except Exception as e:
        return {"status": "deploy_error", "message": str(e)}
