from typing import Optional

from pydantic import BaseModel, field_validator


class Library(BaseModel):
    library_id: int
    name: str
    campus_location: str
    contact_email: str
    phone_number: Optional[str] = None

    @field_validator('phone_number')
    def phone_number_validation(cls, phone: Optional[str]) -> Optional[str]:
        if not phone:
            return None
        return phone

    @field_validator('contact_email')
    def email_validation(cls, email: str) -> str:
        if not email:
            raise ValueError('email must not be empty')