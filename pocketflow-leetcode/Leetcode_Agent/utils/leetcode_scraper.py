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

    def scrape_problem(self, problem_slug):
        try:
            print(f"Scraping problem {problem_slug}")
            question_id = self._get_question_id(problem_slug)
            test_cases = self._get_example_test_cases(problem_slug)
            print(f"Successfully scraped problem {problem_slug} with question ID {question_id} and test cases {test_cases}")
            return question_id, test_cases
        except Exception as e:
            print(f"Error scraping problem {problem_slug}: {e}")
            raise
