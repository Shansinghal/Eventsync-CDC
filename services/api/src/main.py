from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from src.database import SessionLocal, engine
import src.models as models
import json
from src.redis_client import redis_client

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "API running"}


@app.get("/users")
def get_users(db: Session = Depends(get_db)):

    cache_key = "users_list"

    # 1️⃣ Check Redis cache
    cached_users = redis_client.get(cache_key)

    if cached_users:
        print("CACHE HIT ✅")
        return json.loads(cached_users)

    print("CACHE MISS ❌")

    # 2️⃣ Fetch from database
    users = db.query(models.User).all()

    result = [
        {"id": u.id, "username": u.username, "bio": u.bio}
        for u in users
    ]

    # 3️⃣ Store in Redis
    redis_client.set(cache_key, json.dumps(result))

    return result