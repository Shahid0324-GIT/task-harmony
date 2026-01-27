from typing import Optional
from pydantic import BaseModel, Field

class ShipmentDetails(BaseModel):
    product_line: Optional[str] = Field(None, description="The product line, e.g., pl_sea_import_lcl")
    origin_port_code: Optional[str] = Field(None, description="5-letter UN/LOCODE for origin port")
    origin_port_name: Optional[str] = Field(None, description="Name of the origin port")
    destination_port_code: Optional[str] = Field(None, description="5-letter UN/LOCODE for destination port")
    destination_port_name: Optional[str] = Field(None, description="Name of the destination port")
    incoterm: Optional[str] = Field(None, description="Incoterm, e.g., FOB, CIF")
    cargo_weight_kg: Optional[float] = Field(None, description="Cargo weight in kg")
    cargo_cbm: Optional[float] = Field(None, description="Cargo volume in CBM")
    is_dangerous: bool = Field(False, description="Whether the cargo is dangerous goods")

class EmailExtractionOutput(ShipmentDetails):
    id: str
