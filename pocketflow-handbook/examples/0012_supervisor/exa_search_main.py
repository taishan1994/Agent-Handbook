import re
import string
import time

import jieba
import requests
import concurrent.futures

from io import BytesIO
from typing import Tuple, Optional
from requests.exceptions import Timeout
from bs4 import BeautifulSoup
from tqdm import tqdm
from concurrent.futures.thread import ThreadPoolExecutor

# ----------------------- Custom Headers -----------------------
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/58.0.3029.110 Safari/537.36',
    'Referer': 'https://www.google.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# Initialize session
session = requests.Session()
session.headers.update(headers)


def exa_web_search(query, url, timeout=10, num_result=5):
    payload = {
        "query": query,
        "useAutoprompt": False,
        "type": "auto",
        "numResults": num_result,
    }
    headers = {
        "x-api-key": "4fd7be1c-6248-4d1d-abf6-bdf9fc8168f9",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()  # Raise exception if the request failed
        search_results = response.json()
        return search_results
    except Timeout:
        print(f"Bing Web Search request timed out ({timeout} seconds) for query: {query}")
        return {}  # Or you can choose to raise an exception
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during Bing Web Search request: {e}")
        return {}


def extract_relevant_info(search_results):
    """
    Extract relevant information from Bing search results.

    Args:
        search_results (dict): JSON response from the Bing Web Search API.

    Returns:
        list: A list of dictionaries containing the extracted information.
    """
    useful_info = []

    if 'results' in search_results:
        search_results = search_results["results"]
        for id, result in enumerate(search_results):
            info = {
                'id': id + 1,  # Increment id for easier subsequent operations
                'title': result.get('title', ''),
                'url': result.get('url', ''),
                'date': result.get('publishedDate', '').split('T')[0],
                'snippet': result.get('snippet', ''),  # Remove HTML tags
                # Add context content to the information
                'context': ''  # Reserved field to be filled later
            }
            useful_info.append(info)

    return useful_info

def remove_punctuation(text: str) -> str:
    """Remove punctuation from the text."""
    return text.translate(str.maketrans("", "", string.punctuation))


def f1_score(true_set: set, pred_set: set) -> float:
    """Calculate the F1 score between two sets of words."""
    intersection = len(true_set.intersection(pred_set))
    if not intersection:
        return 0.0
    precision = intersection / float(len(pred_set))
    recall = intersection / float(len(true_set))
    return 2 * (precision * recall) / (precision + recall)


def extract_snippet_with_context(full_text: str, snippet: str, context_chars: int = 2500) -> Tuple[bool, str]:
    """
    Extract the sentence that best matches the snippet and its context from the full text.

    Args:
        full_text (str): The full text extracted from the webpage.
        snippet (str): The snippet to match.
        context_chars (int): Number of characters to include before and after the snippet.

    Returns:
        Tuple[bool, str]: The first element indicates whether extraction was successful, the second element is the extracted context.
    """
    try:
        full_text = full_text[:50000]

        snippet = snippet.lower()
        snippet = remove_punctuation(snippet)
        # snippet_words = set(snippet.split())
        snippet_words = set(jieba.lcut_for_search(snippet))

        best_sentence = None
        best_f1 = 0.2

        sentences = re.split(r'(?<=[。？！]) +', full_text)  # Split sentences using regex, supporting ., !, ? endings
        # sentences = sent_tokenize(full_text)  # Split sentences using nltk's sent_tokenize

        for sentence in sentences:
            key_sentence = sentence.lower()
            key_sentence = remove_punctuation(key_sentence)
            # sentence_words = set(key_sentence.split())
            sentence_words = set(jieba.lcut_for_search(key_sentence))
            f1 = f1_score(snippet_words, sentence_words)
            if f1 > best_f1:
                best_f1 = f1
                best_sentence = sentence

        if best_sentence:
            para_start = full_text.find(best_sentence)
            para_end = para_start + len(best_sentence)
            start_index = max(0, para_start - context_chars)
            end_index = min(len(full_text), para_end + context_chars)
            context = full_text[start_index:end_index]
            return True, context
        else:
            # If no matching sentence is found, return the first context_chars*2 characters of the full text
            return False, full_text[:context_chars * 2]
    except Exception as e:
        return False, f"Failed to extract snippet context due to {str(e)}"


def extract_text_from_url(url, snippet: Optional[str] = None):
    """
    Extract text from a URL. If a snippet is provided, extract the context related to it.

    Args:
        url (str): URL of a webpage or PDF.
        use_jina (bool): Whether to use Jina for extraction.
        snippet (Optional[str]): The snippet to search for.

    Returns:
        str: Extracted text or context.
    """
    try:
        response = session.get(url, timeout=20)  # Set timeout to 20 seconds
        response.raise_for_status()  # Raise HTTPError if the request failed
        # Determine the content type
        content_type = response.headers.get('Content-Type', '')
        # Try using lxml parser, fallback to html.parser if unavailable
        try:
            soup = BeautifulSoup(response.content, 'lxml')
        except Exception:
            print("lxml parser not found or failed, falling back to html.parser")
            soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)

        print(text)

        if snippet:
            success, context = extract_snippet_with_context(text, snippet)
            if success:
                return context
            else:
                return text
        else:
            # If no snippet is provided, return directly
            return text[:8000]
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}"
    except requests.exceptions.ConnectionError:
        return "Error: Connection error occurred"
    except requests.exceptions.Timeout:
        return "Error: Request timed out after 20 seconds"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def fetch_page_content(urls, max_workers=4, snippets: Optional[dict] = None):
    """
    Concurrently fetch content from multiple URLs.

    Args:
        urls (list): List of URLs to scrape.
        max_workers (int): Maximum number of concurrent threads.
        use_jina (bool): Whether to use Jina for extraction.
        snippets (Optional[dict]): A dictionary mapping URLs to their respective snippets.

    Returns:
        dict: A dictionary mapping URLs to the extracted content or context.
    """
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Use tqdm to display a progress bar
        futures = {
            executor.submit(extract_text_from_url, url, snippets.get(url) if snippets else None): url
            for url in urls
        }
        for future in tqdm(concurrent.futures.as_completed(futures), desc="Fetching URLs", total=len(urls)):
            url = futures[future]
            try:
                data = future.result()
                results[url] = data
            except Exception as exc:
                results[url] = f"Error fetching {url}: {exc}"
            time.sleep(0.2)  # Simple rate limiting
    return results

