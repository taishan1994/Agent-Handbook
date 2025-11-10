from pocketflow import Node
from utils.call_llm import call_llm
import yaml
import random
from exa_search_main import (
    extract_relevant_info,
    extract_text_from_url,
    extract_snippet_with_context,
    exa_web_search
)
from tqdm import tqdm

def search_web_exa(query):
    url = "https://api.exa.ai/search"
    search_results = exa_web_search(query, url)
    # print(response)
    # search_results = {'requestId': 'f3309744aa28eb86d4231d1af2303b18', 'resolvedSearchType': 'keyword', 'results': [{'id': 'https://topics.gmw.cn/node_68757.htm', 'title': '刘翔宣布正式退役 - 专题- 光明网', 'url': 'https://topics.gmw.cn/node_68757.htm', 'author': None}, {'id': 'https://zh.wikipedia.org/zh-hans/%E5%88%98%E7%BF%94', 'title': '刘翔- 维基百科，自由的百科全书', 'url': 'https://zh.wikipedia.org/zh-hans/%E5%88%98%E7%BF%94', 'author': None}, {'id': 'https://www.163.com/dy/article/FUOQGNBC05452FWC.html', 'title': '刘翔获得过多少世界冠军？别再相信36个冠军6个亚军3个季军了 - 网易', 'url': 'https://www.163.com/dy/article/FUOQGNBC05452FWC.html', 'publishedDate': '2020-12-26T12:00:00.000Z', 'author': None}, {'id': 'https://baike.baidu.com/item/%E5%88%98%E7%BF%94/5836', 'title': '刘翔_百度百科', 'url': 'https://baike.baidu.com/item/%E5%88%98%E7%BF%94/5836', 'author': None}, {'id': 'https://www.sohu.com/a/458095925_120086858', 'title': '原创刘翔一共获得多少个国际冠军？网传36冠不准确来看世界田联数据', 'url': 'https://www.sohu.com/a/458095925_120086858', 'publishedDate': '2021-03-30T12:00:00.000Z', 'author': None}, {'id': 'https://www.163.com/dy/article/E5BNM4QO05491YHB.html', 'title': '刘翔到底拿过多少次世界冠军？不要再被48次大赛36次冠军欺骗了|163', 'url': 'https://www.163.com/dy/article/E5BNM4QO05491YHB.html', 'publishedDate': '2019-01-12T12:00:00.000Z', 'author': None}, {'id': 'https://www.sohu.com/a/545897548_120541359', 'title': '40个世界冠军，刘翔生涯获得多少比赛奖金？上交部分或超1亿 - 搜狐', 'url': 'https://www.sohu.com/a/545897548_120541359', 'publishedDate': '2022-05-11T12:00:00.000Z', 'author': None}, {'id': 'http://web.chinamshare.com/hbwt_html/xwsg/xw/55524637.shtml', 'title': '【燕赵新作为致敬40年】刘翔：开挂的亚洲飞人', 'url': 'http://web.chinamshare.com/hbwt_html/xwsg/xw/55524637.shtml', 'publishedDate': '2018-12-10T12:00:00.000Z', 'author': None}, {'id': 'https://zhidao.baidu.com/question/493585922.html', 'title': '刘翔的了几次冠军 - 百度知道', 'url': 'https://zhidao.baidu.com/question/493585922.html', 'publishedDate': '2017-08-01T12:00:00.000Z', 'author': None}, {'id': 'https://blog.sina.com.cn/s/blog_4bdbe3e00102vmoz.html', 'title': '刘翔记忆: 48次大赛获得36个冠军 - 新浪网站导航', 'url': 'https://blog.sina.com.cn/s/blog_4bdbe3e00102vmoz.html', 'publishedDate': '2015-04-08T12:00:00.000Z', 'author': None}], 'effectiveFilters': {'includeDomains': [], 'excludeDomains': [], 'includeText': [], 'excludeText': [], 'urls': []}, 'costDollars': {'total': 0.005, 'search': {'neural': 0.005}}}
    extracted_info = extract_relevant_info(search_results)

    for info in tqdm(extracted_info, desc="Processing Snippets"):
        full_text = extract_text_from_url(info['url'], snippet="刘翔获得了多少次冠军")  # Get full webpage text
        if full_text and not full_text.startswith("Error"):
            success, context = extract_snippet_with_context(full_text, info['snippet'])
            if success:
                info['context'] = context
            else:
                info['context'] = f"Could not extract context. Returning first 8000 chars: {full_text[:8000]}"
        else:
            info['context'] = f"Failed to fetch full text: {full_text}"
    results_str = "\n\n".join([f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['context']}" for r in extracted_info])
    return results_str

class DecideAction(Node):
    def prep(self, shared):
        """Prepare the context and question for the decision-making process."""
        # Get the current context (default to "No previous search" if none exists)
        context = shared.get("context", "No previous search")
        # Get the question from the shared store
        question = shared["question"]
        # Return both for the exec step
        return question, context
        
    def exec(self, inputs):
        """Call the LLM to decide whether to search or answer."""
        question, context = inputs
        
        print(f"🤔 Agent deciding what to do next...")
        
        # Create a prompt to help the LLM decide what to do next
        prompt = f"""
### CONTEXT
You are a research assistant that can search the web.
Question: {question}
Previous Research: {context}

### ACTION SPACE
[1] search
  Description: Look up more information on the web
  Parameters:
    - query (str): What to search for

[2] answer
  Description: Answer the question with current knowledge
  Parameters:
    - answer (str): Final answer to the question

## NEXT ACTION
Decide the next action based on the context and available actions.
Return your response in this format:

```yaml
thinking: |
    <your step-by-step reasoning process>
action: search OR answer
reason: <why you chose this action>
search_query: <specific search query if action is search>
```"""
        
        # Call the LLM to make a decision
        response = call_llm(prompt)
        
        # Parse the response to get the decision
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        decision = yaml.safe_load(yaml_str)
        
        return decision
    
    def post(self, shared, prep_res, exec_res):
        """Save the decision and determine the next step in the flow."""
        # If LLM decided to search, save the search query
        if exec_res["action"] == "search":
            shared["search_query"] = exec_res["search_query"]
            print(f"🔍 Agent decided to search for: {exec_res['search_query']}")
        else:
            print(f"💡 Agent decided to answer the question")
        
        # Return the action to determine the next node in the flow
        return exec_res["action"]

class SearchWeb(Node):
    def prep(self, shared):
        """Get the search query from the shared store."""
        return shared["search_query"]
        
    def exec(self, search_query):
        """Search the web for the given query."""
        # Call the search utility function
        print(f"🌐 Searching the web for: {search_query}")
        results = search_web_exa(search_query)
        return results
    
    def post(self, shared, prep_res, exec_res):
        """Save the search results and go back to the decision node."""
        # Add the search results to the context in the shared store
        previous = shared.get("context", "")
        shared["context"] = previous + "\n\nSEARCH: " + shared["search_query"] + "\nRESULTS: " + exec_res
        
        print(f"📚 Found information, analyzing results...")
        
        # Always go back to the decision node after searching
        return "decide"

class UnreliableAnswerNode(Node):
    def prep(self, shared):
        """Get the question and context for answering."""
        return shared["question"], shared.get("context", "")
        
    def exec(self, inputs):
        """Call the LLM to generate a final answer with 50% chance of returning a dummy answer."""
        question, context = inputs
        
        # 50% chance to return a dummy answer
        if random.random() < 0.5:
            print(f"🤪 Generating unreliable dummy answer...")
            return "Sorry, I'm on a coffee break right now. All information I provide is completely made up anyway. The answer to your question is 42, or maybe purple unicorns. Who knows? Certainly not me!"
        
        print(f"✍️ Crafting final answer...")
        
        # Create a prompt for the LLM to answer the question
        prompt = f"""
### CONTEXT
Based on the following information, answer the question.
Question: {question}
Research: {context}

## YOUR ANSWER:
Provide a comprehensive answer using the research results.
"""
        # Call the LLM to generate an answer
        answer = call_llm(prompt)
        return answer
    
    def post(self, shared, prep_res, exec_res):
        """Save the final answer and complete the flow."""
        # Save the answer in the shared store
        shared["answer"] = exec_res
        
        print(f"✅ Answer generated successfully")

class SupervisorNode(Node):
    def prep(self, shared):
        """Get the current answer for evaluation."""
        return shared["answer"]
    
    def exec(self, answer):
        """Check if the answer is valid or nonsensical."""
        print(f"    🔍 Supervisor checking answer quality...")
        
        # Check for obvious markers of the nonsense answers
        nonsense_markers = [
            "coffee break", 
            "purple unicorns", 
            "made up", 
            "42", 
            "Who knows?"
        ]
        
        # Check if the answer contains any nonsense markers
        is_nonsense = any(marker in answer for marker in nonsense_markers)
        
        if is_nonsense:
            return {"valid": False, "reason": "Answer appears to be nonsensical or unhelpful"}
        else:
            return {"valid": True, "reason": "Answer appears to be legitimate"}
    
    def post(self, shared, prep_res, exec_res):
        """Decide whether to accept the answer or restart the process."""
        if exec_res["valid"]:
            print(f"    ✅ Supervisor approved answer: {exec_res['reason']}")
        else:
            print(f"    ❌ Supervisor rejected answer: {exec_res['reason']}")
            # Clean up the bad answer
            shared["answer"] = None
            # Add a note about the rejected answer
            context = shared.get("context", "")
            shared["context"] = context + "\n\nNOTE: Previous answer attempt was rejected by supervisor."
            return "retry" 