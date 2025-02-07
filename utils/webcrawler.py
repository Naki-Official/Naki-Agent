import re
import html2text
import markdown
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup


# Define the path to ChromeDriver (update if necessary)
driver_path = 'D:\python-source\meme-trading-bot\dexscreener_scraper\chromedriver\chromedriver.exe'

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")


def extract_main_content(html):
    text = html2text.html2text(html)
    html = markdown.markdown(text)
    
    soup = BeautifulSoup(html, 'html.parser')
    
    for element in soup(['header', 'footer', 'nav', 'aside', 'form', 'button', 'input', 'script', 'style']):
        element.decompose()
    
    # Try to find main content
    main_content = soup.find('main')
    if not main_content:
        main_content = soup.find('article')
    if not main_content:
        main_content = soup.find('div', {'id': 'content'})
    if not main_content:
        main_content = soup.find('div', {'role': 'main'})
    if not main_content:
        main_content = soup.find('div', {'class': 'main-content'})
    
    if main_content:
        return main_content.findAll(string=True)
    else:
        return soup.findAll(string=True)

def filter_sentences(text: str, min_word_count=7):
    sentences = "".join(text)
    sentences = sentences.split('\n')

    filtered_sentences = [sentence for sentence in sentences if len(sentence.split()) > min_word_count]
    
    filtered_sentences = ' '.join(filtered_sentences)
    
    filtered_sentences = re.split(r'(?<=[.!?]) +', filtered_sentences)
    return ' '.join(filtered_sentences)

def extract_text_from_url(url):
    try:
        print(f"Extracting text from URL: {url}")
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        driver.implicitly_wait(5)
        
        html = driver.page_source
        
        # Extract main content using BeautifulSoup
        page_text = extract_main_content(html)
        
        page_text = filter_sentences(page_text)
        return page_text

    except Exception as e:
        print(f"An error occurred: {e}")
        return ""

    finally:
        driver.quit()


if __name__ == "__main__":
    url = "https://akariai.xyz/"

    content = extract_text_from_url(url)

    print(content)