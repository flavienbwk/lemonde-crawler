# -*- coding: utf-8 -*-

import os
import pickle
import random
import re
import sqlite3
import time
import traceback
from typing import List, Union
from urllib.parse import urljoin, urlparse

import lxml.html
import lxml.html.clean
import playwright
import tqdm
from playwright.sync_api import ElementHandle, Page, sync_playwright

FILE_PATH = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
SQLITE_DATABASE = f"{DIR_PATH}/../database/news.sqlite"
COOKIES_FILE = f"{DIR_PATH}/../database/cookies.pickle"

RETRIEVE_RELATED_ARTICLE_LINKS = (
    True
    if os.environ.get("RETRIEVE_RELATED_ARTICLE_LINKS", False) == "true"
    else False  # May lead to irrelevant articles throughout time (liens "Lire aussi...")
)
RETRIEVE_EACH_ARTICLE_LINKS = (
    True
    if os.environ.get("RETRIEVE_EACH_ARTICLE_LINKS", False) == "true"
    else False  # May highly lead to irrelevant articles throughout time
)
PAGE_HEIGHT = 976
PAGE_WIDTH = 960

LEMONDE_EMAIL = os.getenv("LEMONDE_EMAIL")
LEMONDE_PASSWORD = os.getenv("LEMONDE_PASSWORD")

print(f"Initializing SQL Lite connection for {SQLITE_DATABASE}...")
CONNECTION = sqlite3.connect(SQLITE_DATABASE)
cursor = CONNECTION.cursor()

try:
    cursor.execute(
        "CREATE TABLE news \
            (url TEXT PRIMARY KEY,\
            title TEXT, description TEXT,\
            article TEXT, author TEXT,\
            illustration BLOB,\
            date TEXT,\
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP\
        );"
    )
    CONNECTION.commit()
    cursor.close()
except sqlite3.OperationalError:
    pass


def add_article(
    url: str,
    title: str = "",
    description: str = "",
    article: str = "",
    author: str = "",
    illustration: bytes = bytes(),
    date: str = "",
):
    cursor = CONNECTION.cursor()
    query = f"INSERT INTO news(url, title, description, article, author, illustration, date) VALUES (?, ?, ?, ?, ?, ?, ?)"
    parameters = (url, title, description, article, author, illustration, date)
    try:
        cursor.execute(query, parameters)
        CONNECTION.commit()
    except sqlite3.IntegrityError:
        print(f"{url} already crawled.")


def cleanhtml(raw_html: str) -> str:
    """Removes all tags from HTML string keeping only inner texts"""
    if raw_html:
        doc = lxml.html.fromstring(raw_html)
        cleaner = lxml.html.clean.Cleaner(style=True)
        doc = cleaner.clean_html(doc)
        return doc.text_content().strip()
    return ""


def get_html_from_selector(page: Page, selector: str) -> str:
    """Returns the inner HTML of an element on the page from
    its provided selector, or an empty string"""
    try:
        item = page.query_selector(selector)
        return item.inner_html()
    except Exception as e:
        print(f"Can't get selector {selector}")
        return ""


def get_html_from_one_of_selectors(page: Page, selectors: List[str]) -> str:
    """Returns the inner HTML of an element on the page from
    one of its provided selectors, or an empty string.
    First element found in returned.
    """
    item_html = ""
    for selector in selectors:
        if len(item_html) == 0:
            item_html_query = get_html_from_selector(page, selector)
            item_html = item_html_query if item_html_query else ""
        if item_html:
            break
    return item_html


def was_article_crawled(href: str) -> bool:
    query = f'SELECT * FROM news WHERE url="{href}"'
    cursor = CONNECTION.cursor()
    cursor.execute(query)
    articles = cursor.fetchall()
    cursor.close()
    return True if len(articles) else False


def random_scroll(page: Page):
    size = page.viewport_size
    scroll_to = int(size["height"] * (1.0 - (random.randrange(1, 8) / 10)))
    page.evaluate(f"window.scrollBy(0, {scroll_to})")


def random_mouse_move(page: Page, max_height: int, max_width: int):
    y = random.randint(0, max_height)
    x = random.randint(0, max_width)
    page.mouse.move(x, y)


def random_activity(page: Page, page_height: int, page_width: int):
    """Simulates user activity on page"""
    random_scroll(page)
    time.sleep(random.randint(0, 1000) / 1000.0)
    random_mouse_move(page, page_height, page_width)
    time.sleep(random.randint(0, 1000) / 1000.0)
    random_mouse_move(page, page_height, page_width)
    time.sleep(random.randint(0, 1000) / 1000.0)
    random_mouse_move(page, page_height, page_width)
    time.sleep(random.randint(0, 1000) / 1000.0)


def get_article_links_from_element(element: Union[Page, ElementHandle]) -> List[str]:
    hrefs_of_page = element.eval_on_selector_all(
        "a[href^='https://www.lemonde.fr/']",
        "elements => elements.map(element => element.href)",
    )

    # Filtering only article links
    article_hrefs = []
    for href in hrefs_of_page:
        if re.match("https:\/\/www\.lemonde\.fr\/.*\/article\/.*", href):
            href = urljoin(href, urlparse(href).path)
            if href not in article_hrefs:
                article_hrefs.append(href)
    return article_hrefs


# ===================
# CRAWLING CODE BELOW
# ===================

