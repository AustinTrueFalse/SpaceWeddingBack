from pydantic import BaseModel
from typing import List, Optional

class LocationInfo(BaseModel):
    header: str
    text: str

class PersonInfo(BaseModel):
    header: str
    text: str

class ColorsInfo(BaseModel):
    header: str
    colors: List[str] = []
    manInfo: PersonInfo
    womanInfo: PersonInfo

class BottomInfo(BaseModel):
    header: str
    text: str
    subtext: str

class FooterInfo(BaseModel):
    text: str

class Invite(BaseModel):
    header: str
    mainPhoto: str
    secondPhoto: str
    locationInfo: LocationInfo
    colorsInfo: ColorsInfo
    bottomInfo: BottomInfo
    footerInfo: FooterInfo

    class Config:
        orm_mode = True
