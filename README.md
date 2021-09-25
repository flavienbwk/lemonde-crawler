# :spider: Le Monde crawler

<p align="center">
<img src="https://travis-ci.com/flavienbwk/lemonde-crawler.svg?branch=master"/>
</p>

_Le Monde_ (english: _The World_) is the most famous newspaper in France. It offers thousands of articles through its online website.

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

## Usage (Docker)

1. Copy and fill your credentials in `.env` :

    ```bash
    cp .env.example .env
    ```

    Edit `CRAWLER_EMAIL` and `CRAWLER_PASSWORD` matching your Le Monde's credentials (we recommend a premium account to avoid any limit)

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
    CRAWLER_EMAIL='...' CRAWLER_PASSWORD='...' python3 ./scripts/crawler.py
    ```

## Ideas

- You might be interested in [Prefect](https://prefect.io) to automate this crawling task each day
