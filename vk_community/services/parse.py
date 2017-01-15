import logging
import re
from typing import Dict, Any, Iterable, Tuple, List

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import wait, expected_conditions
from vk_community.services.lyrics import open_url


def parse_from_vk_dev(url: str, web_driver: WebDriver):
    open_url(url, web_driver)
    waiter = wait.WebDriverWait(web_driver, 10)
    button_xpath = '//*[@id="dev_req_run_btn"]'
    waiter.until(expected_conditions.visibility_of_element_located(
        locator=(By.XPATH, button_xpath)))
    button = web_driver.find_element_by_xpath(button_xpath)
    button.click()
    waiter.until(expected_conditions.text_to_be_present_in_element(
        locator=(By.XPATH, button_xpath), text_='Run'))
    res = web_driver.find_element_by_xpath('//*[@id="dev_result"]')
    links = [element.get_attribute('href')
             for element in res.find_elements_by_tag_name('a')]
    json = load_vk_json(res.text)
    for item in json['response']['items']:
        for attachment in item.get('attachments', []):
            type_ = attachment['type']
            if type_ in {'photo', 'sticker'}:
                set_links_to_photo(attachment[type_], links)
            elif type_ in {'audio', 'doc'}:
                set_plain_link(attachment[type_], links)
            elif type_ == 'video':
                set_links_to_video(attachment[type_], links)
    return json


def load_vk_json(vk_json: str) -> Dict[str, Any]:
    if not (vk_json.startswith('{') and vk_json.endswith('}')):
        raise ValueError('JSON should be surrounded by braces.')
    vk_json = vk_json[1:-1].strip()
    lines = vk_json.split('\n')
    _, json = parse_object(lines)
    return json


def parse_object(lines: List[str]) -> Dict[str, Any]:
    res = dict()
    ind = 0
    while ind < len(lines):
        line = lines[ind]
        re_search = re.search('^"(\w+)": (-?\d|"|\[\{|\{)', line)
        if re_search is not None:
            key = re_search.group(1)
            value_type = re_search.group(2)
            next_ind = ind + 1
            if value_type == '{':
                inc, value = parse_object(lines[next_ind:])
                ind += inc
            elif value_type == '[{':
                inc, value = parse_list(lines[next_ind:])
                ind += inc
            elif re.match('^-?\d$', value_type):
                value = parse_number(line)
            else:
                lines[ind] = re.sub('^"\w+": "', '', line)
                inc, value = parse_string(lines[ind:])
                ind += inc

            res[key] = value
        ind += 1
        if line.startswith('}'):
            return ind, res
    return ind, res


def parse_list(lines: List[str]) -> List[Dict[str, Any]]:
    res = list()
    ind, value = parse_object(lines)
    res.append(value)
    while '}]' not in lines[ind - 1] and ind < len(lines):
        inc, value = parse_object(lines[ind:])
        res.append(value)
        ind += inc
    return ind, res


def parse_string(lines: List[str]) -> Tuple[int, str]:
    ind = 0
    for ind, line in enumerate(lines):
        if line.endswith('",') or line.endswith('"'):
            break
    lines[ind] = re.sub('",?$', '', lines[ind])
    value = '\n'.join(lines[: ind + 1])
    return ind, value


def parse_number(line: str) -> int:
    re_search = re.search('(?:^"\w+": )(-?\d+)', line)
    value = int(re_search.group(1))
    return value


def set_links_to_photo(raw_photo: Dict[str, Any], full_links: Iterable[str]):
    links_keys = [key for key in raw_photo.keys()
                  if key.startswith('photo')]
    for link_key in links_keys:
        link = raw_photo[link_key]
        raw_photo[link_key] = get_full_link(link, full_links)


def set_plain_link(raw_audio: Dict[str, Any], full_links: Iterable[str]):
    link = raw_audio['url']
    raw_audio['url'] = get_full_link(link, full_links)


def set_links_to_video(raw_video: Dict[str, Any], full_links: Iterable[str]):
    # set full links of video preview photos
    set_links_to_photo(raw_video, full_links)
    player_link = raw_video.get('player')
    if player_link is not None:
        raw_video['player'] = get_full_link(player_link, full_links)
    for key, link in raw_video.get('files', {}).items():
        raw_video['files'][key] = get_full_link(link, full_links)


def get_full_link(link: str, full_links: Iterable[str]):
    if '...' in link:
        link_parts = re.split('\.{3,}', link)
        try:
            link = next(full_link
                        for full_link in full_links
                        if all(link_part in full_link
                               for link_part in link_parts))
        except StopIteration as exc:
            logging.exception(exc)
    return link