not_working_articles = []
with sync_playwright() as p:
    is_docker = True if os.environ.get("IS_DOCKER", False) == "true" else False
    browser = p.chromium.launch(headless=True if is_docker else False)
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(10000)
    page.set_viewport_size({"width": PAGE_WIDTH, "height": PAGE_HEIGHT})

    # Handling login
    is_login_needed = True
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "rb") as cookies_fs:
            cookies = pickle.loads(cookies_fs.read())
        context.add_cookies(cookies)
        page.goto(os.environ.get("START_LINK", "https://www.lemonde.fr/"))

        try:
            page.wait_for_load_state()
            badge_subscribed = page.query_selector(
                "div.Connexion__account > a > span.AccountMenu > span.AccountMenu__type > span"
            )
            is_login_needed = True if badge_subscribed == None else False
        except playwright._impl._api_types.TimeoutError as e:
            print(traceback.format_exc())
            print("Need to login again !")

    if is_login_needed:
        print("Logging in...")
        page.goto("https://secure.lemonde.fr/sfuser/connexion")

        # Skip GPDR modal
        time.sleep(2)
        gpdr_selector = "body > div.gdpr-lmd-standard.gdpr-lmd-standard--transparent-deny > div > header > a"
        try:
            page.wait_for_selector(gpdr_selector)
            page.click(gpdr_selector)
        except playwright._impl._api_types.TimeoutError as e:
            print("No GPDR modal found. Trying to login...")

        # Login
        page.wait_for_selector("#email")
        page.type("#email", LEMONDE_EMAIL, delay=random.randint(30, 120))
        page.wait_for_selector("#password")
        page.type("#password", LEMONDE_PASSWORD, delay=random.randint(30, 120))
        page.wait_for_selector("#login > main > form > div > .button")
        page.click("#login > main > form > div > .button")
        print("Logged in !")
        time.sleep(4)

        # Save cookies
        cookies = context.cookies()
        with open(COOKIES_FILE, "wb+") as cookies_fs:
            cookies_fs.write(pickle.dumps(cookies))
        page.goto(os.environ.get("START_LINK", "https://www.lemonde.fr/"))
    else:
        print("Good, we're connected back.")

    page.wait_for_load_state()
    article_hrefs = get_article_links_from_element(page)
    nb_crawled_news = 0
    nb_total_articles = len(article_hrefs)

    with tqdm.tqdm(
        total=nb_total_articles, position=0, leave=True, unit="article"
    ) as pbar:
        while article_hrefs:
            pbar.update(1)
            article_href = article_hrefs.pop()

            if was_article_crawled(article_href):
                print(f"Article already in database : {article_href}")
                pbar.update(0)
                continue

            try:
                page.goto(article_href)
                random_activity(page, PAGE_HEIGHT, PAGE_WIDTH)
                time.sleep(1)
                random_activity(page, PAGE_HEIGHT, PAGE_WIDTH)

                article_content_html = ""
                article_contents = page.query_selector_all(".article__paragraph")
                for article_content in article_contents:
                    article_content_html += "\n\n" + article_content.inner_html()

                try:
                    article_image = page.query_selector(
                        "section > section.article__wrapper.article__wrapper--premium > article > figure > img"
                    )
                    article_image_bytes = article_image.screenshot()
                except Exception as e:
                    print("No image found for this article")
                    article_image_bytes = None

                article_title_html = get_html_from_selector(page, "h1.article__title")
                article_description_html = get_html_from_selector(
                    page, ".article__desc"
                )
                article_date_html = get_html_from_selector(page, ".meta__date")
                article_author_html = get_html_from_one_of_selectors(
                    page,
                    [
                        "#js-authors-list",
                        ".article__author-link",
                        ".article__author-description",
                        ".meta__author",
                    ],
                )

                add_article(
                    url=article_href,
                    title=cleanhtml(article_title_html),
                    description=cleanhtml(article_description_html),
                    article=cleanhtml(article_content_html),
                    author=cleanhtml(article_author_html),
                    illustration=article_image_bytes,
                    date=cleanhtml(article_date_html),
                )
                nb_crawled_news += 1

                try:
                    if RETRIEVE_RELATED_ARTICLE_LINKS:
                        new_article_links = get_article_links_from_element(
                            page.query_selector(".article__wrapper")
                        )
                        for new_article_link in new_article_links:
                            if (
                                was_article_crawled(new_article_link) is False
                                and new_article_link not in not_working_articles
                                and new_article_link not in article_hrefs
                            ):
                                article_hrefs.append(new_article_link)
                                nb_total_articles += 1
                except AttributeError as e:
                    print("Could not retrieve more links for this article", flush=True)

                if RETRIEVE_EACH_ARTICLE_LINKS:
                    new_article_links = get_article_links_from_element(page)
                    for new_article_link in new_article_links:
                        if (
                            was_article_crawled(new_article_link) is False
                            and new_article_link not in not_working_articles
                            and new_article_link not in article_hrefs
                        ):
                            article_hrefs.append(new_article_link)
                            nb_total_articles += 1
            except Exception as e:
                not_working_articles.append(article_href)
                print(traceback.format_exc())
                print(e)

            pbar.total = nb_total_articles
            pbar.refresh()

    print(f"Crawled {nb_crawled_news} articles in total")
    browser.close()

CONNECTION.close()
