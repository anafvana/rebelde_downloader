from requests import get
from bs4 import BeautifulSoup, Tag
from re import findall
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from os.path import isfile
from sys import base_prefix, prefix


def logit(msg: str):
    with open("rebelde.log", "a+") as f:
        print(msg, file=f)


def find_episode_pages(url: str) -> list[str]:
    res = get(url=url)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")
    videoboxes = soup.find_all(attrs={"class": "videobox"})
    pages: list[str] = []

    for videobox in videoboxes:
        if not isinstance(videobox, Tag):
            logit(
                f"""find_episode_pages() :: isinstance(videobox, Tag)
                ERROR: videobox element is of type {type(videobox)}, expected Tag
                Element:
                {videobox}"""
            )
            continue

        meta = videobox.find("a", attrs={"class": "title"}, href=True)
        if isinstance(meta, Tag):
            href_attr = meta["href"]
            href = href_attr if isinstance(href_attr, str) else href_attr[0]
            pages.append(href)
        else:
            logit(
                f"""find_episode_pages() :: isinstance(meta, Tag)
                ERROR: meta element is of type {type(meta)}, expected Tag
                Element:
                {meta}
                """
            )

    return pages


def find_download_link(url: str, driver: webdriver.Chrome) -> tuple[str, str]:
    driver.get(url)
    html = driver.page_source

    soup = BeautifulSoup(html, "html.parser")
    title = [
        x for x in soup.find_all("h2") if findall(r"(.*?Capitulo.*?)\n", x.string)
    ][0]
    title = (
        title.string.strip()
        .removeprefix("Rebelde - ")
        .removesuffix("Completo Hd")
        .strip()
    )
    video = soup.find_all("video")
    return (title, video[0]["src"])


def download_link(title: str, url: str):
    path = f"Downloaded/{title}.mp4"
    if isfile(path=path):
        return

    res = get(url)
    res.raise_for_status()

    with open(path, mode="wb+") as file:
        file.write(res.content)


def worker(page: int):
    print(f"Running worker for page {page} of 22")
    logit(f"{datetime.now()} - Start Thread@{page}")
    # From Series page, get link to episode pages
    url = f"https://enpantallas.com/?cat_name=Rebelde&op=search&per_page=20&page={page}"
    page_urls = find_episode_pages(url=url)

    # From episode pages, get video url and title
    try:
        # FOR DESKTOP (Tested on MacOS)
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()), options=options
        )

        # FOR SERVERS (Tested on RH server) - REQUIRES MANUAL INSTALL
        # options = Options()
        # options.add_argument("--headless")
        # options.add_argument("--no-sandbox")
        # options.add_argument("--disable-dev-shm-usage")
        # driver = webdriver.Chrome(
        #     service=ChromeService(executable_path="/usr/bin/chromedriver"),
        #     options=options,
        # )

    except Exception as err:
        print(f"Failed to create driver @Thread{page}")
        logit(f"ERROR @Thread{page} - Could not create driver\n{err}")

    episode_links = []
    for page_url in page_urls:
        try:
            episode_links.append(find_download_link(page_url, driver=driver))
        except Exception as err:
            print(
                f"Thread{page}: Failed {'at first item' if not episode_links else f'after {episode_links[-1][0]}'}. URL: {page_url}"
            )
            logit(f"Failed @Thread{page} {page_url}:\n{err}")
    driver.close()

    for title, page_url in episode_links:
        print(f"Starting download @Thread{page}")
        try:
            download_link(title=title, url=page_url)
            print(f"Downloaded {title}")
        except Exception as err:
            msg = f"\nError @ {title}:\n{err}\n"
            print(msg)
            logit(msg)


if __name__ == "__main__":
    logit(f"Started at {datetime.now()}")
    if prefix == base_prefix:
        logit(f"ERROR: not in venv. prefix={prefix}; base_prefix={base_prefix}")
        print("FATAL: Not in venv. Terminating")
        exit(1)

    pool = ThreadPoolExecutor(max_workers=2)

    for p in range(1, 23):
        pool.submit(worker, page=p)

    pool.shutdown(wait=True)

    print("Y soy rebelde cuando no sigo a los demás")
    logit(f"Finished at {datetime.now()}")
