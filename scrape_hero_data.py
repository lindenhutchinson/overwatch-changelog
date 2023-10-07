import requests
from bs4 import BeautifulSoup
import re
import json
import os

# Function to scrape hero URLs from the main heroes page
def scrape_hero_urls():
    heroes_url = 'https://overwatch.fandom.com/wiki/Heroes'

    try:
        response = requests.get(heroes_url)
        if response.status_code == 200:
            page_content = response.text

            # Define the regex pattern to match hero URLs
            hero_url_pattern = r"href=\"(http:\/\/overwatch\.gamepedia\.com\/\w+)\"" 

            # Use the findall function to extract all matched URLs
            hero_urls = re.findall(hero_url_pattern, page_content)

            return hero_urls

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []

# Function to fetch and parse the HTML content of a hero's page
def fetch_hero_html(hero_url):
    try:
        response = requests.get(hero_url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to retrieve data from {hero_url}. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

# Function to extract hero name from HTML content
def extract_hero_name(soup):
    hero_name = soup.find('h1').text.strip()
    return hero_name

# Function to extract ability data from HTML content
def extract_ability_data(soup):
    ability_boxes = soup.find_all(class_='ability_details_main')
    
    hero_abilities = []
    for ability_box in ability_boxes:
        # Extract ability name and keybind
        ability_name, keybind = extract_ability_name_and_keybind(ability_box)
        
        # Extract ability details
        stats_dict = extract_ability_details(ability_box)
        
        hero_abilities.append({
            'name': ability_name,
            'keybind': keybind,
            'stats': stats_dict
        })
    
    return hero_abilities

# Function to extract ability name and keybind from an ability box
def extract_ability_name_and_keybind(ability_box):
    ability_name = ability_box.find(class_='abilityHeader').text.strip()
    keybind = 'LCLICK'
    if 'Alt Fire' in ability_name:
        keybind = 'RCLICK'
        ability_name = ability_name.rstrip('Alt Fire')
    else:
        if check_bind := re.findall(r'[a-z]([A-Z]+)$', ability_name):
            keybind = check_bind[0]
            ability_name = ability_name.rstrip(keybind)
    
    return ability_name, keybind

# Function to extract ability details from an ability box
def extract_ability_details(ability_box):
    summary_info = ability_box.find(class_='summaryInfoAndImage')
    ability_info = summary_info.find_next_sibling('div')
    stats_dict = {}
    
    for stat_div in ability_info.find_all('div'):
        stats = stat_div.find_all('div')
        if len(stats) == 2:
            stat_key, stat_val = stats
            stat_span = stat_key.find('span')
            stat_key = stat_key.get_text().rstrip(':')
            
            stat_title = stat_span.attrs.get('title') if stat_span else None
            stat_val = stat_val.get_text().strip()
            stat_val = stat_val.replace('–', '-')
            
            if "✓" in stat_val:
                stat_val = True
            elif "✕" in stat_val:
                stat_val = False
            elif '∞' in stat_val:
                stat_val = 'inf'
            
            stats_dict[stat_key] = {
                'value': stat_val,
                'info': stat_title,
            }
    
    return stats_dict

# Function to extract ability changes from HTML content
def extract_changelog(soup):
    changelog_table = soup.find_all(class_="wds-tab__content wds-is-current")[-1]
    changelog = []
    if changelog_table: 
        for date, desc in zip(changelog_table.find_all(id="patch")[1:], changelog_table.find_all(id="description")[1:]):
            # dev comments by in a div or a p element. there's no consistency, it's madness
            
            dev_comments = desc.find('div')
            if dev_comments:
                dev_comments = dev_comments.get_text()
            else:
                dev_comments = ''
            ability_changes = desc.find_all('p')
            changes_list = []
            for change in ability_changes:
                ability_change_ul = change.next_sibling.next_sibling
                
                if ability_change_ul:
                    # if this element isn't followed by a ul, it must be dev comments in a p element
                    if not ability_change_ul.name == 'ul':
                        dev_comments = change.get_text()
                    else:
                        if ability_name := change.find_all('a'):
                            ability_name = ability_name[-1].get_text()   
                        else:
                            # when this happens, its shields, health, armour or a new ability
                            # fuggit, just say its unknown
                            dev_comments += f"\n{change.get_text()}"
                            ability_name = 'Unknown'
                            
                        ability_change = [text.get_text() for text in ability_change_ul.find_all('li')]
                        changes_list.append({
                            'ability':ability_name,
                            'changes':ability_change
                        })
                  
            changelog.append({
                'date': date.get_text(),
                'dev_comments': dev_comments,
                'ability_changes':changes_list
            })
        
    return changelog

# Function to scrape hero information and store in JSON format
def scrape_hero_info(hero_url):
    results_dir = os.path.abspath('./heroes')
    if not os.path.exists(results_dir):
        os.mkdir(results_dir)
        
    html_content = fetch_hero_html(hero_url)
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        hero_name = extract_hero_name(soup)
        hero_abilities = extract_ability_data(soup)
        hero_changelog = extract_changelog(soup)
        
        hero_details = {
            'Name': hero_name,
            'Abilities': hero_abilities,
            'Changelog': hero_changelog
        }
        
        with open(os.path.join(results_dir, f"{hero_name}.json"), "w+") as fn:
            json.dump(hero_details, fn, indent=4)

if __name__ == "__main__":
    hero_urls = scrape_hero_urls()
    for hero_url in hero_urls:
        print(hero_url)
        scrape_hero_info(hero_url)
