from fastapi import FastAPI,Depends,HTTPException,Request,UploadFile,File,Form
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
import settings,getapis,utils,json
from datetime import datetime,timedelta
from starlette.concurrency import run_in_threadpool
from PIL import UnidentifiedImageError
from database import get_db,Base,engine
import models,schemas,auths,osrm
import image_utils,cv2,uuid
import numpy as np
from typing_extensions import Annotated,List,Optional
from sqlalchemy.orm import Session
from sqlalchemy import select,func


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow all origins (⚠️ not recommended for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all domains
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

Base.metadata.create_all(engine)

db_dependency = Annotated[Session,Depends(get_db)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/user/Login/')

app.mount("/media", StaticFiles(directory="media"), name="media")

@app.post('/user/Signup/',tags=['Auth'],status_code=200)
async def createUser(req:schemas.User,user_agent:Request,db:db_dependency):
    user = db.query(models.User).filter(models.User.username==req.username).first()
    if user:
        raise HTTPException(status_code=400,detail="Username is already used.")
    new_user = models.User(
        username=req.username,
        password=auths.hashed_password(req.password),
        email=req.email
    )
    new_log = models.Log(
        status="Account created.",
        user_agent=str(user_agent.headers.get("user-agent"))
    )
    new_user.logs.append(new_log)
    profile = models.Profile(
        role=req.role,
        address=req.address,
        work_location=req.work_location
    )
    new_user.profile=profile
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "detail":"User created."
    }

@app.post('/user/Login/',tags=['Auth'],response_model=schemas.Token)
async def loginUser(request:Annotated[OAuth2PasswordRequestForm,Depends()],user_agent:Request,db:db_dependency):
    user = auths.authenticate_user(username=request.username,password=request.password,db=db)
    ref_time = datetime.utcnow() - timedelta(minutes=5)
    if user is not False:
        latest_log = db.query(models.Log).filter(
            models.Log.user_id == user.user_id
        ).order_by(models.Log.id.desc()).first()
        if latest_log and latest_log.created_at > ref_time and latest_log.status=="Logged in":
            raise HTTPException(status_code=400,detail="Login Session not expired")
        token = auths.create_access_token(user.user_id,user.username,timedelta(minutes=5))
        new_log = models.Log(
            status="Logged in",
            user_id=user.user_id,
            user_agent=str(user_agent.headers.get("user-agent")),
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return schemas.Token(
            access_token=token,
            token_type='bearer'
        )
    else:
        raise HTTPException(status_code=400,detail="Invalid Username or Password.")

@app.post('/user/logout/',tags=['Auth'],status_code=200)
async def logout_user(token:str,user_agent:Request,db:db_dependency):
    username,user_id = auths.verify_token(token)
    user = db.query(models.User).filter(models.User.user_id==user_id).first()
    if user is not None:
        logout_request = models.Log(
            status="Logged out",
            user_agent=str(user_agent.headers.get("user-agent"))
        )
        user.logs.append(logout_request)
        db.add(logout_request)
        db.commit()
        db.refresh(logout_request)
        return {"detail":"Signed out"}
    raise HTTPException(status_code=400,detail="Invalid request.")

@app.get('/user/details',tags=['User'],response_model=schemas.User)
async def getProfile(db:db_dependency,token:str=Depends(oauth2_scheme)):
    username,user_id = auths.verify_token(token)
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401,detail="User not found.")
    return user

@app.get('/user/Profile',tags=['User'])
async def getProfile(db:db_dependency,token:str=Depends(oauth2_scheme)):
    username,user_id = auths.verify_token(token)
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401,detail="User not found.")
    return user.profile

@app.post('/consignment/create',tags=['Consignments'],response_model=schemas.Consignment)
async def createConsignment(
    db: db_dependency,
    image: UploadFile = File(...),
    consignment_name: str = Form(...),
    source: str = Form(...),
    destination: str = Form(...),
    destination_pincode: str = Form(...),
    source_pincode: str = Form(...),
    token: str = Depends(oauth2_scheme)
):
    username,user_id = auths.verify_token(token)
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401,detail="User not found.")
    id = str(uuid.uuid4())
    new_consignment = models.Consignment(
        consignment_name = consignment_name,
        consignment_id = id,
        source = source,
        destination = destination,
        destination_pincode = destination_pincode,
    )
    content = await image.read()
    if len(content) > settings.max_image_size:
        raise HTTPException(status_code=400,detail="Image should be less than 5mb.")
    
    try:
        new_filename = await run_in_threadpool(image_utils.upload_image,content)
    except UnidentifiedImageError as err:
        raise HTTPException(
            status_code=400,
            detail="Invalid file uploaded."
        )from err
    new_consignment.image=new_filename
    new_consignment.qr_code = image_utils.generate_qr(id)
    warehouse,hub,min_distance = utils.get_nearest_warehouse(str(destination_pincode),utils.hubs)
    source_lat,source_lon = utils.get_coordinates(source_pincode)
    hub_lat = hub['lat']
    hub_lon = hub['lon']
    nearest_airport_to_hub = utils.get_nearest_airport(float(hub_lat),float(hub_lon))
    nearest_airport = utils.get_nearest_airport(float(source_lat),float(source_lon))
    min_dist = nearest_airport_to_hub['min_dist']
    
    new_path = models.DeliveryRoute(
        delivery_stops=[],
        hub=hub['hub'],
        nearest_hubs=hub,
        nearest_warehouse=warehouse
    )
    if min_distance > min_dist:
        new_path.delivery_stops.append(nearest_airport)
        new_path.delivery_stops.append(nearest_airport_to_hub)
    new_consignment.paths=new_path
    user.consignments.append(new_consignment)
    db.commit()
    db.refresh(user)

    return new_consignment

