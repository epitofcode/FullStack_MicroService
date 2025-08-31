from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware # <-- 1. IMPORT THIS

import crud, models, schemas, auth
from database import SessionLocal, engine

# This creates the 'users' table in the database if it doesn't exist
# It reads the metadata from models.py
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FarmVidhya User Service",
    description="Handles user sign-up and login.",
    version="1.0.0"
)

# --- 2. ADD THE CORS MIDDLEWARE BLOCK ---
# This block allows the webpage at port 8003 (our queue_service docs)
# to make API calls to this server (at port 8001).
origins = [
    "http://localhost:8003",
    "http://127.0.0.1:8003",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ------------------------------------

# Dependency to get a DB session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/signup", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.post("/login", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.email, "user_id": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}