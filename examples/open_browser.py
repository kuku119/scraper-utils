"""
测试打开浏览器
"""

import asyncio
from pathlib import Path

from scraper_utils.exceptions.browser_exception import BrowserLaunchedError
from scraper_utils.utils.browser_util import PersistentContextManager

if __name__ == '__main__':
    cwd = Path.cwd()

    async def main():
        """"""
        # pcm = PersistentContextManager(
        #     user_data_dir=cwd.joinpath('temp/chrome_data'),
        #     executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        #     channel='chrome',
        #     headless=False,
        # )
        # browser = await pcm.start()
        #
        # input('Enter...')
        #
        # await pcm.close()

        ##########

        # async with PersistentContextManager(
        #     user_data_dir=cwd.joinpath('temp/chrome_data'),
        #     executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        #     channel='chrome',
        #     headless=False,
        # ) as pcm:
        #     context = pcm.context
        #
        #     page = await context.new_page()
        #     await page.goto('https://www.baidu.com')
        #
        #     input('Enter...')

        ##########

        # pcm1 = PersistentContextManager(
        #     user_data_dir=cwd.joinpath('temp/chrome_data'),
        #     executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        #     channel='chrome',
        #     headless=False,
        # )
        # pcm2 = PersistentContextManager(
        #     user_data_dir=cwd.joinpath('temp/chrome_data_2'),
        #     executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        #     channel='chrome',
        #     headless=False,
        # )
        # pcm1_1 = PersistentContextManager(
        #     user_data_dir=cwd.joinpath('temp/chrome_data'),
        #     executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        #     channel='chrome',
        #     headless=False,
        # )
        #
        # await pcm1.start()
        # await pcm2.start()
        #
        # ####
        # # 为什么 except BrowserLaunchedError 抓不到 BrowserLaunchedError 异常，
        # # 反而在 except Exception 能抓到 BrowserLaunchedError 异常
        # try:
        #     await pcm1_1.start()
        # except BrowserLaunchedError as ble:  # 抓不到异常
        #     print('except BrowserLaunchedError')
        #     print(ble, ble.__class__.__name__)
        # except RuntimeError as re:  # 抓不到异常
        #     print('except RuntimeError')
        #     print(re, re.__class__.__name__)
        # except Exception as e:  # 为什么这里能抓到异常
        #     print('except Exception')
        #     print(e, e.__class__.__name__)
        # ####
        #
        # ####
        # # 为什么以这种方式就能正常拿到 BrowserLaunchedError
        # # results = await asyncio.gather(pcm1_1.start(), return_exceptions=True)
        # # for r in results:
        # #     print(r)
        # ####
        #
        # await pcm1.close()
        # await pcm2.close()
        # await pcm1_1.close()

        ###########

        # async with PersistentContextManager(
        #     user_data_dir=cwd.joinpath('temp/chrome_data'),
        #     executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        #     channel='chrome',
        #     headless=False,
        # ) as pcm1:
        #     try:
        #         async with PersistentContextManager(
        #             user_data_dir=cwd.joinpath('temp/chrome_data'),
        #             executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        #             channel='chrome',
        #             headless=False,
        #         ) as pcm2:
        #             pass
        #     except BrowserLaunchedError as ble:  # 抓不到异常
        #         print('except BrowserLaunchedError')
        #         print(ble)
        #     except Exception as e:  # 为什么这里能抓到异常
        #         print('except Exception')
        #         print(e)

    print('程序开始')
    asyncio.run(main())
    print('程序结束')
