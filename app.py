import socket
import qrcode
from PIL import Image
from flask import Flask, render_template, request, redirect, url_for, jsonify
import time
import threading

# Global variables for tracking start times
start_time_one = None
start_time_two = None

app = Flask(__name__)

# Player information and stopwatches
player_one_name = "Player One"
player_two_name = "Player Two"
player_one_time = 0
player_two_time = 0
running_one = False
running_two = False

# Function to continuously update stopwatches
def update_stopwatches():
    global player_one_time, player_two_time, running_one, running_two
    while True:
        if running_one:
            player_one_time += 0.1  # Increment by 0.1 seconds
            update_obs_text("player_one_time.txt", format_time(player_one_time))
        if running_two:
            player_two_time += 0.1  # Increment by 0.1 seconds
            update_obs_text("player_two_time.txt", format_time(player_two_time))
        time.sleep(0.1)  # Update every 0.1 seconds for tenths of a second


# Function to format time in MM:SS:Milliseconds (Tenths of a second)
def format_time(elapsed_time):
    minutes, rem = divmod(elapsed_time, 60)
    seconds = rem % 60
    tenths_of_second = (elapsed_time * 10) % 10  # Tenths of a second
    return f"{minutes:02}:{int(seconds):02}.{int(tenths_of_second):01}"



# Function to update the text file that OBS reads
def update_obs_text(filename, content):
    with open(filename, "w") as f:
        f.write(content)

# Start the background thread to update stopwatches continuously
stopwatch_thread = threading.Thread(target=update_stopwatches, daemon=True)
stopwatch_thread.start()

# Flask Routes
@app.route('/')
def index():
    global player_one_name, player_two_name, player_one_time, player_two_time
    return render_template('index.html', 
                           player_one_name=player_one_name, 
                           player_two_name=player_two_name,
                           player_one_time=format_time(player_one_time),
                           player_two_time=format_time(player_two_time))

# Endpoint to fetch the current stopwatch times as JSON
@app.route('/get_times')
def get_times():
    return jsonify({
        'player_one_time': format_time(player_one_time),
        'player_two_time': format_time(player_two_time)
    })


@app.route('/set_player', methods=['POST'])
def set_player():
    global player_one_name, player_two_name
    if request.form['player'] == 'one':
        player_one_name = request.form['name']
        update_obs_text("player_one_name.txt", player_one_name)  # Save Player 1 name
    else:
        player_two_name = request.form['name']
        update_obs_text("player_two_name.txt", player_two_name)  # Save Player 2 name
    return redirect(url_for('index'))

@app.route('/start_stop', methods=['POST'])
def start_stop():
    global running_one, running_two
    if request.form['player'] == 'one':
        running_one = not running_one  # Toggle the stopwatch on/off for Player 1
    else:
        running_two = not running_two  # Toggle the stopwatch on/off for Player 2
    return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset():
    global player_one_time, player_two_time
    if request.form['player'] == 'one':
        player_one_time = 0
        update_obs_text("player_one_time.txt", format_time(player_one_time))  # Reset Player 1 time
    else:
        player_two_time = 0
        update_obs_text("player_two_time.txt", format_time(player_two_time))  # Reset Player 2 time
    return redirect(url_for('index'))

# Get the local IP address
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable, just a common local address
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# Generate QR code for the Flask app URL
def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img.save("qr_code.png")
    img.show()  # Display the QR code for scanning

if __name__ == '__main__':
    # Get local IP and port
    ip_address = get_local_ip()
    port = 5000
    url = f"http://{ip_address}:{port}/"

    # Generate and show QR code
    generate_qr_code(url)

    # Start the Flask server
    app.run(host='0.0.0.0', port=port, debug=True)
