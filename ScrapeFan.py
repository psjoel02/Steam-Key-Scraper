import time

import requests
import csv
import urllib.parse
import edgedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import NoSuchElementException


def ScrapeFan(ID):

    Fan_url_start = 'https://www.fanatical.com/en/search?search='
    Fan_url_end = '&drm=steam'
    sub1 = "discount_final_price\">"
    sub2 = "</div></div></div>"
    FanPrice = 0.0
    WishlistAvailable = 1
    game_name = ''
    chars = set('abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789')
    Titles = ['Name', 'Review Summary', 'Review Score', '# of Reviews',
              'Release Date', 'Type', 'Price']

    data_file = open('Fanatical_Wishlist.csv', 'w', encoding='utf-8')
    csv_writer = csv.writer(data_file)
    csv_writer.writerow(Titles)
    # open data file for writing Fanatical and Steam information

    print("\nWould you like results more or less accurate?\n"
          "Less accurate results may include games that Fanatical does not have,\n"
          "whereas more accurate will use the official Steam price if the exact game is not found.\n")
    accuracy = input("Type 0 for less accurate and 1 for more accurate: ")

    while (len(accuracy) != 1 or not accuracy.isdigit()) and (accuracy != 0 or accuracy != 1):
        accuracy = input("\nYour choice must be a 0 or 1 digit. Please try again: ")

    edgedriver_autoinstaller.install()
    Edge_options = Options()
    Edge_options.add_argument("--window-size=1920,1080")
    Edge_options.add_argument("--disable-extensions")
    Edge_options.add_argument("--proxy-server='direct://'")
    Edge_options.add_argument("--proxy-bypass-list=*")
    Edge_options.add_argument("--start-maximized")
    Edge_options.add_argument('--headless')
    Edge_options.add_argument('--disable-gpu')
    Edge_options.add_argument('--disable-dev-shm-usage')
    Edge_options.add_argument('--no-sandbox')
    Edge_options.add_argument('--ignore-certificate-errors')
    Edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    Edge_options.add_argument('log-level=3')
    driver = webdriver.Edge(options=Edge_options)
    driver.get("http://www.python.org")
    assert "Python" in driver.title
    # use webdriver bundled with script

    response = requests.get('https://store.steampowered.com/wishlist/profiles/' + ID + '/wishlistdata')
    json_response = response.json()

    for game in json_response:
        try:
            game_parsed = \
                urllib.parse.quote(
                    json_response.get(game).get('name').replace('™', '').replace('®', '').replace('&amp;', '&'))
            URL = Fan_url_start + game_parsed + Fan_url_end
            driver.get(URL)
            time.sleep(3)
        except AttributeError:
            print("Wishlist data could not be found. Double check that your wishlist is public."
                  "\nLink for Steam's wishlist support: "
                  "https://help.steampowered.com/en/faqs/view/0CAD-3B4D-B874-A065#wl-whosee")
            WishlistAvailable = 0
            driver.close()

        # convert Steam name into % URL format for Fanatical
        if WishlistAvailable == 1:
            try:
                exact_name = driver.find_elements("xpath", "//a[contains(@class,'faux-block-link__overlay-link')]")
                i = 0
                for x in exact_name:
                    if i == 63:
                        exact_name = x.get_attribute('href')
                        exact_name = exact_name.rsplit('/', 1)[1].replace('-', ' ').upper()

                        # match characters between Steam listing and Fanatical top result URL
                        break
                    i += 1
            except NoSuchElementException:
                exact_name = 'DNE'
            try:
                result = driver.find_elements("xpath", "//span[contains(@class,'card-price')]")
                prices = ''
                for x in result:
                    if "$" in x.text:
                        prices = x.text
                        break
                # if card-price element was found (any result exists)
                if result is not None and WishlistAvailable == 1:
                    # if there is a result on Fanatical for the game
                    # double check if there is a sale price for the game
                    if accuracy == '0':
                        # if user selected lower accuracy (if result on Fanatical exists)
                        gameList = [
                            json_response.get(game).get('name').replace('™', '').replace('®', '').replace('&amp;', '&'),
                            json_response.get(game).get('review_desc'),
                            json_response.get(game).get('reviews_percent'),
                            json_response.get(game).get('reviews_total'),
                            json_response.get(game).get('release_string'),
                            json_response.get(game).get('type')]

                        # add Steam data to list
                        if not json_response.get(game).get('is_free_game'):
                            try:
                                gameList.append(prices)
                                FanPrice += float(prices.replace("$", ''))
                            except ValueError:
                                try:
                                    # if exact match was not found, use Steam result (more accurate)
                                    price = (str(json_response.get(game).get('subs')[0]))
                                    idx1 = price.index(sub1)
                                    idx2 = price.index(sub2)
                                    res = '$'
                                    for idx in range(idx1 + len(sub1) + 1, idx2):
                                        res = res + price[idx]
                                    gameList.append(res)
                                    FanPrice += float(res.replace("$", ''))
                                except IndexError:
                                    # if no steam price is available it has not been released
                                    gameList.append("N/A")
                        else:
                            # if it is a free game, use that result
                            gameList.append('$0.00')
                        # print results for testing, replace with below
                        csv_writer.writerow(gameList)
                        # req = requests.get(URL)
                    else:
                        # if user selected higher accuracy (only exact matches on Fanatical)
                        gameList = [
                            json_response.get(game).get('name').replace('™', '').replace('®', '').replace('&amp;', '&'),
                            json_response.get(game).get('review_desc'),
                            json_response.get(game).get('reviews_percent'),
                            json_response.get(game).get('reviews_total'),
                            json_response.get(game).get('release_string'),
                            json_response.get(game).get('type')]

                        # add Steam data to list
                        if not json_response.get(game).get('is_free_game'):
                            # if exact match was not found, use Steam result (more accurate)
                            try:
                                if json_response.get(game).get('name').upper() in exact_name and exact_name != 'DNE':
                                    try:
                                        gameList.append(prices)
                                        FanPrice += float(prices.replace("$", ''))
                                        # initially try Fanatical results
                                    except IndexError:
                                        gameList.append("N/A")
                                else:
                                    try:
                                        # if it fails use Steam results
                                        price = (str(json_response.get(game).get('subs')[0]))
                                        idx1 = price.index(sub1)
                                        idx2 = price.index(sub2)
                                        res = '$'
                                        for idx in range(idx1 + len(sub1) + 1, idx2):
                                            res = res + price[idx]
                                        gameList.append(res)
                                        FanPrice += float(res.replace("$", ''))
                                    except IndexError:
                                        # if no steam price is available it has not been released
                                        gameList.append("N/A")
                            except IndexError:
                                try:
                                    # if it fails use Steam results
                                    price = (str(json_response.get(game).get('subs')[0]))
                                    idx1 = price.index(sub1)
                                    idx2 = price.index(sub2)
                                    res = '$'
                                    for idx in range(idx1 + len(sub1) + 1, idx2):
                                        res = res + price[idx]
                                    gameList.append(res)
                                    FanPrice += float(res.replace("$", ''))
                                except IndexError:
                                    # if no steam price is available it has not been released
                                    gameList.append("N/A")

                        else:
                            # if it is a free game, use that result
                            gameList.append('$0.00')
                        # print(list)
                        # print results for testing, replace with below
                        csv_writer.writerow(gameList)
                        # req = requests.get(URL)
                else:
                    # only used in extreme scenarios where no game at all is found in Fanatical's database
                    try:
                        print("Game not found on Fanatical: " + json_response.get(game).get('name'))
                    except AttributeError:
                        print("Fanatical data not found")

            except NoSuchElementException:
                # if Selenium fails, notify user that data was not found
                if WishlistAvailable == 1:
                    print("Data not found for: " + json_response.get(game).get('name'))
        else:
            break

    if WishlistAvailable == 1:
        TotalList = ['Total:', '', '', '', '', '', '$' + str("{:.2f}".format(FanPrice))]
        csv_writer.writerow('')
        csv_writer.writerow(TotalList)
        driver.close()
        data_file.close()

        print("\nData from Fanatical was entered in the Fanatical_Wishlist.csv file"
              "\nYour total from Fanatical is: $" + str("{:.2f}".format(FanPrice)))