if __name__ == '__main__':
    url = "https://api.exa.ai/search"
    query = "刘翔获得了多少次冠军"
    response = exa_web_search(query, url)
    print(type(response))
    # search_results = {'requestId': 'f3309744aa28eb86d4231d1af2303b18', 'resolvedSearchType': 'keyword', 'results': [{'id': 'https://topics.gmw.cn/node_68757.htm', 'title': '刘翔宣布正式退役 - 专题- 光明网', 'url': 'https://topics.gmw.cn/node_68757.htm', 'author': None}, {'id': 'https://zh.wikipedia.org/zh-hans/%E5%88%98%E7%BF%94', 'title': '刘翔- 维基百科，自由的百科全书', 'url': 'https://zh.wikipedia.org/zh-hans/%E5%88%98%E7%BF%94', 'author': None}, {'id': 'https://www.163.com/dy/article/FUOQGNBC05452FWC.html', 'title': '刘翔获得过多少世界冠军？别再相信36个冠军6个亚军3个季军了 - 网易', 'url': 'https://www.163.com/dy/article/FUOQGNBC05452FWC.html', 'publishedDate': '2020-12-26T12:00:00.000Z', 'author': None}, {'id': 'https://baike.baidu.com/item/%E5%88%98%E7%BF%94/5836', 'title': '刘翔_百度百科', 'url': 'https://baike.baidu.com/item/%E5%88%98%E7%BF%94/5836', 'author': None}, {'id': 'https://www.sohu.com/a/458095925_120086858', 'title': '原创刘翔一共获得多少个国际冠军？网传36冠不准确来看世界田联数据', 'url': 'https://www.sohu.com/a/458095925_120086858', 'publishedDate': '2021-03-30T12:00:00.000Z', 'author': None}, {'id': 'https://www.163.com/dy/article/E5BNM4QO05491YHB.html', 'title': '刘翔到底拿过多少次世界冠军？不要再被48次大赛36次冠军欺骗了|163', 'url': 'https://www.163.com/dy/article/E5BNM4QO05491YHB.html', 'publishedDate': '2019-01-12T12:00:00.000Z', 'author': None}, {'id': 'https://www.sohu.com/a/545897548_120541359', 'title': '40个世界冠军，刘翔生涯获得多少比赛奖金？上交部分或超1亿 - 搜狐', 'url': 'https://www.sohu.com/a/545897548_120541359', 'publishedDate': '2022-05-11T12:00:00.000Z', 'author': None}, {'id': 'http://web.chinamshare.com/hbwt_html/xwsg/xw/55524637.shtml', 'title': '【燕赵新作为致敬40年】刘翔：开挂的亚洲飞人', 'url': 'http://web.chinamshare.com/hbwt_html/xwsg/xw/55524637.shtml', 'publishedDate': '2018-12-10T12:00:00.000Z', 'author': None}, {'id': 'https://zhidao.baidu.com/question/493585922.html', 'title': '刘翔的了几次冠军 - 百度知道', 'url': 'https://zhidao.baidu.com/question/493585922.html', 'publishedDate': '2017-08-01T12:00:00.000Z', 'author': None}, {'id': 'https://blog.sina.com.cn/s/blog_4bdbe3e00102vmoz.html', 'title': '刘翔记忆: 48次大赛获得36个冠军 - 新浪网站导航', 'url': 'https://blog.sina.com.cn/s/blog_4bdbe3e00102vmoz.html', 'publishedDate': '2015-04-08T12:00:00.000Z', 'author': None}], 'effectiveFilters': {'includeDomains': [], 'excludeDomains': [], 'includeText': [], 'excludeText': [], 'urls': []}, 'costDollars': {'total': 0.005, 'search': {'neural': 0.005}}}
    # extracted_info = extract_relevant_info(search_results)

    # for info in tqdm(extracted_info, desc="Processing Snippets"):
    #     full_text = extract_text_from_url(info['url'], snippet="刘翔获得了多少次冠军")  # Get full webpage text
    #     if full_text and not full_text.startswith("Error"):
    #         success, context = extract_snippet_with_context(full_text, info['snippet'])
    #         if success:
    #             info['context'] = context
    #         else:
    #             info['context'] = f"Could not extract context. Returning first 8000 chars: {full_text[:8000]}"
    #     else:
    #         info['context'] = f"Failed to fetch full text: {full_text}"


    # print(extracted_info)