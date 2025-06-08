# delete all images in /images

import os


for root, dirs, files in os.walk('images'):
    for file in files:
        file_path = os.path.join(root, file)
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
            
            