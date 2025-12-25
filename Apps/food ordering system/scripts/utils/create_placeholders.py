"""
Create basic placeholder images for the food ordering system.
This script generates simple colored squares as fallback images.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder_images():
    """Create basic placeholder images for different categories."""
    
    # Create placeholders directory if it doesn't exist
    placeholders_dir = "media/placeholders"
    os.makedirs(placeholders_dir, exist_ok=True)
    
    # Define placeholder configurations
    placeholders = {
        'restaurant_default.jpg': {'size': (800, 600), 'color': '#6366f1', 'text': 'Restaurant'},
        'food_default.jpg': {'size': (600, 400), 'color': '#f97316', 'text': 'Food Item'},
        'user_default.jpg': {'size': (200, 200), 'color': '#8b5cf6', 'text': 'User'},
        'general_default.jpg': {'size': (600, 400), 'color': '#6b7280', 'text': 'Default'},
        
        # Cuisine-specific restaurant placeholders
        'restaurant_italian.jpg': {'size': (800, 600), 'color': '#dc2626', 'text': 'Italian Restaurant'},
        'restaurant_american.jpg': {'size': (800, 600), 'color': '#2563eb', 'text': 'American Restaurant'},
        'restaurant_indian.jpg': {'size': (800, 600), 'color': '#ea580c', 'text': 'Indian Restaurant'},
        'restaurant_japanese.jpg': {'size': (800, 600), 'color': '#16a34a', 'text': 'Japanese Restaurant'},
        'restaurant_mexican.jpg': {'size': (800, 600), 'color': '#eab308', 'text': 'Mexican Restaurant'},
        'restaurant_chinese.jpg': {'size': (800, 600), 'color': '#dc2626', 'text': 'Chinese Restaurant'},
        'restaurant_thai.jpg': {'size': (800, 600), 'color': '#16a34a', 'text': 'Thai Restaurant'},
        'restaurant_mediterranean.jpg': {'size': (800, 600), 'color': '#0891b2', 'text': 'Mediterranean Restaurant'},
        'restaurant_generic.jpg': {'size': (800, 600), 'color': '#6b7280', 'text': 'Restaurant'},
        
        # Food category placeholders
        'pizza.jpg': {'size': (600, 400), 'color': '#dc2626', 'text': 'Pizza'},
        'burger.jpg': {'size': (600, 400), 'color': '#b91c1c', 'text': 'Burger'},
        'pasta.jpg': {'size': (600, 400), 'color': '#f59e0b', 'text': 'Pasta'},
        'chicken.jpg': {'size': (600, 400), 'color': '#f97316', 'text': 'Chicken'},
        'rice.jpg': {'size': (600, 400), 'color': '#eab308', 'text': 'Rice Dish'},
        'dessert.jpg': {'size': (600, 400), 'color': '#ec4899', 'text': 'Dessert'},
        'bread.jpg': {'size': (600, 400), 'color': '#d97706', 'text': 'Bread'},
        'fries.jpg': {'size': (600, 400), 'color': '#fbbf24', 'text': 'Fries'},
        'salad.jpg': {'size': (600, 400), 'color': '#16a34a', 'text': 'Salad'},
        'soup.jpg': {'size': (600, 400), 'color': '#ea580c', 'text': 'Soup'},
        'drink.jpg': {'size': (600, 400), 'color': '#06b6d4', 'text': 'Drink'},
        'menu_item_generic.jpg': {'size': (600, 400), 'color': '#6b7280', 'text': 'Menu Item'},
    }
    
    for filename, config in placeholders.items():
        # Create image with specified color
        img = Image.new('RGB', config['size'], config['color'])
        draw = ImageDraw.Draw(img)
        
        # Add text to center of image
        try:
            # Try to use a larger font
            font_size = min(config['size']) // 10
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Calculate text position
        text_bbox = draw.textbbox((0, 0), config['text'], font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (config['size'][0] - text_width) // 2
        y = (config['size'][1] - text_height) // 2
        
        # Add text with white color for contrast
        draw.text((x, y), config['text'], fill='white', font=font)
        
        # Save the image
        filepath = os.path.join(placeholders_dir, filename)
        img.save(filepath, 'JPEG', quality=85)
        print(f"Created: {filepath}")

if __name__ == "__main__":
    create_placeholder_images()
    print("All placeholder images created successfully!")
