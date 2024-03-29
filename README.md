# :spider: Le Monde crawler

**:warning: THIS PROJECT ISN'T MAINTAINED ANYMORE, PLEASE VISIT [News Crawler](https://github.com/flavienbwk/news-crawler), THE SUCCESSOR OF THIS PROJECT.**

_Le Monde_ is the most famous newspaper in France. It offers thousands of articles through its online website.

<hr/>

This project allows browsing most recent articles from their website and store them in a SQLite database :

- URL
- Title
- Description (short summary)
- Article content
- Author
- Illustration (blob)
- Date

Features :

- Persisting login cookies
- Article caching : only crawling new articles

This project uses [Playwright](https://github.com/microsoft/playwright).

:warning: **DISCLAIMER : This project is for educational purpose only ! Do NOT use it for any other intent.** It was developed as a fun side-project to train my scraping skills.

## Parameters

| Name                           | Type | Description                                                                 |
| ------------------------------ | ---- | --------------------------------------------------------------------------- |
| LEMONDE_EMAIL                  | str  | Your _Le Monde_ email address                                               |
| LEMONDE_PASSWORD               | str  | Your _Le Monde_ password                                                    |
| START_LINK                     | str  | After login, start scraping articles from this page                         |
| RETRIEVE_RELATED_ARTICLE_LINKS | bool | Crawl links in currently scraped article pointing to other similar articles |
| RETRIEVE_EACH_ARTICLE_LINKS    | bool | Crawl all article links present in the currently scraped article            |

## Usage (Docker)

1. Copy and fill your credentials in `.env` :

    ```bash
    cp .env.example .env
    ```

    Edit `LEMONDE_EMAIL` and `LEMONDE_PASSWORD` matching your Le Monde's credentials (we recommend a premium account to avoid any limit)

2. Running the container

    ```bash
    docker-compose up
    ```

## Usage (CLI)

You must have `Python>=3.7` and `pip` installed.

1. Install dependencies

    ```bash
    pip3 install -r requirements.txt
    ```

2. Run CLI

    ```bash
    LEMONDE_EMAIL='...' LEMONDE_PASSWORD='...' python3 ./scripts/crawler.py
    ```

## Ideas

- You might be interested in [Prefect](https://prefect.io) to automate this crawling task each day
