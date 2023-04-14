from time import sleep
import shift
# import logging

# logging.basicConfig(filename='example.log', format="",level=logging.DEBUG)

def cancel_orders(trader, ticker):
    # cancel all the remaining orders
    for order in trader.get_waiting_list():
        if (order.symbol == ticker):
            trader.submit_cancellation(order)
            # logging.debug(f"time: {trader.get_last_trade_time()}, cancel all existing orders for {ticker}! executed size: {order.executed_size}")
            sleep(1)  # the order cancellation needs a little time to go through


def close_positions(trader, ticker):
    # NOTE: The following orders may not go through if:
    # 1. You do not have enough buying power to close your short postions. Your strategy should be formulated to ensure this does not happen.
    # 2. There is not enough liquidity in the market to close your entire position at once. You can avoid this either by formulating your
    #    strategy to maintain a small position, or by modifying this function to close ur positions in batches of smaller orders.

    # close all positions for given ticker
    item = trader.get_portfolio_item(ticker)
    # close any long positions
    long_shares = item.get_long_shares()
    if long_shares > 0:
        print(f"market selling because {ticker} long shares = {long_shares}")
        order = shift.Order(shift.Order.Type.MARKET_SELL,
                            ticker, int(long_shares/100))  # we divide by 100 because orders are placed for lots of 100 shares
        trader.submit_order(order)
        # logging.debug(f"time: {trader.get_last_trade_time()}, closing long positions function for {ticker}!")
        sleep(1)  # we sleep to give time for the order to process

    # close any short positions
    short_shares = item.get_short_shares()
    if short_shares > 0:
        print(f"market buying because {ticker} short shares = {short_shares}")
        order = shift.Order(shift.Order.Type.MARKET_BUY,
                            ticker, int(short_shares/100))
        trader.submit_order(order)
        # logging.debug(f"time: {trader.get_last_trade_time()}, closing short positions function for {ticker}!")
        sleep(1)