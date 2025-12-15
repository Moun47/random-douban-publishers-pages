import requests
from bs4 import BeautifulSoup
import json
import time

def get_total_pages(publisher_id):
    url = f"https://book.douban.com/press/{publisher_id}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
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
        # 避免请求过于频繁
        time.sleep(0.5)
    
    # 保存结果到JSON文件
    with open('publishers_with_pages.json', 'w', encoding='utf-8') as f:
        json.dump(publishers, f, ensure_ascii=False, indent=2)
    
    print(f"已完成所有出版社页数获取，共 {len(publishers)} 家出版社")
    print("结果已保存到 publishers_with_pages.json 文件")

if __name__ == "__main__":
    main()