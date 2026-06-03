from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from pydantic import BaseModel, Field
from typing import List
from .tools.email_tool import EmailTool
from crewai.memory import Memory
import os


# Pydantic Models for structured outputs from agents

class FlightOption(BaseModel):
    """A single flight option"""
    airline: str = Field(description="Airline name")
    departure: str = Field(description="Departure time and date")
    arrival: str = Field(description="Arrival time and date")
    duration: str = Field(description="Total flight duration")
    price: str = Field(description="Estimated price in USD")

class FlightList(BaseModel):
    """List of flight options"""
    flights: List[FlightOption] = Field(description="List of available flight options")


class HotelOption(BaseModel):
    """A single hotel option"""
    name: str = Field(description="Hotel name")
    location: str = Field(description="Hotel neighborhood or area")
    price_per_night: str = Field(description="Price per night in USD")
    rating: str = Field(description="Hotel rating out of 5")
    highlights: str = Field(description="Key features and highlights of the hotel")

class HotelList(BaseModel):
    """List of hotel options"""
    hotels: List[HotelOption] = Field(description="List of available hotel options")


class DayPlan(BaseModel):
    """A single day in the itinerary"""
    day: str = Field(description="Day number and date")
    morning: str = Field(description="Morning activities and recommendations")
    afternoon: str = Field(description="Afternoon activities and recommendations")
    evening: str = Field(description="Evening activities, dinner recommendations")

class ItineraryPlan(BaseModel):
    """Full day by day itinerary"""
    destination: str = Field(description="Travel destination")
    days: List[DayPlan] = Field(description="Complete day by day itinerary")


# Crew

@CrewBase
class TravelPlanner():
    """TravelPlanner crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'


    # Agents

    @agent
    def flight_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['flight_researcher'],
            tools=[SerperDevTool()],
            verbose=True
        )

    @agent
    def hotel_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['hotel_researcher'],
            tools=[SerperDevTool()],
            verbose=True
        )

    @agent
    def itinerary_planner(self) -> Agent:
        return Agent(
            config=self.agents_config['itinerary_planner'],
            tools=[SerperDevTool()],
            verbose=True
        )

    @agent
    def travel_coordinator(self) -> Agent:
        return Agent(
            config=self.agents_config['travel_coordinator'],
            tools=[EmailTool()],
            verbose=True,
            memory=True
        )


    # Tasks

    @task
    def find_flights(self) -> Task:
        return Task(
            config=self.tasks_config['find_flights'],
            output_pydantic=FlightList
        )

    @task
    def find_hotels(self) -> Task:
        return Task(
            config=self.tasks_config['find_hotels'],
            output_pydantic=HotelList
        )

    @task
    def plan_itinerary(self) -> Task:
        return Task(
            config=self.tasks_config['plan_itinerary'],
            output_pydantic=ItineraryPlan
        )

    @task
    def compile_travel_plan(self) -> Task:
        return Task(
            config=self.tasks_config['compile_travel_plan'],
        )


    # Crew

    @crew
    def crew(self) -> Crew:
        """Creates the TravelPlanner crew"""

        manager = Agent(
            config=self.agents_config['manager'],
            allow_delegation=True,
            verbose=True
        )

        memory = Memory(
            embedder={
                "provider": "google",
                "config": {
                    "model": "models/text-embedding-004",
                    "api_key": os.getenv("GOOGLE_API_KEY")
                }
            }
        )

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            verbose=True,
            manager_agent=manager,
            memory=memory,
        )