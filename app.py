from flask import Flask, jsonify

import pandas as pd
from flask_cors import CORS 

import os
from sqlalchemy import create_engine
# dotenv adds .env variables to the environment
from dotenv import load_dotenv

# Load variables
load_dotenv()
key = os.environ['KEY']

# Create engine and connect to PostgreSQL
engine = create_engine('postgresql://postgres:'+key+'@localhost:5432/covid-19-db')
connection = engine.connect()


app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
CORS(app)

# Source: https://gist.github.com/gyli/f60f0374defc383aa098d44cfbd318eb/revisions
# sorted(dictionary.items()) could be used but it returns a list of dictionaries
# for convenience, this will be used 
def dict_reorder(item):
    if isinstance(item, dict):
        item = {k: v for k, v in sorted(item.items())}
        for k, v in item.items():
            if isinstance(v, dict):
                item[k] = dict_reorder(v)
    return item


#def df_to_dict_vacc(df,column):




@app.route("/vaccines")
def vaccines():

    df = pd.read_sql_query("SELECT * FROM vaccines_man", engine)

    names = df["vaccine"].unique()
    # Sort to keep the color order
    names = sorted(names, key=str.lower)

    data = []

    # Iterate through the dataframe and make a dictionary out of each vaccine manufacturer 
    for name in names:
        date_val = []
        total_vacc = []

        dates = df.loc[df["vaccine"] == name]["date"]
        vaccines = df.loc[df["vaccine"] == name]["total_vaccinations"]
        
        for date in dates:
            date_val.append(str(date))

        for vaccine in vaccines:
            total_vacc.append(vaccine)
        
        vacc_dic = {
        
        "x": date_val,
        "y": total_vacc,
        "type":"scatter",
        "name": name,
        "mode": "lines"
        }
        
        data.append(vacc_dic)

    return jsonify(data)


@app.route("/vaccines/difference")
def vaccines_difference():

    # Need the total_vaccinations to be INT type, instead of big INT
    # This is due to the fact that the LAG() function only takes the same data type for all arguments 
    connection.execute('ALTER TABLE vaccines_man ALTER COLUMN total_vaccinations TYPE integer;')

    # LAG() is used to access the previous row
    df = pd.read_sql_query("SELECT location, date, vaccine , total_vaccinations, total_vaccinations - LAG(total_vaccinations,1,0) OVER (PARTITION BY vaccine ORDER BY date) AS Total_Diff FROM vaccines_man", engine)
        
    data = []
    names = df["vaccine"].unique()
    names = sorted(names, key=str.lower)

    # The query returns a non-0 value for the first row of each manufacturer's total_diff, that value has to be 0
    for name in names:
        index = df.loc[df["vaccine"] == name].index[0]
        df.at[index, 'total_diff'] = 0

    for name in names:
        date_val = []
        total_vacc_diff = []

        dates = df.loc[df["vaccine"] == name]["date"]
        vaccines_diff = df.loc[df["vaccine"] == name]["total_diff"]
        
        for date in dates:
            date_val.append(str(date))

        for vaccine in vaccines_diff:
            total_vacc_diff.append(vaccine)
        
        vacc_dic = {
        
        "x": date_val,
        "y": total_vacc_diff,
        "type":"scatter",
        "name": name,
        "mode": "lines"
        }
        
        data.append(vacc_dic)

    return jsonify(data)

@app.route("/allvaccines")
def all_vacc_man():

    df = pd.read_sql_query("SELECT * FROM all_vaccines", engine)
    countries = df["location"].unique()

    dic = {}
    for country in countries:
    
        countries_dic = {country:{}}
        new_df = df.loc[df["location"] == country]
        names = new_df["vaccine"].unique()
        dic[country] = {}
        
        for name in names:
            date_val = []
            total_vacc = []

            dates = new_df.loc[new_df["vaccine"] == name]["date"]
            vaccines = new_df.loc[new_df["vaccine"] == name]["total_vaccinations"]

            for date in dates:
                date_val.append(str(date))

            for vaccine in vaccines:
                total_vacc.append(vaccine)

            dic_vac ={
                        "x": date_val,
                        "y": total_vacc,
                        "type":"scatter",
                        "name": country + ": " + name
                    }
            dic[country][name] = dic_vac
    
    reordered_dict = dict_reorder(dic)

    return jsonify(reordered_dict)


@app.route("/allvaccines_change")
def all_vacc_change_man():

    connection.execute('ALTER TABLE all_vaccines ALTER COLUMN total_vaccinations TYPE integer;')

    df = pd.read_sql_query("SELECT location, date, vaccine , total_vaccinations, total_vaccinations - LAG(total_vaccinations,1,0) OVER (PARTITION BY vaccine ORDER BY location, date) AS Total_Diff FROM all_vaccines", engine)

    countries = df["location"].unique()

    dic = {}

    for country in countries:
        
        countries_dic = {country:{}}
        new_df = df.loc[df["location"] == country]
        names = new_df["vaccine"].unique()
        dic[country] = {}
        
        for name in names:
            date_val = []
            total_vacc = []

            index = new_df.loc[new_df["vaccine"] == name].index[0]
            new_df.at[index, 'total_diff'] = 0

            dates = new_df.loc[new_df["vaccine"] == name]["date"]
            vaccines = new_df.loc[new_df["vaccine"] == name]["total_diff"]

            for date in dates:
                date_val.append(str(date))

            for vaccine in vaccines:
                total_vacc.append(vaccine)

            dic_vac ={
                        "x": date_val,
                        "y": total_vacc,
                        "type":"scatter",
                        "name": country + ": " + name
                    }

            dic[country][name] = dic_vac


    reordered_dict = dict_reorder(dic)

    return jsonify(reordered_dict)


if __name__ == '__main__':
    app.run()