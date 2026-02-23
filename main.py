"""
知识星球内容爬取工具 - 命令行入口
"""
import argparse
import logging
from datetime import datetime

from scraper import ScraperConfig, Scraper, parse_time_arg

# 全局时间过滤范围默认值
DEFAULT_START_TIME = '2026-01-01'
DEFAULT_END_TIME = datetime.now().strftime('%Y-%m-%d')

# 是否爬取图片和文件（默认不爬取）
DEFAULT_NO_IMAGES = True
DEFAULT_NO_FILES = True

GROUP = ''
COOKIES = ''

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='知识星球内容爬取工具')
    parser.add_argument('--start-time', type=str, default=DEFAULT_START_TIME,
                        help='爬取的起始时间（包含），格式：YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS')
    parser.add_argument('--end-time', type=str, default=DEFAULT_END_TIME,
                        help='爬取的结束时间（包含），格式：YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS')
    parser.add_argument('--no-images', action='store_true', default=DEFAULT_NO_IMAGES,
                        help='不爬取图片')
    parser.add_argument('--no-files', action='store_true', default=DEFAULT_NO_FILES,
                        help='不爬取文件')
    parser.add_argument('--gui', action='store_true', default=False,
                        help='启动图形界面模式')
    args = parser.parse_args()

    if args.gui:
        from gui import main as gui_main
        gui_main()
    else:
        # 命令行模式
        start_time = parse_time_arg(args.start_time)
        end_time = parse_time_arg(args.end_time)

        if start_time:
            logger.info('起始时间: {}'.format(start_time))
        if end_time:
            logger.info('结束时间: {}'.format(end_time))
        if start_time and end_time and start_time > end_time:
            logger.error('起始时间不能晚于结束时间！')
            exit(1)

        enable_images = not args.no_images
        enable_files = not args.no_files
        if not enable_images:
            logger.info('已禁用图片爬取')
        if not enable_files:
            logger.info('已禁用文件爬取')

        config = ScraperConfig(
            group=GROUP,
            cookies=COOKIES,
            start_time=start_time,
            end_time=end_time,
            enable_images=enable_images,
            enable_files=enable_files,
        )

        scraper = Scraper(config)
        scraper.run()
