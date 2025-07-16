import dash
from dash import html, dcc, Input, Output, no_update, State
import dash_bootstrap_components as dbc
import os
from jupyter_dash import JupyterDash
import time

time_periods = ["AM", "IP", "PM", "OP", "WD"]
year_options = ["2018", "2026", "2031", "2036", "2041", "2046", "2051", "2056"]
scenario_options = ["Central", "Committed"]
scenario_options_to_scenario_name = {
    "Central": "RC25v1_02",
    "Committed": "RC25v1_02_CF"
}
metric_options = ["Volumes", "Capacity", "V/C", "Congested Speed", "Lanes"]
metric_options_to_metric_code = {
    "Volumes": "VEH",
    "Capacity": "HYCAP",
    "V/C": "VC",
    "Congested Speed": "CSPD",
    "Lanes": "LANES"
}
# Set restrictions for options
scenario_restrictions = {
    "Central": ["2018", "2026", "2031", "2036", "2041", "2046", "2051", "2056"],
    "Committed": ["2026", "2031", "2036", "2041"],
    # "None": ["None"]
}
year_restrictions = {
    "2018": ["Central"],
    "2026": ["Central", "Committed"],
    "2031": ["Central", "Committed"],
    "2036": ["Central", "Committed"],
    "2041": ["Central", "Committed"],
    "2046": ["Central"],
    "2051": ["Central"],
    "2056": ["Central"]
}
year_2_restrictions = {
    "2018": ["Central", "None"],
    "2026": ["Central", "Committed", "None"],
    "2031": ["Central", "Committed", "None"],
    "2036": ["Central", "Committed", "None"],
    "2041": ["Central", "Committed", "None"],
    "2046": ["Central", "None"],
    "2051": ["Central", "None"],
    "2056": ["Central", "None"]
}
metric_restrictions_to_tp = {
    "Volumes": ["AM", "IP", "PM", "OP", "WD"],
    "Capacity": ["AM", "IP", "PM", "OP"],
    "V/C": ["AM", "IP", "PM", "OP"],
    "Congested Speed": ["AM", "IP", "PM", "OP"],
    "Lanes": ["AM", "IP", "PM", "OP"]
}
time_period_restrictions = {
    "AM": ["Volumes", "Capacity", "V/C", "Congested Speed", "Lanes"],
    "IP": ["Volumes", "Capacity", "V/C", "Congested Speed", "Lanes"],
    "PM": ["Volumes", "Capacity", "V/C", "Congested Speed", "Lanes"],
    "OP": ["Volumes", "Capacity", "V/C", "Congested Speed", "Lanes"],
    "WD": ["Volumes"],
}

# SETTING STYLES
top_margin = 52
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": top_margin,
    "left": 0,
    "bottom": 0,
    # "width": "9.9rem",
    "width": "12.5%",
    "height": "100%",
    "padding": "0rem 1rem",
    "background-color": "#53565A",
}
CONTENT_STYLE = {
    "position": "fixed",
    "top": top_margin,
    "margin-top": "3remrem",
    "margin-left": "12.5%",
    "margin-right": "2rem",
    "padding": "0rem 1rem",
    "width": "87.5%",
    "height": "100%",
    "bottom": 0,
    "background-color": "#e6fff7",
}
label_style = {'text-align': 'left', 'font-family': 'VIC', 'vertical-align': 'bottom', "font-weight": "bold",
               'color': '#f7f8fa', 'width': '200px'}
option_style = {'font-family': 'VIC', 'font-size': '12px'}

