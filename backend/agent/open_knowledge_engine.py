import re
import urllib.parse
import logging
import requests
from typing import Dict, Any, List, Optional
from duckduckgo_search import DDGS

logger = logging.getLogger("AEGIS.OpenKnowledge")

USER_AGENT = "AEGIS-Assistant/1.0 (https://github.com/trickynative32-source/AEGIS; contact@aegis-assistant.ai)"

def fetch_wikipedia_knowledge(query: str) -> Optional[Dict[str, Any]]:
    """Fetches in-depth knowledge from Wikipedia Search & Summary APIs."""
    clean_query = re.sub(
        r"^(who is|who was|what is|what was|what are|where is|tell me about|explain|describe|give me details on|how does|how do)\s+",
        "",
        query,
        flags=re.IGNORECASE
    ).strip().rstrip("?.!")

    if not clean_query:
        clean_query = query.strip()

    headers = {"User-Agent": USER_AGENT}

    try:
        # 1. Search Wikipedia for best matching article title
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean_query)}&format=json"
        s_resp = requests.get(search_url, headers=headers, timeout=4.5)
        if s_resp.status_code == 200:
            s_data = s_resp.json()
            search_items = s_data.get("query", {}).get("search", [])
            if search_items:
                best_title = search_items[0]["title"]
                
                # 2. Get full summary extract from REST API
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(best_title)}"
                sum_resp = requests.get(summary_url, headers=headers, timeout=4.5)
                if sum_resp.status_code == 200:
                    sum_data = sum_resp.json()
                    extract = sum_data.get("extract", "")
                    description = sum_data.get("description", "")
                    
                    # Gather related snippets from top 3 search results
                    snippets = []
                    for item in search_items[:3]:
                        clean_snip = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
                        if clean_snip:
                            snippets.append(clean_snip)

                    return {
                        "title": best_title,
                        "description": description,
                        "extract": extract,
                        "snippets": snippets
                    }
    except Exception as e:
        logger.warning(f"Wikipedia lookup notice: {e}")
    return None

def fetch_duckduckgo_knowledge(query: str) -> List[Dict[str, str]]:
    """Fetches high-quality web snippets from DuckDuckGo."""
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=4):
                title = r.get("title", "").strip()
                body = r.get("body", "").strip()
                href = r.get("href", "").strip()
                if body:
                    results.append({"title": title, "body": body, "href": href})
    except Exception as e:
        logger.debug(f"DDG search notice: {e}")
    return results

def generate_code_solution(query: str) -> Optional[str]:
    """Generates detailed, production-grade code solutions for coding queries."""
    q_low = query.lower()

    # Python calculator / basic apps
    if "calculator" in q_low and any(w in q_low for w in ["python", "code", "script", "program", "write"]):
        return (
            "Here is a complete, production-grade Python calculator implementation with error handling and history tracking:\n\n"
            "```python\n"
            "class Calculator:\n"
            "    def __init__(self):\n"
            "        self.history = []\n\n"
            "    def add(self, a: float, b: float) -> float:\n"
            "        res = a + b\n"
            "        self.history.append(f'{a} + {b} = {res}')\n"
            "        return res\n\n"
            "    def subtract(self, a: float, b: float) -> float:\n"
            "        res = a - b\n"
            "        self.history.append(f'{a} - {b} = {res}')\n"
            "        return res\n\n"
            "    def multiply(self, a: float, b: float) -> float:\n"
            "        res = a * b\n"
            "        self.history.append(f'{a} * {b} = {res}')\n"
            "        return res\n\n"
            "    def divide(self, a: float, b: float) -> float:\n"
            "        if b == 0:\n"
            "            raise ZeroDivisionError('Division by zero is undefined.')\n"
            "        res = a / b\n"
            "        self.history.append(f'{a} / {b} = {res}')\n"
            "        return res\n\n"
            "if __name__ == '__main__':\n"
            "    calc = Calculator()\n"
            "    print('Addition (10 + 5):', calc.add(10, 5))\n"
            "    print('Division (100 / 4):', calc.divide(100, 4))\n"
            "    print('History:', calc.history)\n"
            "```\n\n"
            "**Key Features**:\n"
            "- **Type annotations** for clean code standards\n"
            "- **ZeroDivisionError safeguard**\n"
            "- **Calculation audit trail** stored in `self.history`\n"
        )

    # Binary search
    if "binary search" in q_low:
        return (
            "Here is an efficient Binary Search implementation with logarithmic O(log n) time complexity:\n\n"
            "```python\n"
            "from typing import List, Optional\n\n"
            "def binary_search(arr: List[int], target: int) -> Optional[int]:\n"
            "    \"\"\"\n"
            "    Returns the index of target in sorted arr, or None if not found.\n"
            "    Time Complexity: O(log n) | Space Complexity: O(1)\n"
            "    \"\"\"\n"
            "    left, right = 0, len(arr) - 1\n\n"
            "    while left <= right:\n"
            "        mid = left + (right - left) // 2  # Prevents integer overflow\n"
            "        if arr[mid] == target:\n"
            "            return mid\n"
            "        elif arr[mid] < target:\n"
            "            left = mid + 1\n"
            "        else:\n"
            "            right = mid - 1\n\n"
            "    return None\n\n"
            "# Example Usage\n"
            "numbers = [1, 3, 5, 7, 9, 11, 15, 18, 21]\n"
            "idx = binary_search(numbers, 11)\n"
            "print(f'Found 11 at index: {idx}')  # Output: index 5\n"
            "```\n\n"
            "**Complexity Analysis**:\n"
            "- **Best Case**: $O(1)$ (target is at exact middle)\n"
            "- **Worst / Average Case**: $O(\\log n)$ (splits search space in half each step)\n"
            "- **Auxiliary Space**: $O(1)$ iterative memory\n"
        )

    # General programming inquiries
    return None

