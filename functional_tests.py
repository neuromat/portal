from selenium import webdriver


browser = webdriver.Firefox()

# A neuroscience researcher discovered a new site that
# provides a data base with neuroscience experiments.
# She goes to checkout its home page
browser.get('http://localhost:8000')

# She notices the page title and header mention
# Neuroscience Experiments Database
assert 'Neuroscience Experiments Database' in browser.title

# She sees the home page have a list of experiments
# and click one one of that to check it out

# She see that there is a search box in top of page.
# So, she types in input search box:
# "Brachial Plexus" and wait to see the results.

# Then she see that some entries returned that
# supposely has "Brachial Plexus" string in one
# or more fields

browser.quit()