app = JupyterDash(external_stylesheets=[dbc.themes.BOOTSTRAP])
sidebar = html.Div([
    html.Br(),
    html.H3("User Settings", style={'width': '100%', 'text-align': 'center', 'font-family': 'VIC', 'color': '#f7f8fa',
                                    "font-weight": "bold"}),
    html.Br(),
    html.Div([
        html.Div([
            html.Label("Scenario 1", style={'text-align': 'left', 'font-family': 'VIC', 'vertical-align': 'bottom',
                                            "font-weight": "bold", 'color': '#f7f8fa', 'width': '100%'}),
            dcc.Dropdown(
                id="selected_s1",
                options=scenario_options,
                value="Central",
                clearable=False,
                style={'font-family': 'VIC', 'font-size': '12px', 'width': '130px'}
            )

        ]),
        html.Div([
            html.Label("Year", style={'text-align': 'left', 'font-family': 'VIC', 'vertical-align': 'bottom',
                                      "font-weight": "bold", 'color': '#f7f8fa', 'width': '100%',
                                      'padding-right': '3.5px'}),
            dcc.Dropdown(
                id="selected_s1_year",
                options=year_options,
                value="2036",
                clearable=False,
                style={'font-family': 'VIC', 'font-size': '12px', 'width': '80px'}
            ),
        ])
    ], style=dict(display='flex', width='100%')),
    html.Br(),
    html.Div([
        html.Div([
            html.Label("Scenario 2", style={'text-align': 'left', 'font-family': 'VIC', 'vertical-align': 'bottom',
                                            "font-weight": "bold", 'color': '#f7f8fa', 'width': '100%'}),
            dcc.Dropdown(
                id="selected_s2",
                options=["None"] + scenario_options,
                value="Central",
                clearable=False,
                style={'font-family': 'VIC', 'font-size': '12px', 'width': '130px'}
            )

        ]),
        html.Div([
            html.Label("Year", style={'text-align': 'left', 'font-family': 'VIC', 'vertical-align': 'bottom',
                                      "font-weight": "bold", 'color': '#f7f8fa', 'width': '100%',
                                      'padding-right': '3.5px'}),
            dcc.Dropdown(
                id="selected_s2_year",
                options=["None"] + year_options,
                value="2026",
                clearable=False,
                style={'font-family': 'VIC', 'font-size': '12px', 'width': '80px'}
            ),
        ])
    ], style=dict(display='flex', width='100%')),
    html.Br(),
    html.Label("Metric", style=label_style),
    dcc.Dropdown(
        id="selected_metric",
        options=metric_options,
        value="Volumes",
        clearable=False,
        style=option_style
    ),
    html.Label("Time period", style=label_style),
    dcc.Dropdown(
        id="selected_tp",
        options=time_periods,
        value="AM",
        clearable=False,
        style=option_style
    ),
    html.Br(), html.Br(), html.Br(), html.Br(), html.Br(), html.Br(), html.Br(), html.Br(), html.Br(),
    html.Br(), html.Br(), html.Br(), html.Br(), html.Br(), html.Br(), html.Br(), html.Br(),
    html.Img(src=r'assets/_BANNERS_LOGOS/DTP_Brandmark_White_Screen.png', alt='image', width="160", height="50")

], style=SIDEBAR_STYLE)

map_content = html.Div([
    html.Iframe(
        id="map-frame",
        src="/assets/Y2018_RC25v1_02_vs_Y2036_RC25v1_02_VEH_AM_DIFF.html",
        width="100%",
        height="100%"
    ),
    html.Div(id="legend-container"),
], style=CONTENT_STYLE)

app.layout = html.Div([
    html.Div([
        html.Img(src=r'assets/_BANNERS_LOGOS/VITM_Rd_Banner.png', alt='image', width='100%', height='100%'),
    ], style={'position': 'relative'}),
    sidebar,
    map_content,
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Welcome to the VITM Reference Case Road Network Dashboard!")),
            dbc.ModalBody(
                [
                    html.P(
                        "The Reference Case is a suite of common forecasting assumptions for future land use, transport networks and modelling parameters. These assumptions are implemented in DTP’s strategic transport model, the VITM, and the model is referred to as the VITM Reference Case. The VITM Reference Case is DTP’s central scenario forecast of transport system demand, capacity and travel conditions over the next 30 years. It is calibrated to a base year of 2018 and includes forecasts from 2026 to 2056 in five-year increments. It aims to represent private car, public transport and road freight travel at a strategic level."),
                    html.P(
                        "Each year DTP refreshes the Reference Case to ensure it is underpinned by current information and evidence. While some of the assumptions within it align with DTP plans and known government commitments, it does not aim to represent any kind of plan, commitment or target of DTP or the Victorian Government. Rather, it aims to represent a reasonably expected trajectory of transport demand and capacity considering a balanced view of historic trends and measured future projections. For this reason, the Reference Case may differ from target outcomes and transport system service levels. It can be thought of as more of a ‘business as usual’ forecasting scenario rather than a plan or target state. Specific assumptions within it should not be taken as any kind of signal of future government investment or commitment."),
                    html.P(
                        "Annual updates to VITM Reference case occur around the middle of each year to support business cases being submitted to in the Victorian State Budget process. Projects being developed should typically use the most recent Reference Case available when submitting business cases. Where this is not possible due to particular project life cycles and timeframes, sensitivity testing of outdated Reference Case information should be undertaken."),
                ]
            ),
            dbc.ModalFooter([
                html.Img(src=r'assets/_BANNERS_LOGOS/DTP_Brandmark_DarkGrey_Screen.svg', alt='image', width="160", height="50")
            ]
            ),
        ],
        id="startup-modal",
        is_open=True,
        style={'font-family': 'VIC', 'font-size': '12px', "max-width": "100%", "width": "100%"},
    ),
])


