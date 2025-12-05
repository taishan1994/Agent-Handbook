import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup

class LeetCodeAPI:
    def __init__(self, cookie: str, csrftoken: str):
        self.cookie = cookie
        self.csrftoken = csrftoken
        self.base_url = "https://leetcode.com"
        self.graphql_url = f"{self.base_url}/graphql/"

    def _get_headers(self):
        headers = {
            'Content-Type': 'application/json',
            'Cookie': self.cookie
        }
        print("Generated headers:", headers)
        return headers

    def fetch_problem_plain_text(self, link):
        match = re.search(r'/problems/([^/]+)/', link)
        if not match:
            raise ValueError("Invalid LeetCode problem URL")
        slug = match.group(1)
        print(f"Extracted slug: {slug}")

        payload = json.dumps({
            "query": """query questionContent($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        content
        mysqlSchemas
      }
    }""",
            "variables": {"titleSlug": slug}
        })
        print("Payload for plain text fetch:", payload)

        try:
            print(f"Fetching problem: {slug}")
            response = requests.post(self.graphql_url, headers=self._get_headers(), data=payload)
            print("Response status:", response.status_code)
            response.raise_for_status()

            response_json = response.json()
            print("Response JSON keys:", list(response_json.keys()))
            html_content = response_json.get('data', {}).get('question', {}).get('content', '')
            if not html_content:
                print("No content found for problem.")
                return "", slug
            
            print(html_content)
            soup = BeautifulSoup(html_content, "html.parser")
            print("Successfully fetched problem text.")
            return soup.get_text(), slug
        except requests.exceptions.RequestException as e:
            print(f"Error fetching problem plain text: {e}")
            raise

    def generate_template(self, problem_slug, code_lang):
        payload = json.dumps({
            "query": """
                query questionEditorData($titleSlug: String!) {
                  question(titleSlug: $titleSlug) {
                    questionId
                    questionFrontendId
                    codeSnippets {
                      lang
                      langSlug
                      code
                    }
                    envInfo
                    enableRunCode
                  }
                }
            """,
            "variables": {
                "titleSlug": problem_slug
            }
        })
        print("Payload for code template:", payload)

        try:
            print(f"Generating template for {problem_slug} in {code_lang}")
            response = requests.post(self.graphql_url, headers=self._get_headers(), data=payload)
            print("Response status:", response.status_code)
            response.raise_for_status()
            data = response.json()
            print("Code snippet languages available:", [s["langSlug"] for s in data['data']['question']['codeSnippets']])

            code_snippets = data['data']['question']['codeSnippets']
            matched_snippet = next((s for s in code_snippets if s['langSlug'] == code_lang), None)
            if matched_snippet:
                print("Successfully generated template.")
                return matched_snippet['code']
            else:
                print(f"No template found for language: {code_lang}")
                return f"No code found for language: {code_lang}"
        except (requests.exceptions.RequestException, KeyError) as e:
            print(f"Error generating template: {e}")
            return f"Error fetching code: {e}"

    def run_code(self, problem_slug, code_lang, code):
        try:
            print(f"Running code for {problem_slug}")
            question_id = self._get_question_id(problem_slug)
            url = f"{self.base_url}/problems/{problem_slug}/interpret_solution/"

            test_cases = self._get_example_test_cases(problem_slug)
            print("Test cases used for run:", test_cases)

            payload = json.dumps({
                "lang": code_lang,
                "question_id": question_id,
                "typed_code": code,
                "data_input": "\n".join(test_cases)
            })
            print("Payload for running code:", payload)

            headers = self._get_headers()
            headers['x-csrftoken'] = self.csrftoken
            headers['Origin'] = self.base_url
            headers['Referer'] = f"{self.base_url}/problems/{problem_slug}"
            print("Headers for run code request:", headers)

            response = requests.post(url, headers=headers, data=payload)
            print("Run code response status:", response.status_code)
            response.raise_for_status()
            interpret_id = response.json().get('interpret_id')
            print(f"Interpretation ID: {interpret_id}")

            print(f"Waiting for result of interpretation {interpret_id}...")
            time.sleep(4)

            check_url = f"{self.base_url}/submissions/detail/{interpret_id}/check/"
            response = requests.get(check_url, headers=headers)
            print("Result check response status:", response.status_code)
            response.raise_for_status()
            print("Successfully ran code.")
            return response.json()
        except (requests.exceptions.RequestException, KeyError) as e:
            print(f"Error running code: {e}")
            raise

    def submit_code(self, problem_slug, code_lang, code):
        try:
            print(f"Submitting code for {problem_slug}")
            question_id = self._get_question_id(problem_slug)
            url = f"{self.base_url}/problems/{problem_slug}/submit/"

            payload = json.dumps({
                "lang": code_lang,
                "question_id": question_id,
                "typed_code": code
            })
            print("Payload for submission:", payload)

            headers = self._get_headers()
            headers['x-csrftoken'] = self.csrftoken
            headers['Origin'] = self.base_url
            headers['Referer'] = f"{self.base_url}/problems/{problem_slug}"

            response = requests.post(url, headers=headers, data=payload)
            print("Submit response status:", response.status_code)
            response.raise_for_status()
            submission_id = response.json().get('submission_id')
            print(f"Submission ID: {submission_id}")

            print(f"Waiting for result of submission {submission_id}...")
            time.sleep(4)

            check_url = f"{self.base_url}/submissions/detail/{submission_id}/check/"
            response = requests.get(check_url, headers=headers)
            print("Submission result check status:", response.status_code)
            response.raise_for_status()
            print("Successfully submitted code.")
            return response.json()
        except (requests.exceptions.RequestException, KeyError) as e:
            print(f"Error submitting code: {e}")
            raise

    def _get_question_id(self, problem_slug):
        try:
            print(f"Fetching question ID for {problem_slug}")
            payload = json.dumps({
                "query": '''
                    query consolePanelConfig($titleSlug: String!) {
                      question(titleSlug: $titleSlug) {
                        questionId
                      }
                    }
                ''',
                "variables": {
                    "titleSlug": problem_slug
                }
            })
            print("Payload for question ID:", payload)
            response = requests.post(self.graphql_url, headers=self._get_headers(), data=payload)
            print("Question ID fetch response status:", response.status_code)
            response.raise_for_status()
            question_id = response.json()['data']['question']['questionId']
            print(f"Successfully fetched question ID: {question_id}")
            return question_id
        except (requests.exceptions.RequestException, KeyError) as e:
            print(f"Error fetching question ID: {e}")
            raise

    def _get_example_test_cases(self, problem_slug):
        try:
            print(f"Fetching example test cases for {problem_slug}")
            payload = json.dumps({
                "query": '''
                    query consolePanelConfig($titleSlug: String!) {
                      question(titleSlug: $titleSlug) {
                        exampleTestcaseList
                      }
                    }
                ''',
                "variables": {
                    "titleSlug": problem_slug
                }
            })
            print("Payload for example test cases:", payload)
            response = requests.post(self.graphql_url, headers=self._get_headers(), data=payload)
            print("Example test case fetch response status:", response.status_code)
            response.raise_for_status()
            test_cases = response.json()['data']['question']['exampleTestcaseList']
            print("Successfully fetched example test cases:", test_cases)
            return test_cases
        except (requests.exceptions.RequestException, KeyError) as e:
            print(f"Error fetching example test cases: {e}")
            raise


