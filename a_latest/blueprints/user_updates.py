# set_frametime.py
from flask import Blueprint, request, session, jsonify, render_template
import pandas as pd
import os
from blueprints.structure_data import structure_data

def daily_activities(df1a):

    # Create df2a from df1a with columns day, activities, type, start, end
    df2a = df1a[['activities', 'type', 'start_time', 'end_time']].copy()
    df2a.insert(0, 'day', 'MONDAY')
    return df2a