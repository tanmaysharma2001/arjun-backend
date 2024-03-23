import uvicorn
from fastapi import Depends, FastAPI
from auth.verify import Protected
from qa.endpoints import router as qa_router

app = FastAPI()

app.include_router(
    qa_router,
    tags=["qa"],
    dependencies=[Depends(Protected())],
)


@app.get("/", status_code=200)
def root():
    return {"message": "OK"}


@app.get("/health", status_code=200)
def health():
    return {"message": "OK"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
