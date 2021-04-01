import srsly
from pathlib import Path
from typing import List, Optional
from fastapi import Request, Form, File, APIRouter, Depends
from fastapi.templating import Jinja2Templates
from app.util.login import get_current_username
from collections import Counter, namedtuple
from itertools import chain

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(dependencies=[Depends(get_current_username)])

Token = namedtuple("Token", ["text", "lemma_", "pos_", "ent_type_", "tag_"])


@router.get("/corpus")
async def read_items(request: Request):
    new_lang = Path.cwd() / "new_lang"
    if len(list(new_lang.iterdir())) > 0:
        text_path = list(new_lang.iterdir())[0] / "texts"
        corpus = ""
        text_count = 0
        for text in text_path.iterdir():
            corpus += text.read_text()
            text_count += 1
        # create doc from corpus with obj, count tokens
        lang_name = list(new_lang.iterdir())[0].name
        try:
            mod = __import__(f"new_lang.{lang_name}", fromlist=[lang_name.capitalize()])
        except SyntaxError:  # Unable to load __init__ due to syntax error
            # redirect /edit?file_name=examples.py
            message = "[*] SyntaxError, please correct this file to proceed."
            return RedirectResponse(url="/edit?file_name=tokenizer_exceptions.py")
        cls = getattr(mod, lang_name.capitalize())
        nlp = cls()
        doc = nlp(corpus)
        # I use namedtuple/Token rather than spaCy Token for needed results and variation of tokens
        token_count = len([t for t in doc])
        ignore = [
            "\n",
            " ",
            "\n\n",
            "\n     ",
            "\n\n\n\n",
        ] #TODO update this with lang/char_classes: HYPHENS, PUNCT, UNITS, CONCAT_QUOTES
        tokens = [
            Token(
                text=t.text,
                lemma_=t.lemma_,
                pos_=t.pos_,
                ent_type_=t.ent_type_,
                tag_=t.tag_,
            )
            for t in doc
            if not t.text in ignore and not t.is_punct
        ]
        to_json = []
        for i in Counter(tokens).most_common():
            dict_ = i[0]._asdict()
            dict_["count"] = i[1]
            to_json.append(dict_)
        tokens_json = srsly.json_dumps(to_json)
        try:
            sent_count = len([s for s in doc.sents])
        except ValueError:
            sent_count = False
        ent_count = len([e for e in doc.ents])
        stats = {
            "texts": text_count,
            "tokens": token_count,
            "sents": sent_count,
            "ents": ent_count,
        }
        return templates.TemplateResponse(
            "corpus.html",
            {"request": request, "stats": stats, "tokens_json": tokens_json},
        )
    else:
        return templates.TemplateResponse("corpus.html", {"request": request})

@router.get("/update_corpus")
async def update_items(text:str,lemma:str, pos:str = None,ent:str =None):
    """A get endpoint to receive data updates from the corpus page. 

    Args:
        text (str): [description]
        lemma (str): [description]
        pos (str, optional): [description]. Defaults to None.
        ent (str, optional): [description]. Defaults to None.
    """
    
    #Read the lookups directory, make dict of table names and path to json files
    new_lang = Path.cwd() / "new_lang"
    lang_name = list(new_lang.iterdir())[0].name
    lookups_path = new_lang / lang_name / "lookups"
    for lookup in lookups_path.iterdir():
        key = lookup.stem[lookup.stem.find('_') + 1:]
        if 'lemma' in key:
            lemma_data = srsly.read_json(lookup)
        if 'entity' in key:
            ent_data = srsly.read_json(lookup)
        if 'pos' in key:
            pos_data = srsly.read_json(lookup)
    # use type to the open lookups file 
    # Check if key exists in the file 
    # if not add new entry
    # if so, update value
    
    if lemma and lemma_data.get(text, None):
        lemma_data[text] = lemma
    if pos and pos_data.get(text, None):
        pos_data[text] = pos
    if ent and ent_data.get(text, None):
        ent_data[text] = ent
    #save to updated dicts to files 
    for lookup in lookups_path.iterdir():
        key = lookup.stem[lookup.stem.find('_') + 1:]
        if lemma and 'lemma' in key:
            srsly.write_json(lookup)
        if ent and 'entity' in key:
            srsly.write_json(lookup)
        if pos and 'pos' in key:
            srsly.write_json(lookup)

    
