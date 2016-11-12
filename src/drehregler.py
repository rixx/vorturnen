import asyncio
import sys


PER_SECOND = 0
THRESHOLD = 100


async def update_redis():
    while True:
        global PER_SECOND
        global THRESHOLD

        if PER_SECOND > 0:
            print('Incrementing by {}. Limit is {}.'.format(PER_SECOND, THRESHOLD))
        elif PER_SECOND == 0:
            print('Not incrementing.')
        await asyncio.sleep(1)


def get_user_input():
    global PER_SECOND
    global THRESHOLD

    command = sys.stdin.readline().strip()
    if command.startswith('t '):
        try:
            THRESHOLD = int(command[2:])
            print('Moved threshold to {}'.format(THRESHOLD))
        except:
            print('Could not parse threshold value.')
    elif command.startswith('r '):
        try:
            PER_SECOND = int(command[2:])
            print('Moved rate to {}'.format(PER_SECOND))
        except Exception as e:
            print('Could not parse rate value "{}": {}'.format(command[2:], str(e)))
    else:
        print('Enter `t <value>` to change threshold and `r <value>` to modify the change rate.')


if __name__ == '__main__':
    print('Starting with {}'.format(PER_SECOND))
    update_task = asyncio.async(update_redis())
    loop = asyncio.get_event_loop()
    loop.add_reader(sys.stdin, get_user_input)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    loop.close()
