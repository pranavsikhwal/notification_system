from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from database import get_db
from models import User
from auth_utils import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user
  
  
  
# Client sends request
#         │
#         ▼
# Authorization: Bearer <JWT Token>
#         │
#         ▼
# Extract the token
#         │
#         ▼
# Verify the token (Is it valid? Has it expired?)
#         │
#         ▼
# Extract user_id from the token
#         │
#         ▼
# Find that user in the database
#         │
#         ▼
# User exists?
#    │          │
#   No         Yes
#    │          │
# 401 Error   Return User object