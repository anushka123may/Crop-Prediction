"""
MongoDB Setup Script for Crop Advisor
This script helps you set up MongoDB for the application.
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("=" * 50)
    print("MongoDB Setup for Crop Advisor")
    print("=" * 50)
    
    # Try local MongoDB first
    try:
        print("\n1. Testing local MongoDB connection...")
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✓ Local MongoDB is running!")
        print("  Connection URI: mongodb://localhost:27017/")
        
        # Create database and collections
        db = client['crop_advisor_db']
        db.create_collection('users')
        db.create_collection('recommendations')
        
        # Create indexes
        db.users.create_index('username', unique=True)
        db.users.create_index('email', unique=True)
        db.recommendations.create_index('user_id')
        db.recommendations.create_index('timestamp')
        
        print("✓ Database 'crop_advisor_db' created")
        print("✓ Collections created: users, recommendations")
        print("✓ Indexes created")
        print("\nYou're all set! Run 'python App.py' to start the application.")
        return True
        
    except ConnectionFailure:
        print("✗ Local MongoDB is not running")
        print("\nOptions:")
        print("1. Install MongoDB locally:")
        print("   - Download from: https://www.mongodb.com/try/download/community")
        print("   - Or use MongoDB Atlas (cloud): https://www.mongodb.com/cloud/atlas")
        print("\n2. If using MongoDB Atlas:")
        print("   - Get your connection string")
        print("   - Update MONGO_URI in App.py")
        print("   - Format: mongodb+srv://username:password@cluster.mongodb.net/")
        return False

if __name__ == "__main__":
    test_mongodb_connection()