if __name__ == "__main__":
    api = LeetCodeAPI(cookie="aliyungf_tc=b661ee8dba2eed7d24bbdca13c2ff05c3ac01550ae1bcf0136f23bdd5888949c; sl-session=evKXDk+nMmnCJgYELzPXKg==; csrftoken=JAhWyIhlyk3mrsZkTY6WOo6APrNMXMja; gr_user_id=398e40e9-0a2f-4bfa-9a65-cd03a57e4588; Hm_lvt_f0faad39bcf8471e3ab3ef70125152c3=1764840915; HMACCOUNT=0567C89CFD22D8D2; a2873925c34ecbd2_gr_last_sent_cs1=bo-er; _gid=GA1.2.1949930630.1764840931; tfstk=gK9IF6DGzy4IiQOAOToaGKzxIl6S0ckqRusJm3eU29BKV8T2Dp7ErDA1PF_ixpuhL8dWm3bdU9JEFQ_Op_AFzw75F3Yjbqkq3HxhEO3quxuoiC5hnzedvzSTBiW5vhPaSGxhET3NN9Q7lHYFVprFeTn1Bgs4yTe8pcNOxNed2JI8WcslWTIL9WBOBgI4e7QJyhn1qNQReTLRBcslWaBRebYQcgGC-HicJfXYnuo-5Ne8edsC6f-dWb86BM9hlHpQe8nAA6_vvNgI96UO63fWEu25NHdDriLLJ4_kChppME3aTwdfVnRWvveOLpxpM_pxr7KhLw69pIZ8eh6CyEShGyg1kpx9nOCZHmt9Ie-HC3r-eG8VWHvdFxncd9QdCGvrSJQW6QpFtT4KPav6Xpd54CwVll6UNl10FG_qfcNuZz6vG4zs6C3F9GjC_ci_JQfdjG_qfcNuZ6IGAiosfydl.; a2873925c34ecbd2_gr_session_id=538c8bf4-f000-4143-be44-6e714019c4e6; a2873925c34ecbd2_gr_last_sent_sid_with_cs1=538c8bf4-f000-4143-be44-6e714019c4e6; a2873925c34ecbd2_gr_session_id_sent_vst=538c8bf4-f000-4143-be44-6e714019c4e6; LEETCODE_SESSION=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuZXh0X2FmdGVyX29hdXRoIjoiLyIsIl9hdXRoX3VzZXJfaWQiOiIyNjA1NTYiLCJfYXV0aF91c2VyX2JhY2tlbmQiOiJkamFuZ28uY29udHJpYi5hdXRoLmJhY2tlbmRzLk1vZGVsQmFja2VuZCIsIl9hdXRoX3VzZXJfaGFzaCI6ImRmN2RjMWFkZGJkMGM0ZTE3ZjVmNTVkOTc2NzUyYTYxMDlmMmEyZmRmNzhkODJiOWE2ZDcwYzBlZDVjMWVlODAiLCJpZCI6MjYwNTU2LCJlbWFpbCI6IjQ2MTYwMDM3MUBxcS5jb20iLCJ1c2VybmFtZSI6ImJvLWVyIiwidXNlcl9zbHVnIjoiYm8tZXIiLCJhdmF0YXIiOiJodHRwczovL2Fzc2V0cy5sZWV0Y29kZS5jbi9hbGl5dW4tbGMtdXBsb2FkL3VzZXJzL2JvLWVyL2F2YXRhcl8xNTQwODg1MjA0LnBuZyIsInBob25lX3ZlcmlmaWVkIjp0cnVlLCJpcCI6IjU4LjI1MC4yNTAuMjQiLCJfdGltZXN0YW1wIjoxNzY0ODQwOTI3LjY5NTE2NDQsImV4cGlyZWRfdGltZV8iOjE3NjczODA0MDAsInZlcnNpb25fa2V5XyI6MCwiZGV2aWNlX2lkIjoiNGEzMzQyMGYyZDBjMGZmMGExMDljZGUwYTc2ZmZmZjQiLCJsYXRlc3RfdGltZXN0YW1wXyI6MTc2NDkwMTMwMn0.UMLC4Ex19BSjpqFKI3kMplVs_XWw7qxh2FfDNuNqkBo; a2873925c34ecbd2_gr_cs1=bo-er; Hm_lpvt_f0faad39bcf8471e3ab3ef70125152c3=1764901324; _ga=GA1.2.2063381244.1764840930; _ga_PDVPZYN3CW=GS2.1.s1764901011$o4$g1$t1764901714$j60$l0$h0", csrftoken="JAhWyIhlyk3mrsZkTY6WOo6APrNMXMja") 
    print(api.fetch_problem_plain_text(link="https://leetcode.cn/problems/two-sum/"))
    # print(api.generate_template(problem_slug="two-sum", code_lang="python3"))
    # print(api._get_example_test_cases(problem_slug="two-sum"))
    # api._get_question_id(problem_slug="two-sum")
