import re
import urllib.parse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from vk_community.config import (MUSIXMATCH_URL, MUSIXMATCH_ELEMENT_CLASS_NAME,
                                 LYRICS_WIKIA_URL, LYRICS_WIKIA_ELEMENT_CLASS_NAME,
                                 AZLYRICS_URL, AZLYRICS_ELEMENT_XPATH)


def load_lyrics_from_musixmatch(artist: str, title: str, web_driver: WebDriver):
    search_res = re.search(r' \(feat\. .+\)$', title)
    if search_res:
        features = search_res.group(0)
        artist += features
        title = title.replace(features, '')
    artist = '-'.join(re.sub('\W+', ' ', artist).strip().split(' '))
    title = '-'.join(re.sub('\W+', ' ', title).strip().split(' '))
    track_path = '/'.join([artist, title])
    url = urllib.parse.urljoin(MUSIXMATCH_URL, track_path)
    try:
        web_driver.get(url)
    except TimeoutException:
        pass
    finally:
        try:
            web_driver.execute_script("window.stop();")
            lyrics_blocks = web_driver.find_elements_by_class_name(
                MUSIXMATCH_ELEMENT_CLASS_NAME
            )
            lyrics_blocks = list(lyrics_block.text
                                 for lyrics_block in lyrics_blocks)
        except TimeoutException:
            lyrics_blocks = list()

    lyrics = '\n'.join(lyrics_blocks)
    return lyrics


def load_lyrics_from_wikia(artist: str, title: str, web_driver: WebDriver) -> str:
    track_path = ':'.join([artist, title])
    url = urllib.parse.urljoin(LYRICS_WIKIA_URL, track_path)
    try:
        web_driver.get(url)
    except TimeoutException:
        pass
    finally:
        try:
            web_driver.execute_script("window.stop();")
            lyrics_blocks = web_driver.find_elements_by_class_name(
                LYRICS_WIKIA_ELEMENT_CLASS_NAME
            )
            lyrics_blocks = list(lyrics_block.text.replace('<br>', '\n')
                                 for lyrics_block in lyrics_blocks)
        except TimeoutException:
            lyrics_blocks = list()

    lyrics = '\n'.join(lyrics_blocks)
    return lyrics


def load_lyrics_from_azlyrics(artist: str, title: str, web_driver: WebDriver) -> str:
    search_res = re.search(r' \(feat\. .+\)$', title)
    if search_res:
        features = search_res.group(0)
        title = title.replace(features, '')
    artist = re.sub('\W+', '', artist.lower()).strip()
    title = re.sub('\W+', '', title.lower()).strip() + '.html'
    track_path = '/'.join([artist, title])
    url = urllib.parse.urljoin(AZLYRICS_URL, track_path)
    try:
        web_driver.get(url)
    except TimeoutException:
        pass
    finally:
        try:
            web_driver.execute_script("window.stop();")
            lyrics_blocks = web_driver.find_elements_by_xpath(
                AZLYRICS_ELEMENT_XPATH
            )
            lyrics_blocks = list(lyrics_block.text
                                 for lyrics_block in lyrics_blocks)
        except TimeoutException:
            lyrics_blocks = list()

    lyrics = '\n'.join(lyrics_blocks)
    return lyrics
