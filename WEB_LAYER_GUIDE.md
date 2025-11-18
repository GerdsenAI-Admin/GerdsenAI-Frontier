# Substrate Web Layer Guide

## Overview

The Substrate web layer provides a complete REST API and web interface for the transparent AI coordination platform. This enables users to create profiles, find matches, and collaborate through a user-friendly interface.

## Architecture

```
Web Layer
├── Backend (FastAPI)
│   ├── REST API endpoints
│   ├── Semantic matching integration
│   ├── Transparency engine integration
│   └── SQLite persistence
│
└── Frontend (HTML/JavaScript)
    ├── Profile creation
    ├── Match finding
    ├── Statistics dashboard
    └── Real-time API integration
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
# Option A: Using the startup script
./run_api_server.sh

# Option B: Manually
export PYTHONPATH=/home/user/GerdsenAI-Frontier:$PYTHONPATH
python -m uvicorn substrate.web.backend.api:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Open the Web Interface

```bash
# In a browser, open:
file:///home/user/GerdsenAI-Frontier/substrate/web/frontend/index.html

# Or serve it with Python:
cd substrate/web/frontend
python -m http.server 8080
# Then open: http://localhost:8080
```

### 4. Run Integration Tests

```bash
# Make sure API server is running first
python test_api_integration.py
```

## API Endpoints

### Health Check
```
GET /
Returns API status and version
```

### User Profiles
```
POST /profiles
Create or update a user profile

GET /profiles/{user_id}
Get a user profile
```

### Matching
```
POST /match
Find matches for a need
Returns matches with complete transparency

POST /needs
Post a new need

POST /match/{match_id}/accept
Accept a proposed match

POST /match/{match_id}/reject
Reject a proposed match
```

### Outcomes & Learning
```
POST /outcomes
Report collaboration outcome
System learns from this for future matching
```

### Statistics
```
GET /stats
Get system-wide statistics

GET /stats/user/{user_id}
Get user-specific statistics
```

## API Usage Examples

### Create a Profile

```bash
curl -X POST http://localhost:8000/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "engineer_001",
    "capabilities": [
      {
        "type": "skill",
        "name": "ROS2 Development",
        "description": "Expert in robotics software",
        "proficiency": 0.9,
        "tags": ["robotics", "ros2"],
        "privacy_level": "network"
      }
    ],
    "location_region": "North America",
    "timezone": "America/Los_Angeles",
    "domains": ["robotics", "software"]
  }'
```

### Find Matches

```bash
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "engineer_001",
    "need_name": "Need hardware integration help",
    "need_description": "Building a robot, need help with sensors...",
    "need_domain": "robotics",
    "need_tags": ["hardware", "sensors"],
    "max_results": 5
  }'
```

## Web Interface Features

### 1. Find Matches Tab
- Describe your problem or need
- AI analyzes and finds semantic matches
- View detailed match explanations
- See transparency information (confidence, evidence, uncertainty)

### 2. Profile Tab
- Create your profile
- List capabilities in simple format: "Name - Description"
- Set location and timezone
- Profiles are indexed for matching

### 3. Statistics Tab
- View total matches created
- Success rate of collaborations
- Total outcomes tracked
- Real-time system statistics

## Key Features

### Complete Transparency
Every match includes:
- **Match Score**: Overall compatibility (0-1)
- **Confidence**: How certain the system is (0-1)
- **Complementarity**: How well skills complement (0-1)
- **Feasibility**: Practical viability (0-1)
- **Explanation**: Human-readable reasoning
- **Evidence**: Supporting data points
- **Uncertainty Factors**: What could affect accuracy

### Semantic Matching
The system uses AI to:
- Understand problem descriptions semantically
- Find capabilities that actually solve the problem
- Detect complementarity opportunities
- Explain matches in human terms

### Privacy-Preserving
- User data stored locally in SQLite
- Shareable profiles can be privacy-controlled
- Only necessary information exposed via API
- No centralized tracking of private data

### Learning System
- Records match outcomes
- Improves matching over time
- Tracks success patterns
- Provides statistical insights

## Database Schema

The system maintains:
- **users**: User profiles and preferences
- **capabilities**: User capabilities and expertise
- **needs**: Posted needs and problems
- **matches**: Match records with provenance
- **outcomes**: Collaboration results
- **learning_signals**: Data for improving matching

All stored in `./substrate_data/substrate.db`

## Development Workflow

### 1. Start Development Server
```bash
./run_api_server.sh
```

The server will auto-reload on code changes.

### 2. Test Changes
```bash
# Run integration tests
python test_api_integration.py

# Or test manually with curl/browser
```

### 3. Check Logs
```bash
# API logs are printed to console when running with --reload
# Or check: /tmp/substrate_api.log if running in background
```

## Integration Test

The `test_api_integration.py` script:
1. Creates test user profiles (software, hardware, AI experts)
2. Posts needs from each user
3. Finds matches using semantic AI
4. Verifies complementarity detection
5. Checks statistics tracking
6. Validates complete workflow

Run it to verify the system is working:
```bash
python test_api_integration.py
```

Expected output:
```
✓ API Status: online
✓ Profile created: test_user_software_001
✓ Found 3 matches
✓ Top match score: 0.85
🌟 COMPLEMENTARITY DETECTED!
✓ All tests passed!
```

## Next Steps

### Phase 1: Enhanced Features (Current)
- ✅ REST API implementation
- ✅ Semantic matching
- ✅ Transparency engine
- ✅ Web interface
- ✅ Integration tests

### Phase 2: Advanced Features (Next)
- [ ] WebSocket support for real-time notifications
- [ ] Advanced visualization of match provenance
- [ ] Team optimization (multi-user matching)
- [ ] Outcome prediction models
- [ ] Mobile-responsive design

### Phase 3: Production Ready
- [ ] Authentication and authorization
- [ ] Rate limiting and security
- [ ] Cloud deployment configuration
- [ ] Performance optimization
- [ ] Comprehensive test coverage

## Troubleshooting

### "Module not found" errors
```bash
export PYTHONPATH=/home/user/GerdsenAI-Frontier:$PYTHONPATH
```

### "Cannot connect to API"
- Make sure API server is running on port 8000
- Check: `curl http://localhost:8000/`
- Look for errors in console/logs

### "No matches found"
- Need to create some user profiles first
- Use the Profile tab or API to add profiles
- System needs at least 2 profiles to match

### Database issues
```bash
# Reset database (caution: deletes all data)
rm -rf substrate_data/substrate.db
# Restart API server to recreate
```

## Contributing

The web layer is designed to be extended. Key extension points:
- Add new API endpoints in `substrate/web/backend/api.py`
- Add new UI features in `substrate/web/frontend/index.html`
- Improve matching algorithms in `substrate/cloud/matching/`
- Enhance transparency in `substrate/cloud/transparency/`

## Documentation

- **[README.md](README.md)** - Project overview
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[SUBSTRATE_VISION.md](SUBSTRATE_VISION.md)** - Vision and mission
- **[WEB_LAYER_GUIDE.md](WEB_LAYER_GUIDE.md)** - This file

## Support

For issues or questions:
1. Check this guide
2. Review the integration test script
3. Check API logs
4. Open an issue on GitHub

---

**The web layer makes Substrate accessible to everyone.**

Create a profile. Find a match. Solve a problem. Change the world.
