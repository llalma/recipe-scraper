import time

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import requests
from typing import NamedTuple

class Ingredient(NamedTuple):
    name: str
    amount: str

    def __str__(self):
        return f'Item: {self.name} Amount: {self.amount}'

wait_time = 50

def get_recipe_links(driver, page_url):
    """
    Get the recipe links
    """

    # GoTo page and wait for required elements to load
    driver.get(page_url)
    WebDriverWait(driver, wait_time).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "h2[data-recipe-card-title='true']")))

    # Get all elements which is a recipe title
    recipe_titles = driver.find_elements(By.CSS_SELECTOR, "h2[data-recipe-card-title='true']")

    return [recipe.find_element_by_xpath('..').get_attribute("href") for recipe in recipe_titles]

def get_recipe_data(driver, recipe_url):

    #Get page data
    driver.get(recipe_url)

    #Wait for page title to appear
    WebDriverWait(driver, wait_time).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "h1[data-recipe-title='true']")))

    #Get recipe title
    recipe_title = driver.find_element(By.CSS_SELECTOR, "h1[data-recipe-title='true']").text + ' ' + driver.find_element(By.CSS_SELECTOR, "h3[data-recipe-headline='true']").text

    #Get nutrion information if I care at somepoint

    #Get Ingredients
    ingredients = driver.find_element(By.CSS_SELECTOR, 'section[data-recipe-ingredients="true"]').find_elements(By.TAG_NAME, "li")
    ingredients = [Ingredient(*ingredient.text.split('\n')) for ingredient in ingredients]

    #Get pantry items
    pantry_items = ''
    if len(driver.find_elements_by_tag_name('ul')) > 1:
        pantry_items = driver.find_elements_by_tag_name('ul')[1].text.split('\n')[0].split(',')

    #Click "Show Cooking Steps"
    unhide_steps_button = driver.find_element(By.CSS_SELECTOR, 'button[data-test-id="toggle-cooking-steps"]')
    driver.execute_script("arguments[0].scrollIntoView();", unhide_steps_button)
    unhide_steps_button.click()

    #Get Steps
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'ol'))).text
    steps = driver.find_element_by_tag_name('ol').find_elements_by_tag_name("p")
    steps = [step.text for step in steps]

    return {
        'Title': recipe_title,
        'Link': recipe_url,
        'Ingredients': ingredients,
        'Pantry Items': pantry_items,
        'Steps': steps
    }

def stringify_recipies(recipies):

    output = []
    format = "Title: {0}\n" \
             "Ingredients: \n{1}\n" \
             "Pantry Items: \n{2}\n" \
             "Link: {4}\n"

    for recipe in recipies:
        output.append(format.format(recipe['Title'],
                          '\n'.join(map(lambda i: f"\t{i}", recipe['Ingredients'])),
                          '\n'.join(map(lambda i: f"\t{i}", recipe['Pantry Items'])),
                          recipe['Steps'],
                          recipe['Link']))

    return '\n\n'.join(output)


def send_email(recipies):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart()
    msg['From'] = 'lhulsmanbenson@gmail.com'
    msg['To'] = 'lhulsmanbenson@gmail.com'
    msg['Subject'] = 'This weeks Recipies'
    message = stringify_recipies(recipies)
    msg.attach(MIMEText(message))

    mailserver = smtplib.SMTP('smtp.gmail.com', 587)
    # identify ourselves to smtp gmail client
    mailserver.ehlo()
    # secure our email with tls encryption
    mailserver.starttls()
    # re-identify ourselves as an encrypted connection
    mailserver.ehlo()
    mailserver.login('lhulsmanbenson@gmail.com', 'dvfuoovbcdtqpdiu')

    mailserver.sendmail('lhulsmanbenson@gmail.com', 'lhulsmanbenson@gmail.com', msg.as_string())

    mailserver.quit()


def main():
    url = r'https://www.everyplate.com.au/weekly-menu'
    driver = webdriver.Chrome('./chromedriver')

    recipe_links = get_recipe_links(driver, url)

    #Delete cookies otherwise website prevents loading of the sepcific recipem if the list of the weekly recipies was just visited
    driver.delete_all_cookies()

    recipies = []
    for recipe in recipe_links:
        time.sleep(30)
        recipies.append(get_recipe_data(driver, recipe))

    send_email(recipies)

    x=1


if __name__ == '__main__':
    main()