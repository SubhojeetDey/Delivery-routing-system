import pandas as pd

def generate_coordinates():
    data = {
        "State": [
            "Maharashtra", "Maharashtra", "Tamil Nadu", "Tamil Nadu", 
            "Karnataka", "Karnataka", "Uttar Pradesh", "Uttar Pradesh", 
            "Gujarat", "Gujarat","Maharashtra", "Maharashtra", "Tamil Nadu",
            "Karnataka", "Uttar Pradesh", "Gujarat","West Bengal","West Bengal",
            "West Bengal","West Bengal","West Bengal"
        ],
        "Airport": [
            "Nagpur Intl", "Nashik Airport", "Coimbatore Intl", "Madurai Airport",
            "Mangaluru Intl", "Hubballi Airport", "Varanasi Intl", "Prayagraj Airport",
            "Surat Intl", "Vadodara Airport","Mumbai Intl", "Pune Airport", "Chennai Intl", 
            "Bengaluru Intl", "Lucknow Intl", "Ahmedabad Intl","Kolkata Intl", "Bagdogra Intl", 
            "Durgapur (RDP)", "Cooch Behar", "Balurghat"
        ],
        "Lat": [
            21.0922, 20.1194, 11.0297, 9.8344, 
            12.9614, 15.3617, 25.4522, 25.4400, 
            21.1177, 22.3294,19.0896, 18.5822, 
            12.9941, 13.1986, 26.7606, 23.0772,
            22.6547, 26.6812, 23.6231, 26.3283, 25.2617
        ],
        "Long": [
            79.0472, 73.9136, 77.0434, 78.0933, 
            74.8900, 75.0847, 82.8594, 81.7339, 
            72.7453, 73.2194,72.8656, 73.9197, 
            80.1708, 77.7066, 80.8892, 72.6347,
            88.4467, 88.3286, 87.2422, 89.4632, 88.7956

        ]
    }

    df = pd.DataFrame(data)
    return df


df=generate_coordinates()
df.to_csv("india_logistics_airports.csv", index=False)

print(f"Total Airports Generated: {len(df)}")
print(df.tail(10))