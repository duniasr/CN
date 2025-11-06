from abc import ABC, abstractmethod
from typing import List, Optional
from models.note import Note

class Database(ABC):
    
    @abstractmethod
    def initialize(self):
        pass
    
    @abstractmethod
    def create_note(self, note: Note) -> Note:
        pass
    
    @abstractmethod
    def get_note(self, note_id: str) -> Optional[Note]:
        pass
    
    @abstractmethod
    def get_all_notes(self) -> List[Note]:
        pass
    
    @abstractmethod
    def update_note(self, note_id: str, note: Note) -> Optional[Note]:
        pass
    
    @abstractmethod
    def delete_note(self, note_id: str) -> bool:
        pass