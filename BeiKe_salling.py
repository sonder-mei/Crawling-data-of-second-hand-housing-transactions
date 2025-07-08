import requests
import time
import random
import pandas as pd
from bs4 import BeautifulSoup
import json
import urllib.parse

def init_session(config):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br'
    })
    session.cookies.update(config["cookies"])
    session.config = config
    return session

def get_params(session):
    return {
        '_t': str(int(time.time() * 1000)),
        'srcid': session.config['srcid']
    }

def fetch_list_page(session, page_url):
    try:
        time.sleep(random.uniform(1.0, 2.0))  # 增加延迟防止被封
        response = session.get(page_url, params=get_params(session), timeout=10)
        response.encoding = 'utf-8'  # 显式设置编码
        response.raise_for_status()
        return parse_list_page(response.text)
    except Exception as e:
        print(f"列表页请求失败: {str(e)}")
        return []

def parse_list_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.select('ul.sellListContent li.clear')
    
    results = []
    for item in items:
        try:
            title = item.select_one('.title a')
            total_price = item.select_one('.totalPrice span')
            unit_price = item.select_one('.unitPrice span')
            position_info = item.select_one('.positionInfo a')
            house_info = item.select_one('.houseInfo')
            follow_info = item.select_one('.followInfo')
            tags = [tag.text for tag in item.select('.tag span')]
            community = item.select_one('.positionInfo a')
            
            info = {
                '房源标题': title.text.strip() if title else '暂无数据',
                '总价(万)': total_price.text.strip() if total_price else '暂无数据',
                '单价(元/平)': unit_price.text.strip() if unit_price else '暂无数据',
                '小区名称': community.text.strip() if community else '暂无数据',
                '房屋信息': house_info.text.strip().replace('\n', '').replace(' ', '') if house_info else '暂无信息',
                '楼层信息': position_info.text.strip() if position_info else '暂无信息',
                '关注人数': follow_info.text.strip().split('人')[0] if follow_info else '0',
                '房源标签': '|'.join(tags) if tags else '无标签',
                '发布时间': follow_info.text.strip().split('人')[1] if follow_info else '0',
                '详情页链接': item.select_one('a.img[href]')['href'] if item.select_one('a.img[href]') else '无链接',
                'VR看房': '有' if item.select_one('.vr_logo') else '无',
                '必看好房': '是' if item.select_one('.goodhouse_tag') else '否'
            }
            results.append(info)
        except Exception as e:
            print(f"解析异常: {str(e)}")
    return results

def extract_release_time(text):
    if '发布' in text:
        return text.split('发布')[-1].strip()
    return '未知'

def get_total_pages(session, base_url):
    try:
        response = session.get(base_url, params=get_params(session))
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        page_box = soup.select_one('div[comp-module="page"]')
        if page_box and 'page-data' in page_box.attrs:
            page_data = json.loads(page_box['page-data'])
            total_pages = page_data.get('totalPage', 1)
            print(f"从分页元素获取到总页数: {total_pages}")
            return total_pages
        
        print("无法从分页元素获取总页数，将尝试爬取第一页")
        return 1
    except Exception as e:
        print(f"获取总页数失败: {str(e)}")
        return 1

def crawl_full_data(session):
    config = session.config
    all_data = []
    
    try:
        encoded_region = urllib.parse.quote(config['region'])
        base_url = f"https://{config['city']}.ke.com/ershoufang/{encoded_region}/"
        total_pages = get_total_pages(session, base_url)
        
        print(f"\n需要爬取 {total_pages} 页数据\n")
    except Exception as e:
        print(f"初始化失败: {str(e)}")
        total_pages = 1 

    for page in range(1, total_pages + 1):
        encoded_region = urllib.parse.quote(config['region'])
        page_url = f"https://{config['city']}.ke.com/ershoufang/{encoded_region}/pg{page}"
        
        for retry in range(3):  
            try:
                print(f"正在爬取第 {page} 页: {page_url}")
                list_data = fetch_list_page(session, page_url)
                if list_data:
                    all_data.extend(list_data)
                    print(f"第 {page} 页完成，获取 {len(list_data)} 条数据，累计 {len(all_data)} 条")
                else:
                    print(f"第 {page} 页无数据")
                break
            except Exception as e:
                print(f"第 {retry+1} 次重试失败: {str(e)}")
                if retry == 2:
                    print(f"第 {page} 页爬取失败，跳过")
                time.sleep(random.uniform(2, 4)) 
        
        time.sleep(random.uniform(2, 3)) 
    
    return all_data

