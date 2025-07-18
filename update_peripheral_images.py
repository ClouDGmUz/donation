import sqlite3

# Connect to the database
conn = sqlite3.connect('donations.db')
cursor = conn.cursor()

# Update gaming peripherals to use local images
peripheral_updates = [
    ('ASUS ROG Swift PG32UQX', '/static/images/display.jpg'),
    ('Logitech G Pro X Superlight', '/static/images/mouse.jpg'),
    ('SteelSeries Arctis Pro Wireless', '/static/images/headset.jpg')
]

for component_name, local_image_path in peripheral_updates:
    cursor.execute(
        'UPDATE components SET image_url = ? WHERE name = ?',
        (local_image_path, component_name)
    )
    print(f"Updated {component_name} to use {local_image_path}")

# Commit changes and close connection
conn.commit()
conn.close()

print("Database updated successfully with local image paths for gaming peripherals!")