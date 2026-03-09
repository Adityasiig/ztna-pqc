from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import PlainTextResponse
import uvicorn
import os

app = FastAPI(title="Resource Server (The Goal)")

# Create the goal file if it doesn't exist
GOAL_FILE = "goal.txt"
if not os.path.exists(GOAL_FILE):
    with open(GOAL_FILE, "w") as f:
        f.write("CONGRATULATIONS! You have successfully bypassed the Zero Trust Gateway and reached the highly classified Goal File.\n\nProject: ZTNA-PQC Gateway")

@app.get("/")
def home():
    return {"message": "Resource Server running. The goal file is at /secret-file"}

@app.get("/secret-file", response_class=PlainTextResponse)
def get_secret(authorization: str = Header(None)):
    """
    This endpoint represents the protected resource.
    It ONLY allows access if a valid token from the ZTNA Gateway is provided.
    """
    # 1. Check if the token exists
    if not authorization:
        raise HTTPException(status_code=401, detail="Access Denied: No ZTNA Token Provided.")
    
    # 2. In a real system, the Resource Server would ask the Gateway to verify this token.
    # For our demo, we just verify it matches the format issued by our Gateway.
    if not authorization.startswith("Bearer ZTNA-"):
        raise HTTPException(status_code=403, detail="Access Denied: Invalid ZTNA Token format.")

    # 3. If the token is valid, serve the highly classified file!
    try:
        with open(GOAL_FILE, "r") as f:
            content = f.read()
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail="Goal file missing!")

if __name__ == "__main__":
    print("Starting Resource Server on port 8080...")
    print("This server holds the 'goal.txt' file.")
    uvicorn.run(app, host="0.0.0.0", port=8080)
