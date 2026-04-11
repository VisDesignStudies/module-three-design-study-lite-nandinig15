import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Data Prep
df = pd.read_csv('energy.csv')

state_to_code = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
    'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
    'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
    'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
    'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
    'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
    'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
    'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
    'District of Columbia': 'DC'
}
df['StateCode'] = df['State'].map(state_to_code)

# Aggregation
cols = df.columns
df['Total_Coal'] = df[[c for c in cols if 'Consumption.' in c and '.Coal' in c]].sum(axis = 1)
df['Total_Gas'] = df[[c for c in cols if 'Consumption.' in c and '.Natural Gas' in c]].sum(axis = 1)

petro_keys = ['.Petroleum', '.Distillate Fuel Oil', '.Kerosene', '.Other Petroleum Products']
df['Total_Petro'] = df[[c for c in cols if 'Consumption.' in c and any(k in c for k in petro_keys)]].sum(axis = 1)

renew_keys = ['.Solar', '.Wind', '.Wood', '.Geothermal', '.Hydropower']
df['Renew_Total'] = df[[c for c in cols if 'Consumption.' in c and any(k in c for k in renew_keys)]].sum(axis = 1)

df['Fossil_Total'] = df['Total_Coal'] + df['Total_Gas'] + df['Total_Petro']

df['Total_Energy'] = df[[c for c in cols if 'Consumption.' in c]].sum(axis = 1)

df['Renew_Share'] = (df['Renew_Total'] / df['Total_Energy']) * 100

df_map = df[df['Year'] == df['Year'].max()]

# 2. Dashboard
app = dash.Dash(__name__)

server = app.server

app.layout = html.Div(style = {'fontFamily': 'Times New Roman', 'padding': '40px', 'backgroundColor': '#f8f9fa'}, children=[
    html.H1("US Energy Transition: Strategic Policy Tool", style = {'textAlign': 'center', 'marginBottom': '30px'}),
    
    html.Div([
        dcc.Graph(
            id = 'usa-map',
            style = {'height': '600px'},
            figure = px.choropleth(
                df_map, locations = 'StateCode', locationmode = "USA-states",
                color = 'Renew_Share', scope = "usa", color_continuous_scale = "YlGn",
                title = "State Renewable Share Overview (Click a State)"
            ).update_layout(margin = {"r":0,"t":50,"l":0,"b":0})
        )
    ], style = {'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '15px', 'boxShadow': '0px 4px 12px rgba(0,0,0,0.1)', 'marginBottom': '30px'}),

    # VERDICT
    html.Div(id='verdict-box', style = {'padding': '25px', 'fontSize': '26px', 'textAlign': 'center', 'borderRadius': '12px', 'marginBottom': '30px', 'fontWeight': 'bold'}),

    # ROW 1: Task 1 and Task 2 (Side by Side)
    html.Div(style = {'display': 'flex', 'gap': '25px', 'marginBottom': '30apx'}, children=[
        html.Div([
            dcc.Graph(id='task1-abs', style = {'height': '500px'}) 
        ], style = {'width': '50%', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '15px', 'boxShadow': '0px 4px 12px rgba(0,0,0,0.1)'}),
        
        html.Div([
            dcc.Graph(id='task2-share', style = {'height': '500px'})
        ], style = {'width': '50%', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '15px', 'boxShadow': '0px 4px 12px rgba(0,0,0,0.1)'})
    ]),
    
    html.Div([
        dcc.Graph(id='task3-breakdown', style = {'height': '550px'}) 
    ], style = {'width': '100%', 'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '15px', 'boxShadow': '0px 4px 12px rgba(0,0,0,0.1)'})
])

# 3. Callback
@app.callback(
    [Output('task1-abs', 'figure'), Output('task2-share', 'figure'), 
     Output('task3-breakdown', 'figure'), Output('verdict-box', 'children'), 
     Output('verdict-box', 'style')],
    [Input('usa-map', 'clickData')]
)
def update_dashboard(clickData):
    state_code = clickData['points'][0]['location'] if clickData else "NY"
    code_to_state = {v: k for k, v in state_to_code.items()}
    state_name = code_to_state.get(state_code, "New York")
    dff = df[df['State'] == state_name].sort_values('Year')
    
    # Verdict
    f_change = dff['Fossil_Total'].iloc[-1] - dff['Fossil_Total'].iloc[0]
    r_change = dff['Renew_Total'].iloc[-1] - dff['Renew_Total'].iloc[0]
    if f_change < 0 and r_change > 0:
        verdict = f"{state_name}: SUBSTITUTION"
        v_style = {'backgroundColor': '#28a745', 'color': 'white'}
    else:
        verdict = f"{state_name}: ADDITIVE GROWTH"
        v_style = {'backgroundColor': '#ffc107', 'color': '#212529'}

    # Task 1
    task1 = go.Figure()
    task1.add_trace(go.Scatter(x = dff['Year'], y = dff['Fossil_Total'], name = "Fossils", line = dict(color = '#D85A30', width = 4)))
    task1.add_trace(go.Scatter(x = dff['Year'], y = dff['Renew_Total'], name = "Renewables", line = dict(color = '#28a745', width = 4)))
    task1.update_layout(title = f"Task 1: Energy Trends over Time - {state_name}", template = 'plotly_white', xaxis_title = "Year", yaxis_title = "Consumption (Billion BTU)")
    
    # Task 2
    task2 = go.Figure()
    task2.add_trace(go.Scatter(x = dff['Year'], y = dff['Renew_Share'], fill = 'tozeroy', name = "Renewable %", line = dict(color = '#28a745', width = 3)))
    task2.update_layout(title = f"Task 2: Energy that is Renewable (%) - {state_name}", template='plotly_white', xaxis_title = "Year", yaxis_title = "Renewable Share (%)")

    # Task 3
    task3 = go.Figure()
    task3.add_trace(go.Scatter(x = dff['Year'], y = dff['Total_Coal'], name = "Coal", stackgroup = 'fossil', line = dict(color = '#343a40')))
    task3.add_trace(go.Scatter(x = dff['Year'], y = dff['Total_Gas'], name = "Natural Gas", stackgroup = 'fossil', line = dict(color = '#17a2b8')))
    task3.add_trace(go.Scatter(x = dff['Year'], y = dff['Total_Petro'], name = "Petroleum", stackgroup = 'fossil', line = dict(color = '#fd7e14')))
    task3.update_layout(title = f"Task 3: Detailed Fossil Breakdown - {state_name}", template = 'plotly_white', xaxis_title = "Year", yaxis_title = "Consumption (Billion BTU)")

    return task1, task2, task3, verdict, v_style

if __name__ == '__main__':
    app.run(debug = True, host='0.0.0.0', port=int(os.environ.get("PORT", 8080))))
