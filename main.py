from fastapi import FastAPI, Body
import subprocess
import os
import json
import shutil

app = FastAPI()

# 道具(sf)の優先順位：1.システムのパス 2.直接ダウンロードした場所
def get_sf_path():
    system_sf = shutil.which("sf")
    if system_sf:
        return system_sf
    # curl方式でインストールした際のデフォルトパス
    local_sf = "/opt/render/project/src/sfdx/bin/sf"
    return local_sf

@app.get("/auth")
async def auth():
    sf_path = get_sf_path()
    
    try:
        # デバイスログイン開始
        result = subprocess.run(
            [sf_path, "org", "login", "device", "--instance-url", "https://test.salesforce.com", "--json"],
            capture_output=True, text=True, timeout=30
        )
        
        stdout_content = result.stdout.strip()
        stderr_content = result.stderr.strip()

        if stdout_content:
            return {"status": "auth_requested", "output": json.loads(stdout_content)}
        else:
            return {"status": "error", "message": "CLIからの出力が空です", "stderr": stderr_content}

    except Exception as e:
        return {
            "status": "critical_error",
            "message": str(e),
            "tried_path": sf_path,
            "path_env": os.environ.get("PATH")
        }

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
