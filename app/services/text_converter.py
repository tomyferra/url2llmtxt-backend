from bs4 import BeautifulSoup
import logging
import re
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class TextConverterService:
    @staticmethod
    def extract_text(html_content: str, base_url: str = None) -> dict:
        """
        Extracts the main text, title, and metadata from HTML content.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else "Untitled Page"
        title = re.sub(r'[\\/*?:"<>|]', "", title).strip() # Sanitize filename

        # Remove script and style elements
        for script_or_style in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script_or_style.decompose()

        # Preserve links: replace <a> with "text (link: url)"
        for a in soup.find_all('a', href=True):
            link_text = a.get_text(strip=True)
            href = a['href']
            # If href is relative, it doesn't matter much for the AI prompt as long as it knows the base URL,
            # but we can improve it later if needed.
            if link_text:
                a.replace_with(f"{link_text} (Link: {href})")

        # Get text
        text = soup.get_text(separator='\n')

        # Break into lines and remove leading and trailing whitespace
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)

        if base_url:
            cleaned_text = f"BaseURL: {base_url}\n\n{cleaned_text}"

        return {
            "title": title,
            "text": cleaned_text
        }

    @staticmethod
    def ai_enhancer_text(html_content: str, url: str = None) -> dict:
        """
        Extracts text from HTML and then enhances it using Gemini AI.
        """
        # First extract the clean text and title
        data = TextConverterService.extract_text(html_content, base_url=url)
        title = data["title"]
        text = data["text"]

        try:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            # Use a verified model name
            model = genai.GenerativeModel(os.getenv("GEMINI_MODEL"))
            prompt = f"""
                        You are an AI agent that converts raw scraped webpage text into a clean, well-structured Markdown (.md) document.

                        Your task is to extract the meaningful content and format it following the exact structure below.

                        -----------------------
                        FORMATTING RULES
                        -----------------------

                        1. The output MUST be valid Markdown.
                        2. The first line MUST be the main page title.
                        3. If a short description or summary exists, place it under the title using a Markdown quote block:
                        > Description here
                        The description MUST be 1–2 sentences and include relevant keywords that describe the page topic.
                        4. After the description, include any important introductory notes as bullet points.
                        5. Organize the rest of the content into logical sections using:
                        ## Section Name
                        6. Extract useful links and format them exactly like this:

                        - [Link title](URL): Short explanation of the link. 
                        Make sure the URL is valid and complete (include https:// if missing). 
                        If the link is not relevant, omit it. Make sure the URL is clickable. 
                        If you find a link that has href, append the base url to it. BaseURL is found in the raw text.
                        Description requirements:

                        MUST be at least 12–20 words

                        MUST include meaningful keywords (e.g. categories, locations, product types, technologies, use-cases)

                        MUST add helpful context inferred from the page (but DO NOT hallucinate facts)
                        7. If a link does not have enough context to generate a meaningful description, omit the description:
                        Link title
                        8. URL handling:
                        - Ensure all URLs are complete and valid (include https:// if missing)
                        - Resolve relative links using the BaseURL found in the raw text
                        9. Content enrichment (VERY IMPORTANT):
                        - Expand descriptions with relevant semantic keywords when possible
                        - Include entities such as:
                          - locations (e.g. countries, regions, cities)
                          - categories (e.g. wine types, technologies, industries)
                          - attributes (e.g. flavor profile, use-case, features)
                        - Do NOT invent unknown facts — only enrich using safe, general knowledge or clear context

                        10. Remove irrelevant content such as:
                        - navigation menus
                        - headers/footers
                        - ads
                        - repeated UI elements
                        - "edit this page"
                        - "back to top"

                        11. Keep descriptions concise (1 sentence if possible).

                        12. Preserve only meaningful documentation content.

                        13. If the page contains examples or tutorials, place them under a section called:

                        ## Examples

                        14. If there are additional references or external documentation, place them under:

                        ## Optional

                        15. Do NOT explain what you are doing.
                        16. Do NOT include commentary.
                        17. Output ONLY the final Markdown.

                        -----------------------
                        OUTPUT TEMPLATE
                        -----------------------

                        # Title

                        > Optional description

                        Optional notes:

                        - Important note
                        - Important note

                        ## Section Name

                        - [Link title](URL): Short description

                        ## Examples

                        - [Example name](URL): Short description

                        ## Optional

                        - [Link title](URL)

                        -----------------------
                        RAW WEBPAGE TEXT
                        -----------------------

                        {text}
                        """
                        
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(temperature=0)
            )
            
            return {
                "title": f"{title}",
                "text": response.text
            }
        except Exception as e:
            logger.error(f"Gemini Enhancement failed: {e}")
            # Fallback to normal text if AI fails
            return data