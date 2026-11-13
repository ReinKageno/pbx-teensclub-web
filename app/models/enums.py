from enum import Enum


class NotifyType(str, Enum):
    EMAIL = "email"
    SYSTEM = "system"
    DONATION = "donation"
    SAVING = "saving"

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class GoalStatus(str, Enum):
    ACTIVE = "active"
    UPCOMING = "upcoming"
    FINISHED = "finished"