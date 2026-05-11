"""
知识星球内容爬取工具 - 命令行入口
"""
import argparse
import json
import logging
import os
from datetime import datetime, timedelta

from scraper import ScraperConfig, Scraper, parse_time_arg

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.zsxq_config.json')


def load_config():
    """从 .zsxq_config.json 加载配置，返回字典，文件不存在或解析失败时返回空字典"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

# 全局时间过滤范围默认值
DEFAULT_START_TIME = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
DEFAULT_END_TIME = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

# 是否爬取图片和文件（默认不爬取）
DEFAULT_NO_IMAGES = True
DEFAULT_NO_FILES = True

# 从配置文件加载初始值（命令行参数可覆盖）
_cfg = load_config()
GROUP = _cfg.get('group', '')
COOKIES = _cfg.get('cookies', '')

# 若配置文件中 end_time 为空，则沿用 DEFAULT_END_TIME
_cfg_end_time = _cfg.get('end_time', '')
if _cfg_end_time:
    DEFAULT_END_TIME = _cfg_end_time

_cfg_start_time = _cfg.get('start_time', '')
if _cfg_start_time:
    DEFAULT_START_TIME = _cfg_start_time

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
