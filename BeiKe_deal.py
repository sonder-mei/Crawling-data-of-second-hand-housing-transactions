import requests
import time
import random
import pandas as pd
from bs4 import BeautifulSoup
import math
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

def init_session(config):
    """初始化会话对象"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'https://{config["city"]}.ke.com/chengjiao/',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br'
    })
    session.cookies.update(config["cookies"])
    session.config = config
    return session

def get_params(session):
    """生成动态请求参数"""
    return {
        '_t': str(int(time.time() * 1000)),
        'srcid': session.config['srcid']
    }

def fetch_list_page(session, page_url, region):
    """抓取列表页数据"""
    try:
        time.sleep(random.uniform(0.5, 1.0))  # 增加延迟防止被封
        response = session.get(page_url, params=get_params(session), timeout=10)
        response.encoding = 'utf-8'  # 显式设置编码
        response.raise_for_status()
        return parse_list_page(response.text, region)
    except Exception as e:
        print(f"列表页请求失败: {str(e)}")
        return []

def parse_list_page(html, region):
    """解析列表页信息"""
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.select('ul.listContent li')
    
    results = []
    for item in items:
        try:
            # 提取基本信息
            title = item.select_one('.title a')
            total_price = item.select_one('.totalPrice .number')
            unit_price = item.select_one('.unitPrice .number')
            house_info = item.select_one('.houseInfo')
            position_info = item.select_one('.positionInfo')
            deal_date = item.select_one('.dealDate')
            
            # 处理挂牌价和成交周期
            deal_cycle_info = item.select_one('.dealCycleeInfo')
            listing_price = '暂无数据'
            deal_cycle = '暂无数据'
            if deal_cycle_info:
                spans = deal_cycle_info.select('span')
                for span in spans:
                    if '挂牌' in span.text:
                        listing_price = span.text.strip()
                    elif '成交周期' in span.text:
                        deal_cycle = span.text.strip()
            
            info = {
                '区域': region,
                '房源标题': title.text.strip() if title else '暂无数据',
                '成交日期': deal_date.text.strip() if deal_date else '未知',
                '总价(万)': total_price.text if total_price else '暂无数据',
                '单价(元/平)': unit_price.text if unit_price else '暂无数据',
                '房屋信息': house_info.text.strip() if house_info else '暂无信息',
                '楼层信息': position_info.text.strip() if position_info else '暂无信息',
                '挂牌价': listing_price,
                '成交周期': deal_cycle,
                '详情页链接': item.select_one('a.img[href]')['href'] if item.select_one('a.img[href]') else '无链接'
            }
            results.append(info)
        except Exception as e:
            print(f"解析异常: {str(e)}")
    return results

def crawl_region(session, region):
    """爬取单个区域的完整数据"""
    config = session.config
    all_data = []
    config["region"] = region  # 更新当前区域
    
    try:
        # 获取总页数 - 直接从页面元素获取
        base_url = f"https://{config['city']}.ke.com/chengjiao/{region}/"
        response = session.get(base_url, params=get_params(session))
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找分页元素 - 根据你提供的HTML结构调整选择器
        page_data = soup.select_one('div[comp-module="page"]')
        if page_data and page_data.has_attr('page-data'):
            # 从page-data属性中获取总页数
            page_info = json.loads(page_data['page-data'])
            total_pages = page_info.get('totalPage', 1)
            current_page = page_info.get('curPage', 1)
            print(f"\n区域 {region} 共有 {total_pages} 页数据 (当前第 {current_page} 页)\n")
        else:
            # 备用方案：检查是否有房源数据
            items = soup.select('ul.listContent li')
            if items:
                print(f"区域 {region} 只有1页数据")
                total_pages = 1
            else:
                print(f"区域 {region} 没有找到房源数据")
                return []
    except json.JSONDecodeError:
        print(f"区域 {region} 分页数据解析失败，尝试备用方案")
        total_pages = 1
    except Exception as e:
        print(f"区域 {region} 获取页数失败: {str(e)}")
        total_pages = 1  # 如果获取页数失败，至少爬取第一页

    for page in range(1, total_pages + 1):
        page_url = f"https://{config['city']}.ke.com/chengjiao/{region}/pg{page}"
        
        for retry in range(3):  # 增加重试次数
            try:
                print(f"正在爬取区域 {region} 第 {page}/{total_pages} 页: {page_url}")
                list_data = fetch_list_page(session, page_url, region)
                if list_data:
                    all_data.extend(list_data)
                    print(f"区域 {region} 第 {page} 页完成，获取 {len(list_data)} 条数据，累计 {len(all_data)} 条")
                else:
                    print(f"区域 {region} 第 {page} 页无数据")
                break
            except Exception as e:
                print(f"区域 {region} 第 {retry+1} 次重试失败: {str(e)}")
                if retry == 2:
                    print(f"区域 {region} 第 {page} 页爬取失败，跳过")
                time.sleep(random.uniform(1, 3))  # 失败后增加等待时间
        
        time.sleep(random.uniform(1, 2))  # 增加页面间的延迟
    
    return all_data

def crawl_multiple_regions(config, regions, max_workers=3):
    """并发爬取多个区域"""
    session = init_session(config)
    all_data = []
    
    # 使用线程池并发爬取
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(crawl_region, session, region): region for region in regions}
        
        for future in as_completed(futures):
            region = futures[future]
            try:
                region_data = future.result()
                all_data.extend(region_data)
                print(f"区域 {region} 爬取完成，共 {len(region_data)} 条数据")
            except Exception as e:
                print(f"区域 {region} 爬取过程中出现错误: {str(e)}")
    
    return all_data

if __name__ == "__main__":
    # ================== 用户配置区域 ==================
    CONFIG = {
        "city": "sx",       # 目标城市拼音
        "cookies": {
            'lianjia_uuid': 'a9ba1fe8-770c-433e-a306-e8c30fbdab07',
            'lianjia_token': '2.00101efd5470ebd13a01b3d465afde00e5',
            'security_ticket': 'mrYyisn39oNOhtva8rHZtgjAmzD2t0jZa2iooYSnTZcp/GG7AdZJ/eidum6paOOw94UQLs3NjheXFWXyPMm7MhsKM+Exfrr9634s8A/RPBNWksBSAptLvY3jVLEbCj1SM8WvBM5ATgITRPRfD+1BkTpU27lrBDDZ/22CmOXcX8Q='
        },
        "srcid": 'eyJ0Ijoie1wiZGF0YVwiOlwiYWM3ZDhiNzA4ZGZjZjBlMzM1YzFhOWJmMmZiMDFlZGI5NGNkMGM4Yzg1NDIwZjg2OWQzMjA4NzBlODhhNmJiNjJmMDBmNTY4YTYyMDQzMDI5YjEyNjM5YzE2N2E4OTEyMDliMWZjZTgwYWYxYmZhOTMxMzU0MzQ4NWY1NDE1ODRkMDdiOWU2ZDYxZjdhMDgyZWY2ZmQ2YzgyN2UzMjIzNGJmNjZjYTAxZjQ2M2EzNzg0N2Q0MTgwY2Q2YzlkMTQ0MzUyNzdhYTliYmJjNWViMTJiOGE2MWJhNjZlZGVmMzY2OWVkMjUyNTVjMjU3OWQ3YzBjMjdlMjU0NzNiYmM2ZGQzMjEzMjA0ODJmNTdjNGYzNDc0MDBlODY5ZDRhMzA4MTFkN2NmN2Y3NWM3Y2RkZTI0YWJjMGM1NjRhY2Y2NmRcIixcImtleV9pZFwiOlwiMVwiLFwic2lnblwiOlwiZDlmMGFmMTJcIn0iLCJyIjoiaHR0cHM6Ly9zeC5rZS5jb20vY2hlbmdqaWFvLyIsIm9zIjoid2ViIiwidiI6IjAuMSJ9'
    }
    
    # 要爬取的区域列表
    REGIONS = [ 
        "shangyuqu/lc1",
        "shangyuqu/lc2",
        "shangyuqu/lc3",
        "shengzhoushi",
        "xinchangxian",
        "keqiaoqu/lc1",
        "keqiaoqu/lc2",
        "keqiaoqu/lc3",
        "zhujishi",
        "yuechengqu/lc1",
        "yuechengqu/lc2",
        "yuechengqu/lc3"
    ]
    
    # 输出的excel路径
    output_name = f'{CONFIG["city"]}_multiple_regions_transaction_data.xlsx'
    # ================================================

    # 执行爬取
    start_time = time.time()
    print(f"开始爬取 {CONFIG['city']} 的 {len(REGIONS)} 个区域数据...")
    final_data = crawl_multiple_regions(CONFIG, REGIONS)
    
    # 保存结果
    if final_data:
        df = pd.DataFrame(final_data)
        # 确保列顺序
        columns_order = [
            '区域', '房源标题', '成交日期', '总价(万)', '单价(元/平)', '房屋信息',
            '楼层信息', '挂牌价', '成交周期', '详情页链接'
        ]
        df = df[columns_order]
        
        try:
            # 使用openpyxl引擎，更好地支持中文
            df.to_excel(output_name, index=False, engine='openpyxl')
            print(f"\n数据已成功保存至: {output_name}")
            print(f"总计 {len(df)} 条数据，耗时 {(time.time()-start_time)/60:.1f} 分钟")
        except Exception as e:
            print(f"保存文件时出错: {str(e)}")
            # 尝试保存为CSV格式
            csv_name = output_name.replace('.xlsx', '.csv')
            df.to_csv(csv_name, index=False, encoding='utf_8_sig')
            print(f"已改为保存为CSV格式: {csv_name}")
    else:
        print("没有获取到任何数据")
