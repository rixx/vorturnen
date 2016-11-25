#!/usr/bin/env python3.5
"""
An example script combining polling-like background tasks and user interaction
via Python3.5 asyncio. See drehregler-legacy.py for Python3.4.

Global data is saved inside the redis, because if you have a data store, you
might as well use it.
"""
import asyncio
import curses
import sys

import redis


REDIS = None
REDIS_CURRENT = 'QUEUEPOS'
REDIS_RATE = 'dreh.PER_SECOND'
REDIS_TARGET = 'MAXUSERS'
REDIS_THRESHOLD = 'dreh.THRESHOLD'
STATUS_LINE = 'Rate: {0: >10}/s | Limit: {1: >10} | Current limit: {2: >10} | Current requests: {3: >10}'
WINDOW = None


async def update_redis():
    """
    Update the redis value in 1s intervals.
    """
    remainder = 0
    while True:
        rate = float(REDIS.get(REDIS_RATE).decode() or 0)
        threshold = int(float(REDIS.get(REDIS_THRESHOLD) or 0))
        current = int(REDIS.get(REDIS_TARGET) or 0)
        waiting = int(REDIS.get(REDIS_CURRENT) or 0)
        status_line = STATUS_LINE.format(rate, threshold, current, waiting)

        if rate > 0:
            if current + rate <= threshold:
                incrby = int(rate)
                remainder += rate - incrby
                if remainder >= 1:
                    incrby += int(remainder)
                    remainder = remainder - int(remainder)
                REDIS.incrby(REDIS_TARGET, incrby)
        WINDOW.addstr(0, 0, status_line)
        WINDOW.move(1, 2)
        WINDOW.refresh()
        await asyncio.sleep(1)


def get_user_input():
    """
    Read, clean and process user input.
    """
    def print_user_line(msg):
        WINDOW.addstr(2, 0, msg)
        WINDOW.clrtoeol()

    command = WINDOW.getstr(1, 2).decode()
    if command.startswith('t ') or command.startswith('r '):
        remainder = command[2:].strip()
        offset = remainder.startswith('+')
        remainder = remainder[1:] if offset else remainder

        try:
            value = float(remainder)
        except Exception as e:
            print_user_line('Could not parse value "{}": {}'.format(command[2:], str(e)))

        key = REDIS_THRESHOLD if command.startswith('t') else REDIS_RATE
        value += float(REDIS.get(key)) if offset else 0
        REDIS.set(key, str(value))
        print_user_line('Updated {} to {}.'.format(key, value))
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
