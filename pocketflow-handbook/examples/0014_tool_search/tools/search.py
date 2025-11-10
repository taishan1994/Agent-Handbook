import os

from typing import Dict, List, Optional

from .exa_search_main import (
    extract_relevant_info,
    extract_text_from_url,
    extract_snippet_with_context,
    exa_web_search
)
from tqdm import tqdm

class SearchTool:
    """Tool for performing web searches using SerpAPI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize search tool with API key
        
        Args:
            api_key (str, optional): SerpAPI key. Defaults to env var SERPAPI_API_KEY.
        """
        pass
            
    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Perform Google search via SerpAPI
        
        Args:
            query (str): Search query
            num_results (int, optional): Number of results to return. Defaults to 5.
            
        Returns:
            List[Dict]: Search results with title, snippet, and link
        """
        # Configure search parameters
        url = "https://api.exa.ai/search"
        search_results = exa_web_search(query, url)
        # print(response)
        # search_results = {'requestId': 'f3309744aa28eb86d4231d1af2303b18', 'resolvedSearchType': 'keyword', 'results': [{'id': 'https://topics.gmw.cn/node_68757.htm', 'title': '刘翔宣布正式退役 - 专题- 光明网', 'url': 'https://topics.gmw.cn/node_68757.htm', 'author': None}, {'id': 'https://zh.wikipedia.org/zh-hans/%E5%88%98%E7%BF%94', 'title': '刘翔- 维基百科，自由的百科全书', 'url': 'https://zh.wikipedia.org/zh-hans/%E5%88%98%E7%BF%94', 'author': None}, {'id': 'https://www.163.com/dy/article/FUOQGNBC05452FWC.html', 'title': '刘翔获得过多少世界冠军？别再相信36个冠军6个亚军3个季军了 - 网易', 'url': 'https://www.163.com/dy/article/FUOQGNBC05452FWC.html', 'publishedDate': '2020-12-26T12:00:00.000Z', 'author': None}, {'id': 'https://baike.baidu.com/item/%E5%88%98%E7%BF%94/5836', 'title': '刘翔_百度百科', 'url': 'https://baike.baidu.com/item/%E5%88%98%E7%BF%94/5836', 'author': None}, {'id': 'https://www.sohu.com/a/458095925_120086858', 'title': '原创刘翔一共获得多少个国际冠军？网传36冠不准确来看世界田联数据', 'url': 'https://www.sohu.com/a/458095925_120086858', 'publishedDate': '2021-03-30T12:00:00.000Z', 'author': None}, {'id': 'https://www.163.com/dy/article/E5BNM4QO05491YHB.html', 'title': '刘翔到底拿过多少次世界冠军？不要再被48次大赛36次冠军欺骗了|163', 'url': 'https://www.163.com/dy/article/E5BNM4QO05491YHB.html', 'publishedDate': '2019-01-12T12:00:00.000Z', 'author': None}, {'id': 'https://www.sohu.com/a/545897548_120541359', 'title': '40个世界冠军，刘翔生涯获得多少比赛奖金？上交部分或超1亿 - 搜狐', 'url': 'https://www.sohu.com/a/545897548_120541359', 'publishedDate': '2022-05-11T12:00:00.000Z', 'author': None}, {'id': 'http://web.chinamshare.com/hbwt_html/xwsg/xw/55524637.shtml', 'title': '【燕赵新作为致敬40年】刘翔：开挂的亚洲飞人', 'url': 'http://web.chinamshare.com/hbwt_html/xwsg/xw/55524637.shtml', 'publishedDate': '2018-12-10T12:00:00.000Z', 'author': None}, {'id': 'https://zhidao.baidu.com/question/493585922.html', 'title': '刘翔的了几次冠军 - 百度知道', 'url': 'https://zhidao.baidu.com/question/493585922.html', 'publishedDate': '2017-08-01T12:00:00.000Z', 'author': None}, {'id': 'https://blog.sina.com.cn/s/blog_4bdbe3e00102vmoz.html', 'title': '刘翔记忆: 48次大赛获得36个冠军 - 新浪网站导航', 'url': 'https://blog.sina.com.cn/s/blog_4bdbe3e00102vmoz.html', 'publishedDate': '2015-04-08T12:00:00.000Z', 'author': None}], 'effectiveFilters': {'includeDomains': [], 'excludeDomains': [], 'includeText': [], 'excludeText': [], 'urls': []}, 'costDollars': {'total': 0.005, 'search': {'neural': 0.005}}}
        extracted_info = extract_relevant_info(search_results)

        for info in tqdm(extracted_info, desc="Processing Snippets"):
            full_text = extract_text_from_url(info['url'], snippet=query)  # Get full webpage text
            if full_text and not full_text.startswith("Error"):
                success, context = extract_snippet_with_context(full_text, info['snippet'])
                if success:
                    info['context'] = context
                else:
                    info['context'] = f"Could not extract context. Returning first 8000 chars: {full_text[:8000]}"
            else:
                info['context'] = f"Failed to fetch full text: {full_text}"

        processed_results = []
        for result in extracted_info[:num_results]:
            processed_results.append({
                "title": result.get("title", ""),
                "snippet": result.get("context", ""),
                "link": result.get("url", "")
            })
            
        return processed_results
       
