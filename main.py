from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Expense
import datetime
from database import engine, SessionLocal

app= FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates= Jinja2Templates(directory="templates")

def get_db():
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def display_home_page(request:Request, db: Session= Depends(get_db)):
    get_today_expenses= db.query(Expense).filter(Expense.date == datetime.date.today()).all()
    get_today_total= db.query(func.sum(Expense.amount)).filter(Expense.date == datetime.date.today()).scalar()
    
    return templates.TemplateResponse("homepage.html", { "request": request, "get_today_expenses": get_today_expenses, "get_today_total": get_today_total})


@app.get("/add", response_class=HTMLResponse)
def display_form(request:Request):
    return templates.TemplateResponse("form.html", {"request":request})


