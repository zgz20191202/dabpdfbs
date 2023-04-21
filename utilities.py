from time import sleep
import shift


def cancel_orders_wrap_up(trader, ticker):
    # cancel all the remaining orders
    if len(trader.get_waiting_list()) != 0:
        for order in trader.get_waiting_list():
            if (order.symbol == ticker):
                trader.submit_cancellation(order)
                print(f"{trader.get_last_trade_time()}: 1st time ready to cancel orders no matter what! order id: {order.id}. cancel existing {order.type } order for {ticker}! executed size: {order.executed_size}, price: {order.price}")
                sleep(1)  # the order cancellation needs a little time to go through
    

def close_positions_wrap_up(trader, ticker):
    print(f"running close positions function for {ticker}")
    item = trader.get_portfolio_item(ticker)
    # close any long positions
    long_shares = item.get_long_shares()
    if long_shares > 0:
        print(f"market selling because {ticker} long shares = {long_shares}")
        order = shift.Order(shift.Order.Type.MARKET_SELL,
                            ticker, int(long_shares/100))  # we divide by 100 because orders are placed for lots of 100 shares
        trader.submit_order(order)
        sleep(1)  
    # close any short positions
    short_shares = item.get_short_shares()
    if short_shares > 0:
        print(f"market buying because {ticker} short shares = {short_shares}")
        order = shift.Order(shift.Order.Type.MARKET_BUY,
                            ticker, int(short_shares/100))
        trader.submit_order(order)
        sleep(1)
    print(f"time: {trader.get_last_trade_time()}, after wrap up closing. {ticker} has long {trader.get_portfolio_item(ticker).get_long_shares()} shares and short {trader.get_portfolio_item(ticker).get_short_shares()} shares!")