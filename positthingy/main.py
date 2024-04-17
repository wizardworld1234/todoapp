from typing import List
from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
import io
from sqlalchemy.orm import Session
from typing import List
from database import Base, SessionLocal, engine, MainData, Comment
from models import MainDataModel, CommentCreate, StatusUpdate
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from crud import get_data_by_branch, get_comments_for_data
from sqlalchemy import func
from typing import Optional
from collections import defaultdict

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/comments/{main_data_id}", response_class=HTMLResponse)
def read_comments(main_data_id: int, request: Request, db: Session = Depends(get_db)):
    # Fetch the main data entry to get advisor and metric
    main_data = db.query(MainData).filter(MainData.id == main_data_id).first()
    if not main_data:
        raise HTTPException(status_code=404, detail=f"Main data with ID {main_data_id} not found")

    # Fetch comments associated with the main data ID
    comments = db.query(Comment).filter(Comment.main_data_id == main_data_id).all()

    # Return the template response with additional advisor and metric
    return templates.TemplateResponse("comments.html", {
        "request": request,
        "comments": comments,
        "main_data_id": main_data_id,
        "advisor": main_data.advisor,
        "metric": main_data.metric
    })

@app.get("/data", response_model=List[MainDataModel])
def read_data_by_branch(branch: str, db: Session = Depends(get_db)):
    data_entries = db.query(MainData).filter(MainData.branch == branch).all()
    return data_entries


