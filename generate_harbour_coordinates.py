import pandas as pd

def generate_seaport_coordinates():
    data = {
        "State": [
            "West Bengal", "Odisha", "Andhra Pradesh", "Tamil Nadu", 
            "Tamil Nadu", "Tamil Nadu", "Kerala", "Karnataka", 
            "Goa", "Maharashtra", "Maharashtra", "Gujarat", 
            "Gujarat", "Andhra Pradesh"
        ],
        "Port_Name": [
            "Haldia Port", "Paradip Port", "Visakhapatnam Port", "Chennai Port",
            "Ennore (Kamarajar) Port", "V.O. Chidambaranar (Tuticorin)", "Cochin Port", "New Mangalore Port",
            "Mormugao Port", "Mumbai Port Trust", "Jawaharlal Nehru Port (JNPT)", "Kandla (Deendayal) Port",
            "Mundra Port", "Gangavaram Port"
        ],
        "Lat": [
            22.0667, 20.2744, 17.6868, 13.1011, 
            13.2611, 8.7534, 9.9637, 12.9257, 
            15.4111, 18.9438, 18.9500, 23.0100, 
            22.7373, 17.6200
        ],
        "Long": [
            88.0698, 86.6744, 83.2185, 80.2931, 
            80.3339, 78.1974, 76.2653, 74.8183, 
            73.7956, 72.8422, 72.9500, 70.2100, 
            69.7075, 83.2400
        ],
        "Type": [
            "Major", "Major", "Major", "Major", 
            "Major", "Major", "Major", "Major", 
            "Major", "Major", "Major", "Major", 
            "Private/Large", "Private/Large"
        ]
    }

    df = pd.DataFrame(data)
    return df



df_ports = generate_seaport_coordinates()
df_ports.to_csv("india_logistics_seaports.csv", index=False)

print(f"Total Seaports Generated: {len(df_ports)}")
print(df_ports.head(10))