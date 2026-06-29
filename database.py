from sqlmodel import SQLModel , create_engine , Field 
from typing import Optional
from config import settings
from datetime import datetime


class users(SQLModel,table = True):
    u_id: Optional[int] = Field(default=None,primary_key=True)
    username: str = Field(nullable=False,unique=True)
    password: str = Field(nullable=False)
    
class message(SQLModel,table = True):
    m_id: Optional[int] = Field(default = None,primary_key=True)
    u_id: int = Field(foreign_key='users.u_id')
    role: str
    content: str = Field(nullable=False)
    timestamp: datetime = Field(default=datetime.utcnow(), nullable=False)

engine = create_engine(settings.dev_db_url)

def create_db_and_table():
    SQLModel.metadata.create_all(engine)


create_db_and_table()                       