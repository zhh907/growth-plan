"""划转服务:带输入校验和显式异常处理。"""
import logging

logger = logging.getLogger(__name__)

MIN_AMOUNT = 0.01
MAX_AMOUNT = 1_000_000.0


def validate_amount(amount):
    if not isinstance(amount, (int, float)):
        raise TypeError(f"amount must be numeric, got {type(amount).__name__}")
    if amount < MIN_AMOUNT:
        raise ValueError(f"amount below minimum {MIN_AMOUNT}")
    if amount > MAX_AMOUNT:
        raise ValueError(f"amount above maximum {MAX_AMOUNT}")
    return float(amount)


def transfer(amount, balance):
    amount = validate_amount(amount)      # 第 21 行:防护在这里(模拟审计员的切片看不到它)
    if amount > balance:
        raise ValueError("insufficient balance")
    return balance - amount
