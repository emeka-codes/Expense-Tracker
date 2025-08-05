from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Expense
import datetime
from database import engine, SessionLocal
from typing import List


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
    return templates.TemplateResponse("homepage.html", {"request": request, "get_today_expenses": get_today_expenses, "get_today_total": get_today_total})


@app.post("/add_expense", response_class=HTMLResponse)
def add_expense(request: Request, amount:float = Form(...), category:str = Form(...), description:str = Form(...), db: Session= Depends(get_db)):
    expense= Expense(amount=amount, category= category, description= description)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return RedirectResponse("/", status_code=302)


@app.get("/expenses_by_date", response_class=HTMLResponse)
def get_expense(request: Request, date: str = "" , db: Session= Depends(get_db)):
    parsed_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    get_expenses= db.query(Expense).filter(Expense.date == parsed_date).all()
    get_total= db.query(func.sum(Expense.amount)).filter(Expense.date == parsed_date).scalar()
    return templates.TemplateResponse("homepage.html", {"request": request, "get_expenses": get_expenses, "get_total": get_total, "selected_date": parsed_date})


@app.post("/delete-selected")
def delete_selected_expenses(expense_ids: List[int] = Form(...), db: Session = Depends(get_db)):
    db.query(Expense).filter(Expense.id.in_(expense_ids)).delete(synchronize_session=False)
    db.commit()
    return RedirectResponse(url="/", status_code=303)