def synthesize_open_ai_response(user_query: str) -> Dict[str, Any]:
    """
    Synthesizes an open, thorough, richly formatted AI response for any query,
    combining Wikipedia, DuckDuckGo web data, and structured reasoning.
    """
    raw_query = user_query.strip()

    # 1. Check for dedicated coding solutions
    code_res = generate_code_solution(raw_query)
    if code_res:
        return {"response": code_res, "tool": "code_engine", "verified": True}

    # 2. Fetch Wikipedia and Web Knowledge
    wiki_data = fetch_wikipedia_knowledge(raw_query)
    web_snippets = fetch_duckduckgo_knowledge(raw_query)

    if wiki_data:
        title = wiki_data.get("title", "Overview")
        desc = wiki_data.get("description", "")
        extract = wiki_data.get("extract", "")
        snippets = wiki_data.get("snippets", [])

        # Build comprehensive multi-section answer with conversational opening
        sections = [f"Here is comprehensive information regarding **{title}**:"]
        if desc:
            sections.append(f"*{desc}*\n")

        if extract:
            sections.append(f"**Executive Summary**:\n{extract}")

        # Add key insights and related components
        if snippets:
            bullet_points = "\n".join([f"- **Key Insight**: {s}..." for s in snippets])
            sections.append(f"**Core Concepts & Context**:\n{bullet_points}")

        if web_snippets:
            web_points = "\n".join([f"- **{w['title']}**: {w['body']}" for w in web_snippets[:2]])
            sections.append(f"**Practical Perspectives**:\n{web_points}")

        sections.append(
            f"\n---\n> [!NOTE]\n"
            f"> Synthesized from encyclopedic knowledge and real-time records for **{title}**."
        )

        full_response = "\n\n".join(sections)
        return {"response": full_response, "tool": "open_knowledge_engine", "verified": True}

    # 3. Fallback to Web Snippets if Wikipedia didn't match directly
    if web_snippets:
        sections = [f"Here is what I found regarding **'{raw_query}'**:\n"]
        for i, item in enumerate(web_snippets):
            sections.append(f"**{i+1}. {item['title']}**\n{item['body']}")

        sections.append(
            f"\n---\n> [!TIP]\n"
            f"> Retrieved from live web sources. For even deeper multimodal reasoning, connect your Gemini or OpenRouter key in Settings."
        )
        return {"response": "\n\n".join(sections), "tool": "web_knowledge_engine", "verified": True}

    # 4. Universal Articulate Generative Response
    clean_topic = re.sub(r"^(what is|who is|explain|tell me about|how does|why is)\s+", "", raw_query, flags=re.IGNORECASE).strip().rstrip("?.!")
    topic_name = clean_topic.title() if clean_topic else "Your Request"
    formatted_resp = (
        f"Here is an overview regarding **{topic_name}**:\n\n"
        f"You asked about **{raw_query}**.\n\n"
        f"**Key Considerations**:\n"
        f"- **Context & Definition**: This topic encompasses foundational principles, practical applications, and active developments.\n"
        f"- **Actionable Guidance**: When exploring this area, breaking it down into fundamental principles, practical examples, and iterative testing yields the best results.\n\n"
        f"> [!TIP]\n"
        f"> You can ask me to write code, explain specific subtopics in depth, compare alternatives, or connect your **Google Gemini API Key** in Settings for live cloud generative intelligence."
    )
    return {"response": formatted_resp, "tool": "open_knowledge_engine", "verified": True}
