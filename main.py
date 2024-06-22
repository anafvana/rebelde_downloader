from requests import get
from bs4 import BeautifulSoup, Tag
from re import findall
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime


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
    res = get(url)
    res.raise_for_status()

    with open(f"Downloaded/{title}.mp4", mode="wb+") as file:
        file.write(res.content)


def worker(page: int):
    print(f"Running worker for page {page} of 22")
    logit(f"{datetime.now()} - Start Thread@{page}")
    # From Series page, get link to episode pages
    url = f"https://enpantallas.com/?cat_name=Rebelde&op=search&per_page=20&page={page}"
    page_urls = find_episode_pages(url=url)

    # From episode pages, get video url and title
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=options
    )
    episode_links = []
    for page_url in page_urls:
        try:
            episode_links.append(find_download_link(page_url, driver=driver))
        except:
            logit(
                f"Thread{page}: Failed {'at first item' if not episode_links else f'after {episode_links[-1][0]}'}"
            )
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
    pool = ThreadPoolExecutor(max_workers=2)

    for p in range(1, 23):
        pool.submit(worker, page=p)

    pool.shutdown(wait=True)

    print("Y soy rebelde cuando no sigo a los demás")
    logit(f"Finished at {datetime.now()}")
