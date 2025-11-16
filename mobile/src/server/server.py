import subprocess
import psutil
import os
import asyncio
from io import BytesIO

from pathlib import Path
from flask import Flask, jsonify, request, send_file
from PIL import Image
from dotenv import load_dotenv

from uuid import uuid4

from src.intent import IntentService
from src.locus import LocusMCPClient

load_dotenv()

app = Flask(__name__)
ngrok_process = None

@app.route('/')
def hello_world():
    return 'Hello, Teej'

@app.route('/locus/intent/prompt', methods=['GET'])
def intent_prompt():
    return jsonify({
        'prompt': '''
SYSTEM PROMPT: Shopping-From-Screenshot Agent

You are a Shopping Assistant AI that helps users buy items they point out from an uploaded screenshot.

Interaction Flow

1. Greet & Ask

When a screenshot is provided, examine it and respond with a friendly opener such as:
	•	“What would you like from this image?”
	•	“Tell me which item you’re interested in.”

2. Clarify User Intent

After the user selects an item, ask 2–3 short clarifying questions required to fully identify it:
	•	variant / model / style
	•	size, color, or material
	•	visible distinguishing features
	•	any preferences the user expresses

Questions must be concise and directly tied to the image.

3. AI Provides Budget Estimate

After the user answers:
	1.	You estimate a reasonable price range for the item.
	2.	Present it like:
	•	“This will probably cost around $X–$Y. Does that work for you?”
	3.	The user only confirms or declines—never provides their own number first.

4. Final Confirmation

When the user confirms the budget:
	1.	Acknowledge the confirmation.
	2.	Say you will go work on getting the item and follow up later.
	3.	Provide a long, fully detailed final item description that summarizes everything the user clarified:
	•	item name / type
	•	color / size / material
	•	important visible features
	•	style cues or brand-like qualities
	•	any user preferences
	•	context from the screenshot (e.g., “the blue one on the left”)
	•	the max price from your estimate
	4.	Phrase it as something you will use to locate the item, e.g.:
“Great, I’ll start working on this now and follow up once it’s ordered.
Here is the detailed item description I will use to locate it (including the max price):
<long, thorough, all-details description + max price>”

Behavior Rules
	•	Stay fully in character as a shopping assistant.
	•	Never mention screenshots or image analysis explicitly—act like you see the content naturally.
	•	Never mention that you are an AI.
	•	Keep responses short during the interaction, except for the final item description, which should be detailed.
	•	Never show internal reasoning.
	•	Do not actually place orders—just say you’ll work on it.
	•	The final message must always include:
	1.	A long, comprehensive description containing all known details about the item
	2.	The max price from your estimate
         '''
    })

@app.route('/locus/image', methods=['POST'])
def upload_image():
    # Try to get image from files (multipart/form-data)
    if 'image' in request.files:
        file = request.files['image']
        image = Image.open(file.stream)
    # Try to get image from raw data
    elif request.data:
        image = Image.open(BytesIO(request.data))
    # Try to get image path from JSON
    elif request.is_json:
        data = request.get_json()
        image_path = data.get('image_path')
        if image_path:
            image = Image.open(image_path)
        else:
            return jsonify({"error": "No image provided"}), 400
    else:
        return jsonify({"error": "No image provided"}), 400
    
    # Save the image to images/locus/image.png
    output_dir = Path("images/locus")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "image.png"
    image.save(output_path)
    
    return jsonify({"status": "Image saved successfully", "path": str(output_path)})

@app.route('/locus/intent', methods=['POST'])
def make_intent():
    data = request.get_json(force=True) or {}
    item_description = data.get("item_description")
    price = data.get("price")
        
    intent_service = IntentService()
    
    image_uuid = uuid4()
    
    with open("images/locus/image.png", "rb") as f:
        image_bytes = f.read()
        
    intent_service.upload_image(
        image_uuid=f"{image_uuid}.png",
        image_data=image_bytes  # Pass bytes directly
    )
    
    intent_service.create_intent(
        user_id="dce043c3-6786-40c5-956c-69a65a9fb772",
        image_uuid=f"{image_uuid}",
        description=item_description,
        max_amount_usd=float(price)
    )
    
    return jsonify({})

@app.route('/locus/pay', methods=['POST'])
def make_payment():
    data = request.get_json(force=True) or {}
    price = data.get('price')
    
    if price is None:
        return jsonify({"error": "price is required"}), 400
    
    async def send_payment():
        api_key = os.getenv('LOCUS_API_KEY')
        if not api_key:
            raise ValueError("LOCUS_API_KEY not found in environment variables")
        client = LocusMCPClient(api_key=api_key)
        result = await client.send_to_address(
            address='0xfb7d867d5f0d92c784aac2b7a9df17557c8bfc47',
            amount=float(price),
            memo='hi ty'
        )
        return result
    
    try:
        result = asyncio.run(send_payment())
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def start_server(port=3000):
    """Start the Flask server and ngrok tunnel"""
    global ngrok_process
    
    # Start ngrok in the background
    ngrok_cmd = f"ngrok start --all"
    ngrok_process = subprocess.Popen(
        ngrok_cmd.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Start Flask server
    app.run(host='0.0.0.0', port=port, debug=True)
    
def stop_server():
    """Stop both the Flask server and ngrok tunnel"""
    global ngrok_process
    
    # Kill ngrok process
    if ngrok_process:
        ngrok_process.terminate()
        try:
            ngrok_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ngrok_process.kill()
        ngrok_process = None
    
    # Kill any remaining processes on the port
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.connections():
                if conn.laddr.port == 3000:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass 