import shift
from utilities import * 
import pandas as pd
import numpy as np
import logging
from datetime import timedelta

# strategy parameters
short_ema_period = 8
long_ema_period = 13
cross_threshold = 0.01
logging.basicConfig(filename='example.log', format="",level=logging.DEBUG)


def send_order(trader: shift.Trader, order_type ,ticker, target_price, order_size):
    """
    send orders
    """
    price = round(target_price, 2)  
    order_size = int((order_size// 100) * 100)
    if order_size < 100:
        logging.debug(f"time: {trader.get_last_trade_time()}, order size smaller than 100! order type: {order_type}, order size: {order_size}, order price: {price} ticker: {ticker} ")
        return None
    if order_size >= 100 and order_type in [shift.Order.Type.LIMIT_BUY, shift.Order.Type.LIMIT_SELL]:
        order = shift.Order(order_type, ticker, order_size, price)
        logging.debug(f"time: {trader.get_last_trade_time()}, send a new limit order! order type: {order_type}, order size: {order_size}, order price: {price} ticker: {ticker} ")
    if order_size >= 100 and order_type in [shift.Order.Type.MARKET_BUY, shift.Order.Type.MARKET_SELL]:
        order = shift.Order(order_type, ticker, order_size)
        logging.debug(f"time: {trader.get_last_trade_time()}, send a new market order! order type: {order_type}, order size: {order_size}, order price: {price} ticker: {ticker} ")
    trader.submit_order(order)


def get_ema(prices, period: int) -> float:
    """
    Calculates the Exponential Moving Average (EMA) for the given prices of a single product and period
    """
    if len(prices) < period:
        return sum(prices) / len(prices)
    multiplier = 2 / (period + 1)
    ema_prev = sum(prices[-period:]) / period
    for price in prices[-period + 1:]:
        ema = (price - ema_prev) * multiplier + ema_prev
        ema_prev = ema
    return ema 


def generate_signal(ema_long_ls, ema_short_ls):
    """
    when short ema is crossing long ema, return long signal
    when short ema is falling below long ema, return short signal
    """
    signal = 0
    if len(ema_long_ls) == 1:
        if ema_long_ls[-1] - cross_threshold > ema_short_ls[-1]:
            signal = -1
        elif ema_long_ls[-1] + cross_threshold < ema_short_ls[-1]:
            signal = 1
    elif len(ema_long_ls) > 1:
        if ema_long_ls[-1] - cross_threshold > ema_short_ls[-1] and ema_long_ls[-2] < ema_short_ls[-2]:
            signal = -1
        elif ema_long_ls[-1] + cross_threshold < ema_short_ls[-1] and ema_long_ls[-2] > ema_short_ls[-2]:
            signal = 1
    return signal
    

def stop_loss(trader, ticker, fair_price_ls):
    """
    stop loss when losing 10%
    """
    portfolio = trader.get_portfolio_item(ticker)
    stop_flag = False
    if portfolio.get_long_shares() > 0:
        if (portfolio.get_long_price() - fair_price_ls[-1])/portfolio.get_long_price() > 0.1:
            # sell all position
            close_positions(trader, ticker)
            stop_flag = True
    if portfolio.get_short_shares() > 0:
        if (portfolio.get_short_price() - fair_price_ls[-1])/portfolio.get_short_price() < -0.1:
            # buy back all position
            close_positions(trader, ticker)
            stop_flag = True
    return stop_flag


def stop_profit(trader, ticker, fair_price_ls):
    """
    stop profit when earning 20%
    """
    portfolio = trader.get_portfolio_item(ticker)
    stop_flag = False
    if portfolio.get_long_shares() > 0:
        if (portfolio.get_long_price() - fair_price_ls[-1])/portfolio.get_long_price() < -0.2:
            # sell all position
            close_positions(trader, ticker)
            stop_flag = True
    if portfolio.get_short_shares() > 0:
        if (portfolio.get_short_price() - fair_price_ls[-1])/portfolio.get_short_price() > 0.2:
            # buy back all position
            close_positions(trader, ticker)
            stop_flag = True
    return stop_flag


def dual_ema(trader: shift.Trader, ticker, endtime):
    logging.debug(f"time: {trader.get_last_trade_time()}, {ticker} ready for dual ema!")

    intial_pnl = trader.get_portfolio_item(ticker).get_realized_pl()
    best_bid_ls = []
    best_ask_ls = []
    fair_price_ls = []
    ema_long_ls = []
    ema_short_ls = []
    signal_ls = []

    while (trader.get_last_trade_time() < endtime - timedelta(minutes=1)):
        cancel_orders(trader, ticker)
        best_price = trader.get_best_price(ticker)
        best_bid_price = best_price.get_bid_price()
        best_ask_price = best_price.get_ask_price()
        best_bid_ls.append(best_bid_price)
        best_ask_ls.append(best_ask_price)
        fair_price_ls.append((best_bid_price + best_ask_price)/2)

        if len(fair_price_ls) >= long_ema_period:
            logging.debug(f"time: {trader.get_last_trade_time()}, {ticker} ready for trading!")
            ema_short_ls.append(get_ema(fair_price_ls, short_ema_period))
            ema_long_ls.append(get_ema(fair_price_ls, long_ema_period))

            if stop_loss(trader, ticker, fair_price_ls):
                logging.debug(f"time: {trader.get_last_trade_time()}, {ticker} stop loss triggered! Need to cool down")
                signal_ls = []
            elif stop_profit(trader, ticker, fair_price_ls):
                logging.debug(f"time: {trader.get_last_trade_time()}, {ticker} stop profit triggered! Need to cool down")
                signal_ls = []
            else:
                signal = generate_signal(ema_long_ls, ema_short_ls)
                buy_power = trader.get_portfolio_summary().get_total_bp()
                if signal == 1:
                    logging.debug(f"time: {trader.get_last_trade_time()}, {ticker} receive buy signal!")
                    # buy
                    target_price = best_bid_price + 0.01
                    ticker_short_position = trader.get_portfolio_item(ticker).get_short_shares()
                    order_size = ticker_short_position if ticker_short_position > 0 else min(100, buy_power/target_price)
                    send_order(trader, shift.Order.Type.LIMIT_BUY,ticker, target_price, order_size)
                    signal_ls.append(signal)
                if signal == -1:
                    logging.debug(f"time: {trader.get_last_trade_time()}, {ticker} receive sell signal!")
                    # sell
                    target_price = best_ask_price - 0.01
                    ticker_long_position = trader.get_portfolio_item(ticker).get_long_shares()
                    order_size = ticker_long_position if ticker_long_position > 0 else min(100, buy_power/target_price)
                    send_order(trader, shift.Order.Type.LIMIT_SELL,ticker, target_price, order_size)
                    signal_ls.append(signal)
        sleep(1)
    
    if (trader.get_last_trade_time() >= endtime - timedelta(minutes=1)) and trader.get_last_trade_time() < endtime:
        # cancel unfilled orders and close positions for this ticker
        cancel_orders(trader, ticker)
        close_positions(trader, ticker)
        print(f"total profits/losses for {ticker}: {trader.get_portfolio_item(ticker).get_realized_pl() - intial_pnl}")