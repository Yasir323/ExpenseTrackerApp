import asyncio

from fastapi import FastAPI
from aiosmtplib import SMTP
from email.message import EmailMessage

from app.models import DbExpense
from app.crud import get_emails
app = FastAPI()


async def send_email_async(to_email: str, subject: str, body: str):
    try:
        async with SMTP(hostname="smtp.example.com", port=587, use_tls=True) as smtp:
            message = EmailMessage()
            message["From"] = "your@example.com"
            message["To"] = to_email
            message["Subject"] = subject
            message.set_content(body)
            await smtp.send_message(message)
    except:
        pass


async def send_expense_notification(expense: DbExpense):
    subject = "New Expense Added"
    users = [expense.payee_id] + list(set(p.user_id for p in expense.participants))
    user_email_map = await get_emails(users)
    tasks = []
    for participant in expense.participants:
        if participant.user_id == expense.payee_id:
            body = f"You created a new expense. Amount paid = {expense.amount}"
        else:
            body = f"You have been added to a new expense. Total amount owed: {participant.amount}"
        tasks.append(asyncio.create_task(send_email_async(user_email_map[participant.user_id], subject, body)))
    await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
