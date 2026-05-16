#!/bin/bash

# 获取昨天和今天的日期
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
TODAY=$(date +%Y-%m-%d)
TOMORROW=$(date -d "tomorrow" +%Y-%m-%d)

mkdir ./scraper_logs

# 执行爬虫
python3 main.py \
  --start-time "$YESTERDAY" \
  --end-time "$TOMORROW" \
  --no-images \
  --no-files >> ./scraper_logs/$(date +%Y-%m-%d).log 2>&1

echo "爬取完成，时间：$(date '+%Y-%m-%d %H:%M:%S')" >> ./scraper_logs/$(date +%Y-%m-%d).log