@app.callback(
    Output("map-frame", "src"),
    Output("legend-container", "children"),
    Input("selected_s1_year", "value"),
    Input("selected_s1", "value"),
    Input("selected_s2_year", "value"),
    Input("selected_s2", "value"),
    Input("selected_metric", "value"),
    Input("selected_tp", "value")
)
def display_selected_map(s1y, s1, s2y, s2, metric, tp):
    # Cache-busting to force iframe to reload file
    if (metric == "Volumes" or metric == "Capacity" or metric == "Lanes") and (s2 != "None"):
        map_output = f"/assets/Y{s1y}_{scenario_options_to_scenario_name[s1]}_vs_Y{s2y}_{scenario_options_to_scenario_name[s2]}_{metric_options_to_metric_code[metric]}_{tp}_DIFF.html?t={int(time.time())}"
    #elif metric == "V/C" or metric == "Congested Speed":
    #    map_output = f"/assets/Y{s1y}_{scenario_options_to_scenario_name[s1]}_{tp}_{metric_options_to_metric_code[metric]}.html?t={int(time.time())}"
    else:
        map_output = f"/assets/Y{s1y}_{scenario_options_to_scenario_name[s1]}_{metric_options_to_metric_code[metric]}_{tp}.html?t={int(time.time())}"
    if metric == "Volumes" and s2 != "None":
        legend = html.Img(src=f"/assets/_LEGENDS/_LEGEND_VOL_COMP.png",
                          style={"height": "50px", "width": "440px", "position": "absolute", "top": "800px",
                                 "left": "35px", "zIndex": "10", "pointer-events": "none"})
    elif metric == "Volumes" and s2 == "None":
        legend = html.Img(src=f"/assets/_LEGENDS/_LEGEND_VOL.png",
                          style={"height": "30px", "width": "273px", "position": "absolute", "top": "820px",
                                 "left": "35px", "zIndex": "10", "pointer-events": "none"})
    elif metric == "Capacity" and s2 != "None":
        legend = html.Img(src=f"/assets/_LEGENDS/_LEGEND_CAP_COMP.png",
                          style={"height": "50px", "width": "440px", "position": "absolute", "top": "800px",
                                 "left": "35px", "zIndex": "10", "pointer-events": "none"})
    elif metric == "Capacity" and s2 == "None":
        legend = html.Img(src=f"/assets/_LEGENDS/_LEGEND_CAP.png",
                          style={"height": "30px", "width": "273px", "position": "absolute", "top": "820px",
                                 "left": "35px", "zIndex": "10", "pointer-events": "none"})
    elif metric == "V/C":
        legend = html.Img(src=f"/assets/_LEGENDS/_LEGEND_VC.png",
                          style={"height": "150px", "width": "200px", "position": "absolute", "top": "700px",
                                 "left": "35px", "zIndex": "10", "pointer-events": "none"})
    elif metric == "Congested Speed":
        legend = html.Img(src=f"/assets/_LEGENDS/_LEGEND_SPEED.png",
                          style={"height": "150px", "width": "200px", "position": "absolute", "top": "700px",
                                 "left": "35px", "zIndex": "10", "pointer-events": "none"})
    elif metric == "Lanes" and s2 != "None":
        legend = html.Img(src=f"/assets/_LEGENDS/_LEGEND_LANE_COMP.png",
                          style={"height": "130px", "width": "200px", "position": "absolute", "top": "725px",
                                 "left": "35px", "zIndex": "10", "pointer-events": "none"})
    elif metric == "Lanes" and s2 == "None":
        legend = html.Img(src=f"/assets/_LEGENDS/_LEGEND_LANE.png",
                          style={"height": "130px", "width": "200px", "position": "absolute", "top": "725px",
                                 "left": "35px", "zIndex": "10", "pointer-events": "none"})
    return map_output, legend


