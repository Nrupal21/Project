"""
AI services for itinerary generation.

This module provides AI-powered services for generating travel itineraries based on
destinations, duration, interests, and other user preferences using OpenAI's API.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential

import openai
from langchain.prompts import ChatPromptTemplate
from destinations.models import Destination, Attraction

# Set up logging
logger = logging.getLogger(__name__)

class ItineraryAIService:
    """
    Service for generating AI-powered travel itineraries.
    
    This class handles the integration with OpenAI's API to generate
    personalized travel itineraries based on user preferences.
    """
    
    def __init__(self):
        """
        Initialize the ItineraryAIService with OpenAI API key.
        
        Loads API key from Django settings and configures the OpenAI client.
        """
        # Get API key from settings
        self.api_key = os.environ.get('OPENAI_API_KEY', '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')
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Default model
        self.model = "gpt-4"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_itinerary(self, 
                          destination: Destination,
                          start_date: datetime.date,
                          end_date: datetime.date,
                          interests: List[str],
                          budget_level: str = "medium",
                          travel_pace: str = "moderate",
                          accessibility_needs: Optional[List[str]] = None,
                          ) -> Dict[str, Any]:
        """
        Generate a complete travel itinerary using AI.
        
        This method calls the OpenAI API with structured prompts to generate
        a detailed travel itinerary for the specified destination and dates.
        
        Args:
            destination: The Destination object to create an itinerary for
            start_date: The start date of the trip
            end_date: The end date of the trip
            interests: List of traveler interests (e.g., "history", "food", "nature")
            budget_level: Budget level ("budget", "medium", "luxury")
            travel_pace: Pace of travel ("relaxed", "moderate", "intensive")
            accessibility_needs: Optional list of accessibility requirements
            
        Returns:
            Dict containing the structured itinerary data with days, activities, and recommendations
        """
        if not self.api_key:
            logger.error("Cannot generate itinerary: OpenAI API key not configured")
            return {
                "error": "OpenAI API key not configured. Please configure the API key in settings."
            }
        
        try:
            # Get attractions for context
            attractions = Attraction.objects.filter(destination=destination, is_active=True)[:10]
            attractions_text = "\n".join([f"- {a.name}: {a.description}" for a in attractions])
            
            # Calculate trip duration
            duration = (end_date - start_date).days + 1
            
            # Format dates
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            # Format interests
            interests_text = ", ".join(interests)
            
            # Format accessibility needs
            accessibility_text = ""
            if accessibility_needs:
                accessibility_text = "Accessibility needs: " + ", ".join(accessibility_needs)
            
            # Build the prompt
            system_prompt = """
            You are an expert travel planner specialized in creating detailed daily itineraries.
            Create a comprehensive day-by-day travel plan that includes:
            1. A daily schedule with morning, afternoon, and evening activities
            2. Recommended attractions with brief descriptions
            3. Estimated time needed for each activity
            4. Suggested places to eat with cuisine type
            5. Practical travel tips specific to the location
            6. Accommodation recommendations appropriate for the budget level
            
            Format your response as valid JSON with the following structure:
            {
                "itinerary_title": "string",
                "overview": "string",
                "days": [
                    {
                        "day_number": number,
                        "date": "YYYY-MM-DD",
                        "accommodation": "string",
                        "activities": [
                            {
                                "title": "string",
                                "description": "string",
                                "start_time": "HH:MM",
                                "end_time": "HH:MM",
                                "location": "string",
                                "cost_estimate": "string"
                            }
                        ],
                        "meals": [
                            {
                                "meal_type": "string",
                                "place": "string",
                                "cuisine": "string",
                                "cost_estimate": "string"
                            }
                        ],
                        "notes": "string"
                    }
                ],
                "packing_tips": ["string"],
                "local_customs": ["string"],
                "budget_tips": ["string"]
            }
            """
            
            user_prompt = f"""
            Create a {duration}-day itinerary for {destination.name} ({destination.region.name}) from {start_date_str} to {end_date_str}.
            
            Destination details:
            {destination.description}
            
            Notable attractions:
            {attractions_text}
            
            Traveler preferences:
            - Interests: {interests_text}
            - Budget level: {budget_level}
            - Travel pace: {travel_pace}
            {accessibility_text}
            
            Please create a realistic itinerary with specific attraction names, actual locations, and realistic timing.
            Use local time for scheduling activities. Include local dining options for breakfast, lunch, and dinner.
            """

            # Call OpenAI API
            logger.info(f"Generating itinerary for {destination.name}, {duration} days")
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            # Parse the response
            itinerary_json = json.loads(response.choices[0].message.content)
            
            # Validate the structure (basic validation)
            if not all(key in itinerary_json for key in ['itinerary_title', 'overview', 'days']):
                logger.warning(f"AI response missing required fields: {itinerary_json.keys()}")
                return {
                    "error": "Generated itinerary is missing required fields",
                    "partial_data": itinerary_json
                }
            
            logger.info(f"Successfully generated itinerary for {destination.name}")
            return itinerary_json
            
        except Exception as e:
            logger.error(f"Error generating itinerary: {str(e)}")
            return {"error": f"Failed to generate itinerary: {str(e)}"}
    
    def generate_activity_recommendations(self, 
                                         destination: Destination,
                                         interests: List[str],
                                         count: int = 5) -> List[Dict[str, Any]]:
        """
        Generate activity recommendations for a specific destination.
        
        This method uses AI to suggest activities based on the destination and traveler interests.
        
        Args:
            destination: The Destination object to recommend activities for
            interests: List of traveler interests
            count: Number of recommendations to generate
            
        Returns:
            List of dictionaries containing activity recommendations
        """
        if not self.api_key:
            logger.error("Cannot generate recommendations: OpenAI API key not configured")
            return []
        
        try:
            # Format interests
            interests_text = ", ".join(interests)
            
            # Build the prompt
            system_prompt = """
            You are a knowledgeable travel guide providing activity recommendations.
            For each activity recommendation, include:
            1. Activity name
            2. Brief description (2-3 sentences)
            3. Estimated duration
            4. What makes it special
            
            Format your response as a JSON array of objects with the following structure:
            [
                {
                    "title": "string",
                    "description": "string",
                    "duration": "string",
                    "location": "string",
                    "cost_estimate": "string",
                    "best_time": "string"
                }
            ]
            """
            
            user_prompt = f"""
            Recommend {count} interesting activities in {destination.name} ({destination.region.name}) 
            for a traveler interested in {interests_text}.
            
            Destination details:
            {destination.description}
            
            Provide realistic activity recommendations with actual places and attractions.
            """

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Parse the response
            recommendations = json.loads(response.choices[0].message.content)
            
            if not isinstance(recommendations, list):
                recommendations = recommendations.get('recommendations', [])
            
            return recommendations[:count]  # Limit to requested count
            
        except Exception as e:
            logger.error(f"Error generating activity recommendations: {str(e)}")
            return []
