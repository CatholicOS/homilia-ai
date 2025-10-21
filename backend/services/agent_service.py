import json
from typing import List, Dict, Any, Optional

import asyncio
import datetime
from strands import Agent, tool
from strands.models.openai import OpenAIModel
import os
from catholic_mass_readings import USCCB, models
from document_processing_service import DocumentProcessingService
from s3_service import S3Service

# Initialize USCCB client
usccb = USCCB()

@tool
def get_relevant_docs_tool(query: str) -> dict[str, str]:
    """
    Get relevant homilies and bulletins from the database based on the query using semantic vector search

    This tool retrieves the most relevant chunks from the database, along with some metadata about the document.

    Args:
        query: The query to search for
    Returns:
        dict[str, str]: A dictionary of the documents (keys: "file_id", "filename", "source", "text", "metadata")
    """
    document_processing_service = DocumentProcessingService()
    return document_processing_service.search_documents(query)

@tool
def get_doc_tool(file_id: str) -> dict[str, str]:
    """
    Get the full text of a document from the database by id

    This tool retrieves the full text of a document from the database by id.

    Args:
        file_id: The id of the document to get
    Returns:
        str: The full text of the document
    """
    s3_service = S3Service()
    file_bytes = s3_service.get_file_bytes(file_id)['file_bytes']
    return file_bytes.decode('utf-8')


@tool
def get_date_tool() -> str:
    """
    Get the current date
    Returns:
        str: The current date in the format YYYY-MM-DD
    """
    return datetime.datetime.now().strftime("%Y-%m-%d")

@tool
async def get_readings_tool(date: str) -> dict[str, str]:
    """
    Get the readings for the given date
    Args:
        date: The date to get the readings for in the format YYYY-MM-DD
    Returns:
        dict[str, str]: A dictionary of the readings (keys: "first reading", "second reading", "gospel") for the given date
    """
    year, month, day = date.split('-')
    return await get_readings(int(year), int(month), int(day))

@tool
def get_documents_by_date_tool(start_date: str, end_date: str = None, parish_id: str = None, document_type: str = None) -> dict[str, str]:
    """
    Get documents created within a date range from the database
    
    This tool retrieves documents that were created between the start_date and end_date (inclusive).
    You can optionally filter by parish_id and document_type.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format (optional, defaults to start_date)
        parish_id: Optional parish identifier to filter by
        document_type: Optional document type to filter by (e.g., "homily", "bulletin")
    Returns:
        dict[str, str]: A dictionary containing the documents created in the date range
    """
    document_processing_service = DocumentProcessingService()
    return document_processing_service.get_documents_by_date(
        start_date=start_date,
        end_date=end_date,
        parish_id=parish_id,
        document_type=document_type
    )


async def get_readings(year: int, month: int, day: int) -> dict[str, str]:
    """
    Get the readings for the given date
    Args:
        year: The year to get the readings for
        month: The month to get the readings for
        day: The day to get the readings for
    Returns:
        dict[str, str]: A dictionary with keys "first reading", "second reading", "gospel"
    """
    
    mass = await usccb.get_mass_from_date(datetime.date(year, month, day))
    
    # Extract readings from the mass object
    readings = {
        "first reading": "",
        "second reading": "",
        "gospel": ""
    }
    
    # Parse the readings from the mass sections
    reading_count = 0
    for section in mass.sections:
        if section.type_.is_reading:
            # This is a reading section (first or second reading)
            if reading_count == 0:
                readings["first reading"] = section.readings[0].text if section.readings else ""
                reading_count += 1
            elif reading_count == 1:
                readings["second reading"] = section.readings[0].text if section.readings else ""
                reading_count += 1
        elif section.type_.is_gospel:
            # This is the gospel section
            readings["gospel"] = section.readings[0].text if section.readings else ""
    
    return readings

def create_agent():
    """
    Create an agent that can be used to process documents and get readings
    """
    # Configure OpenAI model for Strands
    openai_model = OpenAIModel(
        client_args={
            "api_key": os.getenv("OPENAI_API_KEY"),
        },
        model_id="gpt-4o",  # Using GPT-4o for better performance
        params={
            "max_tokens": 2000,
            "temperature": 0.7,
        }
    )
    
    agent = Agent(
        name="Homilia Agent",
        description="A agent that can be used to answer questions with homilies and bulletins and get readings",
        model=openai_model,
        tools=[get_relevant_docs_tool, get_doc_tool, get_date_tool, get_readings_tool, get_documents_by_date_tool]
    )
    return agent

if __name__ == "__main__":
    agent = create_agent()
    agent("What are the readings for today?")