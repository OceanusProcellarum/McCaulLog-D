from flask import Flask, render_template, request, redirect
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import requests
import math

# Much, much inspiration from the IMDb project: https://repl.it/@JoshManigsaca/IMDbday4#main.py

'''
SETUP
'''
app = Flask(__name__)

# Global variables
error_message = ''
representatives_display_list = [] # For display table
representatives_key_list = [] # For autocorrect and python
chosen_representative = ''
vote_result = {}

# Scrape representatives
representatives_url = 'https://www.house.gov/representatives'
representatives_page = requests.get(representatives_url)
representatives_html = BeautifulSoup(representatives_page.content, 'html.parser')
representatives = representatives_html.find_all('td',class_='views-field views-field-text-3 views-field-text-11')

# Sort only Texas reps
start_index = None
end_index = None
for i in range(len(representatives)):
  if representatives[i].a.text == "Gohmert, Louie":
    start_index = i
  if representatives[i].a.text == "Babin, Brian":
    end_index = i

# Add Texas reps to display list
for i in range(start_index, end_index + 1):
  representative_name = representatives[i].a.text
  representatives_display_list.append(representative_name)

# (Preliminary data scrape to create keys) Scrape records
default_url = 'https://clerk.house.gov/evs/2021/roll009.xml'
default_page = requests.get(default_url)
default_html = BeautifulSoup(default_page.content, 'html.parser')
default_votes = default_html.find_all('recorded-vote')

# Add Texas rep names to key list
for vote in default_votes:
  name = vote.legislator.attrs["sort-field"]
  if vote.legislator.attrs["state"] == "TX":
    representatives_key_list.append(name)

# Scrape to see how many total roll calls exist
    roll_url = 'https://clerk.house.gov/evs/2021/ROLL_000.asp'
    roll_page = requests.get(roll_url)
    roll_html = BeautifulSoup(roll_page.content, 'html.parser')
    total = roll_html.find_all('tr')

'''
WEBSITE PAGES
'''
# Main page
@app.route('/', methods=['GET'])
def index():

    return render_template(
        'index.html',
        representatives_display_list=representatives_display_list, error_message=error_message, representatives_key_list=representatives_key_list, vote_result=vote_result, chosen_representative=chosen_representative)

# Search function
@app.route('/search', methods=['POST'])
def search():
    global error_message
    global vote_result
    global chosen_representative

    # Reset
    vote_result = {}
    chosen_representative = ''
    error_message = get_representative_info(request.form.get('vote-record-search'))

    return redirect('/')

'''
MISCELLANEOUS FUNCTIONALITY
'''
# Search functionality
def get_representative_info(representative):
    global error_message
    global vote_result
    global chosen_representative

    # Scrape data about rep from record sites per roll call
    if representative in representatives_key_list:
      chosen_representative = representative
      for number in range(1, len(total)):
        # Scrape record site
        vote_url = 'https://clerk.house.gov/evs/2021/roll'+str(number).zfill(3)+'.xml'
        # (REFERENCE) https://www.csestack.org/python-padding-number-string/
        vote_page = requests.get(vote_url)
        votes_html = BeautifulSoup(vote_page.content, 'html.parser')
        votes = votes_html.find_all('recorded-vote')

        # Add Texas rep names to key list
        for vote in votes:
          name = vote.legislator.attrs["sort-field"]
          if name == chosen_representative:
            # Get data
            code = votes_html.find('legis-num')
            description = votes_html.find('vote-desc')
            question = votes_html.find('vote-question')
            action_date = votes_html.find('action-date')
            decision = vote.vote.text

            # Prettify? data?
            information = [code, description, question, action_date]
            for info in information:
              info_index = information.index(info)
              try:
                information[info_index] = info.get_text()
                if info.get_text() == '':
                  information[info_index] = "None given"
              except:
                information[info_index] = "None given"
            information.append(decision)

            # Update main dict with data
            vote_result.update({number: information})
      return ''
    else:
      return 'That is not a Texas representative, please choose from the given options.'


# Import some useful functions
@app.context_processor
def html_function_1():
    return dict(ceil=math.ceil)

# Run flask/website
app.run(host='0.0.0.0', port=8080)