if __name__ == "__main__":
    CONFIG = {
        "city": "jiangmen",      
        "region": "rs碧桂园翡翠湾",
        "cookies": {
            'lianjia_uuid': 'a9ba1fe8-770c-433e-a306-e8c30fbdab07',
            'lianjia_token': '2.00141b520674ee7e6805b67b372b1d4ba7',
            'security_ticket': 'Z3OxH6hrT4x8NNhTWOYnYxGF5kc4+D7zgvwkaXSR1cnv6yeBvZHLTKwdrp+M7WBAZ0yvDc7SEqcu2JZpanggThsJz079kJqEpTNpnIVMc9gJKrA23QWBhkn/9j67D6NPhlf6I+6g/W2eZmIbgpD3Rib9tLUpjEX9aFTVQIt3sRM='
        },
        "srcid": 'eyJ0Ijoie1wiZGF0YVwiOlwiYWM3ZDhiNzA4ZGZjZjBlMzM1YzFhOWJmMmZiMDFlZGI5NGNkMGM4Yzg1NDIwZjg2OWQzMjA4NzBlODhhNmJiNmNmODIwYjIyMzNjYTQ0NThhYWIzY2Y1ZGZhZTk4ZTU1YzBhOWYwYzA4M2NiZjUxZWFhNDhhMzk0NDY4M2IzZTBkMGZhMmE2NGQyYTA1YzQ3OTY3ZDM5YzM0ODUzYzRjMmQ2NGNhNDEwZjA1NDYwYmM2YmEwYTVmYmQxNmEwMzE5NGRmZWQwYmQ2NjVjZGE3ZjE5OTk0NDhjNmI1ODkxOGIwZjIxNzQ3NjEyZjFhNTJhMzI0YThjYmE4ZGNkZTBhNGNkNDNkOTQwNzFkMGJjMGVlMDU3NzMwZDVmYjVhYjJjZTVhNTVlZmVhODVmM2NkNzI0NDI4ZTgwZGFhMzk3YmJcIixcImtleV9pZFwiOlwiMVwiLFwic2lnblwiOlwiZjVmMGM3YjRcIn0iLCJyIjoiaHR0cHM6Ly9zaC5rZS5jb20vY2hlbmdqaWFvL3JzJUU0JUI4JTg3JUU3JUE3JTkxJUU2JTk3JUE5JUU1JTlGJThFLyIsIm9zIjoid2ViIiwidiI6IjAuMSJ9'
    }
    
    output_name = f'{CONFIG["city"]}_{CONFIG["region"]}_onsale_data.xlsx'

    session = init_session(CONFIG)

    start_time = time.time()
    print("开始爬取在售房源数据...")
    final_data = crawl_full_data(session)
    
    if final_data:
        df = pd.DataFrame(final_data)
        columns_order = [
            '房源标题', '总价(万)', '单价(元/平)', '小区名称', '房屋信息',
            '楼层信息', '关注人数', '房源标签', '发布时间', 
            'VR看房', '必看好房', '详情页链接'
        ]
        df = df[columns_order]
        
        try:
            df.to_excel(output_name, index=False, engine='openpyxl')
            print(f"\n数据已成功保存至: {output_name}")
            print(f"总计 {len(df)} 条数据，耗时 {(time.time()-start_time)/60:.1f} 分钟")
        except Exception as e:
            print(f"保存文件时出错: {str(e)}")
            csv_name = output_name.replace('.xlsx', '.csv')
            df.to_csv(csv_name, index=False, encoding='utf_8_sig')
            print(f"已改为保存为CSV格式: {csv_name}")
    else:
        print("没有获取到任何数据")
