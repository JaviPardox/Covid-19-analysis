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

# first_order: big group, example: countries
# second_order: small group within big group, example: vaccines
# df: dataframe with data 
# parameters: list of parameters for plotting, it has to be 2 elements x and y respectively
# graph_type: type of graph, example: scatter
# differential_column: default to False, set to True if the data has a column of rate of change from some data
def second_order_dic(first_order, second_order, df, parameters, graph_type, differential_column = False):
    
    order1 = df[first_order].unique()
    dic = {}
    
    for order1_element in order1:
        
        new_df = df.loc[df[first_order] == order1_element]
        order2 = new_df[second_order].unique()
        dic[order1_element] = {}
        
        for order2_element in order2:
            
            param1_list = []
            param2_list = []
            
            # If the data has a rate of change column, set first row to 0
            if(differential_column == True):
                index = new_df.loc[new_df[second_order] == order2_element].index[0]
                new_df.at[index, parameters[1]] = 0
            
            # Get series of data for graph parameters under the second order element
            param1 = new_df.loc[new_df[second_order] == order2_element][parameters[0]]
            param2 = new_df.loc[new_df[second_order] == order2_element][parameters[1]]
            
            for element in param1:
                param1_list.append(element)

            for element in param2:
                param2_list.append(element)
                                                                        
            nested_dic = {
                            "x": param1_list,
                            "y": param2_list,
                            "type": graph_type,
                            "name": order2_element
            }
                                                                        
            dic[order1_element][order2_element] = nested_dic
    
    return dic


# first_order: filter by, example: vaccines
# df: dataframe with data 
# parameters: list of parameters for plotting, it has to be 2 elements x and y respectively
# graph_type: type of graph, example: scatter
# differential_column: default to False, set to True if the data has a column of rate of change from some data
# isDateFormat: set to true if the x axis data is in datetime format
def first_order_dic(first_order, df, parameters, graph_type, differential_column = False, isDateFormat = False):
    
    # Sort by first order
    order1 = df[first_order].unique()
    data = []
    
    for order1_element in order1:
        
        param1_list = []
        param2_list = []
        
        # If the data has a rate of change column, set first row to 0
        if(differential_column == True):
            index = df.loc[df[first_order] == order1_element].index[0]
            df.at[index, parameters[1]] = 0
        
        # Get columns data for plotting
        param1 = df.loc[df[first_order] == order1_element][parameters[0]]
        param2 = df.loc[df[first_order] == order1_element][parameters[1]]
        
        # Format to string in case the data is in datetime format
        if(isDateFormat == True):
            for element in param1:
                param1_list.append(str(element))
        else:
            for element in param1:
                param1_list.append(element)
            
        for element in param2:
            param2_list.append(element)
            
        dic = {
            
            "x": param1_list,
            "y": param2_list,
            "type": graph_type,
            "name": order1_element
            
        }
        
        data.append(dic)
        
    return data


@app.route("/allvaccines")
def all_vacc_man():

    df = pd.read_sql_query("SELECT * FROM all_vaccines", engine)
    first_order = "location"
    second_order = "vaccine"
    parameters = ["date","total_vaccinations"] #x,y
    graph_type = "scatter"       
                                                                            
    dic = second_order_dic(first_order,second_order,df,parameters,graph_type,differential_column=False)
        
    reordered_dict = dict_reorder(dic)

    return jsonify(reordered_dict)


@app.route("/allvaccines_change")
def all_vacc_change_man():

    df = pd.read_sql_query("SELECT location, date, vaccine , total_vaccinations, total_vaccinations - LAG(total_vaccinations,1,0) OVER (PARTITION BY vaccine ORDER BY location, date) AS Total_Diff FROM all_vaccines", engine)
    first_order = "location"
    second_order = "vaccine"
    parameters = ["date","total_diff"] #x,y
    graph_type = "scatter"       
                                                                        
    dic = second_order_dic(first_order,second_order,df,parameters,graph_type,differential_column=True)        

    reordered_dict = dict_reorder(dic)

    return jsonify(reordered_dict)


@app.route("/vaccines_states")
def vaccines_states():

    dic = {}
    df = pd.read_sql_query("SELECT * FROM states_vaccinations", engine)
    df = df.dropna()
    graph_type = "scatter"
    sortby = "location"
    # Get rid of date and location
    columns = df.columns.tolist()[2:-1]

    for column in columns:
        parameters = ["date",column] #x,y
        data = first_order_dic(sortby, df, parameters, graph_type)
        formated_name = column.replace("_", " ").title() 
        dic[formated_name] = data

    return jsonify(dic)      

@app.route("/map_stats")
def map_stats():

    df = pd.read_sql_query("SELECT * FROM states_vaccinations", engine)
    df = df.dropna()
    states = df["location"].unique()

    new_df = pd.DataFrame()

    # Get last row from each state
    for state in states:
        new_row = df.loc[df["location"] == state].iloc[-1]
        temp_df = pd.DataFrame(new_row).T
        new_df = pd.concat([new_df,temp_df],ignore_index=True)

    postal_df = pd.read_sql_query("SELECT * FROM postal_names", engine)
    postal_df = postal_df.rename(columns={"State":"location"}).drop(columns=["Abbrev"])
    postal_df

    new_df = new_df.merge(postal_df, how="left", on="location").dropna()
    new_df["share_doses_used"] = new_df["share_doses_used"].multiply(100)
    data = new_df.to_dict(orient='records')

    return jsonify(data)

if __name__ == '__main__':
    app.run()