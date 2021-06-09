import httpx
import json
import csv
import srsly
from pathlib import Path
from typing import List, Optional

from fastapi import Request, Form, File, UploadFile, APIRouter, Depends, Query
from fastapi.templating import Jinja2Templates
from app.util.login import get_current_username

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(dependencies=[Depends(get_current_username)])


@router.get("/lookups")
async def read_items(request: Request):
    new_lang = Path.cwd() / "new_lang"
    if len(list(new_lang.iterdir())) > 0:
        return templates.TemplateResponse("lookups.html", {"request": request})

    else:
        return templates.TemplateResponse(
            "error_please_create.html", {"request": request}
        )

@router.post("/upload_lookups")
async def update_lookups(file: UploadFile = File(...),lookup_type:str= Form(...)):
    contents = file.file.read()
    contents = contents.decode("utf-8")

    #load lookups file 
    new_lang = Path.cwd() / "new_lang"
    if len(list(new_lang.iterdir())) > 0:
        path = list(new_lang.iterdir())[0] / "lookups"
        if lookup_type == "pos":
            json_file = list(path.glob("*upos*"))[0]
        if lookup_type == "lemma":
            json_file = list(path.glob("*lemma*"))[0]
        if lookup_type == "features":
            json_file = list(path.glob("*features*"))[0]
        if json_file.exists():
            lookup = srsly.read_json(json_file)

    # load CSV file 
    if file.content_type == 'text/csv':
        reader = csv.reader(contents.splitlines())
        for row in reader:
            if row[0] == 'key' and row[1] == 'value':
                pass
            else:
                lookup[row[0]] = row[1] 
        srsly.write_json(json_file, lookup)
            
        
    if file.content_type == 'application/json':
        data = srsly.json_loads(contents)
        join_dicts = {**lookup, **data}
        srsly.write_json(json_file, join_dicts)
    


###None of these are needed vvv
@router.get("/edit_lookup")
async def edit_pos(request: Request, type: str):
    context = {}
    context["request"] = request
    new_lang = Path.cwd() / "new_lang"
    if len(list(new_lang.iterdir())) > 0:
        path = list(new_lang.iterdir())[0] / "lookups"
        if type == "pos":
            json_file = list(path.glob("*upos*"))[0]
        if type == "lemma":
            json_file = list(path.glob("*lemma*"))[0]
        if type == "features":
            json_file = list(path.glob("*features*"))[0]
        if json_file.exists():
            context["code"] = srsly.read_json(json_file)
        else:
            raise HTTPException(status_code=404, detail="File not found")
    return templates.TemplateResponse("edit_json.html", context)

@router.post("/edit_lookup")
async def update_code(request: Request,):

    data = await request.json()
    type = data["type"]
    code = data["code"]

    new_lang = Path.cwd() / "new_lang"
    if len(list(new_lang.iterdir())) > 0:
        if len(list(new_lang.iterdir())) > 0:
            path = list(new_lang.iterdir())[0] / "lookups"
            if type == "pos":
                json_file = list(path.glob("*upos*"))[0]
            if type == "lemma":
                json_file = list(path.glob("*lemma*"))[0]
            if type == "features":
                json_file = list(path.glob("*features*"))[0]

            if json_file.exists():
                json_file.write_text(code)
                code = srsly.read_json(json_file) #Redundant, right?
            else:
                raise HTTPException(status_code=404, detail="File not found")

        
    return templates.TemplateResponse(
        "edit_json.html", {"request": request, "code": code}
    )

@router.get("/lemma_json")
async def datatable_json(request:Request,
    #See https://datatables.net/manual/server-side
    draw:int = None,
    start:int = None,
    length:int = None, #number of entries per page):
    order:int = None,
    columns:str = None
    ):
    try:
        search = request.query_params['search[value]']
    except KeyError:
        search = ''
    new_lang = Path.cwd() / "new_lang"
    if len(list(new_lang.iterdir())) > 0:
        path = list(new_lang.iterdir())[0] / "lookups"
        json_file = list(path.glob("*lemma*"))[0]
        lemma_data = srsly.read_json(json_file)

        data = []
        id = 1
        for key, value in lemma_data.items():
            data.append({"id": id, "word":key, "lemma":value})
            id += 1
        if search != '':
            data = [d for d in data if search.lower() in d['word'].lower() or search.lower() in d['lemma'].lower()]
        #data = [[f'''<p contenteditable="true" onclick="testing(this)">{key}</p>''',f'''<p contenteditable="true" onkeyup="edit_lemma(this,'{key}','{value}')">{value}</p>'''] for key, value in data]
        
        filtered = len(data)
        return {
            "draw": draw,
            "recordsTotal": len(lemma_data),
            "recordsFiltered": filtered,
            "data":data,
            "result":"ok",
            "error":None
        }

# @router.get("/update_lemma")
# async def update_lemma(
#     key:str,
#     value:str, 
#     col:int,
#     row:int,
#     new_key:str = None, 
#     new_value:str = None, 
#     new:str ='false', 
#     delete:str ='false'):

#     new_lang = Path.cwd() / "new_lang"
#     if len(list(new_lang.iterdir())) > 0:
#         path = list(new_lang.iterdir())[0] / "lookups"
#         json_file = list(path.glob("*lemma*"))[0]
#         lemma_data = srsly.read_json(json_file)
#         if new == 'false' and delete =='false':
#             if new_key:
#                 print('has new key')
#                 lemma_data[new_key] = lemma_data[key]
#                 del lemma_data[key]
#                 result = {"new_key":new_key, "col":col, "row":row}
#             if new_value:
#                 print('has new value') 
#                 lemma_data[key] = new_value
#                 result = {"new_value":new_value, "col":col, "row":row}

#         srsly.write_json(json_file, lemma_data)
#         return result
