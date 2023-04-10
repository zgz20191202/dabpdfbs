import shift
from time import sleep
from datetime import datetime
import datetime as dt
from threading import Thread
from utilities import * 
from strategies import *
import logging

def main(trader):
    # keeps track of times for the simulation
    check_frequency = 60
    start_time = datetime.combine(trader.get_last_trade_time(), dt.time(9, 38, 0))
    end_time = datetime.combine(trader.get_last_trade_time(), dt.time(15, 50, 0))
    logging.basicConfig(filename='example.log', format="",level=logging.DEBUG)

    logging.debug(f"start time: {start_time}")
    logging.debug(f"end time: {end_time}")
    logging.debug(f"current time: {trader.get_last_trade_time()}")
    

    while trader.get_last_trade_time() < start_time:
        logging.debug(f"{trader.get_last_trade_time()} still waiting for market open")
        sleep(check_frequency)

    # we track our overall initial profits/losses value to see how our strategy affects it
    initial_pl = trader.get_portfolio_summary().get_total_realized_pl()

    threads = []

    # in this example, we simultaneously and independantly run our trading alogirthm on all DOW 30 stocks
    tickers = trader.get_stock_list()

    print("START")

    for ticker in tickers:
        # initializes threads containing the strategy for each ticker
        threads.append(
            Thread(target=record, args=(trader, ticker, end_time)))

    for thread in threads:
        thread.start()

    # wait until endtime is reached
    while trader.get_last_trade_time() < end_time:
        sleep(check_frequency)
        logging.debug("end time not reached")
    
    logging.debug("end time reached!")

    # wait for all threads to finish
    for thread in threads:
        # NOTE: this method can stall your program indefinitely if your strategy does not terminate naturally
        # setting the timeout argument for join() can prevent this
        thread.join(timeout = 5)

    # make sure all remaining orders have been cancelled and all positions have been closed
    for ticker in tickers:
        cancel_orders(trader, ticker)
        close_positions(trader, ticker)

    print("END")
    print(f"final bp: {trader.get_portfolio_summary().get_total_bp()}")
    print(
        f"final profits/losses: {trader.get_portfolio_summary().get_total_realized_pl() - initial_pl}")


if __name__ == '__main__':
    with shift.Trader("skl_test10") as trader:
        trader.connect("initiator.cfg", "15n55Y770n")
        sleep(1)
        trader.sub_all_order_book()
        sleep(1)

        main(trader)
