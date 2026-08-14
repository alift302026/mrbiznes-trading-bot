from sqlalchemy import (
    func,
    select,
)

from app.models.database import (
    SessionLocal,
)

from app.models.support import (
    SupportMessage,
    SupportTicket,
)


VALID_CATEGORIES = {
    "technical",
    "payment",
    "alerts",
    "suggestion",
    "other",
}

OPEN_STATUSES = {
    "open",
    "answered",
}


# ============================================================
# CREATE TICKET
# ============================================================

def create_ticket(
    telegram_id,
    category,
    message,
):

    category = (
        category
        .strip()
        .lower()
    )

    message = (
        message
        .strip()
    )

    if category not in VALID_CATEGORIES:
        raise ValueError(
            "Invalid support category"
        )

    if len(message) < 3:
        raise ValueError(
            "Message is too short"
        )

    if len(message) > 4000:
        raise ValueError(
            "Message is too long"
        )

    with SessionLocal() as db:

        # Anti-spam:
        # Maximum 3 open/answered tickets per user.
        active_count = db.scalar(
            select(
                func.count(
                    SupportTicket.id
                )
            ).where(
                SupportTicket.telegram_id
                == telegram_id,

                SupportTicket.status.in_(
                    OPEN_STATUSES
                ),
            )
        ) or 0

        if active_count >= 3:

            raise ValueError(
                "Too many open tickets"
            )

        ticket = SupportTicket(
            telegram_id=telegram_id,
            category=category,
            status="open",
        )

        db.add(ticket)
        db.flush()

        support_message = (
            SupportMessage(
                ticket_id=ticket.id,
                sender_type="user",
                sender_id=telegram_id,
                message=message,
            )
        )

        db.add(
            support_message
        )

        db.commit()
        db.refresh(ticket)

        return ticket


# ============================================================
# USER TICKETS
# ============================================================

def user_tickets(
    telegram_id,
    limit=20,
):

    with SessionLocal() as db:

        return list(
            db.scalars(
                select(
                    SupportTicket
                )
                .where(
                    SupportTicket.telegram_id
                    == telegram_id
                )
                .order_by(
                    SupportTicket.id.desc()
                )
                .limit(limit)
            ).all()
        )


# ============================================================
# GET TICKET
# ============================================================

def get_ticket(
    ticket_id,
    telegram_id=None,
):

    with SessionLocal() as db:

        query = (
            select(
                SupportTicket
            )
            .where(
                SupportTicket.id
                == ticket_id
            )
        )

        if telegram_id is not None:

            query = query.where(
                SupportTicket.telegram_id
                == telegram_id
            )

        return db.scalar(
            query
        )


# ============================================================
# TICKET MESSAGES
# ============================================================

def ticket_messages(
    ticket_id,
):

    with SessionLocal() as db:

        return list(
            db.scalars(
                select(
                    SupportMessage
                )
                .where(
                    SupportMessage.ticket_id
                    == ticket_id
                )
                .order_by(
                    SupportMessage.id.asc()
                )
            ).all()
        )


# ============================================================
# USER REPLY
# ============================================================

def user_reply(
    ticket_id,
    telegram_id,
    message,
):

    message = (
        message
        .strip()
    )

    if (
        len(message) < 1
        or len(message) > 4000
    ):
        return False

    with SessionLocal() as db:

        ticket = db.scalar(
            select(
                SupportTicket
            )
            .where(
                SupportTicket.id
                == ticket_id,

                SupportTicket.telegram_id
                == telegram_id,
            )
        )

        if ticket is None:
            return False

        if ticket.status == "closed":
            return False

        item = SupportMessage(
            ticket_id=ticket.id,
            sender_type="user",
            sender_id=telegram_id,
            message=message,
        )

        ticket.status = "open"

        db.add(item)
        db.commit()

        return True


# ============================================================
# ADMIN REPLY
# ============================================================

def admin_reply(
    ticket_id,
    admin_id,
    message,
):

    message = (
        message
        .strip()
    )

    if (
        len(message) < 1
        or len(message) > 4000
    ):
        return False

    with SessionLocal() as db:

        ticket = db.get(
            SupportTicket,
            ticket_id,
        )

        if ticket is None:
            return False

        if ticket.status == "closed":
            return False

        item = SupportMessage(
            ticket_id=ticket.id,
            sender_type="admin",
            sender_id=admin_id,
            message=message,
        )

        ticket.status = "answered"

        db.add(item)
        db.commit()

        return True


# ============================================================
# CLOSE TICKET
# ============================================================

def close_ticket(
    ticket_id,
    telegram_id=None,
):

    with SessionLocal() as db:

        query = (
            select(
                SupportTicket
            )
            .where(
                SupportTicket.id
                == ticket_id
            )
        )

        if telegram_id is not None:

            query = query.where(
                SupportTicket.telegram_id
                == telegram_id
            )

        ticket = db.scalar(
            query
        )

        if ticket is None:
            return False

        ticket.status = "closed"

        db.commit()

        return True


# ============================================================
# ADMIN OPEN TICKETS
# ============================================================

def open_tickets(
    limit=50,
):

    with SessionLocal() as db:

        return list(
            db.scalars(
                select(
                    SupportTicket
                )
                .where(
                    SupportTicket.status
                    != "closed"
                )
                .order_by(
                    SupportTicket.id.desc()
                )
                .limit(limit)
            ).all()
        )