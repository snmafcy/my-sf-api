from fastapi import FastAPI, Body
import subprocess
import os
import json

app = FastAPI()

# パスを 'sfdx' に完全に固定
SFDX_PATH = "/opt/render/project/src/sfdx/bin/sfdx"

@app.get("/auth")
async def auth():
    try:
        # コマンドも 'sfdx' 時代の確実な形式に固定
        result = subprocess.run(
            [SFDX_PATH, "force:auth:device:login", "--instanceurl", "https://test.salesforce.com", "--json"],
            capture_output=True, text=True, timeout=60
        )
        
        # ログ出力（RenderのLogsタブで確認用）
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")

        if result.stdout.strip():
            return {"status": "auth_requested", "output": json.loads(result.stdout)}
        else:
            return {"status": "error", "stderr": result.stderr}

    except Exception as e:
        return {"status": "critical_error", "message": str(e)}

@app.post("/deploy")
async def deploy(
    apex_code: str = Body(..., embed=True), 
    class_name: str = Body(..., embed=True),
    sf_username: str = Body(..., embed=True)
):
    # デプロイも 'sfdx' コマンドに書き換え
    # (force:source:deploy ならプロジェクト構成がなくても1ファイルでいけます)
    os.makedirs("classes", exist_ok=True)
    with open(f"classes/{class_name}.cls", "w") as f: f.write(apex_code)
    with open(f"classes/{class_name}.cls-meta.xml", "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?><ApexClass xmlns="http://soap.sforce.com/2006/04/metadata"><apiVersion>60.0</apiVersion><status>Active</status></ApexClass>')

    try:
        # main.py の subprocess.run の部分を以下のように書き換えます
result = subprocess.run(
    [
        SFDX_PATH, "force:auth:device:login", 
        "--instanceurl", "https://test.salesforce.com", 
        "--clientid", "3MVG96vIeT8jJWjI9k1auQmihZbrZy6ljZ4Gcqa_PVMJ9Vl8aGSJIsCgHj5L4rf9MaVhlMWyYJ66WPDsA5hFI", # ←ここを追加！
        "--json"
    ],
    capture_output=True, text=True, timeout=60
)
        return {"status": "finished", "output": json.loads(result.stdout)}
    except Exception as e:
        return {"status": "deploy_error", "message": str(e)}
