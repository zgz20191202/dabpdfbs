import shift
from time import sleep
from datetime import datetime, timedelta
import datetime as dt
from threading import Thread
from utilities import * 
from strategies import *
# import logging

def main(trader):
    # keeps track of times for the simulation
    check_frequency = 60
    # for main competition
    start_time = datetime.combine(trader.get_last_trade_time(), dt.time(9, 40, 0))
    end_time = datetime.combine(trader.get_last_trade_time(), dt.time(15, 40, 0))

    # for test only
    # current = trader.get_last_trade_time()
    # start_time = current
    # end_time = start_time + timedelta(minutes=5)

    # logging.basicConfig(filename='day1.log', format="",level=logging.DEBUG)
    # logging.debug(f"start time: {start_time}")
    # logging.debug(f"end time: {end_time}")
    # logging.debug(f"current time: {trader.get_last_trade_time()}")
    
    while trader.get_last_trade_time() < start_time:
        # logging.debug(f"{trader.get_last_trade_time()} still waiting for market open")
        sleep(check_frequency)

    initial_pl = trader.get_portfolio_summary().get_total_realized_pl()

    threads = []
    tickers = trader.get_stock_list()
    print("START")
    for ticker in tickers:
        threads.append(Thread(target=dual_ema, args=(trader, ticker, end_time)))
    
    # for pair trading
    # stock_pair_ls = ["JPM", "GS"]
    # threads.append(Thread(target=pair_trade, args=(trader, stock_pair_ls, end_time)))

    for thread in threads:
        thread.start()
        sleep(1)

    # wait until endtime is reached
    while trader.get_last_trade_time() < end_time:
        # logging.debug("end time not reached")
        sleep(check_frequency)
    
    # logging.debug("end time reached!")

    # wait for all threads to finish
    for thread in threads:
        thread.join(timeout = 5)

    # make sure all remaining orders have been cancelled and all positions have been closed
    for ticker in tickers:
        cancel_orders(trader, ticker)
        close_positions(trader, ticker)

    print("END")
    print(f"final bp: {trader.get_portfolio_summary().get_total_bp()}")
    print(
        f"final profits/losses: {trader.get_portfolio_summary().get_total_realized_pl() - initial_pl}")
    print(f"total shares traded: {trader.get_portfolio_summary().get_total_shares()}")


if __name__ == '__main__':
    with shift.Trader("skl") as trader:
        trader.connect("initiator.cfg", "15n55Y770n")
        sleep(1)
        trader.sub_all_order_book()
        sleep(1)

        main(trader)
