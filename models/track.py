from pydantic import BaseModel
from typing import List, Optional

class TrackInfo(BaseModel):
    title: str
    artist: str
    url: str
    image_url: str
    source: str

class PlaylistCreate(BaseModel):
    playlistName: str
    tracks: List[TrackInfo] = []

class Playlist(PlaylistCreate):
    id: str

class PlaylistUpdate(BaseModel):
    playlistName: Optional[str] = None
    tracks: Optional[List[TrackInfo]] = None
    
    class Config:
        orm_mode = True
        use_enum_values = True