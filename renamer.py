from datetime import datetime
from glob import glob
from os import makedirs
from re import findall
from shutil import move
from sys import base_prefix, prefix
from threading import Lock, Thread
from typing import Callable

from bs4 import BeautifulSoup, Tag
from requests import get

# Shared dictionary to store results
results: dict[int, dict[int, str]] = {}
lock = Lock()

S1_END = 215
S2_END = 335


def logit(msg: str):
    with open("rebelde.log", "a+") as f:
        print(msg, file=f)


def find_episode_names(season: int):
    # Get TVDB page
    res = get(url=f"https://thetvdb.com/series/rebelde/seasons/official/{season}")
    res.raise_for_status()

    # Locate episode table
    soup = BeautifulSoup(res.text, "html.parser")
    episode_div = soup.find_all(attrs={"id": "episodes"})
    episode_table: Tag
    for div in episode_div:
        if not isinstance(div, Tag):
            continue

        find_table = div.find("table")
        if find_table and isinstance(find_table, Tag):
            episode_table = find_table
            break

    if not episode_table:
        print(f"Oh no, failed on season {season}")
        return

    # Extract episode data from table
    rows = episode_table.find_all("tr")
    cells = [row.find_all("td")[:2] for row in rows]
    cells = [pair for pair in cells if len(pair) == 2]

    # Formatter for episode number
    ep_nr: Callable[[Tag], int] = lambda cell: (
        int(findall("S[0-9]+E([0-9]+)", cell_str)[0])
        if (cell_str := cell.string) is not None
        else -1
    )

    # Formatter for episode title
    ep_title: Callable[[Tag], str] = lambda cell: (
        a_tag.string.strip()
        if isinstance((a_tag := cell.find("a")), Tag) and a_tag.string
        else "Title not found"
    )

    # Iterate through episode data and format
    episode_names = {ep_nr(cell0): ep_title(cell1) for [cell0, cell1] in cells}

    with lock:
        results[season] = episode_names


def rename_episode(ep: str):
    ep_nr = int(findall("Capitulo ([0-9]+).*", ep)[0])
    season = 1
    if ep_nr > S2_END:
        ep_nr = ep_nr - S2_END
        season = 3
    elif ep_nr > S1_END:
        ep_nr = ep_nr - S1_END
        season = 2

    try:
        move(
            src=ep,
            dst=f's{"{:02d}".format(season)}/S{"{:02d}".format(season)}E{"{:03d}".format(ep_nr)} - {results[season][ep_nr]}.mp4',
        )
    except Exception as err:
        print(f"Could not rename episode {ep}")
        logit(
            f"ERROR Renaming episode {ep}. Found ep_nr={ep_nr}, season={season}.\nerr: {err}"
        )


if __name__ == "__main__":
    threads = []
    logit(f"Started at {datetime.now()}")
    if prefix == base_prefix:
        logit(f"ERROR: not in venv. prefix={prefix}; base_prefix={base_prefix}")
        print("FATAL: Not in venv. Terminating")
        exit(1)

    for i in range(1, 4):
        makedirs(f's{"{:02d}".format(i)}', exist_ok=True)
        thread = Thread(target=find_episode_names, kwargs=({"season": i}))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    files = glob("./Downloaded/*.mp4")
    for file in files:
        rename_episode(file)

    print("Si soy rebelde es que quizás nadie me conoce bien")
    logit(f"Finished at {datetime.now()}")
