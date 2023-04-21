import shift
from time import sleep
from datetime import datetime, timedelta
import datetime as dt
from threading import Thread
from utilities import * 
from strategies import *

def main(trader):
    # keeps track of times for the simulation
    check_frequency = 60
    # # for main competition
    start_time = datetime.combine(trader.get_last_trade_time(), dt.time(9, 50, 0))
    end_time = datetime.combine(trader.get_last_trade_time(), dt.time(15, 57, 0))

    # for test only
    # current = trader.get_last_trade_time()
    # start_time = current
    # end_time = start_time + timedelta(minutes=5)

    print(f"start time: {start_time}")
    print(f"end time: {end_time}")
    print(f"current time: {trader.get_last_trade_time()}")
    
    while trader.get_last_trade_time() < start_time:
        print(f"{trader.get_last_trade_time()} still waiting for market open")
        sleep(check_frequency)

    initial_pl = trader.get_portfolio_summary().get_total_realized_pl()

    threads = []
    tickers = trader.get_stock_list()
    initial_pl_ls = [trader.get_portfolio_item(ticker).get_realized_pl() for ticker in tickers]

    print("START")

    threads.append(Thread(target=pure_momentum, args=(trader, tickers, end_time)))

    for thread in threads:
        thread.start()
        sleep(1)

    # wait until endtime is reached
    while trader.get_last_trade_time() <= end_time:
        print("end time not reached")
        sleep(check_frequency)
    
    print("end time reached!")

    # wait for all threads to finish
    for thread in threads:
        thread.join(timeout = 5)

    # make sure all remaining orders have been cancelled and all positions have been closed
    for ticker in tickers:
        cancel_orders_wrap_up(trader, ticker)
        close_positions_wrap_up(trader, ticker)
    print("END")
    print(f"final bp: {trader.get_portfolio_summary().get_total_bp()}")

    final_pl_ls = [trader.get_portfolio_item(ticker).get_realized_pl() for ticker in tickers]
    for i in range(len(tickers)):
        print(f"final pnl for {ticker}: {final_pl_ls[i] - initial_pl_ls[i]}")
    
    print(f"final total pnl: {trader.get_portfolio_summary().get_total_realized_pl() - initial_pl}")
    print(f"total shares traded: {trader.get_portfolio_summary().get_total_shares()}")


if __name__ == '__main__':
    with shift.Trader("skl") as trader:
        trader.connect("initiator.cfg", "15n55Y770n")
        sleep(1)
        trader.sub_all_order_book()
        sleep(1)

        main(trader)
