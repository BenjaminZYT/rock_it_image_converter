import dash
from dash import dcc, html, Input, Output, State
import dash_uploader as du
import os
from PIL import Image
import shutil

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server
UPLOAD_FOLDER = "./uploads"
CONVERTED_FOLDER = "./converted"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

# Configure Dash Uploader
du.configure_upload(app, UPLOAD_FOLDER)

app.layout = html.Div([
    html.H1("Image File Converter"),
    du.Upload(id='uploader',
              text="Drag and Drop or Click to Upload",
              text_completed="File Uploaded!",
              filetypes=['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif', 'heic'],
              max_file_size=1800),  # Max size in MB
    html.Div(id='upload-status', style={"marginTop": "20px", "color": "green"}),

    html.Label("Select Output Format:"),
    dcc.Dropdown(
        id='format-dropdown',
        options=[
            {"label": ext.upper(), "value": ext} for ext in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif']
        ],
        placeholder="Select a format",
        style={"width": "50%"}
    ),

    html.Button("Convert and Download", id='convert-button', n_clicks=0),
    html.Div(id='conversion-status', style={"marginTop": "20px", "color": "blue"}),

    html.Button("Reset", id='reset-button', n_clicks=0, style={"marginTop": "20px"})
])

@app.callback(
    Output('upload-status', 'children'),
    Input('uploader', 'isCompleted'),
    State('uploader', 'fileNames'),
    State('uploader', 'filePaths')
)
def file_uploaded(is_completed, filenames, filepaths):
    if is_completed and filenames and filepaths:
        # Save the uploaded file manually to the UPLOAD_FOLDER
        for filepath, filename in zip(filepaths, filenames):
            shutil.move(filepath, os.path.join(UPLOAD_FOLDER, filename))
        return f"File '{filenames[0]}' has been uploaded."
    return ""

@app.callback(
    Output('conversion-status', 'children'),
    [Input('convert-button', 'n_clicks'),
     Input('reset-button', 'n_clicks')],
    [State('uploader', 'fileNames'),
     State('format-dropdown', 'value')]
)
def convert_and_download(n_convert, n_reset, filenames, output_format):
    ctx = dash.callback_context
    if not ctx.triggered:
        return ""

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'reset-button':
        return ""

    if not filenames or not output_format:
        return "Please upload a file and select an output format."

    input_file = os.path.join(UPLOAD_FOLDER, filenames[0])
    base_filename = os.path.splitext(filenames[0])[0]
    output_file = os.path.join(CONVERTED_FOLDER, f"{base_filename}.{output_format}")

    try:
        with Image.open(input_file) as img:
            img.convert("RGB").save(output_file, format=output_format.upper())
        
        # Provide a download link
        return html.A("Converted image file downloaded! Click here to download.",
                     href=f"/converted/{base_filename}.{output_format}",
                     download=f"{base_filename}.{output_format}",
                     style={"color": "green"})
    except Exception as e:
        return f"An error occurred during conversion: {e}"

@app.callback(
    [Output('upload-status', 'children'),
     Output('conversion-status', 'children'),
     Output('format-dropdown', 'value'),
     Output('uploader', 'isCompleted')],
    Input('reset-button', 'n_clicks')
)
def reset_app(n_reset):
    if n_reset > 0:
        return "", "", None, False
    return dash.no_update

# Serve converted files
@app.server.route('/converted/<filename>')
def serve_converted_file(filename):
    return dash.server.send_from_directory(CONVERTED_FOLDER, filename)

if __name__ == "__main__":
    app.run_server(debug=False)
