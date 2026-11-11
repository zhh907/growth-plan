//+------------------------------------------------------------------+
//| SampleC.mq4 — MA trend martingale skeleton (partial hardening)   |
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
   static datetime lastBarTime = 0;
   if(Time[0] == lastBarTime)
      return;
   lastBarTime = Time[0];

   double fast = iMA(Symbol(), 0, MaFastPeriod, 0, MODE_EMA, PRICE_CLOSE, 0);
   double slow = iMA(Symbol(), 0, MaSlowPeriod, 0, MODE_EMA, PRICE_CLOSE, 0);

   if(fast > slow)
      OpenTrade(OP_BUY);
   else if(fast < slow)
      OpenTrade(OP_SELL);
}

double NormalizeLots(double lots)
{
   double lotStep = MarketInfo(Symbol(), MODE_LOTSTEP);
   double minLot  = MarketInfo(Symbol(), MODE_MINLOT);
   double maxLot  = MarketInfo(Symbol(), MODE_MAXLOT);
   if(lotStep > 0)
      lots = MathFloor(lots / lotStep) * lotStep;
   lots = MathMax(minLot, MathMin(maxLot, lots));
   return(lots);
}

void OpenTrade(int type)
{
   int existing = CountOrders(type);
   if(existing >= MaxTrades)
      return;

   double lots = NormalizeLots(BaseLots * MathPow(Multiplier, existing));

   double price = (type == OP_BUY) ? Ask : Bid;
   double tp = (type == OP_BUY) ? price + TakeProfitPips * Point
                                : price - TakeProfitPips * Point;

   int ticket = OrderSend(Symbol(), type, lots, price, 3, 0, tp,
                          "SampleC", 99999, 0, clrRed);
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
      if(OrderMagicNumber() != 99999) continue;
      if(OrderType() == type) count++;
   }
   return(count);
}
