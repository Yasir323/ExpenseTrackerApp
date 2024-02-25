import asyncio

from app.crud import get_emails, get_user_balance
from app.database import get_db
from app.notification import send_email_async


async def send_weekly_summary():
    # Prepare email content
    subject = "Weekly Summary: Amounts Owed"

    user_email_map = await get_emails()
    db = get_db()
    tasks = []
    for user_id, email in user_email_map.items():
        body = "Here is the summary of amounts owed:\n\n"
        user_balance = await get_user_balance(db, user_id)
        for b in user_balance:
            if b["amount_owed"] > 0:
                body += f"You owe {b['amount_owed']} to {b['user']}\n"
            elif b["amount_owed"] < 0:
                body += f"{b['user']} owes you {b['amount_owed']}\n"
            else:
                continue
        tasks.append(asyncio.create_task(send_email_async(email, subject, body)))
    await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
