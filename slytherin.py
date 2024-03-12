from openai import OpenAI
import os
import shutil
import requests
from datetime import datetime
import json
import base64

api_key = os.getenv('OPENAI_API_KEY')

if api_key is None:
    print("Please set the OPENAI_API_KEY environment variable.")
else:
    # Now you can use the API key, for example:
    client = OpenAI(api_key=api_key)
    print("API key found.")

# Replace 'your_api_key_here' with your actual OpenAI API key
theModel = "gpt-4-vision-preview"
originalPrompt = ""
revisedPrompt = ""
original_image_filename = ""
generated_image_filename = ""
imageURL = ""
image_path = ""
image_specific_dir = ""

# Ensure the 'data' directory exists
data_dir = 'data'
os.makedirs(data_dir, exist_ok=True)

def copy_jpeg_to_data_folder(jpeg_file_path, image_specific_dir):
    # Check if the file exists
    if not os.path.isfile(jpeg_file_path):
        print(f"The file {jpeg_file_path} does not exist. Please check the path.")
        print(f"Current working directory: {os.getcwd()}")
        return
    
    # Define the destination folder
    data_folder = image_specific_dir
    
    # Ensure the 'data' directory exists, create if it does not
    os.makedirs(data_folder, exist_ok=True)
    
    # Extract the filename from the given path
    filename = os.path.basename(jpeg_file_path)
    
    # Define the destination path for the copied file
    destination_path = os.path.join(data_folder, filename)
    
    # Copy the file to the destination
    shutil.copy(jpeg_file_path, destination_path)
    print(f"File {filename} copied to {data_folder} folder.")


def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def createJSON(originalPrompt, revisedPrompt, generated_image_filename, image_specific_dir):
    print("in createJSON")
    print("image specific dir: ", image_specific_dir)
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
    #create_json_file(data, os.path.join(data_dir, json_filename))
    print(os.path.join(data_dir, json_filename))
    create_json_file(data, os.path.join(image_specific_dir, json_filename))

def create_json_file(data, filename):
    """Create a JSON file with the given data."""
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def save_image(image_path, destination_folder):
    #print("Image path: ", image_path)
    """Save a copy of the image to the specified folder."""
    shutil.copy(image_path, destination_folder)

def download_image(image_url, destination_path):
    """Download an image from a URL and save it to a specified path."""
    response = requests.get(image_url)
    with open(destination_path, 'wb') as file:
        file.write(response.content)

def process_image(image_path):
    """Process an image: analyze, generate a new image, and save relevant data."""

    # Extract the base filename (without extension) to use as the folder name
    base_filename = os.path.splitext(os.path.basename(image_path))[0]
    
    # Create a new directory for this specific image processing
    image_specific_dir = os.path.join(data_dir, base_filename)
    os.makedirs(image_specific_dir, exist_ok=True)
    print ("image_specific_dir: ", image_specific_dir)
    copy_jpeg_to_data_folder(image_path, image_specific_dir)


    # Save a copy of the original image in the 'data' folder
    original_image_filename = encode_image(image_path)
    #download_image(original_image_filename, os.path.join(data_dir, original_image_filename))

    try:
        response = client.chat.completions.create(model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What’s in this image?"},
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{original_image_filename}"},
                ],
            }
        ],
        max_tokens=300)

        # Extracting the analysis result
        original_prompt = response.choices[0].message.content
        print(original_prompt)
        print("before generateImage")
        print(image_specific_dir)
        generateImage(original_prompt, image_specific_dir)
        
        
    except Exception as e:
        print(f"Error in process image: {e}")
        return None
    
def generateImage(originalPrompt, image_specific_dir):
    print("in generateImage")
    print("image_specific_dir: ", image_specific_dir)
    
    try:
        response = client.images.generate(model="dall-e-3",
        prompt=originalPrompt,
        n=1,
        size="1024x1024")

        revised_prompt = response.data[0].revised_prompt
        imageURL = response.data[0].url
        generated_image_filename = f"generated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        print(generated_image_filename)
        download_image(imageURL, os.path.join(image_specific_dir, generated_image_filename))

        createJSON(originalPrompt, revised_prompt, generated_image_filename, image_specific_dir)
    
    except Exception as e:
        print(f"Error in generate image: {e}")

def process_all_images_in_folder(folder_path):
    # List all files in the given directory
    all_files = os.listdir(folder_path)

    # Filter out JPEG files
    jpeg_files = [file for file in all_files if file.lower().endswith(('.jpg', '.jpeg'))]

    # Process each JPEG file
    for jpeg_file in jpeg_files:
        image_path = os.path.join(folder_path, jpeg_file)
        print(f"Processing {image_path}...")
        #process_image(image_path)  # Assuming process_image is defined as before


if __name__ == '__main__':
    # image_path = '/Users/miguelsicart/Making/Echo_Serpent/sourceImages/test_image.jpeg'  # Replace with the path to your image
    # process_image(image_path)
    process_all_images_in_folder('/Users/miguelsicart/Making/Echo_Serpent/sourceImages')