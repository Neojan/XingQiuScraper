"""
知识星球内容爬取核心模块
可被 CLI 和 GUI 共同调用
"""
import queue
import time
import threading
import requests
import json
import logging
import os
import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Callable

logger = logging.getLogger(__name__)


@dataclass
class ScraperConfig:
    """爬取配置"""
    group: str = '88882252841552'
    cookies: str = ''
    start_time: str = ''
    end_time: str = ''
    enable_images: bool = False
    enable_files: bool = False
    output_dir: str = './output'


class Scraper:
    """知识星球爬取器"""

    def __init__(self, config: ScraperConfig,
                 on_log: Optional[Callable[[str], None]] = None,
                 on_progress: Optional[Callable[[str, int], None]] = None,
                 on_finished: Optional[Callable[[bool, str], None]] = None):
        self.config = config
        self.on_log = on_log or (lambda msg: logger.info(msg))
        self.on_progress = on_progress or (lambda msg, count: None)
        self.on_finished = on_finished or (lambda success, msg: None)

        self.base_url = 'https://api.zsxq.com/v2/groups/{}/topics'.format(config.group)
        self.headers = {
            'cookie': config.cookies,
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
        }

        self._stop_event = threading.Event()
        self._topic_count = 0
        self._image_count = 0
        self._file_count = 0

        # 任务队列
        self.topic_q = queue.Queue()
        self.image_q = queue.Queue()
        self.file_q = queue.Queue()

    def log(self, msg):
        self.on_log(msg)

    def stop(self):
        """请求停止爬取"""
        self._stop_event.set()
        self.log('正在停止爬取...')

    @property
    def is_stopped(self):
        return self._stop_event.is_set()

    # ---- 工具方法 ----

    @staticmethod
    def ensure_dir(path):
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    @staticmethod
    def sanitize_filename(text):
        text = re.sub(r'[\\/:*?"<>|\n\r]', '_', text)
        return text[:80].strip()

    def extract_text(self, topic):
        if topic['type'] == 'talk' and 'talk' in topic:
            return topic['talk'].get('text', '')
        elif topic['type'] == 'q&a' and 'question' in topic:
            return topic['question'].get('text', '')
        return ''

    # ---- Markdown 转换 ----

    def topic_to_markdown(self, topic):
        lines = []
        topic_id = topic['topic_id']
        topic_type = topic['type']
        create_time = topic.get('create_time', 'unknown')

        owner = topic.get('talk', topic.get('question', {})).get('owner', {})
        author = owner.get('name', '未知')
        lines.append('## {}-{}-{}'.format(create_time, author, topic_type))
        lines.append('')

        if topic_type == 'talk' and 'talk' in topic:
            talk = topic['talk']
            text = talk.get('text', '')
            if text:
                lines.append('')
                text = text.replace('#', '-')
                lines.append(text)
                lines.append('')

            if 'images' in talk:
                lines.append('### 图片')
                lines.append('')
                for img in talk['images']:
                    image_id = img['image_id']
                    img_type = img.get('type', 'jpg')
                    lines.append('![image](../images/{}/large.{})'.format(image_id, img_type))
                    lines.append('')

            if 'files' in talk:
                lines.append('### 文件')
                lines.append('')
                for f in talk['files']:
                    file_id = f['file_id']
                    name = f.get('name', 'unknown')
                    lines.append('- [{}](../files/{}/{})'.format(name, file_id, name))
                lines.append('')

        elif topic_type == 'q&a':
            if 'question' in topic:
                question = topic['question']
                text = question.get('text', '')
                q_owner = question.get('owner', {})
                q_author = q_owner.get('name', '未知')
                if text:
                    lines.append('### 提问（{}）'.format(q_author))
                    lines.append('')
                    lines.append(text)
                    lines.append('')

                if 'images' in question:
                    lines.append('#### 提问图片')
                    lines.append('')
                    for img in question['images']:
                        image_id = img['image_id']
                        img_type = img.get('type', 'jpg')
                        lines.append('![image](../images/{}/large.{})'.format(image_id, img_type))
                        lines.append('')

                if 'files' in question:
                    lines.append('#### 提问文件')
                    lines.append('')
                    for f in question['files']:
                        file_id = f['file_id']
                        name = f.get('name', 'unknown')
                        lines.append('- [{}](../files/{}/{})'.format(name, file_id, name))
                    lines.append('')

            if 'answer' in topic:
                answer = topic['answer']
                text = answer.get('text', '')
                a_owner = answer.get('owner', {})
                a_author = a_owner.get('name', '未知')
                if text:
                    lines.append('### 回答（{}）'.format(a_author))
                    lines.append('')
                    lines.append(text)
                    lines.append('')

                if 'images' in answer:
                    lines.append('#### 回答图片')
                    lines.append('')
                    for img in answer['images']:
                        image_id = img['image_id']
                        img_type = img.get('type', 'jpg')
                        lines.append('![image](../images/{}/large.{})'.format(image_id, img_type))
                        lines.append('')

                if 'files' in answer:
                    lines.append('#### 回答文件')
                    lines.append('')
                    for f in answer['files']:
                        file_id = f['file_id']
                        name = f.get('name', 'unknown')
                        lines.append('- [{}](../files/{}/{})'.format(name, file_id, name))
                    lines.append('')

        return '\n'.join(lines)

    def save_topic_as_markdown(self, topic):
        create_time = topic.get('create_time', 'unknown')
        if len(create_time) >= 7:
            year_month = create_time[:7]
        else:
            year_month = 'unknown'

        filename = '{}.md'.format(year_month)
        topics_dir = os.path.join(self.config.output_dir, 'topics')
        self.ensure_dir(topics_dir)

        filepath = os.path.join(topics_dir, filename)
        md_content = self.topic_to_markdown(topic)

        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(md_content)
            f.write('\n---\n\n')

        self.log('已保存 topic 到: {}'.format(filepath))

    # ---- 时间过滤 ----

    def is_in_time_range(self, create_time):
        if self.config.start_time and create_time < self.config.start_time:
            return 'before'
        if self.config.end_time and create_time > self.config.end_time:
            return 'after'
        return 'in'

    # ---- API 请求 ----

    def fetch_topics(self, end_time=None):
        if self.is_stopped:
            return 'done'

        params = {
            'scope': 'all',
            'count': '30',
        }
        if end_time is not None:
            params['end_time'] = end_time

        r = requests.get(self.base_url, headers=self.headers, params=params, allow_redirects=False)
        self.log('请求: {}'.format(r.url))

        d = r.json()
        if not d['succeeded']:
            self.log('获取 topics 失败: {}'.format(d))
            time.sleep(15)
            if not self.is_stopped:
                self.topic_q.put(end_time)
            return

        if len(d['resp_data']['topics']) == 0:
            self.log('所有 topics 已获取完毕！')
            return 'done'

        reached_before_start = False
        filtered_topics = []
        for topic in d['resp_data']['topics']:
            if self.is_stopped:
                return 'done'
            create_time = topic.get('create_time', '')
            status = self.is_in_time_range(create_time)
            if status == 'before':
                reached_before_start = True
                self.log('Topic {} 创建时间 {} 早于起始时间，停止翻页'.format(
                    topic['topic_id'], create_time))
                break
            elif status == 'after':
                continue
            else:
                filtered_topics.append(topic)

        if filtered_topics:
            try:
                for topic in filtered_topics:
                    self.save_topic_as_markdown(topic)
                    self._topic_count += 1
                    self.on_progress('topics', self._topic_count)
                self.log('本页 {} 条 topics 已保存'.format(len(filtered_topics)))
            except Exception as e:
                self.log('保存 Markdown 出错: {}'.format(e))

            for topic in filtered_topics:
                if self.is_stopped:
                    return 'done'
                if topic['type'] == 'talk':
                    if 'talk' in topic:
                        if self.config.enable_images:
                            self._get_images(topic['talk'])
                        if self.config.enable_files:
                            self._get_files(topic['talk'])
                elif topic['type'] == 'q&a':
                    if 'question' in topic:
                        if self.config.enable_images:
                            self._get_images(topic['question'])
                        if self.config.enable_files:
                            self._get_files(topic['question'])
                    if 'answer' in topic:
                        if self.config.enable_images:
                            self._get_images(topic['answer'])
                        if self.config.enable_files:
                            self._get_files(topic['answer'])

        if reached_before_start:
            self.log('已到达起始时间边界，停止爬取')
            return

        end_time = d['resp_data']['topics'][-1]['create_time']
        tmp = str(int(end_time[20:23]) - 1)
        while len(tmp) < 3:
            tmp = '0' + tmp
        end_time = end_time.replace('.' + end_time[20:23] + '+', '.' + tmp + '+')
        self.topic_q.put(end_time)

    def _get_images(self, talk):
        if 'images' in talk:
            for img in talk['images']:
                self.image_q.put(img)

    def _get_files(self, talk):
        if 'files' in talk:
            for file in talk['files']:
                self.file_q.put(file)

    def fetch_images(self, img_info):
        def download(url, image_id, type_, subfix):
            target_dir = os.path.join(self.config.output_dir, 'images', str(image_id), '{}.{}'.format(type_, subfix))
            if not os.path.exists(os.path.dirname(target_dir)):
                try:
                    os.makedirs(os.path.dirname(target_dir))
                except Exception as e:
                    self.log('创建图片目录出错: {}'.format(e))

            with open(target_dir, "wb+") as file:
                response = requests.get(url, headers=self.headers)
                file.write(response.content)
            self.log('图片已保存: {}'.format(target_dir))

        # if 'thumbnail' in img_info:
        #     download(img_info['thumbnail']['url'], img_info['image_id'], 'thumbnail', img_info['type'])
        # if 'large' in img_info:
        #     download(img_info['large']['url'], img_info['image_id'], 'large', img_info['type'])
        if 'original' in img_info:
            download(img_info['original']['url'], img_info['image_id'], 'original', img_info['type'])

        self._image_count += 1
        self.on_progress('images', self._image_count)
        self.log('剩余图片: {}'.format(self.image_q.qsize()))

    def fetch_files(self, file_info):
        def download(url, filename):
            if not os.path.exists(os.path.dirname(filename)):
                try:
                    os.makedirs(os.path.dirname(filename))
                except Exception as e:
                    self.log('创建文件目录出错: {}'.format(e))

            with open(filename, "wb+") as file:
                response = requests.get(url, headers=self.headers)
                file.write(response.content)
            self.log('文件已保存: {}'.format(filename))

        url = 'https://api.zsxq.com/v2/files/{}/download_url'.format(file_info['file_id'])
        r = requests.get(url, headers=self.headers)
        d = r.json()
        if not d['succeeded']:
            self.log('获取文件下载链接失败: {}'.format(d))
            return

        download(d['resp_data']['download_url'],
                 os.path.join(self.config.output_dir, 'files', str(file_info['file_id']), file_info['name']))

        self._file_count += 1
        self.on_progress('files', self._file_count)

    # ---- 线程方法 ----

    def _topics_thread(self):
        while not self.is_stopped:
            try:
                job = self.topic_q.get(timeout=1)
            except queue.Empty:
                continue
            result = self.fetch_topics(job)
            self.topic_q.task_done()
            if result == 'done':
                break

    def _images_thread(self):
        while not self.is_stopped:
            try:
                job = self.image_q.get(timeout=1)
            except queue.Empty:
                continue
            self.fetch_images(job)
            self.image_q.task_done()

    def _files_thread(self):
        while not self.is_stopped:
            try:
                job = self.file_q.get(timeout=1)
            except queue.Empty:
                continue
            self.fetch_files(job)
            self.file_q.task_done()

    # ---- 主入口 ----

    def run(self):
        """在当前线程/新线程中运行爬取任务"""
        try:
            self.ensure_dir(self.config.output_dir)
            self.log('输出目录: {}'.format(os.path.abspath(self.config.output_dir)))

            # 开启线程
            threads = []

            t = threading.Thread(target=self._topics_thread, daemon=True)
            t.start()
            threads.append(t)

            if self.config.enable_images:
                for _ in range(2):
                    t = threading.Thread(target=self._images_thread, daemon=True)
                    t.start()
                    threads.append(t)

            if self.config.enable_files:
                t = threading.Thread(target=self._files_thread, daemon=True)
                t.start()
                threads.append(t)

            # 设置初始 end_time
            initial_end_time = None
            if self.config.end_time:
                initial_end_time = self.config.end_time.replace('.000+', '.001+')
                self.log('使用结束时间作为 API 初始参数: {}'.format(initial_end_time))

            self.topic_q.put(initial_end_time)

            # 等待完成
            self.topic_q.join()
            if self.config.enable_images:
                self.image_q.join()
            if self.config.enable_files:
                self.file_q.join()

            if self.is_stopped:
                self.log('爬取已被用户停止')
                self.on_finished(False, '已停止')
            else:
                self.log('所有任务已完成！共爬取 {} 条 topics'.format(self._topic_count))
                self.on_finished(True, '完成！共爬取 {} 条 topics, {} 张图片, {} 个文件'.format(
                    self._topic_count, self._image_count, self._file_count))

        except Exception as e:
            self.log('爬取出错: {}'.format(e))
            self.on_finished(False, str(e))


def parse_time_arg(time_str):
    """将用户输入的时间字符串转换为 API 可用的 ISO 格式"""
    if not time_str:
        return ''
    time_str = time_str.strip()
    if len(time_str) == 10:  # YYYY-MM-DD
        datetime.strptime(time_str, '%Y-%m-%d')
        return '{}T00:00:00.000+0800'.format(time_str)
    elif len(time_str) == 19:  # YYYY-MM-DDTHH:MM:SS
        datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S')
        return '{}.000+0800'.format(time_str)
    else:
        raise ValueError('不支持的时间格式: {}'.format(time_str))
