# Investment Dashboard

This project is a part of Udacity's Data Science Nanodegree. As part of the Software Engineering module, we were encouraged to develop a web dashboard using python, flask, plotly, and bootstrap, and deployed on Heroku. For this project, I have chosen to build a dashboard to track investments made through GBM+, a Mexican broker.

## Installations

The jupyter notebook with the original data wrangling steps can be installed through anaconda and was written in python 3.10.4.

Additionally, the web app was built on flask and bootstrap, using heroku to deploy. The python packages used can be found in the requirements.txt file. 

The csv files with transaction data are modelled from the transaction history you can download directly from the GBM+ website; naturally, the data was populated with random values for this exercise and does not represent an accurate investment portfolio, though it does follow the structure of a real report.

## Project Motivation
I wanted to build a useful web app that made use of skills acquired through the Nanodegree program, as well as past work experience in web development, and create a data dashboard with actual practical implications. This dashboard is modelled from a spreadsheet I personally used to track invesments, and now automates any steps necessary to update the tracker, save for the manual download of the transaction history.

## File Descriptions
- investment_dashboard.ipynb - Jupyter Notebook with initial data wrangling
- data/month.csv - GBM+ transaction history simulated datasets

## Results & Improvements

I use flask to create the web app, and plotly to build the interactive charts on the dashboard, creating an interesting tracker for any porfolio. I also wanted to test out Heroku for the first time with this project.

As my personal investment tracker, this is very much built around my personal taste -- in fact, as a (Boglehead)[bogleheads.org], it probably has too many bells and whistles. As I only use GBM+, this app is already built around their transaction history download layouts. Again, since I only buy and hold low-cost, broadly-diversified index ETFs, this app does not track stock sales. Perhaps, if in the future I decide to sell something, I might add this feature. 


## Licensing & Acknowledgements
Feel free to reuse this code under the MIT License. Special thanks to the [perrodinero's](perrodinero.blog) [spreadsheet](https://perrodinero.gumroad.com/l/plantilla-para-inversiones) for inspiration.
