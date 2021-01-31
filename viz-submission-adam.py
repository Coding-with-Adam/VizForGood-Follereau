import plotly.express as px
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import dash_bootstrap_components as dbc


# Reshape dataframe from wide to long
df=pd.read_excel("Vizforsocialgood.xlsx", engine='openpyxl', sheet_name="2018", header=None)
df = df.transpose()
new_header = df.iloc[0]  # grab the first row for the header
df = df[1:]              # take the data less the header row
df.columns = new_header  # set the header row as the df header

df = pd.melt(df,id_vars=['Country', 'Local partner', 'Project title', 'Axis of intervention',
                           'Direct beneficiaries', 'Indirect beneficiaries', 'Region',
                           'Voted 2018 project budget €', 'Project share % out of all budget',
                           'Voted 2018 country budget €', 'Country share % out of all budget',
                           "Type de financement (tel que présenté dans l'Accord-Cadre 2016-2020)",
                           'iso_alpha'],
                        value_vars=['2018 results','2018 results2','2018 results3','2018 results4','2018 results5'],
                        var_name='results',value_name='notes')

df19=pd.read_excel("Vizforsocialgood.xlsx", engine='openpyxl', sheet_name="2019", header=None)
df19 = df19.transpose()
new_header = df19.iloc[0]  # grab the first row for the header
df19 = df19[1:]              # take the data less the header row
df19.columns = new_header  # set the header row as the df header

df19 = pd.melt(df19,id_vars=['Country', 'Local partner', 'Project title', 'Axis of intervention',
                             'Direct beneficiaries', 'Indirect beneficiaries', 'Region',
                             'Voted 2019 project budget €', 'Project share % out of all budget',
                             'Voted 2019 country budget €', 'Country share % out of all budget',
                             "Type de financement (tel que présenté dans l'Accord-Cadre 2016-2020)",
                             'iso_alpha'],
                        value_vars=['2019 results','2019 results2','2019 results3','2019 results4',
                                    '2019 results5','2019 results6','2019 results7'],
                        var_name='results',value_name='notes')


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dcc.RadioItems(id='year', options=[{"label": '2018', 'value': '2018'},
                                       {"label": '2019', 'value': '2019'}],
                   value='2018'),
    dcc.Graph(id='treemap',
              figure=px.treemap(df,
                                path=['Country', 'Axis of intervention', 'Region'],
                                color="Country share % out of all budget",
                                values='Voted 2018 project budget €',
                                height=600, width=1450).update_layout(margin=dict(t=25, r=0, l=5, b=20))
              ),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='country-map', config={'displayModeBar':False},
                      figure=px.choropleth(df,
                                           locations="iso_alpha",
                                           hover_name="Country",
                                           scope='africa',
                                           projection='natural earth'
                                           ).update_traces(showlegend=False).update_layout(margin=dict(t=25, r=0, l=5, b=20))
                      )
                 ],width=6),
        dbc.Col([html.Div(id='container')], width=6)
    ])

], fluid=True)


@app.callback(
    Output("treemap", "figure"),
    Input("year","value")
)
def build_treemap(value):
    if value == '2018':
        fig = px.treemap(df,
                   path=['Country', 'Axis of intervention', 'Region'],
                   color="Country share % out of all budget",
                   values='Voted 2018 project budget €',
                   height=600, width=1450).update_layout(
                   margin=dict(t=20, r=0, l=5, b=20))
        return fig
    elif value == '2019':
        fig = px.treemap(df19,
                   path=['Country', 'Axis of intervention', 'Region'],
                   color="Country share % out of all budget",
                   values='Voted 2019 project budget €',
                   height=600, width=1450).update_layout(
                   margin=dict(t=20, r=0, l=5, b=20))
        return fig

