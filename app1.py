from fastapi import FastAPI

app = FastAPI()

### add autorisation
@app.get("/")
def greet_json():
    return {"Hello": "World!"}

## add new endpoints to get data from
