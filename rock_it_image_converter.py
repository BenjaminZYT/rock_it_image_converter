import base64
import io
from PIL import Image
import pillow_heif  # Needed for HEIC support
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.dependencies import Input, Output, State
from dash_extensions import Download
from dash_extensions.snippets import send_file

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# -----------------------------------------------------------------------------
# Layout
# -----------------------------------------------------------------------------
app.layout = dbc.Container(
    [
        html.H2("Image Converter App"),
        html.Hr(),

        # 1. File Upload
        dcc.Upload(
            id="upload-image",
            children=html.Div(
                [
                    "Drag and Drop or ",
                    html.A("Click to Select a File")
                ],
                style={
                    "width": "100%",
                    "height": "60px",
                    "lineHeight": "60px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "5px",
                    "textAlign": "center",
                    "margin": "10px 0"
                }
            ),
            multiple=False,  # Single file at a time
        ),

        # Display message: "File has been uploaded"
        html.Div(id="upload-message", style={"margin": "10px 0", "color": "green"}),

        # 2. Dropdown to select output image format
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Select output format:"),
                        dcc.Dropdown(
                            id="image-format-dropdown",
                            options=[
                                {"label": "JPEG", "value": "jpeg"},
                                {"label": "PNG", "value": "png"},
                                {"label": "BMP", "value": "bmp"},
                                {"label": "TIFF", "value": "tiff"},
                                {"label": "GIF", "value": "gif"},
                            ],
                            value=None,
                            placeholder="Choose an image format",
                            clearable=False,
                        ),
                    ],
                    md=6
                ),
            ]
        ),

        html.Br(),

        # 3. Convert and Download Button
        dbc.Button("Convert and Download", id="convert-download-btn", color="primary", disabled=True),

        # 4. Download component from dash-extensions
        Download(id="download-image-file"),

        html.Br(),
        html.Br(),

        # Display status messages
        html.Div(id="status-message", style={"color": "blue"}),

        html.Br(),

        # 5. Reset Button
        dbc.Button("Reset", id="reset-btn", color="secondary"),

        # Hidden Store to keep the uploaded file content
        dcc.Store(id="uploaded-image-store"),
    ],
    fluid=True
)

# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------

@app.callback(
    Output("upload-message", "children"),
    Output("uploaded-image-store", "data"),
    Output("convert-download-btn", "disabled"),
    Input("upload-image", "contents"),
    State("upload-image", "filename"),
    prevent_initial_call=True
)
def store_uploaded_image(contents, filename):
    """
    This callback triggers when the user uploads a file.
    We parse the base64, store it in dcc.Store, and display a success message.
    """
    if contents is not None:
        # contents format: "data:image/png;base64,...."
        # We only need the base64 part after the comma
        base64_data = contents.split(",")[1]

        return f"File '{filename}' has been uploaded!", base64_data, False
    else:
        return "", None, True


@app.callback(
    Output("download-image-file", "data"),
    Output("status-message", "children"),
    Input("convert-download-btn", "n_clicks"),
    State("uploaded-image-store", "data"),
    State("image-format-dropdown", "value"),
    prevent_initial_call=True
)
def convert_and_download(n_clicks, image_data, selected_format):
    """
    When 'Convert and Download' is clicked, 
    1. Convert the stored image to the selected format,
    2. Trigger file download,
    3. Return appropriate status messages.
    """
    if not image_data:
        return None, "No file to convert!"

    # If user hasn't selected a format yet
    if not selected_format:
        return None, "Please select an output format before converting."

    # Decode the base64 into bytes
    img_bytes = base64.b64decode(image_data)

    # Open the image with PIL
    with Image.open(io.BytesIO(img_bytes)) as pil_image:
        # Convert to RGB if 'P' or 'RGBA' etc. 
        # (Some formats don't like alpha channels or indexed colors.)
        if pil_image.mode in ("RGBA", "P"):
            pil_image = pil_image.convert("RGB")

        # Prepare an in-memory buffer to save the converted image
        buf = io.BytesIO()
        pil_image.save(buf, format=selected_format.upper())
        buf.seek(0)

    # Construct filename for the download
    download_filename = f"converted_image.{selected_format.lower()}"

    # This triggers the download using dash_extensions
    download_data = send_file(buf, download_filename, mime_type=f"image/{selected_format}")

    # Return the download data and a success message
    return download_data, "Converted image file downloaded!"


@app.callback(
    Output("upload-image", "contents"),
    Output("upload-message", "children"),
    Output("uploaded-image-store", "data"),
    Output("convert-download-btn", "disabled"),
    Output("image-format-dropdown", "value"),
    Output("status-message", "children"),
    Input("reset-btn", "n_clicks"),
    prevent_initial_call=True
)
def reset_app(n_clicks):
    """
    Resets the entire app to its original state:
    - Clears the uploaded file contents
    - Clears the upload message
    - Clears the store
    - Disables the Convert button
    - Resets the dropdown
    - Clears status messages
    """
    return None, "", None, True, None, ""


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=False)
