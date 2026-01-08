import requests
from bs4 import BeautifulSoup
import time
import re
import random
import os
import json
import sys
from datetime import datetime
from urllib.parse import urljoin

class DoubanBookScraperV2:
    def __init__(self):
        self.publishers_file = 'publishers_with_pages.json'
        self.plan_file = 'scraping_plan.json'
        self.results_file = 'scraping_results.json'
        self.state_file = 'scraper_state_v2.json'
        self.error_count = 0
        self.max_consecutive_errors = 10
        self.retry_interval = 30 * 60  # 30分钟
        self.current_publisher_index = 0
        self.publishers = []
        self.scraping_plan = {}
        self.results = {}
        self.session = requests.Session()
        
        # 设置用户提供的cookie
        self.session.cookies.update({
            'll': '118254',
            'bid': '7P_pjD5fEhY',
            'push_noty_num': '0',
            'push_doumail_num': '0',
            'viewed': '37297650_37325332_37187825_37148078_26425371_24695638',
            'ct': 'y',
            'dbcl2': '240847482:Gawd5U2XvGY',
            'ck': 'fq8l',
            'frodotk_db': 'd5e244a53b2c2d1181a6cdefb1848733',
            'ap_v': '0,6.0'
        })
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Referer': 'https://book.douban.com/',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1'
        }
    
    def load_publishers(self):
        """加载出版社信息"""
        try:
            with open(self.publishers_file, 'r', encoding='utf-8') as f:
                self.publishers = json.load(f)
            print(f"成功加载 {len(self.publishers)} 家出版社信息")
            return True
        except Exception as e:
            print(f"加载出版社信息失败: {str(e)}")
            return False
    
    def create_scraping_plan(self):
        """创建爬取计划"""
        if os.path.exists(self.plan_file):
            print("爬取计划已存在，加载现有计划")
            with open(self.plan_file, 'r', encoding='utf-8') as f:
                self.scraping_plan = json.load(f)
            return
        
        print("创建爬取计划...")
        for press_id, info in self.publishers.items():
            total_pages = info['total_pages']
            # 计算前10%页数，向上取整
            plan_pages = max(1, int(total_pages * 0.1) + (1 if total_pages * 0.1 % 1 > 0 else 0))
            # 计算预计爬取的链接数量
            expected_links = plan_pages * 10
            
            self.scraping_plan[press_id] = {
                'url': info['url'],
                'total_pages': total_pages,
                'plan_pages': plan_pages,
                'expected_links': expected_links,
                'actual_pages': 0,
                'actual_links': 0
            }
        
        # 保存爬取计划
        with open(self.plan_file, 'w', encoding='utf-8') as f:
            json.dump(self.scraping_plan, f, ensure_ascii=False, indent=2)
        print(f"爬取计划已保存到 {self.plan_file}")
    
    def save_state(self):
        """保存当前爬取状态"""
        state = {
            'current_publisher_index': self.current_publisher_index,
            'publishers': self.publishers,
            'scraping_plan': self.scraping_plan,
            'results': self.results,
            'error_count': self.error_count,
            'timestamp': time.time()
        }
        
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        print(f"状态已保存到 {self.state_file}")
    
    def load_state(self):
        """加载上次爬取状态"""
        if not os.path.exists(self.state_file):
            print("未找到状态文件，将从头开始爬取")
            return False
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            self.current_publisher_index = state.get('current_publisher_index', 0)
            self.publishers = state.get('publishers', {})
            self.scraping_plan = state.get('scraping_plan', {})
            self.results = state.get('results', {})
            self.error_count = state.get('error_count', 0)
            
            timestamp = state.get('timestamp', 0)
            elapsed = time.time() - timestamp
            print(f"加载状态成功! 上次爬取于 {time.ctime(timestamp)} ({int(elapsed/3600)}小时{int((elapsed%3600)/60)}分钟前)")
            
            completed = len(self.results)
            total = len(self.publishers)
            print(f"已完成 {completed} 家出版社，还有 {total - completed} 家待爬取")
            
            return True
        except Exception as e:
            print(f"加载状态文件失败: {str(e)}")
            return False
    
    def check_internet_connection(self):
        """检查网络连接"""
        test_urls = [
            'https://www.baidu.com',
            'https://www.douban.com'
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return True
            except:
                continue
        
        return False
    
    def wait_for_reconnection(self):
        """等待网络重新连接"""
        print("\n网络连接中断，等待重新连接...")
        
        while True:
            try:
                if self.check_internet_connection():
                    print("网络已恢复，继续爬取...")
                    self.error_count = 0  # 重置错误计数
                    return True
                
                # 每5秒检查一次
                time.sleep(5)
                print(".", end="", flush=True)
                
            except KeyboardInterrupt:
                print("\n用户中断，保存状态并退出...")
                self.save_state()
                sys.exit(0)
    
    def wait_for_retry(self):
        """等待重试"""
        print(f"\n连续错误次数达到 {self.max_consecutive_errors} 次，将暂停30分钟后重试")
        self.save_state()
        
        retry_interval = 30 * 60  # 30分钟
        for i in range(retry_interval // 60):
            print(f"剩余 {retry_interval // 60 - i} 分钟重试...")
            time.sleep(60)
            
            # 检查网络连接
            if self.check_internet_connection():
                # 尝试访问豆瓣
                try:
                    response = self.session.get('https://book.douban.com', headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        print("豆瓣访问成功，继续爬取...")
                        self.error_count = 0
                        return True
                except:
                    continue
        
        print("30分钟后重试...")
        return self.check_internet_connection()
    
    def scrape_book_info(self, soup):
        """从页面提取图书信息"""
        books = []
        
        # 查找图书列表
        book_items = soup.select('li.subject-item')
        if not book_items:
            return books
        
        for item in book_items:
            # 提取图书链接
            link_elem = item.select_one('h2 a')
            if not link_elem:
                continue
            book_url = link_elem.get('href', '')
            book_id = re.search(r'/subject/(\d+)/', book_url)
            if not book_id:
                continue
            book_id = book_id.group(1)
            
            # 提取评分
            rating_elem = item.select_one('span.rating_nums')
            rating = rating_elem.text.strip() if rating_elem else '0.0'
            
            # 提取评价人数
            review_elem = item.select_one('span.pl')
            review_count = '0'
            if review_elem:
                review_match = re.search(r'(\d+)人评价', review_elem.text)
                if review_match:
                    review_count = review_match.group(1)
            
            books.append({
                'id': book_id,
                'url': book_url,
                'rating': rating,
                'review_count': review_count
            })
        
        return books
    
    def scrape_publisher(self, press_id, info):
        """爬取单个出版社"""
        plan = self.scraping_plan[press_id]
        url = plan['url']
        plan_pages = plan['plan_pages']
        expected_links = plan['expected_links']
        
        print(f"\n开始爬取出版社 {press_id}")
        print(f"- 出版社URL: {url}")
        print(f"- 总页数: {plan['total_pages']}")
        print(f"- 计划爬取页数: {plan_pages}")
        print(f"- 预计爬取链接数: {expected_links}")
        
        # 初始化当前出版社的结果
        if press_id not in self.results:
            self.results[press_id] = {
                'books': [],
                'plan_pages': plan_pages,
                'actual_pages': 0
            }
        
        books = self.results[press_id]['books']
        actual_pages = self.results[press_id]['actual_pages']
        
        # 开始爬取
        for page in range(actual_pages + 1, plan_pages + 1):
            page_url = url if page == 1 else f"{url}?page={page}"
            
            while True:
                try:
                    # 爬取前检查网络连接
                    if not self.check_internet_connection():
                        self.wait_for_reconnection()
                    
                    # 检查连续错误次数
                    if self.error_count >= self.max_consecutive_errors:
                        if not self.wait_for_retry():
                            continue
                    
                    print(f"\n[出版社 {press_id}] 正在爬取第 {page}/{plan_pages} 页")
                    print(f"- 当前进度: 已爬 {len(books)}/{expected_links} 个链接")
                    print(f"- 全局进度: 已完成 {len(self.results)}/{len(self.publishers)} 家出版社")
                    
                    # 随机延时1-2秒
                    delay = random.uniform(1, 2)
                    print(f"- 页面间延时 {delay:.2f} 秒")
                    time.sleep(delay)
                    
                    # 发送请求
                    response = self.session.get(page_url, headers=self.headers, timeout=15)
                    
                    if response.status_code != 200:
                        print(f"- 错误状态码: {response.status_code}")
                        self.error_count += 1
                        continue
                    
                    # 检查内容长度
                    if len(response.text) < 5000:
                        print(f"- 响应内容过短 ({len(response.text)} 字符)，可能被反爬")
                        self.error_count += 1
                        continue
                    
                    # 解析页面
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 提取图书信息
                    page_books = self.scrape_book_info(soup)
                    if not page_books:
                        print(f"- 第 {page} 页未找到图书信息")
                        self.error_count += 1
                        continue
                    
                    # 添加到结果
                    books.extend(page_books)
                    actual_pages = page
                    
                    # 更新进度
                    self.results[press_id]['books'] = books
                    self.results[press_id]['actual_pages'] = actual_pages
                    self.scraping_plan[press_id]['actual_pages'] = actual_pages
                    self.scraping_plan[press_id]['actual_links'] = len(books)
                    
                    print(f"- 成功爬取 {len(page_books)} 本图书，累计 {len(books)} 本")
                    self.error_count = 0  # 重置错误计数
                    
                    # 保存状态
                    self.save_state()
                    
                    # 跳出重试循环
                    break
                    
                except requests.exceptions.ConnectionError:
                    print(f"- 网络连接错误")
                    self.error_count += 1
                    self.wait_for_reconnection()
                    
                except requests.exceptions.Timeout:
                    print(f"- 请求超时")
                    self.error_count += 1
                    
                except Exception as e:
                    print(f"- 爬取错误: {str(e)}")
                    self.error_count += 1
        
        # 校验爬取结果
        print(f"\n[出版社 {press_id}] 爬取完成")
        print(f"- 计划爬取: {plan_pages} 页，{expected_links} 个链接")
        print(f"- 实际爬取: {actual_pages} 页，{len(books)} 个链接")
        
        # 更新爬取计划
        self.scraping_plan[press_id]['actual_pages'] = actual_pages
        self.scraping_plan[press_id]['actual_links'] = len(books)
        
        # 保存状态
        self.save_state()
        
        # 出版社间延时5-10秒
        delay = random.uniform(5, 10)
        print(f"\n出版社间延时 {delay:.2f} 秒")
        time.sleep(delay)
    
    def save_results(self):
        """保存最终结果"""
        # 保存爬取结果
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n爬取结果已保存到 {self.results_file}")
        
        # 保存更新后的爬取计划
        with open(self.plan_file, 'w', encoding='utf-8') as f:
            json.dump(self.scraping_plan, f, ensure_ascii=False, indent=2)
        print(f"爬取计划已更新并保存到 {self.plan_file}")
    
    def run(self):
        """运行爬虫"""
        print("=== 豆瓣出版社图书爬虫 ===")
        
        # 加载出版社信息
        if not self.load_publishers():
            return
        
        # 加载或创建爬取计划
        self.create_scraping_plan()
        
        # 加载状态
        self.load_state()
        
        # 开始爬取
        press_ids = list(self.publishers.keys())
        for i in range(self.current_publisher_index, len(press_ids)):
            self.current_publisher_index = i
            press_id = press_ids[i]
            
            # 检查是否已爬取完成
            if press_id in self.results and self.results[press_id]['actual_pages'] >= self.scraping_plan[press_id]['plan_pages']:
                print(f"\n出版社 {press_id} 已爬取完成，跳过")
                continue
            
            # 爬取出版社
            self.scrape_publisher(press_id, self.publishers[press_id])
        
        # 所有出版社爬取完成
        print(f"\n=== 爬取任务全部完成 ===")
        print(f"共爬取 {len(self.results)} 家出版社")
        
        # 保存最终结果
        self.save_results()

# 主程序
if __name__ == "__main__":
    try:
        scraper = DoubanBookScraperV2()
        scraper.run()
    except KeyboardInterrupt:
        print("\n用户中断，保存状态...")
        scraper.save_state()
        print("状态已保存，下次运行将从中断处继续")
    except Exception as e:
        print(f"\n程序运行出错: {str(e)}")
        print("尝试保存当前状态...")
        try:
            scraper.save_state()
            print("状态已保存，请检查错误后重新运行程序")
        except:
            print("状态保存失败")
    except:
        print("\n未知错误，程序退出")
        sys.exit(1)