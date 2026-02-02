from fastapi import FastAPI, Body
import subprocess
import os
import json

app = FastAPI()

# パスを 'sfdx' に完全に固定
SFDX_PATH = "/opt/render/project/src/sfdx/bin/sfdx"
# あなたが作成した接続アプリのコンシューマ鍵
CLIENT_ID = "3MVG96vIeT8jJWjI9k1auQmihZbrZy6ljZ4Gcqa_PVMJ9Vl8aGSJIsCgHj5L4rf9MaVhlMWyYJ66WPDsA5hFI"

@app.get("/auth")
async def auth():
    try:
        # タイムアウトを 60 -> 120秒に延長し、フラグを --instance-url に修正
        result = subprocess.run(
            [
                SFDX_PATH, "force:auth:device:login", 
                "--instance-url", "https://test.salesforce.com", # 警告に合わせて修正
                "--clientid", CLIENT_ID,
                "--json"
            ],
            capture_output=True, text=True, timeout=120  # ここを120に増やしました
        )
        
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")

        if result.stdout.strip():
            return {"status": "auth_requested", "output": json.loads(result.stdout)}
        else:
            return {"status": "error", "stderr": result.stderr}

    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Renderのサーバーが遅すぎて時間切れになりました。もう一度リロードしてみてください。"}
    except Exception as e:
        return {"status": "critical_error", "message": str(e)}

@app.post("/deploy")
async def deploy(
    apex_code: str = Body(..., embed=True), 
    class_name: str = Body(..., embed=True),
    sf_username: str = Body(..., embed=True)
):
    # デプロイ用のフォルダ準備
    os.makedirs("classes", exist_ok=True)
    with open(f"classes/{class_name}.cls", "w") as f: 
        f.write(apex_code)
    with open(f"classes/{class_name}.cls-meta.xml", "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?><ApexClass xmlns="http://soap.sforce.com/2006/04/metadata"><apiVersion>60.0</apiVersion><status>Active</status></ApexClass>')

    try:
        # 【修正ポイント】インデントを修正し、コマンドをデプロイ専用の物に戻しました
        result = subprocess.run(
            [
                SFDX_PATH, "force:source:deploy", 
                "-p", "classes", 
                "-u", sf_username, 
                "--json"
            ],
            capture_output=True, text=True, timeout=120
        )
        
        if result.stdout.strip():
            return {"status": "finished", "output": json.loads(result.stdout)}
        else:
            return {"status": "deploy_error", "stderr": result.stderr}
            
    except Exception as e:
        return {"status": "deploy_error", "message": str(e)}