@app.get('/consignment/getALL',tags=['Consignments'],response_model=List[schemas.GetConsignment])
async def getAllConsignment(db:db_dependency,limit: int = 10, skip: int = 0,token:str=Depends(oauth2_scheme)):
    username,user_id = auths.verify_token(token)
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401,detail="User not found.")
    consignments = (
        db.query(models.Consignment)
        .join(models.user_consignment)
        .filter(models.user_consignment.c.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return consignments

@app.get('/consignment/get/',tags=['Consignments'],response_model=schemas.Consignment)
async def getConsignment(
    db: db_dependency,
    consignment_id: Optional[str] = None,
    consignment_name: Optional[str] = None,
    token: str = Depends(oauth2_scheme)
):
    username, user_id = auths.verify_token(token)
    user = auths.verify_user(user_id,db)
    if user is None:
        raise HTTPException(status_code=401,detail="User not found.")
    query = (
        db.query(models.Consignment)
        .join(models.Consignment.users)
        .filter(models.User.user_id == user_id)
    )
    if query is None:
        raise HTTPException(status_code=404,detail="Not Found.")
    if consignment_id:
        query = query.filter(models.Consignment.consignment_id == consignment_id)

    if consignment_name:
        query = query.filter(models.Consignment.consignment_name == consignment_name)

    if query is None:
        raise HTTPException(status_code=404,detail="No consignment Found.")

    consignment = query.first()
    if consignment is None:
        raise HTTPException(status_code=404,detail="No consignment Found.")
    return consignment

@app.patch('/consignment/UpdateDetails/{id}',tags=['Consignments'],response_model=schemas.Consignment)
async def UpdateDetails(
    id:str,
    req:schemas.UpdateConsignment,
    db:db_dependency,
    token:str=Depends(oauth2_scheme)
):
    username,user_id = auths.verify_token(token)
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401,detail="User not found.")
    query = (
        db.query(models.Consignment)
        .join(models.Consignment.users)
        .filter(models.User.user_id == user_id)
    )
    try:
        query = query.filter(models.Consignment.consignment_id == id)
        consignment = query.first()
        update_data =  req.model_dump(exclude_unset=True)
        for key,value in update_data.items():
            setattr(consignment,key,value)
        db.commit()
        db.refresh(consignment)
        return consignment
    except:
        raise HTTPException(status_code=404,detail="No consignment Found.")
    
@app.patch('/consignment/UpdateImage/{id}',tags=['Consignments'])
async def UpdateImage(
    id:str,
    db:db_dependency,
    file:UploadFile=File(...),
    token:str=Depends(oauth2_scheme)
):
    username,user_id = auths.verify_token(token)
    user = auths.verify_user(user_id,db)
    query = (
        db.query(models.Consignment)
        .join(models.Consignment.users)
        .filter(models.User.user_id == user.user_id)
    )
    if query is None:
        raise HTTPException(status_code=404,detail="Consignment not found.")
    consignment = query.filter(models.Consignment.consignment_id==id).first()
    content = await file.read()
    if len(content)>settings.max_image_size:
        raise HTTPException(status_code=400,detail="Invalid File size.")
    old_filename = consignment.image
    try:
        new_filename = await run_in_threadpool(image_utils.upload_image,content)
    except UnidentifiedImageError as err:
        raise HTTPException(
            status_code=400,
            detail="Invalid file uploaded."
        )from err
    consignment.image = new_filename
    db.commit()
    db.refresh(consignment)
    if old_filename:
        image_utils.delete_profile_pic(old_filename)

    return {
        "detail":"Profile updated."
    }

@app.patch('/consignment/ScanQr/',tags=['Consignments'],response_model=schemas.GetConsignment)
async def scanQr(
    db:db_dependency,
    file:UploadFile=File(...),
    status:str = Form(...),
    token:str=Depends(oauth2_scheme)
):
    username, user_id = auths.verify_token(token)
    user = auths.verify_user(user_id, db)

    content = await file.read()
    nparr = np.frombuffer(content, np.uint8)

    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    # QR detector
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img)

    if not data:
        raise HTTPException(status_code=400, detail="QR code not found")

    # Find consignment
    query = db.query(models.Consignment).filter(
        models.Consignment.consignment_id == data
    ).first()

    if not query:
        raise HTTPException(status_code=404, detail="Consignment not found")

    profile = user.profile
    new_log = models.tracking_log(
        current_location = profile.work_location,
        status = status
    )
    query.track_logs.append(new_log)
    query.employee_ids.append(user_id)
    db.commit()
    db.refresh(query)

    return query

