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
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


app= FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates= Jinja2Templates(directory="templates")

ODOO_WEBHOOK_URL = os.getenv("ODOO_WEBHOOK_URL")

def get_db():
    db= SessionLocal()
    try:
        yield db
    finally:
        db.close()

'''def send_to_odoo_webhook(partner_name: str, product_name: str, amount: float, description: str):
    payload = {
        "partner_name": partner_name,
        "product_name": product_name,
        "amount": amount,
        "description": description,
    }
    try:
        res = requests.post(ODOO_WEBHOOK_URL, json=payload, timeout=10)
        res.raise_for_status()
        print("✅ Sent to Odoo webhook:", res.json())
        return res.json()
    except requests.exceptions.RequestException as e:
        print("⚠️ Failed to send webhook:", str(e))
        return {"status": "error", "message": str(e)}'''



@app.get("/", response_class=HTMLResponse)
def display_home_page(request:Request, db: Session= Depends(get_db)):
    get_today_expenses= db.query(Expense).filter(Expense.date == datetime.date.today()).all()
    get_today_total= db.query(func.sum(Expense.amount)).filter(Expense.date == datetime.date.today()).scalar()
    return templates.TemplateResponse("homepage.html", {"request": request, "get_today_expenses": get_today_expenses, "get_today_total": get_today_total})


@app.post("/add_expense", response_class=HTMLResponse)
def add_expense(request: Request, amount:float = Form(...), category:str = Form(...), description:str = Form(...), product_id:str = Form(...), partner_id:str = Form(...), db: Session= Depends(get_db)):
    expense= Expense(amount=amount, category= category, description= description, product_id= product_id, partner_id= partner_id)
    db.add(expense)
    db.commit()
    db.refresh(expense)

    # Send data to Odoo webhook
    payload = {
        "partner_name": partner_id,
        "product_name": product_id,
        "amount": amount,
        "description": description,
    }
    try:
        res = requests.post(ODOO_WEBHOOK_URL, json=payload, timeout=10)
        res.raise_for_status()
        print("✅ Sent to Odoo webhook:", res.json())
        
    except requests.exceptions.RequestException as e:
        print("⚠️ Failed to send webhook:", str(e))
        
    
    return RedirectResponse("/", status_code=302)

    
  
    
    
   
    
''' webhook_result = send_to_odoo_webhook(
        partner_name=partner_id,   # matches Odoo webhook "partner_name"
        product_name=product_id,   # matches Odoo webhook "product_name"
        amount=amount,
        description=description,
    )
    print("Webhook result:", webhook_result)

    return RedirectResponse("/", status_code=302)



 # Create invoice in Odoo
    try:    
        invoice_id = create_invoice_in_odoo(partner_id, product_id, amount, description)
        print(f"Invoice created in Odoo with ID: {invoice_id}")
    except Exception as e:
        print(f"Failed to create invoice in Odoo: {e}")
    return RedirectResponse("/", status_code=302)
'''


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




'''from dotenv import load_dotenv
import os

load_dotenv()

ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USERNAME = os.getenv("ODOO_USERNAME")
ODOO_API_KEY = os.getenv("ODOO_API_KEY")
ODOO_WEBHOOK_URL = os.getenv("ODOO_WEBHOOK_URL")



def call_odoo(service, method, args):
    """Generic helper to call Odoo JSON-RPC"""
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": service,
            "method": method,
            "args": args,
        },
        "id": 1,
    }
    response = requests.post(ODOO_URL, json=payload).json()
    if "error" in response:
        raise Exception(response["error"])
    return response["result"]


def get_uid():
    """Login to Odoo with API key"""
    return call_odoo("common", "login", [ODOO_DB, ODOO_USERNAME, ODOO_API_KEY])


def get_or_create_partner(uid, name):
    """Find partner by name, else create"""
    partners = call_odoo(
        "object", "execute_kw",
        [ODOO_DB, uid, ODOO_API_KEY, "res.partner", "search_read",
         [[["name", "=", name]]], {"fields": ["id"], "limit": 1}]
    )
    if partners:
        return partners[0]["id"]

    # If not found → create new
    return call_odoo(
        "object", "execute_kw",
        [ODOO_DB, uid, ODOO_API_KEY, "res.partner", "create", [{"name": name}]]
    )


def get_or_create_product(uid, name, price=0.0):
    """Find product by name, else create"""
    products = call_odoo(
        "object", "execute_kw",
        [ODOO_DB, uid, ODOO_API_KEY, "product.product", "search_read",
         [[["name", "=", name]]], {"fields": ["id"], "limit": 1}]
    )
    if products:
        return products[0]["id"]

    # If not found → create new product
    return call_odoo(
        "object", "execute_kw",
        [ODOO_DB, uid, ODOO_API_KEY, "product.product", "create",
         [{"name": name, "list_price": price}]]
    )


def create_invoice_in_odoo(customer_name, product_name, amount, description):
    uid = get_uid()

    partner_id = get_or_create_partner(uid, customer_name)
    product_id = get_or_create_product(uid, product_name, price=amount)

    invoice_id = call_odoo(
        "object", "execute_kw",
        [ODOO_DB, uid, ODOO_API_KEY, "account.move", "create", [{
            "move_type": "out_invoice",
            "partner_id": partner_id,
            "invoice_line_ids": [(0, 0, {
                "name": description,
                "price_unit": amount,
                "product_id": product_id
            })]
        }]]
    )

    return invoice_id'''
