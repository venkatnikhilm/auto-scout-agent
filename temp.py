from backend.lambda_fns.check_price import safe_get_html
from backend.agents.xpath_agents import ask_gemini_for_xpath
from backend.scrapper.scraper import extract_with_xpath
from lxml import etree
import requests

html = safe_get_html("https://www.nike.com/t/vomero-18-mens-road-running-shoes-NzWnvcC8/IH4112-902")
xpath_expr = ask_gemini_for_xpath(html, "Notify me when the price of these shoes drops below $100")



tree = etree.HTML(html)

# 3. Execute the XPath
elements = tree.xpath(xpath_expr)

# elements is a list of matching element objects
for el in elements:
    print(el.text)
# print(extract_with_xpath(html, xpath_expr))