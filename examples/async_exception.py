"""
测试异步下的异常
"""

import asyncio


class MyException(Exception):
    pass


async def raise_some_exception(i):
    print(f'开始 {i}')
    raise MyException(f'raise_some_exception {i}')


async def main():
    try:
        await raise_some_exception(5241)
    except MyException as me:
        print('MyException await')
        print(me, me.__class__.__name__)

    print()

    ##########

    # 为什么只抛出了第一个异常？
    tasks = [raise_some_exception(_) for _ in range(100, 106)]
    try:
        await asyncio.gather(*tasks)
    except MyException as me:
        print('MyException gather')
        print(me, me.__class__.__name__)

    print()

    ##########

    # 每个异常都抛出了
    tasks = [raise_some_exception(_) for _ in range(200, 206)]
    for task in asyncio.as_completed(tasks):
        try:
            await task
        except MyException as me:
            print('MyException as_completed')
            print(me, me.__class__.__name__)


if __name__ == '__main__':
    asyncio.run(main())