@app.callback(
    Output("country-map", "figure"),
    Output("container", "children"),
    Input("treemap","clickData"),
    Input("year","value")
)
def update_modal(data, year):
    # if black frame of treemap, don't update
    if data is None:
        return dash.no_update
    # if no currentpath or country is chosen, don't update
    elif data['points'][0].get('currentPath') is None:
        return dash.no_update

    elif data['points'][0]['currentPath'] == '/':
        if data['points'][0].get('label') is None:
            return dash.no_update
        else:
            label_slct = data['points'][0]['label']
            if year == '2018':
                dff = df[df["Country"] == label_slct]
            if year == '2019':
                dff = df19[df19["Country"] == label_slct]
            extract_country_index = dff[
                dff['Country'] == label_slct].index.values.tolist()
            borders = [1 if i in extract_country_index else 4
                       for i in range(len(dff))]

            # build map
            fig = px.choropleth(dff,
                                locations="iso_alpha",
                                hover_name="Country",
                                scope='africa',
                                projection='natural earth'
                                ).update_traces(marker_line_width=borders,
                                                showlegend=False).update_layout(
                margin=dict(t=25, r=0, l=5, b=20))

            # create the table
            table_header = [html.Thead(html.Tr([html.Th(label_slct)]))]
            rows = []
            for x in dff["notes"]:
                if pd.isnull(x):
                    continue
                rows.append(html.Tr([html.Td(x)]))

            table_body = [html.Tbody(rows)]

            return fig, dbc.Table(table_header + table_body, bordered=True)

    # if axis of intervention is chosen (country is parent), don't update
    elif data['points'][0]['parent'] in df.Country.unique():
        label_slct = data['points'][0]['label']
        parent_slct = data['points'][0]['parent']
        if year == '2018':
            dff = df[(df["Axis of intervention"] == label_slct) &
                     (df["Country"] == parent_slct)]
        if year == '2019':
            dff = df19[(df19["Axis of intervention"] == label_slct) &
                     (df19["Country"] == parent_slct)]
            # make selected countries' borders on map thicker
        extract_country_index = dff[
            dff['Country'] == parent_slct].index.values.tolist()
        borders = [1 if i in extract_country_index else 4
                   for i in range(len(dff))]

        # build map
        fig = px.choropleth(dff,
                            locations="iso_alpha",
                            hover_name="Country",
                            scope='africa',
                            projection='natural earth'
                            ).update_traces(marker_line_width=borders,
                                            showlegend=False).update_layout(
            margin=dict(t=25, r=0, l=5, b=20))

        # create the table
        table_header = [html.Thead(html.Tr([html.Th(label_slct)]))]
        rows = []
        for x in dff["notes"]:
            if pd.isnull(x):
                continue
            rows.append(html.Tr([html.Td(x)]))

        table_body = [html.Tbody(rows)]

        return fig, dbc.Table(table_header + table_body, bordered=True)

    # if Region is chosen, build table
    else:
        label_slct = data['points'][0]['label']
        parent_slct = data['points'][0]['parent']
        print(label_slct), print(parent_slct), print(data)
        if year == '2018':
            dff = df[(df.Region == label_slct) & (
                    df["Axis of intervention"] == parent_slct)]
        if year == '2019':
            dff = df19[(df19.Region == label_slct) & (
                    df19["Axis of intervention"] == parent_slct)]
        # make selected countries' borders on map thicker
        extract_country = data['points'][0]['currentPath']
        extract_country = extract_country.split('/')[1]
        extract_country_index = dff[
            dff['Country'] == extract_country].index.values.tolist()
        borders = [1 if i in extract_country_index else 4
                   for i in range(len(dff))]

        # build map
        fig = px.choropleth(dff,
                            locations="iso_alpha",
                            hover_name="Country",
                            scope='africa',
                            projection='natural earth'
                            ).update_traces(marker_line_width=borders,
                                            showlegend=False).update_layout(
            margin=dict(t=25, r=0, l=5, b=20))

        # create the table
        table_header = [html.Thead(html.Tr([html.Th(label_slct)]))]
        rows = []
        for x in dff["notes"]:
            if pd.isnull(x):
                continue
            rows.append(html.Tr([html.Td(x)]))

        table_body = [html.Tbody(rows)]

        return fig, dbc.Table(table_header + table_body, bordered=True)


if __name__ == '__main__':
    app.run_server(debug=True)
