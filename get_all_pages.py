import requests
from bs4 import BeautifulSoup
import json
import time
import random

def get_total_pages(publisher_id):
    url = f"https://book.douban.com/press/{publisher_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # 用户提供的豆瓣登录cookie（使用三引号避免转义问题）
    cookie_str = '''__utma=30149280.893249238.1756990454.1765793581.1765795957.81; __utmb=30149280.24.10.1765795957; __utmv=30149280.24084; __utmz=30149280.1765795957.81.18.utmcsr=moun47.github.io|utmccn=(referral)|utmcmd=referral|utmcct=/; push_doumail_num=0; push_noty_num=0; _pk_ses.100001.8cb4=1; __utmt_douban=1; __utmt=1; _pk_ref.100001.8cb4=%5B%22%22%2C%22%22%2C1765797349%2C%22https%3A%2F%2Fbook.douban.com%2Fpress%2F2387%2F%3Fpage%3D1%22%5D; _vwo_uuid_v2=DB786575BE4351C72BF0DE3BC7EC73EC8|4cd6ec0bfb9ae791d8f251a88b98bf69; ap_v=0,6.0; ct=y; ck=iysI; frodotk_db="10b6ac81b3f12f23322405851bd38d69"; dbcl2="240847482:tGuhkukKU3Q"; __utmc=30149280; viewed="37286500_36560856"; __yadk_uid=iF2sEv0dkeAvcwgTDpEsCODy7avLeqOs; _pk_id.100001.8cb4=65fe489e05b96a5a.1756990454.; bid=Ls3xl37lqe8; ll="108304"'''
    # 将cookie字符串转换为字典
    cookies = {}
    for cookie in cookie_str.split(';'):
        if cookie.strip():
            key, value = cookie.strip().split('=', 1)
            cookies[key] = value
    
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=10)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 找到分页器
        paginator = soup.find('div', class_='paginator')
        if not paginator:
            return 1
        
        # 找到所有页码链接
        page_links = paginator.find_all('a')
        if not page_links:
            return 1
        
        # 提取所有页码数字
        page_numbers = []
        for link in page_links:
            try:
                page_num = int(link.text.strip())
                page_numbers.append(page_num)
            except ValueError:
                continue
        
        if page_numbers:
            return max(page_numbers)
        else:
            return 1
    except Exception as e:
        print(f"获取出版社 {publisher_id} 页数时出错: {e}")
        return 1

def main():
    # 读取出版社链接
    with open('publishers.txt', 'r', encoding='utf-8') as f:
        links = [line.strip() for line in f if line.strip()]
    
    publishers = {}
    
    for link in links:
        # 提取出版社ID
        publisher_id = link.split('/')[-2]
        print(f"正在获取出版社 {publisher_id} 的页数...")
        total_pages = get_total_pages(publisher_id)
        publishers[publisher_id] = {
            "url": link,
            "total_pages": total_pages
        }
        # 避免请求过于频繁，使用随机2-5秒延时
        delay = random.uniform(2, 5)
        print(f"等待 {delay:.2f} 秒...")
        time.sleep(delay)
    
    # 保存结果到JSON文件
    with open('publishers_with_pages.json', 'w', encoding='utf-8') as f:
        json.dump(publishers, f, ensure_ascii=False, indent=2)
    
    print(f"已完成所有出版社页数获取，共 {len(publishers)} 家出版社")
    print("结果已保存到 publishers_with_pages.json 文件")

if __name__ == "__main__":
    main()