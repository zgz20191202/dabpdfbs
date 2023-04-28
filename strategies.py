import shift
from utilities import * 
from datetime import timedelta

# strategy parameters
stop_loss_tick = 4
stop_profit_tick = 6
num_spread_tick = 1



def send_order(trader: shift.Trader, order_type ,ticker, target_price, order_share):
    """
    send orders
    """
    price = round(target_price, 2)  
    order_size = int(order_share// 100)
    for order in trader.get_waiting_list():
        # do not send orders when there is same type of order 
        if (order.symbol == ticker and order.type == order_type) :
            print(f"time: {trader.get_last_trade_time()}, detect waiting orders. don't send new orders ")
    if order_size < 1:
        print(f"time: {trader.get_last_trade_time()}, order size smaller than 1! order type: {order_type}, order size: {order_size}, order price: {price} ticker: {ticker} ")
    if order_size >= 1 and order_type in [shift.Order.Type.LIMIT_BUY, shift.Order.Type.LIMIT_SELL]:
        # if order_type == shift.Order.Type.LIMIT_BUY and trader.get_portfolio_item(ticker).get_long_shares() > 2000:
        #     print(f"time: {trader.get_last_trade_time()}, reach max long position! current long shares: {trader.get_portfolio_item(ticker).get_long_shares()} order type: {order_type}, order size: {order_size} ticker: {ticker} ")
        # if order_type == shift.Order.Type.LIMIT_SELL and trader.get_portfolio_item(ticker).get_short_shares() > 2000:
        #     print(f"time: {trader.get_last_trade_time()}, reach max short position! current short shares: {trader.get_portfolio_item(ticker).get_short_shares()} order type: {order_type}, order size: {order_size} ticker: {ticker} ")
        new_order = shift.Order(order_type, ticker, order_size, price)
        print(f"time: {trader.get_last_trade_time()}, send a new limit order! order type: {order_type}, order size: {order_size}, order price: {price} ticker: {ticker} ")
        trader.submit_order(new_order)


def pure_momentum(trader: shift.Trader, ticker_ls, endtime):
    # k: ticker, v: vwap list
    vwap_price_dict = {ticker: [] for ticker in ticker_ls}
    # k: ticker, v: return
    return_dict = {ticker: 0 for ticker in ticker_ls}
    # k: ticker, v: best bid price
    bid_price_dict = {ticker: 0 for ticker in ticker_ls}
    # k: ticker, v: best ask price
    ask_price_dict = {ticker: 0 for ticker in ticker_ls}
    # portfolio construction and rebalance
    print(f"{trader.get_last_trade_time()}: portfolio construction and rebalance")
    while (trader.get_last_trade_time() < endtime - timedelta(minutes=10)):
        # cancel stale orders
        print(f"{trader.get_last_trade_time()}: cancel stale orders!")
        for ticker in ticker_ls:
            cancel_orders_wrap_up(trader, ticker)
        
        # close previous position
        print(f"{trader.get_last_trade_time()}: close previous position")
        for ticker in ticker_ls:
            print(f"{trader.get_last_trade_time()}: close previous position for {ticker} ")
            close_positions_wrap_up(trader, ticker)

        # update data
        print(f"{trader.get_last_trade_time()}: update data!")
        for ticker in ticker_ls:
            best_price = trader.get_best_price(ticker)
            best_bid_price = best_price.get_bid_price()
            best_ask_price = best_price.get_ask_price()
            best_bid_size = best_price.get_bid_size()
            best_ask_size = best_price.get_ask_size()
            if best_bid_size + best_ask_size == 0:
                print(f"{trader.get_last_trade_time()}: sum of size equal to 0! best_bid_size: {best_bid_size} and best_ask_size: {best_ask_size}, best_bid_size: {best_bid_size}, best_ask_size: {best_ask_size}")
                continue
            VWAP = round((best_bid_price * best_bid_size + best_ask_price * best_ask_size)/(best_bid_size + best_ask_size), 2)
            vwap_price_dict[ticker].append(VWAP)
            bid_price_dict[ticker] = best_bid_price
            ask_price_dict[ticker] = best_ask_price
        if len(vwap_price_dict[ticker]) >=2:
            # get return for tickers
            for ticker in ticker_ls:
                ret_1m = vwap_price_dict[ticker][-1] / vwap_price_dict[ticker][-2] -1
                return_dict[ticker] = ret_1m
            # sort the dictionary by value and store the result as a list of tuples
            sorted_dict = sorted(return_dict.items(), key=lambda x: x[1], reverse=True)
            # get the keys of the top 5 and bottom 5 values
            # top_5_stock_ls = [x[0] for x in sorted_dict[-5:]]
            # bottom_5_stock_ls = [x[0] for x in sorted_dict[:5]]
            top_5_stock_ls = [x[0] for x in sorted_dict[:10]]
            bottom_5_stock_ls = [x[0] for x in sorted_dict[-10:]]
            print(f"{trader.get_last_trade_time()}: top 10 stocks selected: {top_5_stock_ls}")
            print(f"{trader.get_last_trade_time()}: bottom 10 stocks selected: {bottom_5_stock_ls}")

            purchase_power = trader.get_portfolio_summary().get_total_bp()
            print(f"{trader.get_last_trade_time()}: current purchase power: {purchase_power}")

            # rebalance position
            print(f"{trader.get_last_trade_time()}: rebalance for top 5 stocks")
            for ticker in top_5_stock_ls:
                # get current position in money
                target_investment = purchase_power / 20 
                investment_to_change = target_investment
                # investment_to_change = target_investment - current_investment
                if investment_to_change > 0:
                    print(f"{trader.get_last_trade_time()}: rebalance for {ticker}, investment to change: {investment_to_change}")
                    target_bid_price = vwap_price_dict[ticker] - 0.01 * 1
                    order_bid_shares = investment_to_change/target_bid_price
                    send_order(trader, shift.Order.Type.LIMIT_BUY,ticker, target_bid_price, order_bid_shares)
                
            
            print(f"{trader.get_last_trade_time()}: rebalance for bottom 5 stocks")
            for ticker in bottom_5_stock_ls:
                # get current position in money
                target_investment = purchase_power / 20 
                investment_to_change = target_investment
                if target_investment > 0:
                    print(f"{trader.get_last_trade_time()}: rebalance for {ticker}, investment to change: {investment_to_change}")
                    target_ask_price = vwap_price_dict[ticker] + 0.01 * 1
                    order_ask_shares = investment_to_change/target_ask_price
                    send_order(trader, shift.Order.Type.LIMIT_SELL,ticker, target_ask_price, order_ask_shares)
        sleep(90 * 60)

    # stop profit and stop loss phase
    print(f"time: {trader.get_last_trade_time()}, in stopping loss and profit phase!")
    while (trader.get_last_trade_time() >= endtime - timedelta(minutes=10)) and (trader.get_last_trade_time() < endtime - timedelta(minutes=2)):
        # cancel stale orders before doing stop loss and profit
        print(f"{trader.get_last_trade_time()}: cancel stale orders before doing stop loss and profit")
        for ticker in ticker_ls:
            cancel_orders_wrap_up(trader, ticker)
        print(f"{trader.get_last_trade_time()}: monitor stop and loss")
        for ticker in ticker_ls:
            close_price = trader.get_close_price(ticker)
            # positive for long and negative for short
            position = trader.get_portfolio_item(ticker).get_shares()
            # long position stop profit
            if (trader.get_portfolio_item(ticker).get_price() < close_price + 0.01 * stop_profit_tick) and (position > 0):
                send_order(trader, shift.Order.Type.LIMIT_SELL,ticker, close_price, position)
                print(f"time: {trader.get_last_trade_time()}, {ticker} stop profit from long position! stop_profit_tick: {stop_profit_tick}")
            # long position stop loss
            if (trader.get_portfolio_item(ticker).get_price() > close_price + 0.01 * stop_loss_tick) and (position > 0):
                send_order(trader, shift.Order.Type.LIMIT_SELL,ticker, close_price, position)
                print(f"time: {trader.get_last_trade_time()}, {ticker} stop loss from long position! stop_loss_tick: {stop_loss_tick}")
            # short position  stop profit
            if (trader.get_portfolio_item(ticker).get_price() > close_price - 0.01 * stop_profit_tick) and (position < 0):
                send_order(trader, shift.Order.Type.LIMIT_BUY, ticker, close_price, -position)
                print(f"time: {trader.get_last_trade_time()}, {ticker} stop profit from short position! stop_profit_tick: {stop_profit_tick}")
            # short position  stop loss
            if (trader.get_portfolio_item(ticker).get_price() < close_price - 0.01 * stop_profit_tick) and (position < 0):
                send_order(trader, shift.Order.Type.LIMIT_BUY, ticker, close_price, -position)
                print(f"time: {trader.get_last_trade_time()}, {ticker} stop loss from short position! stop_loss_tick: {stop_loss_tick}")
        sleep(15)
    print(f"time: {trader.get_last_trade_time()}, in wrapping up phase!")
    while (trader.get_last_trade_time() >= endtime - timedelta(minutes=2)) and (trader.get_last_trade_time() < endtime):
        for ticker in ticker_ls:
            cancel_orders_wrap_up(trader, ticker)
        if len(trader.get_waiting_list()) == 0:
            for ticker in ticker_ls:
                close_positions_wrap_up(trader, ticker)
        sleep(30)