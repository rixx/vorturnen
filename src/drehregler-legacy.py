#!/usr/bin/env python3.4
"""
An example script combining polling-like background tasks and user interaction
via Python3.5 asyncio.

Global data is saved inside the redis, because if you have a data store, you
might as well use it.
"""
import asyncio
import curses
import sys

import redis


REDIS = None
REDIS_RATE = 'dreh.PER_SECOND'
REDIS_TARGET = 'MAXUSERS'
REDIS_THRESHOLD = 'dreh.THRESHOLD'
WINDOW = None


@asyncio.coroutine
def update_redis():
    """
    Update the redis value in 1s intervals.
    """
    while True:
        rate = int(REDIS.get(REDIS_RATE) or 0)
        threshold = int(REDIS.get(REDIS_THRESHOLD) or 0)
        current = int(REDIS.get(REDIS_TARGET) or 0)
        status_line = 'Rate: {0: >10}/s | Limit: {1: >10} | Current: {2: >10}'
        status_line = status_line.format(rate, threshold, current)

        if rate > 0:
            if current + rate < threshold:
                REDIS.incrby(REDIS_TARGET, rate)
                current += rate
        WINDOW.addstr(0, 0, status_line)
        WINDOW.move(1, 2)
        WINDOW.refresh()
        yield from asyncio.sleep(1)


def get_user_input():
    """
    Read, clean and process user input.
    """
    def print_user_line(msg):
        WINDOW.addstr(2, 0, msg)
        WINDOW.clrtoeol()

    command = WINDOW.getstr(1, 2).decode()
    if command.startswith('t '):
        try:
            threshold = int(command[2:])
            REDIS.set(REDIS_THRESHOLD, threshold)
            print_user_line('Updated threshold to {}.'.format(threshold))
        except Exception as e:
            print_user_line('Could not parse threshold value "{}": {}'.format(command[2:], str(e)))
    elif command.startswith('r '):
        try:
            rate = int(command[2:])
            REDIS.set(REDIS_RATE, rate)
            print_user_line('Updated rate to {}.'.format(rate))
        except Exception as e:
            print_user_line('Could not parse rate value "{}": {}'.format(command[2:], str(e)))
    elif command.startswith('quit'):
        raise KeyboardInterrupt
    else:
        print_user_line('`t <threshold>` | `r <rate>` | `quit`')

    WINDOW.move(1, 2)
    WINDOW.clrtoeol()
    WINDOW.refresh()


if __name__ == '__main__':
    REDIS = redis.StrictRedis(host='localhost', port=6379, db=0)
    REDIS.set(REDIS_RATE, 0)
    REDIS.set(REDIS_THRESHOLD, 100)
    WINDOW = curses.initscr()
    WINDOW.addstr(1, 0, '>')
    WINDOW.addstr(2, 0, '`t <threshold>` | `r <rate>` | `quit`')
    WINDOW.move(1, 2)
    WINDOW.refresh()

    loop = asyncio.get_event_loop()
    loop.add_reader(sys.stdin, get_user_input)
    update_task = asyncio.async(update_redis())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    loop.close()
    curses.endwin()
