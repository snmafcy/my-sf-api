from fastapi import FastAPI, Body
import subprocess
import os
import json

app = FastAPI()

@app.get("/auth")
async def auth():
    # 道具(sf)の場所を明示的に探すか、エラーを捕まえる
    import shutil
    sf_path = shutil.whoami("sf") or "sf" # パスが通っていればその場所を、なければ "sf" を使う
    
    try:
        result = subprocess.run(
            [sf_path, "org", "login", "device", "--instance-url", "https://test.salesforce.com", "--json"],
            capture_output=True, text=True
        )
        
        # 実行結果がある場合はそれを返し、なければエラー出力を返す
        output_to_parse = result.stdout if result.stdout else result.stderr
        return {"status": "auth_requested", "output": json.loads(output_to_parse) if output_to_parse else "No output from CLI"}
        
    except FileNotFoundError:
        return {
            "status": "error",
            "message": "Salesforce CLI (sf) がサーバーに見つかりません。Build Commandを確認してください。"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
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
