from sqlalchemy.orm import Session
from database import MainData, Comment

def get_data_by_branch(db: Session, branch: str):
    return db.query(MainData).filter(MainData.branch == branch).all()

def get_comments_for_data(db: Session, main_data_id: int):
    return db.query(Comment).filter(Comment.main_data_id == main_data_id).all()
