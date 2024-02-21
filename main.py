from flask import Flask, render_template
import pandas as pd
import time, os
import dataparser as dp

app = Flask(__name__, template_folder="")


def load_data(index):
  return dp.optionchain(index)


# Route to render the webpage
@app.route('/')
def index():
  return render_template('webpage.html')


# Route to fetch and display put-call ratio
@app.route('/pcr/<index>')
def get_pcr(index):
  listPCR = dp.pcr(index)
  pcr_html = ""
  for pcr in listPCR:
    pcr_html += "<li><b>" + pcr[3] + "</b><br><b>Call: </b>" + pcr[
        1] + "<br><b>Put: </b>" + pcr[0] + "<br><b>Ratio: </b>" + pcr[
            2] + "</li>"
  return pcr_html


# Route to fetch and display the updated data
@app.route('/index/<index>')
def get_data1(index):
  data = load_data(index)
  return data


@app.route('/<index>')
def get_banknifty(index):
  data = dp.niftyval(index)
  return data


# Main function to run the Flask app
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080)
