//+------------------------------------------------------------------+
//| SampleA.mq4 — MA trend martingale skeleton                       |
//+------------------------------------------------------------------+
#property strict

input double BaseLots     = 0.01;
input double Multiplier   = 1.7;
input int    MaFastPeriod = 10;
input int    MaSlowPeriod = 30;
input int    TakeProfitPips = 60;
input int    MaxTrades    = 5;

int OnInit()
{
   return(INIT_SUCCEEDED);
}

void OnTick()
{
   double fast = iMA(Symbol(), 0, MaFastPeriod, 0, MODE_EMA, PRICE_CLOSE, 0);
   double slow = iMA(Symbol(), 0, MaSlowPeriod, 0, MODE_EMA, PRICE_CLOSE, 0);

   if(fast > slow)
      OpenTrade(OP_BUY);
   else if(fast < slow)
      OpenTrade(OP_SELL);
}

void OpenTrade(int type)
{
   int existing = CountOrders(type);
   if(existing >= MaxTrades)
      return;

   double lots = BaseLots * MathPow(Multiplier, existing);

   double price = (type == OP_BUY) ? Ask : Bid;
   double tp = (type == OP_BUY) ? price + TakeProfitPips * Point
                                : price - TakeProfitPips * Point;

   int ticket = OrderSend(Symbol(), type, lots, price, 3, 0, tp,
                          "SampleA", 12345, 0, clrGreen);
   if(ticket < 0)
      Print("OrderSend failed, error = ", GetLastError());
}

int CountOrders(int type)
{
   int count = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      if(!OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) continue;
      if(OrderSymbol() != Symbol()) continue;
      if(OrderMagicNumber() != 12345) continue;
      if(OrderType() == type) count++;
   }
   return(count);
}
