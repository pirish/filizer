import secrets
from fastapi import FastAPI, HTTPException, Body, Request, Depends, status, APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from config import settings
from pymongo import AsyncMongoClient
from pyodmongo import AsyncDbEngine, DbModel
from pyodmongo.queries import mount_query_filter
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional, List, ClassVar
from common.models import DuplicateStatus, FileModel, ActionUpdate, VERSION, MIN_CLIENT_VERSION
import semver

# export MONGODB_URL="mongodb+srv://localhost:27017/?retryWrites=true&w=majority"

security = HTTPBasic(auto_error=False)

def verify_version(request: Request):
    client_version = request.headers.get("X-Client-Version")
    if not client_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Client-Version header",
        )
    
    try:
        if semver.compare(client_version, MIN_CLIENT_VERSION) < 0:
            raise HTTPException(
                status_code=status.HTTP_426_UPGRADE_REQUIRED,
                detail=f"Client version {client_version} is too old. Minimum required version is {MIN_CLIENT_VERSION}",
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid X-Client-Version format: {client_version}",
        )
    return client_version

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    if not settings.auth.enabled:
        return "anonymous"

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Basic"},
        )

    correct_username = settings.auth.username
    correct_password = settings.auth.password

    # Use secrets.compare_digest for secure comparison
    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

app = FastAPI(dependencies=[Depends(get_current_username)])
templates = Jinja2Templates(directory="server/templates")
api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(verify_version)])

@app.get("/version")
async def get_version():
    return {"version": VERSION, "min_client_version": MIN_CLIENT_VERSION}

engine = AsyncDbEngine(mongo_uri=settings.mongodb_url, db_name=settings.db_name)

@api_router.post("/files/", response_model=FileModel)
async def create_file(request: Request):
    #  data = file.dict(by_alias=True, exclude=["id"])
    data = await request.json()
    file_model = FileModel(**data)
    result = await engine.save(file_model)
    #data["_id"] = str(result.upserted_ids)
    return file_model

@api_router.get("/files/", response_model=List[FileModel])
async def get_files(request: Request):
    query, sort = mount_query_filter(
        Model=FileModel,
        items=request.query_params._dict,
        initial_comparison_operators=[],
    )
    return await engine.find_many(Model=FileModel, query=query, sort=sort)

@api_router.get("/files/{id}", response_model=FileModel)
async def get_file(id: str):
    file = await engine.find_one(Model=FileModel, query={"_id": ObjectId(id)})
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file

@api_router.delete("/files/{id}")
async def delete_file(id: str):
    # pyodmongo delete expects query
    response = await engine.delete(Model=FileModel, query={"_id": ObjectId(id)})
    if response.deleted_count == 0:
         raise HTTPException(status_code=404, detail="File not found")
    return {"status": "deleted", "count": response.deleted_count}

@api_router.put("/files/{id}/action", response_model=FileModel)
async def update_file_action(id: str, action_update: ActionUpdate):
    file = await engine.find_one(Model=FileModel, query={"_id": ObjectId(id)})
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    file.action = action_update.action
    file.action_args = action_update.action_args
    await engine.save(file)
    return file

@api_router.get("/stats")
async def get_stats():
    collection = engine._db[FileModel._collection]
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_files": {"$sum": 1},
                "total_size": {"$sum": "$size"}
            }
        }
    ]
    cursor = collection.aggregate(pipeline)
    results = await cursor.to_list(length=1)
    if not results:
        return {"total_files": 0, "total_size": 0}
    return {
        "total_files": results[0]["total_files"],
        "total_size": results[0]["total_size"]
    }

app.include_router(api_router)

@app.get("/reports")
async def get_reports():
    collection = engine._db[FileModel._collection]
    
    # Duplicate Files Pipeline
    files_pipeline = [
        {"$group": {
            "_id": "$md5",
            "count": {"$sum": 1},
            "files": {"$push": "$$ROOT"},
            "total_size": {"$sum": "$size"}
        }},
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    # Duplicate Directories Pipeline
    dirs_pipeline = [
        {
            "$group": {
                "_id": "$parent_dir",
                "files": {"$push": {"name": "$name", "md5": "$md5"}},
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "parent_dir": "$_id",
                "files": {
                    "$sortArray": {"input": "$files", "sortBy": {"name": 1, "md5": 1}}
                },
                "file_count": "$count"
            }
        },
        {
            "$group": {
                "_id": "$files",
                "directories": {"$push": "$parent_dir"},
                "count": {"$sum": 1},
                "file_count": {"$first": "$file_count"}
            }
        },
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    files_cursor = collection.aggregate(files_pipeline)
    files_results = await files_cursor.to_list(length=None)
    
    dirs_cursor = collection.aggregate(dirs_pipeline)
    dirs_results = await dirs_cursor.to_list(length=None)
    
    # Process files results to be JSON serializable
    processed_files = []
    for group in files_results:
        new_group = group.copy()
        new_files = []
        for file in group["files"]:
            file_dict = dict(file)
            if "_id" in file_dict:
                file_dict["_id"] = str(file_dict["_id"])
            new_files.append(file_dict)
        new_group["files"] = new_files
        processed_files.append(new_group)
    
    # Process dirs results
    processed_dirs = []
    for group in dirs_results:
        processed_dirs.append({
            "files": group["_id"],
            "directories": group["directories"],
            "count": group["count"],
            "file_count": group["file_count"]
        })
    
    return {
        "duplicate_files": processed_files,
        "duplicate_directories": processed_dirs
    }

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")