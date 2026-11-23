import uvicorn

uvicorn.run("alertas.api:app", host="0.0.0.0", port=8001, reload=False)
