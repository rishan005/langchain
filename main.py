import os
import requests
from bs4 import BeautifulSoup
from config import settings
from fastapi import FastAPI , Depends , HTTPException
from pydantic import BaseModel
from sqlmodel import Session , select
from database import engine, users , message

#langchain imports
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate , MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage,AIMessage

from duckduckgo_search import DDGS

os.environ['GROQ_API_KEY'] = settings.GROQ_API_KEY

app = FastAPI()

#--Tools-- 

def search_web(query):
    '''Search the web using DuckDuckGo and return the top result as a string.'''
    with DDGS() as ddgs:
        return'\n'.join([r['body'] for r in ddgs.text(query,max_results=2)])
    
def scrap_web(url:str):
    '''Scrap the content of a web page and return it as a string.'''

    response = requests.get(url)
    soup = BeautifulSoup(response.text,'html.parser')
    for s in soup(['script','style']):
        s.extract()
    return soup.get_text()[:2000] # Limit to 2000 characters

#---database dependency---

def get_db():
    with Session(engine) as session:
        yield session

#---LLM Setup---
model = ChatGroq(model = 'llama-3.1-8b-instant',temperature=0.7)

#---langchain workflow---

prompt = ChatPromptTemplate.from_messages([
    ('system','you are a helpful assistant that can search the web and scrape web pages to answer'),
    MessagesPlaceholder(variable_name='history'),
    ('human','Answer the question: {input}')
])

chain = prompt | model |StrOutputParser()

#---API routes---
class UserSchema(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message:str

#---API Endpoints---
 
@app.post('/register')
def register(user:UserSchema, db:Session = Depends(get_db)):
    existing_user = db.exec(select(users).where(users.username == user.username)).first()
    if existing_user:
        raise HTTPException(status_code=404,detail='Username already exists')
    new_user = users(username = user.username,password = user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return{'message':'User registered sucessfully','user_id':new_user.u_id}

@app.post('/{username}/chat')
def chat(username:str,request:ChatRequest,db:Session=Depends(get_db)):
    user = db.exec(select(users).where(users.username == username)).first()
    if not user:
        raise HTTPException(status_code=404, detail='user not found')
    
    chat_history = db.exec(select(message).where(message.u_id == user.u_id).order_by(message.timestamp)).all()
    history = []
    for msg in chat_history:
        if msg.role == 'user':
            history.append(HumanMessage(content=msg.content))
        else:
            history.append(AIMessage(content=msg.content))

    user_input = request.message

    if 'search' in user_input.lower():
        tool_output = search_web(user_input)
        user_input += f'\nWeb search results:\n{tool_output}'

    response = chain.invoke({'input': user_input,'history': history[-4:]}) #use last 4 messages

    db.add(message(u_id = user.u_id, role='user', content=request.message))
    db.add(message(u_id = user.u_id,role='assistant', content=response))

    db.commit()    

    return{'response':response} 