@app.post("/comments/")
async def add_comment(comment_data: CommentCreate, db: Session = Depends(get_db)):
    # Verify that the referenced MainData exists
    main_data = db.query(MainData).filter(MainData.id == comment_data.main_data_id).first()
    if not main_data:
        raise HTTPException(status_code=404, detail="MainData not found")

    # Create and insert the new comment
    new_comment = Comment(
        main_data_id=comment_data.main_data_id,
        comment=comment_data.comment,
        date_stamp=comment_data.date_stamp
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return {"message": "Comment added successfully", "comment_id": new_comment.id}


@app.post("/update-status/{main_data_id}")
async def update_status(main_data_id: int, update_data: StatusUpdate, db: Session = Depends(get_db)):
    main_data = db.query(MainData).filter(MainData.id == main_data_id).first()
    if not main_data:
        raise HTTPException(status_code=404, detail="MainData not found")
    main_data.status = update_data.status
    main_data.date = update_data.refresh_date
    db.commit()
    return {"message": "Status updated successfully"}

@app.get("/data/{branch}/{lob}")
def read_data(
    branch: str,
    lob: str,
    request: Request,
    db: Session = Depends(get_db),
    advisor: Optional[str] = None,
    metric: Optional[str] = None,
    status: Optional[str] = None
):

    query = db.query(MainData).filter(MainData.branch == branch)
    query = query.filter(MainData.lob == lob)

    # Apply filters if the parameters are provided
    if advisor:
        query = query.filter(MainData.advisor == advisor)
    if metric:
        query = query.filter(MainData.metric == metric)
    if status:
        query = query.filter(MainData.status == status)

    # Execute the query after applying all filters
    data = query.all()
    # Group data by advisor
    data_grouped_by_advisor = defaultdict(list)
    for item in data:
        data_grouped_by_advisor[item.advisor].append(item)

    status_counts = db.query(
        MainData.status,
        func.count(MainData.status)
    ).group_by(MainData.status).all()

    advisor_options = db.query(MainData.advisor).distinct().all()
    advisor_options = [option[0] for option in advisor_options]
    metric_options = db.query(MainData.metric).distinct().all()
    metric_options = [option[0] for option in metric_options]
    status_options = db.query(MainData.status).distinct().all()
    status_options = [option[0] for option in status_options]
    # Convert to dictionary for easier access in the template
    counts = {status: count for status, count in status_counts}

    return templates.TemplateResponse("data3.html", {
        "request": request,
        "data_grouped_by_advisor": data_grouped_by_advisor,
        "branch": branch,
        "lob": lob,
        "counts": counts,
        "advisor_options": advisor_options,
        "metric_options": metric_options,
        "status_options": status_options
    })


@app.get("/admin")
def read_data(
    request: Request,
    db: Session = Depends(get_db),
    advisor: Optional[str] = None,
    metric: Optional[str] = None,
    status: Optional[str] = None,
    branch: Optional[str] = None,
    lob: Optional[str] = None
):

    query = db.query(MainData)

    # Apply filters if the parameters are provided
    if advisor:
        query = query.filter(MainData.advisor == advisor)
    if metric:
        query = query.filter(MainData.metric == metric)
    if status:
        query = query.filter(MainData.status == status)
    if branch:
        query = query.filter(MainData.branch == branch)
    if lob:
        query = query.filter(MainData.lob == lob)

    # Execute the query after applying all filters
    data = query.all()
    # Group data by advisor
    data_grouped_by_advisor = defaultdict(list)
    for item in data:
        data_grouped_by_advisor[item.advisor].append(item)

    status_counts = db.query(
        MainData.status,
        func.count(MainData.status)
    ).group_by(MainData.status).all()

    advisor_options = db.query(MainData.advisor).distinct().all()
    advisor_options = [option[0] for option in advisor_options]
    metric_options = db.query(MainData.metric).distinct().all()
    metric_options = [option[0] for option in metric_options]
    status_options = db.query(MainData.status).distinct().all()
    status_options = [option[0] for option in status_options]
    branch_options = db.query(MainData.branch).distinct().all()
    branch_options = [option[0] for option in branch_options]
    lob_options = db.query(MainData.lob).distinct().all()
    lob_options = [option[0] for option in lob_options]
    # Convert to dictionary for easier access in the template
    counts = {status: count for status, count in status_counts}

    return templates.TemplateResponse("admin2.html", {
        "request": request,
        "data_grouped_by_advisor": data_grouped_by_advisor,
        "counts": counts,
        "advisor_options": advisor_options,
        "metric_options": metric_options,
        "status_options": status_options,
        "branch_options": branch_options,
        "lob_options": lob_options
    })



@app.get("/download-data/{branch}/{lob}")
def download_data(
    branch: str,
    lob: str,
    db: Session = Depends(get_db),
    advisor: Optional[str] = Query(None),
    metric: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    query = db.query(MainData).filter(MainData.branch == branch, MainData.lob == lob)

    # Apply filters if provided
    if advisor:
        query = query.filter(MainData.advisor == advisor)
    if metric:
        query = query.filter(MainData.metric == metric)
    if status:
        query = query.filter(MainData.status == status)

    data = query.all()

    # Create a CSV in-memory
    stream = io.StringIO()
    stream.write("ID,Advisor,ACF2,Branch,LOB,Metric,Refresh Date,Current Value,MOM,QOQ,YOY,Action,Procedure,Status,Date\n")  # Header
    for item in data:
        stream.write(f"{item.id},{item.advisor},{item.acf2},{item.branch},{item.lob},{item.metric},{item.refresh_date},{item.current_value},{item.mom},{item.qoq},{item.yoy},{item.action},{item.procedure},{item.status},{item.date}\n")

    stream.seek(0)  # Go back to the start of the stream

    return StreamingResponse(iter([stream.read()]), media_type="text/csv", headers={
        "Content-Disposition": f"attachment; filename={branch}_{lob}_data.csv"
    })


@app.get("/download-data-admin")
def download_data(
    branch: Optional[str] = Query(None),
    lob: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    advisor: Optional[str] = Query(None),
    metric: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    query = db.query(MainData)

    # Apply filters if provided
    if advisor:
        query = query.filter(MainData.advisor == advisor)
    if metric:
        query = query.filter(MainData.metric == metric)
    if status:
        query = query.filter(MainData.status == status)
    if branch:
        query = query.filter(MainData.branch == branch)
    if lob:
        query = query.filter(MainData.lob == lob)

    data = query.all()


    stream = io.StringIO()
    stream.write("ID,Advisor,ACF2,Branch,LOB,Metric,Refresh Date,Current Value,MOM,QOQ,YOY,Action,Procedure,Status,Date\n")  # Header
    for item in data:
        stream.write(f"{item.id},{item.advisor},{item.acf2},{item.branch},{item.lob},{item.metric},{item.refresh_date},{item.current_value},{item.mom},{item.qoq},{item.yoy},{item.action},{item.procedure},{item.status},{item.date}\n")

    stream.seek(0)

    return StreamingResponse(iter([stream.read()]), media_type="text/csv", headers={
        "Content-Disposition": f"attachment; filename={branch}_{lob}_data.csv"
    })