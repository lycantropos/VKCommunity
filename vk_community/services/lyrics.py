import re
import urllib.parse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver

from vk_community.config import (MUSIXMATCH_URL, MUSIXMATCH_ELEMENT_CLASS_NAME,
                                 LYRICS_WIKIA_URL, LYRICS_WIKIA_ELEMENT_CLASS_NAME,
                                 AZLYRICS_URL, AZLYRICS_ELEMENT_XPATH, GENIUS_URL,
                                 GENIUS_ELEMENT_XPATH)


def load_lyrics_from_musixmatch(artist: str, title: str,
                                web_driver: WebDriver) -> str:
    main_window = open_new_tab(web_driver)

    url = get_musixmatch_url(artist, title)
    open_url(url, web_driver)

    try:
        lyrics_blocks = web_driver.find_elements_by_class_name(
            MUSIXMATCH_ELEMENT_CLASS_NAME
        )
        lyrics_blocks = [lyrics_block.text
                         for lyrics_block in lyrics_blocks]
    except TimeoutException:
        lyrics_blocks = list()
    finally:
        close_tab(main_window, web_driver)

    lyrics = '\n'.join(lyrics_blocks)
    return lyrics


def get_musixmatch_url(artist: str, title: str) -> str:
    search_res = re.search(r' \(feat\. .+\)$', title)
    if search_res:
        features = search_res.group(0)
        artist += features
        title = title.replace(features, '')
    artist = '-'.join(re.sub('\W+', ' ', artist).strip().split(' '))
    title = '-'.join(re.sub('\W+', ' ', title).strip().split(' '))
    track_path = '/'.join([artist, title])
    url = urllib.parse.urljoin(MUSIXMATCH_URL, track_path)
    return url


def load_lyrics_from_wikia(artist: str, title: str,
                           web_driver: WebDriver) -> str:
    main_window = open_new_tab(web_driver)

    url = get_wikia_url(artist, title)
    open_url(url, web_driver)

    try:
        lyrics_blocks = web_driver.find_elements_by_class_name(
            LYRICS_WIKIA_ELEMENT_CLASS_NAME
        )
        lyrics_blocks = [lyrics_block.text.replace('<br>', '\n')
                         for lyrics_block in lyrics_blocks]
    except TimeoutException:
        lyrics_blocks = list()
    finally:
        close_tab(main_window, web_driver)

    lyrics = '\n'.join(lyrics_blocks)
    return lyrics


def get_wikia_url(artist: str, title: str) -> str:
    track_path = ':'.join([artist, title])
    url = urllib.parse.urljoin(LYRICS_WIKIA_URL, track_path)
    return url


def load_lyrics_from_azlyrics(artist: str, title: str,
                              web_driver: WebDriver) -> str:
    main_window = open_new_tab(web_driver)

    url = get_azlyrics_url(artist, title)
    open_url(url, web_driver)

    try:
        lyrics_blocks = web_driver.find_elements_by_xpath(
            AZLYRICS_ELEMENT_XPATH
        )
        lyrics_blocks = [lyrics_block.text
                         for lyrics_block in lyrics_blocks]
    except TimeoutException:
        lyrics_blocks = list()
    finally:
        close_tab(main_window, web_driver)

    lyrics = '\n'.join(lyrics_blocks)
    return lyrics


def get_azlyrics_url(artist: str, title: str) -> str:
    search_res = re.search(r' \(feat\. .+\)$', title)
    if search_res:
        features = search_res.group(0)
        title = title.replace(features, '')
    artist = re.sub('\W+', '', artist.lower()).strip()
    title = re.sub('\W+', '', title.lower()).strip() + '.html'
    track_path = '/'.join([artist, title])
    url = urllib.parse.urljoin(AZLYRICS_URL, track_path)
    return url


def load_lyrics_from_genius(artist: str, title: str,
                            web_driver: WebDriver) -> str:
    main_window = open_new_tab(web_driver)

    url = get_genius_url(artist, title)
    open_url(url, web_driver)

    try:
        lyrics_blocks = web_driver.find_elements_by_xpath(
            GENIUS_ELEMENT_XPATH
        )
        lyrics_blocks = [lyrics_block.text
                         for lyrics_block in lyrics_blocks]
    except TimeoutException:
        lyrics_blocks = list()
    finally:
        close_tab(main_window, web_driver)

    lyrics = '\n'.join(lyrics_blocks)
    return lyrics


def get_genius_url(artist: str, title: str) -> str:
    search_res = re.search(r' \(feat\. .+\)$', title)
    if search_res:
        features = search_res.group(0)
        title = title.replace(features, '')
    artist = '-'.join(
        re.sub('\W+', ' ', artist.replace('.', '').capitalize()).strip().split(' '))
    title = '-'.join(
        re.sub('\W+', ' ', title.replace('.', '').lower()).strip().split(' '))
    track_path = '-'.join([artist, title, 'lyrics'])
    url = urllib.parse.urljoin(GENIUS_URL, track_path)
    return url


def open_new_tab(web_driver: WebDriver):
    while True:
        try:
            main_window = web_driver.current_window_handle
            web_driver.execute_script("window.open('','_blank');")
            new_window = web_driver.window_handles[-1]
            web_driver.switch_to.window(new_window)
            return main_window
        except TimeoutException:
            continue


def open_url(url: str, web_driver: WebDriver):
    try:
        web_driver.get(url)
        return
    except TimeoutException:
        while True:
            try:
                web_driver.execute_script("window.stop();")
                return
            except TimeoutException:
                continue


def close_tab(window_name: str, web_driver: WebDriver):
    while True:
        try:
            web_driver.close()
            web_driver.switch_to.window(window_name)
            return
        except TimeoutException:
            continue
