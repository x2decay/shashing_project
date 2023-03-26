from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
# BeautifulSoup (and requests) might be necessary in the future
# from bs4 import BeautifulSoup
# import requests
import pyautogui as pag
from copy import deepcopy as clone
import time
from src.base.playvs_objects import *


def scrape(driver, teams_to_scrape):
    url = 'https://app.playvs.com/app/standings'
    # If necessary, use Login info for debugging
    email = 'lkryvenko@cherrycreekschools.org'
    password = 'Dogunderfifthdollartree.'
    actions = ActionChains(driver)
    driver.get(url)

    # Login
    driver.implicitly_wait(2)
    email_input = driver.find_element(By.CSS_SELECTOR, 'input[name="email"]')
    password_input = driver.find_element(By.CSS_SELECTOR, 'input[name="password"]')
    email_input.send_keys(*list(email))
    password_input.send_keys(*list(password))
    password_input.send_keys(Keys.ENTER)

    # Switch to Dark Mode
    driver.implicitly_wait(5)
    settings = driver.find_element(By.CSS_SELECTOR, 'div[data-cy="account-settings-navigation"]')
    settings.click()
    driver.implicitly_wait(2)
    dark = driver.find_elements(By.CSS_SELECTOR, 'li[role="menuitem"]')[6]
    dark.click()
    dark.send_keys(Keys.ESCAPE)

    # Switch to Smash
    driver.implicitly_wait(5)
    if len(driver.find_elements(By.CSS_SELECTOR, 'button[data-cy="Colorado CHSAA League of Legends"]')) > 0:
        league = driver.find_element(By.CSS_SELECTOR, 'button[data-cy="Colorado CHSAA League of Legends"]')
        time.sleep(.5)
        league.click()
        driver.implicitly_wait(2)
        smash = driver.find_element(By.CSS_SELECTOR, 'li[data-cy="Colorado CHSAA Super Smash Bros.™ Ultimate"]')
        smash.click()

    # Switch to Spring 2023
    driver.implicitly_wait(5)
    if len(driver.find_elements(By.CSS_SELECTOR, 'button[data-cy="Fall 2022"]')) > 0:
        season = driver.find_element(By.CSS_SELECTOR, 'button[data-cy="Fall 2022"]')
        season.click()
        driver.implicitly_wait(2)
        spring23 = driver.find_element(By.CSS_SELECTOR, 'li[data-cy="Spring 2023"]')
        spring23.click()

    # Switch to Regular Season
    driver.implicitly_wait(5)
    if len(driver.find_elements(By.CSS_SELECTOR, 'button[data-cy="Playoffs')) > 0:
        season = driver.find_element(By.CSS_SELECTOR, 'button[data-cy="Playoffs"]')
        season.click()
        driver.implicitly_wait(2)
        spring23 = driver.find_element(By.CSS_SELECTOR, 'li[data-cy="Regular Season"]')
        spring23.click()

    # Scrape the Teams
    driver.implicitly_wait(2)
    body = driver.find_element(By.XPATH, '//div[..[p[contains(text(),"Overall")]]]')
    # Makes a list of  based on the names that were passed into the method
    teams = {}
    all_teams = body.find_elements(By.CSS_SELECTOR, 'div[role="row"]')
    while len(teams_to_scrape) > 0 and len(all_teams) > 0:
        name = all_teams[0].find_elements(By.XPATH, 'div//a/p[text()]')[0].text
        if name in teams_to_scrape:
            teams[name] = Team(all_teams[0])
            teams_to_scrape.remove(name)
        all_teams.pop(0)

    # Loop through the Teams that where passed into the method
    for team in teams.values():
        # Opens Team Page
        driver.get(team.href)
        # Ensures All Matches are Selected
        driver.implicitly_wait(5)
        more = driver.find_elements(By.XPATH, '//span/div[contains(text(),"Show More")]')
        if len(more) > 0:
            more[0].click()
        # Goes through Every Match
        time.sleep(1)
        driver.implicitly_wait(2)
        matches = driver.find_elements(By.XPATH, '//div[@data-cy="teamMatchHistoryOpponent"]//*[img]')
        for match in matches:
            # Opens and Switches to Match
            match.click()
            windows = driver.window_handles
            driver.switch_to.window(windows[1])
            # Scrape Player Data
            driver.implicitly_wait(5)
            home_team = driver.find_element(By.XPATH, f'//div[div[span[a[contains(text(), "{team.name}")]]]]')
            last_team = home_team
            # since page first loads in the wrong orientation, this waits out until it is correct
            while last_team == home_team:
                last_team = home_team
                home_team = driver.find_element(By.XPATH, f'//div[div[span[a[contains(text(), "{team.name}")]]]]')
            alignment = home_team.get_attribute('style')
            home = alignment == 'text-align: left;'
            driver.implicitly_wait(5)
            xpath = '//div[div[div[div[div[div[p[contains(text(), "Series")]]]]]]]'
            series = driver.find_elements(By.XPATH, xpath)
            for ser in series:
                name = ser.find_elements(By.XPATH, './/p[..[..[p]]]')[0 if home else 1].text
                game_stages = ser.find_elements(By.XPATH, './/p[..[p[contains(text(), "Game")]]]')
                stages = [game_stages[x * 2 + 1].text for x in range(int(len(game_stages) / 2))]  # odd indices only
                triangles = ser.find_elements(By.CSS_SELECTOR, 'div[data-cy="leftTriangle"]')[1:]
                results = [(x.value_of_css_property('visibility') == 'visible') == home for x in triangles]
                # TODO:
                #  - Determine the characters in every game
                #    - Hover over the letter icon
                #    - Find the character name in html
                #    - Commented code below could be useful (place into loop)
                # https://stackoverflow.com/questions/74342917/extract-text-on-mouse-hover-in-python-selenium
                # desired_elem = wait.until(
                #  EC.visibility_of_element_located((By.CSS_SELECTOR, '.SdgPerformanceBar__Block-sc-1yl1q71-2.fBQLcJ')))
                # actions.move_to_element(desired_elem).perform()
                # tt1_text = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, tooltip1))).text
                player_chars = []
                opponent_chars = []
                for g in ser.find_elements(By.XPATH, './/div[div[div[p[contains(text(),"Game")]]]]'):
                    circles = g.find_elements(By.XPATH, './/div/div/div/div[p]')
                    i = 0
                    for circle in circles:
                        mouse_pos = pag.position()
                        last_pos = clone(mouse_pos) + (1, 1)
                        while last_pos != mouse_pos:
                            last_pos = clone(mouse_pos)
                            driver.execute_script(f'window.scrollTo(0, {circle.location["y"]})')
                            playvs = driver.find_element(By.XPATH, '//p[contains(text(), "PlayVS")]')
                            actions.move_to_element(playvs).perform()
                            time.sleep(.05)
                            actions.move_to_element(circle).perform()
                            time.sleep(.2)
                            mouse_pos = pag.position()
                        driver.implicitly_wait(5)
                        xpath = f'/html/body/div[{"6" if team.name == "Creek Smash 1" else "4"}]/div/div'
                        character = driver.find_element(By.XPATH, xpath).text
                        print(f'{home} == {i % 2 == 0} -> {home == (i % 2 == 0)}')
                        if home == (i % 2 == 0):
                            player_chars.append(character)
                        else:
                            opponent_chars.append(character)
                        i += 1
                        # input('↳')
                games = list(zip(player_chars, opponent_chars, stages, results))
                print('Games:')
                for game in games:
                    print('\t'.join(map(str, game)))
                if name not in team.players:
                    team.players[name] = Player(name)
                team.players[name].games += games
            # uncomment "input('↳')" to pause between matches
            # input('↳')
            # Close Match and Return to Team
            driver.close()
            driver.switch_to.window(windows[0])
    driver.quit()

    return teams
