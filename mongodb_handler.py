#!/usr/bin/env python3
"""
MongoDB Handler for Water Quality Application
Handles all database operations for storing water quality predictions
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
import streamlit as st
import uuid


def generate_sample_id() -> str:
    """Generate a unique sample ID like WQ-20260321-A3F2."""
    date_part = datetime.now().strftime("%Y%m%d")
    uid_part  = uuid.uuid4().hex[:4].upper()
    return f"WQ-{date_part}-{uid_part}"

class MongoDBHandler:
    """Handler for MongoDB operations"""
    
    def __init__(self, connection_string="mongodb://localhost:27017", timeout=5000):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection string
            timeout: Connection timeout in milliseconds
        """
        self.connection_string = connection_string
        self.timeout = timeout
        self.client = None
        self.db = None
        self.collection = None
        
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            # Create MongoDB client with timeout
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=self.timeout
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Connect to database and collection
            self.db = self.client['waterDB']
            self.collection = self.db['waterData']
            
            return True, "✅ Connected to MongoDB successfully!"
            
        except ConnectionFailure:
            return False, "❌ Failed to connect to MongoDB. Is MongoDB running?"
        except ServerSelectionTimeoutError:
            return False, "❌ MongoDB connection timeout. Please check if MongoDB is running on localhost:27017"
        except Exception as e:
            return False, f"❌ MongoDB connection error: {str(e)}"
    
    def is_connected(self):
        """Check if MongoDB is connected"""
        try:
            if self.client:
                self.client.admin.command('ping')
                return True
        except:
            pass
        return False
    
    def insert_water_sample(self, sample_data):
        """
        Insert a water sample record into MongoDB
        
        Args:
            sample_data: Dictionary containing water sample information
            
        Returns:
            tuple: (success: bool, message: str, inserted_id: str)
        """
        try:
            # Ensure connection
            if not self.is_connected():
                success, message = self.connect()
                if not success:
                    return False, message, None
            
            # Add timestamp if not present
            if 'timestamp' not in sample_data:
                sample_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Ensure unique sample_id
            if 'sample_id' not in sample_data or not sample_data['sample_id']:
                sample_data['sample_id'] = generate_sample_id()

            # Insert document
            result = self.collection.insert_one(sample_data)
            
            return True, f"✅ Sample saved to MongoDB (ID: {result.inserted_id})", str(result.inserted_id)
            
        except Exception as e:
            return False, f"❌ Failed to save to MongoDB: {str(e)}", None
    
    def get_all_samples(self):
        """
        Retrieve all water samples from MongoDB
        
        Returns:
            list: List of all water sample documents
        """
        try:
            if not self.is_connected():
                success, message = self.connect()
                if not success:
                    return []
            
            # Retrieve all documents, sorted by timestamp (newest first)
            samples = list(self.collection.find().sort('timestamp', -1))
            
            return samples
            
        except Exception as e:
            st.error(f"❌ Failed to retrieve samples from MongoDB: {str(e)}")
            return []
    
    def get_samples_by_location(self, location_name):
        """
        Retrieve water samples for a specific location
        
        Args:
            location_name: Name of the location
            
        Returns:
            list: List of water sample documents for the location
        """
        try:
            if not self.is_connected():
                success, message = self.connect()
                if not success:
                    return []
            
            samples = list(self.collection.find({'location_name': location_name}).sort('timestamp', -1))
            
            return samples
            
        except Exception as e:
            st.error(f"❌ Failed to retrieve samples: {str(e)}")
            return []
    
    def get_unsafe_samples(self):
        """
        Retrieve only unsafe/contaminated water samples.

        Returns:
            list: Documents where result == 'Unsafe' or prediction_result == 'Contaminated'
        """
        try:
            if not self.is_connected():
                success, message = self.connect()
                if not success:
                    return []

            # Match both field naming conventions
            samples = list(self.collection.find(
                {'$or': [{'result': 'Unsafe'}, {'prediction_result': 'Contaminated'}]}
            ).sort('timestamp', -1))

            return samples

        except Exception as e:
            st.error(f"❌ Failed to retrieve unsafe samples: {str(e)}")
            return []

    def get_statistics(self):
        """
        Get statistics about water samples.

        Returns:
            dict: total, safe, contaminated counts
        """
        try:
            if not self.is_connected():
                success, message = self.connect()
                if not success:
                    return {'total': 0, 'safe': 0, 'contaminated': 0}

            total = self.collection.count_documents({})
            safe = self.collection.count_documents(
                {'$or': [{'result': 'Safe'}, {'prediction_result': 'Safe'}]}
            )
            contaminated = self.collection.count_documents(
                {'$or': [{'result': 'Unsafe'}, {'prediction_result': 'Contaminated'}]}
            )

            return {'total': total, 'safe': safe, 'contaminated': contaminated}

        except Exception as e:
            st.error(f"❌ Failed to get statistics: {str(e)}")
            return {'total': 0, 'safe': 0, 'contaminated': 0}
    
    def delete_all_samples(self):
        """
        Delete all water samples from MongoDB
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if not self.is_connected():
                success, message = self.connect()
                if not success:
                    return False, message
            
            result = self.collection.delete_many({})
            
            return True, f"✅ Deleted {result.deleted_count} samples from MongoDB"
            
        except Exception as e:
            return False, f"❌ Failed to delete samples: {str(e)}"
    
    def close(self):
        """Close MongoDB connection"""
        try:
            if self.client:
                self.client.close()
        except:
            pass


# Initialize global MongoDB handler
@st.cache_resource
def get_mongodb_handler():
    """Get or create MongoDB handler instance"""
    return MongoDBHandler()
