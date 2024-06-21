from requests import get
from bs4 import BeautifulSoup, Tag
from re import findall
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


def find_episode_pages() -> list[str]:
    res = get("https://enpantallas.com/category/Rebelde")
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")
    videoboxes = soup.find_all(attrs={"class": "videobox"})
    pages: list[str] = []

    for videobox in videoboxes:
        if not isinstance(videobox, Tag):
            print(
                f"""
                  ERROR: videobox element is of type {type(videobox)}, expected Tag
                  Element:
                  {videobox}
                """
            )
            continue

        href = videobox.find("a", attrs={"class": "title"}, href=True)["href"]
        pages.append(href)

    return pages


def find_download_link(url: str, driver) -> tuple[str, str]:
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
    pass


if __name__ == "__main__":
    # From Series page, get link to episode pages
    page_urls = find_episode_pages()

    # From episode pages, get video url and title
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=options
    )
    episode_links = []
    for url in page_urls:
        try:
            episode_links.append(find_download_link(url, driver=driver))
        except:
            print(
                f"Failed {'at first attempt' if not episode_links else f'after {episode_links[-1][0]}'}"
            )
    driver.close()
