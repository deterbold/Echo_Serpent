import openai
import os
import shutil
import requests
from datetime import datetime
import json
import base64

# Replace 'your_api_key_here' with your actual OpenAI API key
openai.api_key = 'your_api_key_here'
theModel = "gpt-4-vision-preview"
originalPrompt = ""
original_image_filename = ""



# Ensure the 'data' directory exists
data_dir = 'data'
os.makedirs(data_dir, exist_ok=True)

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def createJSON(originalPrompt, revisedPrompt, imageURL):

    generated_image_filename = f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    download_image(imageURL, os.path.join(data_dir, generated_image_filename))
    download_image(original_image_filename, os.path.join(data_dir, original_image_filename))

    # Prepare data for the JSON file
    data = {
        "date_generated": datetime.now().strftime('%Y-%m-%d'),
        "time_generated": datetime.now().strftime('%H:%M:%S'),
        "model": theModel,
        "original_prompt": originalPrompt,
        "revised_prompt": revisedPrompt,
        "original_image_filename": original_image_filename,
        "generated_image_filename": generated_image_filename
    }

    # Create a JSON file with the data
    json_filename = f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    create_json_file(data, os.path.join(data_dir, json_filename))

def create_json_file(data, filename):
    """Create a JSON file with the given data."""
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def save_image(image_path, destination_folder):
    """Save a copy of the image to the specified folder."""
    shutil.copy(image_path, destination_folder)

def download_image(image_url, destination_path):
    """Download an image from a URL and save it to a specified path."""
    response = requests.get(image_url)
    with open(destination_path, 'wb') as file:
        file.write(response.content)

def process_image(image_path):
    """Process an image: analyze, generate a new image, and save relevant data."""
    # Save a copy of the original image in the 'data' folder
    original_image_filename = encode_image(os.path.basename(image_path))

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What’s in this image?"},
                        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{original_image_filename}"},
                    ],
                }
            ],
            max_tokens=300,
        )

        # Extracting the analysis result
        original_prompt = response.choices[0].message['content']
        print(original_prompt)
        generateImage(original_prompt)
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    
    
def generateImage(originalPrompt):
    
    try:
        response = openai.Image.create(
            model="dall-e-3",
            prompt=originalPrompt,
            n=1,
            size="1024x1024"
        )

        # Assuming 'response' contains a direct URL or data for the generated image
        print(response)
        revised_prompt = response.data[0].revised_prompt
        imageURL = response.data[0].url

        createJSON(originalPrompt, revised_prompt, imageURL)
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    image_path = '/path/to/your/image.jpg'  # Replace with the path to your image
    process_image(image_path)
