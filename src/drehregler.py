import asyncio
import sys

import redis


REDIS = None
REDIS_RATE = 'dreh.PER_SECOND'
REDIS_TARGET = 'MAXUSERS'
REDIS_THRESHOLD = 'dreh.THRESHOLD'


async def update_redis():
    global REDIS
    while True:
        rate = int(REDIS.get(REDIS_RATE) or 0)
        threshold = int(REDIS.get(REDIS_THRESHOLD) or 0)
        current = int(REDIS.get(REDIS_TARGET) or 0)

        if rate > 0:
            if current + rate < threshold:
                REDIS.incrby(REDIS_TARGET, rate)
                print('Incrementing by {}. Current is {}. Limit is {}.'.format(rate, current, threshold))
            else:
                print('Not incrementing, would cross threshold.')
        elif rate == 0:
            print('Not incrementing, rate is 0.')
        await asyncio.sleep(1)


def get_user_input():
    global REDIS

    command = sys.stdin.readline().strip()
    if command.startswith('t '):
        try:
            threshold = int(command[2:])
            REDIS.set(REDIS_THRESHOLD, threshold)
            print('Moved threshold to {}'.format(threshold))
        except:
            print('Could not parse threshold value.')
    elif command.startswith('r '):
        try:
            rate = int(command[2:])
            REDIS.set(REDIS_RATE, rate)
            print('Moved rate to {}'.format(rate))
        except Exception as e:
            print('Could not parse rate value "{}": {}'.format(command[2:], str(e)))
    else:
        print('Enter `t <value>` to change threshold and `r <value>` to modify the change rate.')


if __name__ == '__main__':
    REDIS = redis.StrictRedis(host='localhost', port=6379, db=0)
    REDIS.set(REDIS_RATE, 0)
    REDIS.set(REDIS_THRESHOLD, 100)

    loop = asyncio.get_event_loop()
    loop.add_reader(sys.stdin, get_user_input)
    update_task = asyncio.async(update_redis())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    loop.close()
