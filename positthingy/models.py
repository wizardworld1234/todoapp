from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from datetime import date

class CommentModel(BaseModel):
    id: int
    comment: str
    date_stamp: datetime

    class Config:
        orm_mode = True

class MainDataModel(BaseModel):
    id: int
    advisor: str
    acf2: str
    branch: str
    metric: str
    refresh_date: datetime
    current: int
    mom: int
    qoq: int
    yoy: int
    action: str
    procedure: str
    status: str
    date: Optional[str] = None
    comments: List[CommentModel] = []

    class Config:
        orm_mode = True

class CommentCreate(BaseModel):
    main_data_id: int
    comment: str
    date_stamp: datetime

class StatusUpdate(BaseModel):
    status: str
    refresh_date: date
