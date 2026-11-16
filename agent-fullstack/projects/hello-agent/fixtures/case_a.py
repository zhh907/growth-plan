"""结算服务:计算订单总额并写入日志。"""
import logging

logger = logging.getLogger(__name__)


def append_item(item, cart=[]):          # 第 7 行:可变默认参数,所有调用共享同一个列表
    cart.append(item)
    return cart


def load_price(symbol):
    try:
        return {"XAUUSD": 2650.0, "EURUSD": 1.05}[symbol]
    except:                               # 第 15 行:裸 except,吞掉一切异常
        return 0.0


def settlement_amount(items, price):
    return sum(items) * price
