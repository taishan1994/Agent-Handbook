"""
LeetCode Scraper for LeetCode Agent

This module provides utilities for scraping LeetCode problem details.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional


class LeetCodeScraper:
    """
    Scraper for extracting LeetCode problem details.
    """
    
    def __init__(self):
        """Initialize the scraper."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_problem(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape problem details from a LeetCode URL.
        
        Args:
            url: LeetCode problem URL
            
        Returns:
            Dictionary with problem details or None if scraping failed
        """
        try:
            # Extract problem slug from URL
            slug_match = re.search(r'/problems/([^/]+)', url)
            if not slug_match:
                return None
                
            slug = slug_match.group(1)
            
            # Fetch the problem page
            response = self.session.get(url)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract problem title
            title_element = soup.find('div', class_='title__1R1Y')
            title = title_element.text.strip() if title_element else ""
            
            # Extract problem difficulty
            difficulty_element = soup.find('div', class_='difficulty__1Yy9')
            difficulty = difficulty_element.text.strip() if difficulty_element else ""
            
            # Extract problem description
            description_element = soup.find('div', class_='content__1Y2H')
            description = ""
            if description_element:
                # Convert HTML to plain text
                description = self._html_to_text(description_element)
            
            # Extract examples
            examples = []
            example_elements = soup.find_all('div', class_='example__1y9H')
            for example_element in example_elements:
                example_text = self._html_to_text(example_element)
                examples.append(example_text)
            
            # Extract constraints
            constraints = []
            constraint_elements = soup.find_all('div', class_='constraint__1y9H')
            for constraint_element in constraint_elements:
                constraint_text = self._html_to_text(constraint_element)
                constraints.append(constraint_text)
            
            # Extract function signature
            function_signature = self._extract_function_signature(soup)
            
            return {
                'title': title,
                'slug': slug,
                'difficulty': difficulty,
                'description': description,
                'examples': examples,
                'constraints': constraints,
                'function_signature': function_signature,
                'url': url
            }
        
        except Exception as e:
            print(f"Error scraping LeetCode problem: {e}")
            return None
    
    def _html_to_text(self, element) -> str:
        """
        Convert HTML element to plain text.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            Plain text representation
        """
        # Replace code blocks with a marker
        for code in element.find_all('pre'):
            code.replace_with(f"[CODE]\n{code.get_text()}\n[/CODE]")
        
        # Replace inline code with a marker
        for code in element.find_all('code'):
            code.replace_with(f"`{code.get_text()}`")
        
        # Replace line breaks
        for br in element.find_all('br'):
            br.replace_with('\n')
        
        # Replace paragraphs with newlines
        for p in element.find_all('p'):
            p.insert_after('\n')
        
        # Get the text and clean it up
        text = element.get_text()
        text = re.sub(r'\n{3,}', '\n\n', text)  # Replace multiple newlines with at most 2
        return text.strip()
    
    def _extract_function_signature(self, soup) -> str:
        """
        Extract the function signature from the problem page.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            Function signature string
        """
        # Try to find the function signature in the code editor
        signature_element = soup.find('div', class_='ace_line')
        if signature_element:
            return signature_element.get_text().strip()
        
        return ""
    
    def parse_problem_description(self, description: str) -> Dict[str, Any]:
        """
        Parse a problem description text to extract key information.
        
        Args:
            description: Problem description text
            
        Returns:
            Dictionary with parsed information
        """
        # Extract examples using regex
        examples = []
        example_pattern = r'Example\s*\d*:\s*(.*?)(?=Example\s*\d*:|$)'
        example_matches = re.findall(example_pattern, description, re.DOTALL | re.IGNORECASE)
        
        for match in example_matches:
            examples.append(match.strip())
        
        # Extract constraints using regex
        constraints = []
        constraint_pattern = r'Constraints:\s*(.*?)(?=\n\n|$)'
        constraint_match = re.search(constraint_pattern, description, re.DOTALL | re.IGNORECASE)
        
        if constraint_match:
            constraint_text = constraint_match.group(1).strip()
            # Split by bullet points or numbered lists
            constraint_items = re.split(r'[-*]\s*|\d+\.\s*', constraint_text)
            constraints = [c.strip() for c in constraint_items if c.strip()]
        
        return {
            'examples': examples,
            'constraints': constraints
        }

if __name__ == "__main__":
    scraper = LeetCodeScraper()
    problem = scraper.scrape_problem("https://leetcode.com/problems/two-sum/")
    if problem:
        print(problem)