# Restrict year options based on scenario selected
@app.callback(
    Output('selected_s1_year', 'options'),
    Input('selected_s1', 'value')
)
def restrict_scenario1_years(scenario):
    allowed = scenario_restrictions.get(scenario, [])
    return [
        {'label': item, 'value': item, 'disabled': item not in allowed}
        for item in year_options
    ]


@app.callback(
    Output('selected_s2_year', 'options'),
    Input('selected_s2', 'value')
)
def restrict_scenario2_years(scenario):
    allowed = scenario_restrictions.get(scenario, [])
    return [
        {'label': item, 'value': item, 'disabled': item not in allowed}
        for item in year_options
    ]


# Restrict scenario options based on year selected
@app.callback(
    Output('selected_s1', 'options'),
    Input('selected_s1_year', 'value')
)
def restrict_scenario1(year):
    allowed = year_restrictions.get(year, [])
    return [
        {'label': item, 'value': item, 'disabled': item not in allowed}
        for item in scenario_options
    ]


@app.callback(
    Output('selected_s2', 'options'),
    Input('selected_s2_year', 'value')
)
def restrict_scenario2(year):
    allowed = year_2_restrictions.get(year, [])
    return [
        {'label': item, 'value': item, 'disabled': item not in allowed}
        for item in scenario_options + ["None"]
    ]


# Restrict metric options based on time period selected
@app.callback(
    Output('selected_metric', 'options'),
    Input('selected_tp', 'value')
)
def restrict_metrics(tp):
    allowed = time_period_restrictions.get(tp, [])
    return [
        {'label': item, 'value': item, 'disabled': item not in allowed}
        for item in metric_options
    ]


# Restrict tp options based on metric selected
@app.callback(
    Output('selected_tp', 'options'),
    Input('selected_metric', 'value')
)
def restrict_metrics(met):
    allowed = metric_restrictions_to_tp.get(met, [])
    return [
        {'label': item, 'value': item, 'disabled': item not in allowed}
        for item in time_periods
    ]


# Update scenario 2 to None if metric does not allow for comparison
@app.callback(
    Output('selected_s2_year', 'value'),
    Output('selected_s2', 'value'),
    Input('selected_metric', 'value'),
    State('selected_s1', 'value'),
    Input('selected_s1_year', 'value'),
    State('selected_s2', 'value'),
    Input('selected_s2_year', 'value'),
)
def update_scenario2(met, scen1, scen1_year, scen2, scen2_year):
    if met == "V/C" or met == "Congested Speed":
        # s2_year = "None"
        s2 = "None"
        return no_update, s2
    #  elif (met == "Volumes" or met == "Capacity") and scen2 == "None":
    #      s2_year_int = int(scen1_year) + 5
    #      if s2_year_int < 2026:
    #          s2_year_int_update = 2026
    #      elif s2_year_int > 2056:
    #          s2_year_int_update = 2036
    #      else:
    #          s2_year_int_update = s2_year_int
    #      s2_year = str(s2_year_int_update)
    #      s2 = "Central"
    #      return s2_year, s2
    elif scen1 == scen2 and scen1_year == scen2_year:
        if scen1_year != "2036":
            s2_year = "2036"
        else:
            s2_year = "2031"
        return s2_year, no_update
    else:
        return no_update


app.run_server(host="0.0.0.0", port="8002", debug=False, use_reloader=False)
