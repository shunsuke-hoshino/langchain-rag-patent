import os
from flask import Flask, request, render_template
from openai import OpenAI
#from dotenv import load_dotenv
import requests
import csv

from app.appfunction import app

if __name__ == "__main__":
    app.run(debug=True)

#if 'WEBSITE_HOSTNAME' not in os.environ:
#load_dotenv()
#openai_api_key = os.getenv("OPENAI_API_KEY")

#