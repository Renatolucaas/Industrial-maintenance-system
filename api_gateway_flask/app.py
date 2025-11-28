from flask import Flask, request, jsonify, render_template
import boto3
import os
import uuid
from datetime import datetime
import json

app = Flask(__name__)
