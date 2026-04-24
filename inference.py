import mlflow,os,joblib
import pandas as pd


# os.environ['MLFLOW_TRACKING_USERNAME']='ronaksah75'
# os.environ['MLFLOW_TRACKING_PASSWORD']="f0112720c5d8bfcace1909f31c54e3711481166f"
# mlflow.set_tracking_uri("https://dagshub.com/ronaksah75/smart-supply-chain.mlflow")





class Model:
    def __init__(self):
        try:
            # self.config=config
            print("Loading model...")
            # self.model=mlflow.pyfunc.load_model("models:/route_predictor@champion")
            self.model=joblib.load(os.path.join("model.pkl"))
            # self.scaler=mlflow.sklearn.load_model("models:/scaler_model@champion")
            self.scaler=joblib.load(os.path.join("scaler.pkl"))
            print("Model loaded OK:", type(self.model))
        except Exception as e:
            print("MODEL LOAD FAILED:")
            self.model = None
            self.scaler=None

    

    def predict(self,config):

        # df=pd.DataFrame({
        #     "distance_km":[self.config.distance_km],"time_of_day":[self.config.time_of_day],
        #     "day_of_week": [self.config.day_of_week],"weather_condition": [self.config.weather_condition],
        #     "traffic_density_level": [self.config.traffic_density_level],"road_type": [self.config.road_type],
        #     "average_speed_kmph": [self.config.average_speed_kmph]
        # })
        df=pd.DataFrame([config])
        def transform_df(df):

            # day time encodeing
            mapping = {'Morning':1, 'Evening':2, 'Afternoon':3, 'Night':4}
            df['time_of_day'] = df['time_of_day'].map(mapping)

                # week day encoding
            mapping_day_of_week = {'Weekday':1, 'Weekend':2}
            df['day_of_week'] = df['day_of_week'].map(mapping_day_of_week)
                
            # weather encoding
            mapping_weather = {'Clear':1, 'Rain':2, 'Heatwave':3, 'Fog':4}
            df['weather_condition'] = df['weather_condition'].map(mapping_weather)

            # road encoding
            mapping_road = {'Highway':1, 'Inner Road':2, 'Main Road':3}
            df['road_type'] = df['road_type'].map(mapping_road)

            #  traffic encodeing
            mapping_traffic = {'Low':1,'Medium':2, 'High':3, 'Very High':4}
            df['traffic_density_level'] = df['traffic_density_level'].map(mapping_traffic)

   
            X_scaled =self.scaler.transform(df)
            transformed_df = pd.DataFrame(X_scaled, columns=df.columns)
            return transformed_df
        

        # df=df.astype(float)
        scaled_df=transform_df(df)
        y=self.model.predict(scaled_df)

        return y[0]
    





def prediction(config):
    model=Model()
    time = model.predict(config)
    return time