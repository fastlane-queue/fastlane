from fastapi import FastAPI

from newlane.api import router

app = FastAPI()
app.include_router(router)