@app.patch('/user/UpdateProfile/',response_model=schemas.Profile,tags=['Auth'])
async def scanQr(
    req:schemas.Profile,
    db:db_dependency,
    token:str=Depends(oauth2_scheme)
):
    username,user_id = auths.verify_token(token)
    user = auths.verify_user(user_id,db)
    profile = user.profile
    if profile:
        update_data = req.model_dump(exclude_unset=True)
        for key,value in update_data.items():
            setattr(profile,key,value)
        db.commit()
        db.refresh(profile)
        return profile
    raise HTTPException(status_code=400,detail="Invalid Request.")

@app.get('/consignment/CheckPincode{pincode}',tags=['Consignments'])
async def check_pincode(pincode:str,token:str=Depends(oauth2_scheme)):
    hubs = utils.hubs
    for key,coordinates in hubs.items():
        cen_lat = coordinates[0]
        cen_lon = coordinates[1]
        try:
            is_deliverable = utils.is_pincode_in_radius(pincode,cen_lat,cen_lon,10)
            if is_deliverable:
                return True
        except:
            raise HTTPException(status_code=400,detail="Invalid Pincode.")
    return False

@app.get('/Paths/GetPath/{consignment_id}',tags=['Route Optimization'],response_model=schemas.path)
async def get_path(
    consignment_id:str,
    db:db_dependency,
    token:str=Depends(oauth2_scheme)
    
):
    username,user_id = auths.verify_token(token)
    user = auths.verify_user(user_id,db)
    if user is None:
        raise HTTPException(status_code=401,detail="No user Found.")

    consignment = db.query(models.Consignment).filter(models.Consignment.consignment_id==consignment_id).first()
    if consignment is None:
        raise HTTPException(status_code=404,detail="Consignment not Found.")
    path = consignment.paths
    return path

@app.post('/Paths/GetRoute',tags=['Route Optimization'],response_model=schemas.GetRouting)
async def get_matrix(req:schemas.Routing,db:db_dependency,token:str=Depends(oauth2_scheme)):
    username,user_id = auths.verify_token(token)
    user = auths.verify_user(user_id,db)
    if user is None:
        raise HTTPException(status_code=401,detail="No user Found.")
    try:
        paths = db.query(models.DeliveryRoute).filter(models.DeliveryRoute.hub==req.hubs).all()
        warehouse_array = []
        distance_matrix = []
        for i in paths:
            if len(warehouse_array) == 0:
                hub = i.nearest_hubs['hub']
                hub_coordinates = f"{i.nearest_hubs['lat']},{i.nearest_hubs['lon']}"
                warehouse_array.append([hub,hub_coordinates])
            warehouse = i.nearest_warehouse['warehouse_id']
            co_ordinates = i.nearest_warehouse['co-ordinates']
            warehouse_array.append([warehouse,co_ordinates])

        for i in warehouse_array:
            matrix = []
            for j in warehouse_array:
                source_coordinates = i[1].split(',')
                s_lat = float(source_coordinates[0])
                s_lon = float(source_coordinates[1])
                d_coordinates = j[1].split(',')
                d_lat = float(d_coordinates[0])
                d_lon = float(d_coordinates[1])
                distance = utils.haversine(s_lat,s_lon,d_lat,d_lon)
                matrix.append(int(distance))
            distance_matrix.append(matrix)

        routing_data = osrm.create_data_model(distance_matrix,req.vehicle)
        routes = osrm.solve_routing(routing_data)
        routing = []
        for i in routes:
            routing.append([warehouse_array[i][0],warehouse_array[i][1]])
        new_route = models.Routing(
            hub = req.hubs,
            route = routing
        )
        db.add(new_route)
        db.commit()
        return new_route
    except:
        raise HTTPException(status_code=400,detail="Invalid request.")

@app.get('/Paths/RouteCoordinates',tags=['Route Optimization'])
async def get_route(source:str,destination:str,db:db_dependency,token:str=Depends(oauth2_scheme)):
    username,user_id = auths.verify_token(token)
    user = auths.verify_user(user_id,db)
    if user is None:
        raise HTTPException(status_code=401,detail="No user Found.")
    route  = utils.get_path_coordinates(source,destination)
    return route

@app.get('/Deliveries',tags=['Route Optimization'])
async def get_delivery(WorkLocation:str,db:db_dependency,token:str=Depends(oauth2_scheme)):
    username,user_id = auths.verify_token(token)
    user = auths.verify_user(user_id,db)
    if user is None:
        raise HTTPException(status_code=401,detail="No user Found.")
    work = db.query(models.Routing).filter(models.Routing.hub==WorkLocation).order_by(models.Routing.id.desc()).first()
    if work:
        return work
    else:
        raise HTTPException(status_code=404,detail="No work found")
