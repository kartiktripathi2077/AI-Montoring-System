import plotly.graph_objects as go
import calendar
from datetime import datetime


class Graph_Plotly:
    "Class to Create Graphs using the MongoDB Database"

    def __init__(self, database):
        self.database = database  #MongoDB Database object

    def create_graph(self, month_name):
        "Function to create a HTML report Document using Plotly"

        data = self.database.list_collection_names()
        dates = [file.split('_')[1] for file in data]
        d = dict()
        for i in range(len(dates)):
            if calendar.month_name[int(dates[i].split('-')[1])] == month_name:
                #calculating total number of employees present
                d[dates[i]] = self.database[data[i]].estimated_document_count()

        x = list(d.keys())
        y = list(d.values())
        absent = [max(y) - i for i in y]  #Number of absent employees
        fig = go.Figure()
        fig.add_trace(
            go.Bar(x=x, y=y, name="Present", marker_color="rgb(11, 137, 43)"))
        fig.add_trace(
            go.Bar(x=x, y=absent, name="Absent", marker_color='indianred'))
        fig.update_layout(title=f"{month_name} Month's Attendance Report",
                          title_x=0.5,
                          barmode='group',
                          xaxis_tickangle=-70,
                          xaxis_tickfont_size=10,
                          xaxis_title="Dates",
                          yaxis_title="Total Employee's",
                          legend_title="Attendance",
                          xaxis=dict(tickmode='linear'))

        # Creating a report and saving it as an HTML file
        fig.write_html(
            "dashboard\\dashboard_templates\\dashboard\\report.html")

    def create_employee_graph(self, emp_email, month_name, month_data):
        "Function to create a HTML report Document using Plotly for each employee"

        data = self.database[emp_email]
        total_time = []
        idle_time = []

        for i in month_data:
            emp_data = data.find_one({"Date": i})

            if emp_data["Total_Time"]:
                t_time = datetime.strptime(emp_data["Total_Time"], "%H:%M:%S")
                i_time = datetime.strptime(emp_data["Idle_Time"], "%H:%M:%S")
                total_time.append(t_time.hour + (t_time.minute / 60) +
                                  (t_time.second / 3600))
                idle_time.append(i_time.hour + (i_time.minute / 60) +
                                 (i_time.second / 3600))

        fig = go.Figure()
        fig.add_trace(
            go.Bar(x=month_data,
                   y=idle_time,
                   name="Idle Time",
                   marker_color='indianred'))
        fig.add_trace(
            go.Bar(x=month_data,
                   y=total_time,
                   name="Total Time",
                   marker_color="rgb(11, 137, 43)"))

        fig.update_layout(title=emp_data["Name"] +
                          f"'s {month_name} Month Report",
                          title_x=0.5,
                          barmode='group',
                          xaxis_tickangle=-70,
                          xaxis_tickfont_size=10,
                          xaxis_title="Dates",
                          yaxis_title="Time (in Hours)",
                          legend_title="Time",
                          xaxis=dict(tickmode='linear'))

        # Creating a report and saving it as an HTML file
        fig.write_html(
            "dashboard\\dashboard_templates\\dashboard\\report.html")
