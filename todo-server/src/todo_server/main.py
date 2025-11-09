from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"todo_server_version": "0.1.0"}