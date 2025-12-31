from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import routes
from .api.routes import router as validation_router

app = FastAPI(title="Audit Header Validator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api")
app.include_router(validation_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
