import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, callback, State
import dash_bootstrap_components as dbc
import threading
import webbrowser
import time
import os
import signal
import flask
from dash.dependencies import Input, Output

class RadarPlotApp:
    def __init__(self):
        # Initialize app with server
        server = flask.Flask(__name__)
        self.app = Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.emojis = ["😀", "😃", "😄", "😁", "😆", "😊"]
        self.current_angle = 0
        self.current_neck_angle = 0
        self.current_area = 0.5
        self.server_thread = None
        self.port = 8050
        
        # Setup layout with refresh interval
        self.app.layout = dbc.Container([
            html.H1("Spatial Memory Radar"),
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Label("Angle (0-360)"),
                        dcc.Slider(0, 360, 20, value=0, id='angle-slider')
                    ], width=6),
                    dbc.Col([
                        html.Label("Area (0-1)"),
                        dcc.Slider(0, 1, 0.1, value=0.5, id='area-slider')
                    ], width=6)
                ]),
                html.Br(),
                dcc.Graph(id='radar-plot', style={'height': '1500px'}),
                
                # Hidden div for storing current values
                html.Div(id='current-values', style={'display': 'none'}),
                
                # Interval component for auto-refresh (500ms)
                dcc.Interval(id='interval-component', interval=500, n_intervals=0)
            ])
        ])
        
        # Setup radar plot callback from sliders
        @self.app.callback(
            [Output('radar-plot', 'figure'),
             Output('current-values', 'children')],
            [Input('angle-slider', 'value'),
             Input('area-slider', 'value')]
        )
        def update_from_sliders(angle, area):
            self.current_angle = angle
            self.current_area = area
            return self.create_figure(angle, area), f"{angle},{area}"
        
        # Setup auto-update callback from interval
        @self.app.callback(
            Output('radar-plot', 'figure', allow_duplicate=True),
            Input('interval-component', 'n_intervals'),
            State('current-values', 'children'),
            prevent_initial_call=True
        )
        def update_from_interval(n, current_values):
            # Only update if values have changed from what's currently displayed
            if current_values:
                stored_angle, stored_area = map(float, current_values.split(','))
                if stored_angle != self.current_angle or stored_area != self.current_area or self.current_neck_angle != self.current_neck_angle:
                    return self.create_figure(self.current_angle, self.current_area, entity_name="Unknown")
            
            # Return no update if values haven't changed
            from dash.exceptions import PreventUpdate
            raise PreventUpdate
    
    def create_figure_backup(self, angle, area):
        """Create the radar plot figure"""
        fig = go.Figure()
        
        # Add robot emoji at center
        fig.add_trace(go.Scatterpolar(
            r=[0],
            theta=[0],
            mode='text',
            text=["🤖"],
            textfont_size=80,
            name="🤖"
        ))
        
        # Add emoji at position
        fig.add_trace(go.Scatterpolar(
            r=[area],
            theta=[angle],
            mode='text',
            text=[self.emojis[0]],
            textfont_size=60,
            name=self.emojis[0]
        ))
        
        # Configure plot appearance
        fig.update_polars(radialaxis_showgrid=False)
        fig.update_layout(
            polar_angularaxis_direction="clockwise", 
            polar_angularaxis_rotation=90,
            polar=dict(
                radialaxis=dict(
                    showticklabels=False,
                    ticks='',
                    range=[0, 1]
                )
            )
        )
        
        return fig

    def create_figure(self, angle, area, entity_name="Unknown"):
        """Create the radar plot figure"""
        fig = go.Figure()
        
        # Add robot emoji at center
        fig.add_trace(go.Scatterpolar(
            r=[0],
            theta=[0],
            mode='text',
            text=["🤖"],
            textfont_size=80,
            name="🤖"
        ))
        
        # Add emoji at position
        fig.add_trace(go.Scatterpolar(
            r=[area],
            theta=[angle],
            mode='text',
            text=[self.emojis[0]],
            textfont_size=60,
            name=self.emojis[0]
        ))
        
        # Add color sector from -45 to +45 degrees
        fig.add_trace(go.Scatterpolar(
            r=[0, 1, 1, 0],  # Radius for the sector
            theta=[-45, -45, 45, 45],  # Angles for the sector (-45 to +45 degrees)
            fill='toself',  # Fill the area
            fillcolor='rgba(255, 99, 71, 0.6)',  # Color of the sector (tomato with transparency)
            line=dict(color='rgba(255, 99, 71, 0.6)', width=0),  # No border line
            name="Special Sector"
        ))

        # Configure plot appearance
        fig.update_polars(radialaxis_showgrid=False)
        fig.update_layout(
            polar_angularaxis_direction="clockwise", 
            polar_angularaxis_rotation=90,
            polar=dict(
                radialaxis=dict(
                    showticklabels=False,
                    ticks='',
                    range=[0, 1]
                )
            )
        )
    
        return fig
    
    def _run_server(self, debug=False):
        """Internal method to run the server"""
        self.app.run(debug=debug, port=self.port, use_reloader=False)
    
    def start_server(self, open_browser=True):
        """Start the Dash server in a separate thread"""
        self.server_thread = threading.Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Give the server a moment to start
        time.sleep(1)
        
        # Open web browser automatically if requested
        if open_browser:
            webbrowser.open(f'http://localhost:{self.port}/')
        
        print(f"Dash server running in background on http://localhost:{self.port}/")
        return self.server_thread
    
    def stop_server(self):
        """Stop the Dash server"""
        os.kill(os.getpid(), signal.SIGINT)
        
        if self.server_thread:
            self.server_thread.join(timeout=1)
            print("Dash server stopped")
    
    def update_data(self, angle, current_neck_angle, area):
        """Update the plot data - will be automatically reflected in UI"""
        self.current_angle = angle
        self.current_neck_angle = current_neck_angle
        self.current_area = area
        # UI will update on next interval trigger